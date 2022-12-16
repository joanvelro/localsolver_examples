########## tsp.py ##########

import localsolver


def read_elem(filename):
    with open(filename) as f:
        return [str(elem) for elem in f.read().split()]


with localsolver.LocalSolver() as ls:
    #
    # Reads instance data
    #
    file_name = 'instances//rbg443.atsp'
    file_it = iter(read_elem(file_name))

    # The input files follow the TSPLib "explicit" format.
    for pch in file_it:
        if pch == "DIMENSION:":
            nb_cities = int(next(file_it))
        if pch == "EDGE_WEIGHT_SECTION":
            break

    # Distance from i to j
    distance_weight = [[int(next(file_it)) for i in range(nb_cities)] for j in range(nb_cities)]
    print(distance_weight)
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
    print(distance_array)

    # Minimize the total distance
    dist_selector = model.lambda_function(lambda i: model.at(distance_array, cities[i - 1], cities[i]))
    obj = (model.sum(model.range(1, nb_cities), dist_selector)
           + model.at(distance_array, cities[nb_cities - 1], cities[0]))
    model.minimize(obj)

    model.close()

    #
    # Parameterizes the solver
    #
    # if len(sys.argv) >= 4: ls.param.time_limit = int(sys.argv[3])
    # else:

    ls.param.time_limit = 5

    ls.solve()

    print(obj.value)

    for c in cities.value:
        print(c)


