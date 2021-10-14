########## tsp.py ##########

import localsolver
import sys

if len(sys.argv) < 2:
    print("Usage: python tsp.py inputFile [outputFile] [timeLimit]")
    sys.exit(1)


def read_elem(filename):
    with open(filename) as f:
        return [str(elem) for elem in f.read().split()]


with localsolver.LocalSolver() as ls:

    #
    # Reads instance data
    #

    file_it = iter(read_elem(sys.argv[1]))

    # The input files follow the TSPLib "explicit" format.
    for pch in file_it:
        if pch == "DIMENSION:":
            nb_cities = int(next(file_it))
        if pch == "EDGE_WEIGHT_SECTION":
            break

    # Distance from i to j
    distance_weight = [[int(next(file_it)) for i in range(nb_cities)] for j in range(nb_cities)]

    #
    # Declares the optimization model
    #
    model = ls.model

    # A list variable: cities[i] is the index of the ith city in the tour
    cities = model.list(nb_cities)

    # All cities must be visited
    model.constraint(model.count(cities) == nb_cities)

    # Create a LocalSolver array for the distance matrix in order to be able to
    # access it with "at" operators.
    distance_array = model.array(distance_weight)

    # Minimize the total distance
    dist_selector = model.lambda_function(lambda i: model.at(distance_array, cities[i-1], cities[i]))
    obj = (model.sum(model.range(1, nb_cities), dist_selector)
            + model.at(distance_array, cities[nb_cities - 1], cities[0]))
    model.minimize(obj)

    model.close()

    #
    # Parameterizes the solver
    #
    if len(sys.argv) >= 4: ls.param.time_limit = int(sys.argv[3])
    else: ls.param.time_limit = 5

    ls.solve()

    #
    # Writes the solution in a file
    #
    if len(sys.argv) >= 3:
        # Writes the solution in a file
        with open(sys.argv[2], 'w') as f:
            f.write("%d\n" % obj.value)
            for c in cities.value:
                f.write("%d " % c)
            f.write("\n")
