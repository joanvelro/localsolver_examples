########## hosaki.py ##########

import localsolver
import sys
import math

# Black-box function
def hosaki_function(argument_values):
    x1 = argument_values[0]
    x2 = argument_values[1]
    return ((1 - 8*x1 + 7*pow(x1, 2) - 7*pow(x1, 3)/3 + pow(x1, 4)/4) * pow(x2, 2)
        * math.exp(-x2))

def main(evaluation_limit, output_file):
    with localsolver.LocalSolver() as ls:
        # Declares the optimization model
        model = ls.model

        # Numerical decisions
        x1 = model.float(0, 5)
        x2 = model.float(0, 6)

        # Creates and calls blackbox function
        f = model.create_double_blackbox_function(hosaki_function)
        bb_call = model.call(f, x1, x2)

        # Minimizes function call
        model.minimize(bb_call)
        model.close()

        # Parameterizes the solver
        f.blackbox_context.evaluation_limit = evaluation_limit

        ls.solve()

        # Writes the solution in a file
        if output_file is not None:
            with open(output_file, 'w') as f:
                f.write("obj=%f\n" % bb_call.value)
                f.write("x1=%f\n" % x1.value)
                f.write("x2=%f\n" % x2.value)

if __name__ == '__main__':
    output_file = sys.argv[1] if len(sys.argv) > 1 else None
    evaluation_limit = int(sys.argv[2]) if len(sys.argv) > 2 else 30

    main(evaluation_limit, output_file)
