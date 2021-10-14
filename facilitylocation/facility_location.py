########## facility_location.py ##########

import localsolver
import sys

if len(sys.argv) < 2:
    print("Usage: python facility_location.py inputFile [outputFile] [timeLimit]")
    sys.exit(1)


def read_integers(filename):
    with open(filename) as f:
        return [int(elem) for elem in f.read().split()]


with localsolver.LocalSolver() as ls:

    #
    # Reads instance data
    #

    file_it = iter(read_integers(sys.argv[1]))
    # Number of locations
    N = next(file_it)
    # Number of edges between locations
    E = next(file_it)
    # Size of the subset S of facilities
    p = next(file_it)

    # w: Weight matrix of the shortest path between locations
    # wmax: Maximum distance between two locations
    wmax = 0
    w = [None]*N
    for i in range(N):
        w[i] = [None]*N
        for j in range(N):
            w[i][j] = next(file_it)
            if w[i][j] > wmax:
                wmax = w[i][j]

    #
    # Declares the optimization model
    #
    m = ls.model

    # One variable for each location : 1 if facility, 0 otherwise
    x = [m.bool() for i in range(N)]

    # No more than p locations are selected to be facilities
    opened_locations = m.sum(x[i] for i in range(N))
    m.constraint(opened_locations <= p)

    # Costs between location i and j is w[i][j] if j is a facility or 2*wmax if not
    costs = [None]*N
    for i in range(N):
        costs[i] = [None]*N
        for j in range(N):
            costs[i][j] = m.iif(x[j], w[i][j], 2*wmax)

    # Cost between location i and the closest facility
    cost = [None]*N
    for i in range(N):
        cost[i] = m.min(costs[i][j] for j in range(N))

    # Minimize the total cost
    total_cost = m.sum(cost[i] for i in range(N))
    m.minimize(total_cost)

    m.close()

    #
    # Parameterizes the solver
    #
    if len(sys.argv) >= 4: ls.param.time_limit = int(sys.argv[3])
    else: ls.param.time_limit = 20

    ls.solve()

    #
    # Writes the solution in a file following the following format:
    # - value of the objective
    # - indices of the facilities (between 0 and N-1) */
    #
    if len(sys.argv) >= 3:
        with open(sys.argv[2], 'w') as f:
            f.write("%d\n" % total_cost.value)
            for i in range(N):
                if x[i].value == 1:
                    f.write("%d " % i)
            f.write("\n")
