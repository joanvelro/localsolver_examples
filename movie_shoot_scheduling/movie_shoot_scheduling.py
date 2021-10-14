########## movie_shoot_scheduling.py ##########

import traceback

import localsolver
import sys

def read_integers(filename):
    with open(filename) as f:
        return [int(elem) for elem in f.read().split()]

class MssInstance:

    #
    # Read instance data
    #
    def __init__(self, filename):
        file_it = iter(read_integers(filename))
        self.nb_actors = next(file_it)
        self.nb_scenes = next(file_it)
        self.nb_locations = next(file_it)
        self.nb_precedences = next(file_it)
        self.actor_cost = [next(file_it) for i in range(self.nb_actors)]
        self.location_cost = [next(file_it) for i in range(self.nb_locations)]
        self.scene_duration = [next(file_it) for i in range(self.nb_scenes)]
        self.scene_location = [next(file_it) for i in range(self.nb_scenes)]
        self.is_actor_in_scene = [[next(file_it) for i in range(self.nb_scenes)] for i in range(self.nb_actors)]
        self.precedences = [[next(file_it) for i in range(2)] for i in range(self.nb_precedences)]

        self.actor_nb_worked_days = self._compute_nb_worked_days()

    def _compute_nb_worked_days(self):
        actor_nb_worked_days = [0] * self.nb_actors
        for a in range(self.nb_actors):
            for s in range(self.nb_scenes):
                if self.is_actor_in_scene[a][s]:
                    actor_nb_worked_days[a] += self.scene_duration[s]
        return actor_nb_worked_days


def main(instance_file, output_file, time_limit):
    data = MssInstance(instance_file)

    with localsolver.LocalSolver() as ls:
        # Declare the optimization model
        model = ls.model

        # Decision variable: A list, shoot_order[i] is the index of the ith scene to be shot
        shoot_order = model.list(data.nb_scenes)

        # All scenes must be scheduled
        model.constraint(model.count(shoot_order) == data.nb_scenes)

        # Constraint of precedence between scenes
        for i in range(data.nb_precedences):
            model.constraint(model.index(shoot_order, data.precedences[i][0])
                             < model.index(shoot_order, data.precedences[i][1]))

        # Minimize external function
        cost_function = CostFunction(data)
        func = model.create_int_external_function(cost_function.compute_cost)
        func.external_context.lower_bound = 0
        cost = func(shoot_order)
        model.minimize(cost)
        model.close()

        #
        # Parameterize the solver
        #
        ls.param.time_limit = time_limit if len(sys.argv) >= 4 else 20
        ls.solve()

        print(shoot_order.value)

        # Write the solution in a file in the following format:
        # - 1st line: value of the objective;
        # - 2nd line: for each i, the index of the ith scene to be shot.
        if len(sys.argv) >= 3:
            with open(output_file, 'w') as f:
                f.write("%d\n" % cost.value)
                for i in shoot_order.value:
                    f.write("%d " % i)
                f.write("\n")


class CostFunction:

    def __init__(self, data):
        self.data = data

    def compute_cost(self, context):
        shoot_order = context[0]
        if len(shoot_order) < self.data.nb_scenes:
            # Infeasible solution if some shoots are missing
            return sys.maxsize

        location_extra_cost = self._compute_location_cost(shoot_order)
        actor_extra_cost = self._compute_actor_cost(shoot_order)
        return location_extra_cost + actor_extra_cost

    def _compute_location_cost(self, shoot_order):
        nb_location_visits = [0] * self.data.nb_locations
        previous_location = -1
        for i in range(self.data.nb_scenes):
            current_location = self.data.scene_location[shoot_order[i]]
            # When we change location, we increment the number of shoots of the new location
            if previous_location != current_location:
                nb_location_visits[current_location] += 1
                previous_location = current_location
        location_extra_cost = sum(cost * (nb_visits - 1) for cost, nb_visits in zip(self.data.location_cost, nb_location_visits))
        return location_extra_cost

    def _compute_actor_cost(self, shoot_order):
        # Compute first and last days of work for each actor
        actor_first_day = [0] * self.data.nb_actors
        actor_last_day = [0] * self.data.nb_actors
        for j in range(self.data.nb_actors):
            has_actor_started_working = False
            start_day_of_scene = 0
            for i in range(self.data.nb_scenes):
                current_scene = shoot_order[i]
                end_day_of_scene = start_day_of_scene + self.data.scene_duration[current_scene] - 1
                if self.data.is_actor_in_scene[j][current_scene]:
                    actor_last_day[j] = end_day_of_scene
                    if not(has_actor_started_working):
                        has_actor_started_working = True
                        actor_first_day[j] = start_day_of_scene
                # The next scene begins the day after the end of the current one
                start_day_of_scene = end_day_of_scene + 1

        # Compute actor extra cost due to days paid but not worked
        actor_extra_cost = 0
        for j in range(self.data.nb_actors):
            nb_paid_days = actor_last_day[j] - actor_first_day[j] + 1
            actor_extra_cost += (nb_paid_days - self.data.actor_nb_worked_days[j]) * self.data.actor_cost[j]
        return actor_extra_cost



if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python movie_shoot_scheduling.py instance_file [output_file] [time_limit]")
        sys.exit(1)

    instance_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) >= 3 else None
    time_limit = int(sys.argv[3]) if len(sys.argv) >= 4 else 60
    main(instance_file, output_file, time_limit)
