########## aircraft_landing.py ##########

import localsolver
import sys

def read_elem(filename):
    with open(filename) as f:
        return [str(elem) for elem in f.read().split()]

#
# Read instance data
#
def read_instance(instance_file):
    file_it = iter(read_elem(instance_file))
    nb_planes = int(next(file_it))
    next(file_it) # Skip freezeTime value
    earliest_time = []
    target_time = []
    latest_time = []
    earliness_cost = []
    tardiness_cost = []
    separation_time = []

    for p in range(nb_planes):
        next(file_it) # Skip appearanceTime values
        earliest_time.append(int(next(file_it)))
        target_time.append(int(next(file_it)))
        latest_time.append(int(next(file_it)))
        earliness_cost.append(float(next(file_it)))
        tardiness_cost.append(float(next(file_it)))
        separation_time.append([None] * nb_planes)

        for pp in range(nb_planes):
            separation_time[p][pp] = int(next(file_it))
    return (nb_planes, earliest_time, target_time, latest_time, earliness_cost, tardiness_cost, separation_time)

def get_min_landing_time(p, prev, model, separation_time_array, landing_order):
    return model.iif(p > 0,
                     prev + model.at(separation_time_array, landing_order[p - 1], landing_order[p]),
                     0)

def main(instance_file, output_file, time_limit):
    nb_planes, earliest_time, target_time, latest_time, earliness_cost, tardiness_cost, separation_time = read_instance(instance_file)

    with localsolver.LocalSolver() as ls:
        # Declare the optimization model
        model = ls.model

        # A list variable: landingOrder[i] is the index of the ith plane to land
        landing_order = model.list(nb_planes)

        # All planes must be scheduled
        model.constraint(model.count(landing_order) == nb_planes)

        # Create LocalSolver arrays to be able to access them with an "at" operator
        target_time_array = model.array(target_time)
        latest_time_array = model.array(latest_time)
        earliness_cost_array = model.array(earliness_cost)
        tardiness_cost_array = model.array(tardiness_cost)
        separation_time_array = model.array(separation_time)

        # Int variable: preferred landing time for each plane
        preferred_time = [model.int(earliest_time[p], target_time[p]) for p in range(nb_planes)]
        preferred_time_array = model.array(preferred_time)

        # Landing time for each plane
        landing_time_selector = model.lambda_function(lambda p, prev:
                                model.max(preferred_time_array[landing_order[p]],
                                get_min_landing_time(p, prev, model, separation_time_array, landing_order)))
        landing_time = model.array(model.range(0, nb_planes), landing_time_selector)

        # Landing times must respect the separation time with every previous plane.
        for p in range(1, nb_planes):
            last_separation_end = [landing_time[previous_plane] + model.at(separation_time_array, landing_order[previous_plane], landing_order[p])
                                  for previous_plane in range(p)]
            model.constraint(landing_time[p] >= model.max(last_separation_end))
    
        total_cost = model.sum()
        for p in range(nb_planes):
            plane_index = landing_order[p]

            # Constraint on latest landing time
            model.constraint(landing_time[p] <= latest_time_array[plane_index])

            # Cost for each plane
            difference_to_target_time = abs(landing_time[p] - target_time_array[plane_index])
            unit_cost = earliness_cost_array[plane_index] if landing_time[p] < target_time_array[plane_index] else tardiness_cost_array[plane_index]
            total_cost.add_operand(unit_cost * difference_to_target_time)

        # Minimize the total cost
        model.minimize(total_cost)

        model.close()

        #
        # Parameterize the solver
        #
        if len(sys.argv) >= 4:
            ls.param.time_limit = int(sys.argv[3])
        else:
            ls.param.time_limit = 100

        ls.solve()

        # Write the solution in a file following the following format:
        # - 1st line: value of the objective;
        # - 2nd line: for each position p, index of plane at position p.
        if len(sys.argv) >= 3:
            with open(sys.argv[2], 'w') as f:
                f.write("%d\n" % total_cost.value)
                for p in landing_order.value:
                    f.write("%d " % p)
                f.write("\n")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python aircraft_landing.py instance_file [output_file] [time_limit]")
        sys.exit(1)

    instance_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) >= 3 else None
    time_limit = int(sys.argv[3]) if len(sys.argv) >= 4 else 60
    main(instance_file, output_file, time_limit)
