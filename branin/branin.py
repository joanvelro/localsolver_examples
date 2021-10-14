########## branin.py ##########

import localsolver
import sys

with localsolver.LocalSolver() as ls:

    # Parameters of the function
    PI = 3.14159265359
    a = 1
    b = 5.1/(4*pow(PI, 2))
    c = 5/PI
    r = 6
    s = 10
    t = 1/(8*PI)

    #
    # Declares the optimization model
    #
    model = ls.model

    # Numerical decisions
    x1 = model.float(-5.0, 10.0)
    x2 = model.float(0.0, 15.0)

    # f = a(x2 - b*x1^2 + c*x1 - r)^2 + s(1-t)cos(x1) + s
    f = a*(x2 - b*x1**2 + c*x1 - r)**2 + s*(1-t)*model.cos(x1) + s

    # Minimize f
    model.minimize(f)

    model.close()

    #
    # Parameterizes the solver
    #
    if len(sys.argv) >= 3: ls.param.time_limit = int(sys.argv[2])
    else: ls.param.time_limit = 6

    ls.solve()

    #
    # Writes the solution in a file
    #
    if len(sys.argv) >= 2:
        with open(sys.argv[1], 'w') as f:
            f.write("x1=%f\n" % x1.value)
            f.write("x2=%f\n" % x2.value)
