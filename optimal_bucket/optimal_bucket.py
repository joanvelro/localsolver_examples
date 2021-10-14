########## optimal_bucket.py ##########

import localsolver
import sys

with localsolver.LocalSolver() as ls:

    PI = 3.14159265359

    #
    # Declares the optimization model
    #
    m = ls.model

    # Numerical decisions
    R = m.float(0, 1)
    r = m.float(0, 1)
    h = m.float(0, 1)
    
    # Surface must not exceed the surface of the plain disc
    surface = PI*r**2 + PI*(R+r)*m.sqrt((R - r)**2 + h**2)
    m.constraint(surface <= PI)

    # Maximize the volume
    volume = PI*h/3*(R**2 + R*r + r**2)
    m.maximize(volume)

    m.close()

    #
    # Param
    #
    if len(sys.argv) >= 3: ls.param.time_limit = int(sys.argv[2])
    else: ls.param.time_limit = 2

    ls.solve()

    #
    # Writes the solution in a file with the following format:
    #  - surface and volume of the bucket
    #  - values of R, r and h
    #
    if len(sys.argv) >= 2:
        with open(sys.argv[1], 'w') as f:
            f.write("%f %f\n" % (surface.value, volume.value))
            f.write("%f %f %f\n" % (R.value, r.value, h.value))

