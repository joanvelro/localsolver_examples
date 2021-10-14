########## car_sequencing.py ##########

import localsolver
import sys

if len(sys.argv) < 2:
    print("Usage: python car_sequencing.py inputFile [outputFile] [timeLimit]")
    sys.exit(1)


def read_integers(filename):
    with open(filename) as f:
        return [int(elem) for elem in f.read().split()]


with localsolver.LocalSolver() as ls:

    #
    # Reads instance data
    #

    file_it = iter(read_integers(sys.argv[1]))
    nb_positions = next(file_it)
    nb_options = next(file_it)
    nb_classes = next(file_it)
    max_cars_per_window = [next(file_it) for i in range(nb_options)]
    window_size = [next(file_it) for i in range(nb_options)]
    nb_cars = []
    options = []

    for c in range(nb_classes):
        next(file_it)
        nb_cars.append(next(file_it))
        options.append([next(file_it) == 1 for i in range(nb_options)])

    #
    # Declares the optimization model
    #
    model = ls.model

    # class_on_pos[c][p] = 1 if class c is at position p, and 0 otherwise
    class_on_pos = [[model.bool() for j in range(nb_positions)] for i in range(nb_classes)]

    # All cars of class c are assigned to positions
    for c in range(nb_classes):
        model.constraint(model.sum(class_on_pos[c][p] for p in range(nb_positions)) == nb_cars[c])

    # One car assigned to each position p
    for p in range(nb_positions):
        model.constraint(model.sum(class_on_pos[c][p] for c in range(nb_classes)) == 1)

    # options_on_pos[o][p] = 1 if option o appears at position p, and 0 otherwise
    options_on_pos = [None]*nb_options
    for o in range(nb_options):
        options_on_pos[o] = [None]*nb_positions
        for p in range(nb_positions):
            options_on_pos[o][p] = model.or_(class_on_pos[c][p] for c in range(nb_classes) if options[c][o])

    # Number of cars with option o in each window
    nb_cars_windows = [None]*nb_options
    for o in range(nb_options):
        nb_cars_windows[o] = [None]*nb_positions
        for p in range(nb_positions - window_size[o] + 1):
            nb_cars_windows[o][p] = model.sum(options_on_pos[o][p + k] for k in range(window_size[o]))

    # Number of violations of option o capacity in each window
    nb_violations_windows = [None]*nb_options
    for o in range(nb_options):
        nb_violations_windows[o] = [None]*nb_positions
        for p in range(nb_positions - window_size[o] + 1):
            nb_violations_windows[o][p] = model.max(nb_cars_windows[o][p] - max_cars_per_window[o], 0)

    # Minimize the sum of violations for all options and all windows
    total_violations = model.sum(nb_violations_windows[o][p] for p in range(nb_positions - window_size[o] + 1) for o in range(nb_options))
    model.minimize(total_violations)

    model.close()

    #
    # Parameterizes the solver
    #
    if len(sys.argv) >= 4: ls.param.time_limit = int(sys.argv[3])
    else: ls.param.time_limit = 60

    ls.solve()

    #
    # Writes the solution in a file
    #
    if len(sys.argv) >= 3:
        # Writes the solution in a file following the following format:
        # * 1st line: value of the objective;
        # * 2nd line: for each position p, index of class at positions p.
        with open(sys.argv[2], 'w') as f:
            f.write("%d\n" % total_violations.value)
            for p in range(nb_positions):
                for c in range(nb_classes):
                    if class_on_pos[c][p].value == 1:
                        f.write("%d " % c)
                        break

            f.write("\n")
