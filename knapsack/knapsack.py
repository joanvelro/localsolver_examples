########## knapsack.py ##########

import localsolver
import sys

if len(sys.argv) < 2:
    print("Usage: python knapsack.py inputFile [outputFile] [timeLimit]")
    sys.exit(1)


def read_integers(filename):
    with open(filename) as f:
        return [int(elem) for elem in f.read().split()]


with localsolver.LocalSolver() as ls:

    #
    # Reads instance data
    #

    file_it = iter(read_integers(sys.argv[1]))

    # Number of items
    nb_items = next(file_it)

    # Items properties
    weights = [next(file_it) for i in range(nb_items)]
    values = [next(file_it) for i in range(nb_items)]


    # Knapsack bound
    knapsack_bound = next(file_it)

    #
    # Declares the optimization model
    #
    model = ls.model

    # Decision variables x[i]
    x = [model.bool() for i in range(nb_items)]

    # Weight constraint
    knapsack_weight = model.sum(x[i]*weights[i] for i in range(nb_items))
    model.constraint(knapsack_weight <= knapsack_bound)

    # Maximize value
    knapsack_value = model.sum(x[i]*values[i] for i in range(nb_items))
    model.maximize(knapsack_value)

    model.close()

    #
    # Parameterizes the solver
    #
    if len(sys.argv) >= 4: ls.param.time_limit = int(sys.argv[3])
    else: ls.param.time_limit = 20

    ls.solve()

    #
    # Writes the solution in a file
    #
    if len(sys.argv) >= 3:
        with open(sys.argv[2], 'w') as f:
            f.write("%d\n" % knapsack_value.value)
            for i in range(nb_items):
                if x[i].value != 1: continue
                f.write("%d " % i)
            f.write("\n")
