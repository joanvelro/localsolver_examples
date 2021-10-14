########## pdptw.py ##########

import localsolver
import sys
import math


def read_elem(filename):
    with open(filename) as f:
        return [str(elem) for elem in f.read().split()]


def main(instance_file, str_time_limit, sol_file):

    #
    # Reads instance data
    #
    (nb_customers, nb_trucks, truck_capacity, distance_matrix, distance_warehouses, demands, service_time, earliest_start, latest_end, pickUpIndex, deliveryIndex, max_horizon) = read_input_pdptw(instance_file)


    with localsolver.LocalSolver() as ls:
        #
        # Declares the optimization model
        #
        model = ls.model

        # Sequence of customers visited by each truck
        customers_sequences = [model.list(nb_customers) for k in range(nb_trucks)]

        # All customers must be visited by the trucks
        model.constraint(model.partition(customers_sequences))

        # Create demands, earliest, latest and service as arrays to be able to access it with an "at" operator
        demands_array = model.array(demands)
        earliest_array = model.array(earliest_start)
        latest_array = model.array(latest_end)
        service_array = model.array(service_time)

        # Create distance as an array to be able to acces it with an "at" operator
        distance_array = model.array()
        for n in range(nb_customers):
            distance_array.add_operand(model.array(distance_matrix[n]))
        distance_warehouse_array = model.array(distance_warehouses)

        route_distances = [None] * nb_trucks
        end_time = [None] * nb_trucks
        home_lateness = [None] * nb_trucks
        lateness = [None] * nb_trucks

        # A truck is used if it visits at least one customer
        trucks_used = [(model.count(customers_sequences[k]) > 0) for k in range(nb_trucks)]
        nb_trucks_used = model.sum(trucks_used)

        for k in range(nb_trucks):
            sequence = customers_sequences[k]
            c = model.count(sequence)

            # The quantity needed in each route must not exceed the truck capacity at any point in the sequence
            demand_cumulator = model.lambda_function(lambda i, prev: prev + demands_array[sequence[i]])
            route_quantity = model.array(model.range(0, c), demand_cumulator)

            quantity_checker = model.lambda_function(lambda i: route_quantity[i] <= truck_capacity)
            model.constraint(model.and_(model.range(0, c), quantity_checker))

            # Pickups and deliveries
            for i in range(nb_customers):
                if pickUpIndex[i] == -1:
                    model.constraint(model.contains(sequence, i) == model.contains(sequence, deliveryIndex[i]))
                    model.constraint(model.index(sequence, i) <= model.index(sequence, deliveryIndex[i]))

            # Distance traveled by each truck
            dist_selector = model.lambda_function(lambda i: model.at(distance_array, sequence[i - 1], sequence[i]))
            route_distances[k] = model.sum(model.range(1, c), dist_selector) + \
                 model.iif(c > 0, distance_warehouse_array[sequence[0]] + distance_warehouse_array[sequence[c - 1]], 0)

            # End of each visit
            end_selector = model.lambda_function(lambda i, prev: model.max(earliest_array[sequence[i]], \
                        model.iif(i == 0, \
                                  distance_warehouse_array[sequence[0]], \
                                  prev + model.at(distance_array, sequence[i - 1], sequence[i]))) + \
                        service_array[sequence[i]])

            end_time[k] = model.array(model.range(0, c), end_selector)

            # Arriving home after max_horizon
            home_lateness[k] = model.iif(trucks_used[k], \
               model.max(0, end_time[k][c - 1] + distance_warehouse_array[sequence[c - 1]] - max_horizon), 0)

            # Completing visit after latest_end
            late_selector = model.lambda_function(lambda i:  model.max(0, end_time[k][i] - latest_array[sequence[i]]))
            lateness[k] = home_lateness[k] + model.sum(model.range(0, c), late_selector)



        # Total lateness (must be 0 for the solution to be valid)
        total_lateness = model.sum(lateness)


        # Total distance traveled
        total_distance = model.div(model.round(100 * model.sum(route_distances)), 100)


        # Objective: minimize the number of trucks used, then minimize the distance traveled
        model.minimize(total_lateness)
        model.minimize(nb_trucks_used)
        model.minimize(total_distance)

        model.close()

        #
        # Parameterizes the solver
        #
        ls.param.time_limit = int(str_time_limit)

        ls.solve()

        #
        # Writes the solution in a file with the following format:
        #  - number of trucks used and total distance
        #  - for each truck the nodes visited (omitting the start/end at the depot)
        #
        if len(sys.argv) >= 3:
            with open(sol_file, 'w') as f:
                f.write("%d %.2f\n" % (nb_trucks_used.value, total_distance.value))
                for k in range(nb_trucks):
                    if trucks_used[k].value != 1: continue
                    # Values in sequence are in [0..nbCustomers-1]. +2 is to put it back in [2..nbCustomers+1]
                    # as in the data files (1 being the depot)
                    for customer in customers_sequences[k].value:
                        f.write("%d " % (customer + 2))
                    f.write("\n")


# The input files follow the "Li & Lim" format
def read_input_pdptw(filename):
    file_it = iter(read_elem(sys.argv[1]))

    nb_trucks = int(next(file_it))
    truck_capacity = int(next(file_it))
    speed = int(next(file_it))

    next(file_it)

    warehouse_x = int(next(file_it))
    warehouse_y = int(next(file_it))

    for i in range(2): next(file_it)

    max_horizon = int(next(file_it))

    for i in range(3): next(file_it)

    customers_x = []
    customers_y = []
    demands = []
    earliest_start = []
    latest_end = []
    service_time = []
    pickUpIndex = []
    deliveryIndex = []

    while(1):
        val = next(file_it, None)
        if val is None: break
        i = int(val) - 1
        customers_x.append(int(next(file_it)))
        customers_y.append(int(next(file_it)))
        demands.append(int(next(file_it)))
        ready = int(next(file_it))
        due = int(next(file_it))
        stime = int(next(file_it))
        pick = int(next(file_it))
        delivery = int(next(file_it))
        earliest_start.append(ready)
        latest_end.append(due + stime) # in input files due date is meant as latest start time
        service_time.append(stime)
        pickUpIndex.append(pick - 1)
        deliveryIndex.append(delivery - 1)

    nb_customers = i + 1

    # Computes distance matrix
    distance_matrix = compute_distance_matrix(customers_x, customers_y)
    distance_warehouses = compute_distance_warehouses(warehouse_x, warehouse_y, customers_x, customers_y)

    return (nb_customers, nb_trucks, truck_capacity, distance_matrix, distance_warehouses, demands, service_time, earliest_start, latest_end, pickUpIndex, deliveryIndex, max_horizon)


# Computes the distance matrix
def compute_distance_matrix(customers_x, customers_y):
    nb_customers = len(customers_x)
    distance_matrix = [[None for i in range(nb_customers)] for j in range(nb_customers)]
    for i in range(nb_customers):
        distance_matrix[i][i] = 0
        for j in range(nb_customers):
            dist = compute_dist(customers_x[i], customers_x[j], customers_y[i], customers_y[j])
            distance_matrix[i][j] = dist
            distance_matrix[j][i] = dist
    return distance_matrix


# Computes the distances to the warehouse
def compute_distance_warehouses(depot_x, depot_y, customers_x, customers_y):
    nb_customers = len(customers_x)
    distance_warehouses = [None] * nb_customers
    for i in range(nb_customers):
        dist = compute_dist(depot_x, customers_x[i], depot_y, customers_y[i])
        distance_warehouses[i] = dist
    return distance_warehouses



def compute_dist(xi, xj, yi, yj):
    return math.sqrt(math.pow(xi - xj, 2) + math.pow(yi - yj, 2))


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python pdptw.py input_file [output_file] [time_limit]")
        sys.exit(1)

    instance_file = sys.argv[1]
    sol_file = sys.argv[2] if len(sys.argv) > 2 else None
    str_time_limit = sys.argv[3] if len(sys.argv) > 3 else "20"

    main(instance_file, str_time_limit, sol_file)
