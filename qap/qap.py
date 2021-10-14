########## qap.py ##########

import localsolver
import sys

if len(sys.argv) < 2:
    print("Usage: python qap.py inputFile [outputFile] [timeLimit]")
    sys.exit(1)


def read_integers(filename):
    with open(filename) as f:
        return [int(elem) for elem in f.read().split()]


with localsolver.LocalSolver() as ls:

    #
    # Reads instance data
    #

    file_it = iter(read_integers(sys.argv[1]))

    # Number of points
    n = next(file_it)

    # Distance between locations
    A = [[next(file_it) for j in range(n)] for i in range(n)]
    # Flow between factories
    B = [[next(file_it) for j in range(n)] for i in range(n)]

    #
    # Declares the optimization model
    #
    model = ls.model

    # Permutation such that p[i] is the facility on the location i
    p = model.list(n)

    # The list must be complete
    model.constraint(model.eq(model.count(p), n))

    # Create B as an array to be accessed by an at operator
    array_B = model.array(model.array(B[i]) for i in range(n))

    # Minimize the sum of product distance*flow
    obj = model.sum(A[i][j]*model.at(array_B, p[i], p[j]) for j in range(n) for i in range(n))
    model.minimize(obj)

    model.close()

    #
    # Parameterizes the solver
    #
    if len(sys.argv) >= 4: ls.param.time_limit = int(sys.argv[3])
    else: ls.param.time_limit = 300
    ls.solve()

    #
    # Writes the solution in a file with the following format:
    #  - n objValue
    #  - permutation p
    #
    if len(sys.argv) >= 3:
        with open(sys.argv[2], 'w') as outfile:
            outfile.write("%d %d\n" % (n, obj.value))
            for i in range(n):
                outfile.write("%d " % p.value[i])
            outfile.write("\n")
