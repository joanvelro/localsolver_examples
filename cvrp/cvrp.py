########## cvrp.py ##########

import localsolver
import sys
import math


def read_elem(filename):
    with open(filename) as f:
        return [str(elem) for elem in f.read().split()]


def main(instance_file, str_time_limit, sol_file, str_nb_trucks):
    nb_trucks = int(str_nb_trucks)

    #
    # Reads instance data
    #
    (nb_customers, truck_capacity, distance_matrix, distance_warehouses, demands) = read_input_cvrp(instance_file)

    # The number of trucks is usually given in the name of the file
    # nb_trucks can also be given in command line
    if nb_trucks == 0:
        nb_trucks = get_nb_trucks(instance_file)

    with localsolver.LocalSolver() as ls:
        #
        # Declares the optimization model
        #
        model = ls.model

        # Sequence of customers visited by each truck.
        customers_sequences = [model.list(nb_customers) for k in range(nb_trucks)]

        # All customers must be visited by the trucks
        model.constraint(model.partition(customers_sequences))

        # Create demands as an array to be able to access it with an "at" operator
        demands_array = model.array(demands)

        # Create distance as an array to be able to acces it with an "at" operator
        distance_array = model.array()
        for n in range(nb_customers):
            distance_array.add_operand(model.array(distance_matrix[n]))

        distance_warehouse_array = model.array(distance_warehouses)

        route_distances = [None] * nb_trucks

        # A truck is used if it visits at least one customer
        trucks_used = [(model.count(customers_sequences[k]) > 0) for k in range(nb_trucks)]
        nb_trucks_used = model.sum(trucks_used)

        for k in range(nb_trucks):
            sequence = customers_sequences[k]
            c = model.count(sequence)

            # Quantity in each truck
            demand_selector = model.lambda_function(lambda i: demands_array[sequence[i]])
            route_quantity = model.sum(model.range(0, c), demand_selector)
            model.constraint(route_quantity <= truck_capacity)

            # Distance traveled by each truck
            dist_selector = model.lambda_function(lambda i: model.at(distance_array, sequence[i-1], sequence[i]))
            route_distances[k] = model.sum(model.range(1, c), dist_selector) + \
                 model.iif(c > 0, distance_warehouse_array[sequence[0]] + distance_warehouse_array[sequence[c-1]], 0)

        # Total distance traveled
        total_distance = model.sum(route_distances)

        # Objective: minimize the number of trucks used, then minimize the distance traveled
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
                f.write("%d %d\n" % (nb_trucks_used.value, total_distance.value))
                for k in range(nb_trucks):
                    if trucks_used[k].value != 1: continue
                    # Values in sequence are in [0..nbCustomers-1]. +2 is to put it back in [2..nbCustomers+1]
                    # as in the data files (1 being the depot)
                    for customer in customers_sequences[k].value:
                        f.write("%d " % (customer + 2))
                    f.write("\n")


# The input files follow the "Augerat" format.
def read_input_cvrp(filename):
    file_it = iter(read_elem(sys.argv[1]))

    nb_nodes = 0
    while(1):
        token = next(file_it)
        if token == "DIMENSION":
            next(file_it) # Removes the ":"
            nb_nodes = int(next(file_it))
            nb_customers = nb_nodes - 1
        elif token == "CAPACITY":
            next(file_it) # Removes the ":"
            truck_capacity = int(next(file_it))
        elif token == "EDGE_WEIGHT_TYPE":
            next(file_it) # Removes the ":"
            token = next(file_it)
            if token != "EUC_2D":
                print("Edge Weight Type " + token + " is not supported (only EUD_2D)")
                sys.exit(1)
        elif token == "NODE_COORD_SECTION":
            break

    customers_x = [None]*nb_customers
    customers_y = [None]*nb_customers
    depot_x = 0
    depot_y = 0
    for n in range(nb_nodes):
        node_id = int(next(file_it))
        if node_id != n+1:
            print("Unexpected index")
            sys.exit(1)
        if node_id == 1:
            depot_x = int(next(file_it))
            depot_y = int(next(file_it))
        else:
            # -2 because orginal customer indices are in 2..nbNodes
            customers_x[node_id-2] = int(next(file_it))
            customers_y[node_id-2] = int(next(file_it))

    # Compute distance matrix
    distance_matrix = compute_distance_matrix(customers_x, customers_y)
    distance_warehouses = compute_distance_warehouses(depot_x, depot_y, customers_x, customers_y)

    token = next(file_it)
    if token != "DEMAND_SECTION":
        print("Expected token DEMAND_SECTION")
        sys.exit(1)

    demands = [None]*nb_customers
    for n in range(nb_nodes):
        node_id = int(next(file_it))
        if node_id != n+1:
            print("Unexpected index")
            sys.exit(1)
        if node_id == 1:
            if int(next(file_it)) != 0:
                print("Demand for depot should be 0")
                sys.exit(1)
        else:
            # -2 because orginal customer indices are in 2..nbNodes
            demands[node_id-2] = int(next(file_it))

    token = next(file_it)
    if token != "DEPOT_SECTION":
        print("Expected token DEPOT_SECTION")
        sys.exit(1)

    warehouse_id = int(next(file_it))
    if warehouse_id != 1:
        print("Warehouse id is supposed to be 1")
        sys.exit(1)

    end_of_depot_section = int(next(file_it))
    if end_of_depot_section != -1:
        print("Expecting only one warehouse, more than one found")
        sys.exit(1)

    return (nb_customers, truck_capacity, distance_matrix, distance_warehouses, demands)


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


# Computes the distances to warehouse
def compute_distance_warehouses(depot_x, depot_y, customers_x, customers_y):
    nb_customers = len(customers_x)
    distance_warehouses = [None] * nb_customers
    for i in range(nb_customers):
        dist = compute_dist(depot_x, customers_x[i], depot_y, customers_y[i])
        distance_warehouses[i] = dist
    return distance_warehouses



def compute_dist(xi, xj, yi, yj):
    exact_dist = math.sqrt(math.pow(xi - xj, 2) + math.pow(yi - yj, 2))
    return int(math.floor(exact_dist + 0.5))


def get_nb_trucks(filename):
    begin = filename.rfind("-k")
    if begin != -1:
        begin += 2
        end = filename.find(".", begin)
        return int(filename[begin:end])
    print("Error: nb_trucks could not be read from the file name. Enter it from the command line")
    sys.exit(1)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python cvrp.py input_file [output_file] [time_limit] [nb_trucks]")
        sys.exit(1)

    instance_file = sys.argv[1]
    sol_file = sys.argv[2] if len(sys.argv) > 2 else None
    str_time_limit = sys.argv[3] if len(sys.argv) > 3 else "20"
    str_nb_trucks = sys.argv[4] if len(sys.argv) > 4 else "0"

    main(instance_file, str_time_limit, sol_file, str_nb_trucks)
