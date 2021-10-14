########## curve_fitting.py ##########

import localsolver
import sys

if len(sys.argv) < 2:
    print("Usage: python curve_fitting.py inputFile [outputFile] [timeLimit]")
    sys.exit(1)


def read_float(filename):
    with open(filename) as f:
        return [float(elem) for elem in f.read().split()]


with localsolver.LocalSolver() as ls:

    #
    # Reads instance data
    #

    file_it = iter(read_float(sys.argv[1]))

    # Number of observations
    nb_observations = int(next(file_it))

    # Inputs and outputs
    inputs = []
    outputs = []
    for i in range(nb_observations):
        inputs.append(next(file_it))
        outputs.append(next(file_it))

    #
    # Declares the optimization model
    #
    model = ls.model

    # Decision variables : parameters of the mapping function
    a = model.float(-100, 100)
    b = model.float(-100, 100)
    c = model.float(-100, 100)
    d = model.float(-100, 100)

    # Minimize square error bewteen prediction and output
    predictions = [a * model.sin(b - inputs[i]) + c * inputs[i]**2 + d for i in range(nb_observations)]
    errors = [predictions[i] - outputs[i] for i in range(nb_observations)]
    square_error = model.sum(model.pow(errors[i], 2) for i in range(nb_observations))
    model.minimize(square_error)

    model.close()

    #
    # Parameterizes the solver
    #
    if len(sys.argv) >= 4: ls.param.time_limit = int(sys.argv[3])
    else: ls.param.time_limit = 3

    ls.solve()

    #
    # Writes the solution in a file
    #
    if len(sys.argv) >= 3:
        with open(sys.argv[2], 'w') as f:
            f.write("Optimal mapping function\n")
            f.write("a = " + str(a.value) + "\n")
            f.write("b = " + str(b.value) + "\n")
            f.write("c = " + str(c.value) + "\n")
            f.write("d = " + str(d.value) + "\n")
    