########## smallest_circle.py ##########

import localsolver
import sys

if len(sys.argv) < 2:
    print("Usage: python smallest_circle.py inputFile [outputFile] [timeLimit]")
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
    nb_points = next(file_it)

    # Point coordinates
    coord_x = [None]*nb_points
    coord_y = [None]*nb_points

    coord_x[0] = next(file_it)
    coord_y[0] = next(file_it)

    # Minimum and maximum value of the coordinates of the points
    min_x = coord_x[0]
    max_x = coord_x[0]
    min_y = coord_y[0]
    max_y = coord_y[0]

    for i in range(1, nb_points):
        coord_x[i] = next(file_it)
        coord_y[i] = next(file_it)
        if coord_x[i] < min_x:
            min_x = coord_x[i]
        else:
            if coord_x[i] > max_x:
                max_x = coord_x[i]
        if coord_y[i] < min_y:
            min_y = coord_y[i]
        else:
            if coord_y[i] > max_y:
                max_y = coord_y[i]

    #
    # Declares the optimization model
    #
    model = ls.model

    # Numerical decisions
    x = model.float(min_x, max_x)
    y = model.float(min_y, max_y)

    # Distance between the origin and the point i
    radius = [(x - coord_x[i])**2 + (y - coord_y[i])**2 for i in range(nb_points)]

    # Minimize the radius r
    r = model.sqrt(model.max(radius))
    model.minimize(r)

    model.close()

    #
    # Parameterizes the solver
    #
    if len(sys.argv) >= 4: ls.param.time_limit = int(sys.argv[3])
    else: ls.param.time_limit = 6

    ls.solve()

    #
    # Writes the solution in a file
    #
    if len(sys.argv) >= 3:
        with open(sys.argv[2], 'w') as f:
            f.write("x=%f\n" % x.value)
            f.write("y=%f\n" % y.value)
            f.write("r=%f\n" % r.value)
