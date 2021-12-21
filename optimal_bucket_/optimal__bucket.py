#!/usr/bin/python
# -*- coding: utf-8 -*-
"""



"""
import localsolver
import sys


def main(time_limit, file_name):
    with localsolver.LocalSolver() as ls:

        PI = 3.14159265359

        #
        # Declares the optimization model
        #
        m = ls.model

        # After creating the LocalSolver environment LocalSolver(),
        # all the decision variables of the model, are declared with function float()
        # (or also bool(), int(), set(), list()).
        # Numerical decisions
        R = m.float(0, 1)
        r = m.float(0, 1)
        h = m.float(0, 1)

        # Intermediate expressions can be built upon these decision variables by using
        # other operators or functions. For example, in the model above: power (pow),
        # square root (sqrt), less than or equal to (<=)
        # Surface must not exceed the surface of the plain disc
        surface = PI * r ** 2 + PI * (R + r) * m.sqrt((R - r) ** 2 + h ** 2)
        m.constraint(surface <= PI)

        # Many other mathematical operators are available, allowing you to model and solve
        # highly-nonlinear combinatorial optimization problems. The functions constraint or
        # maximize are used for tagging expressions as constrained or maximized.
        # Maximize the volume
        volume = PI * h / 3 * (R ** 2 + R * r + r ** 2)
        m.maximize(volume)

        m.close()

        #
        # Param
        #

        ls.param.time_limit = time_limit

        ls.solve()

        #
        # Writes the solution in a file with the following format:
        #  - surface and volume of the bucket
        #  - values of R, r and h
        #

        with open(file_name, 'w') as f:
            f.write("surface:%f volume:%f\n" % (surface.value, volume.value))
            f.write("R:%f r:%f h:%f\n" % (R.value, r.value, h.value))


if __name__ == '__main__':
    main(time_limit=2, file_name='results.txt')
