#!/usr/bin/python
# -*- coding: utf-8 -*-


import localsolver


def read_integers(filename):
    with open(filename) as f:
        return [int(elem) for elem in f.read().split()]


def main(instance_file, results_file):
    with localsolver.LocalSolver() as ls:
        #
        # Reads instance data
        #

        file_it = iter(read_integers(instance_file))

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

        # Permutation such that p[i] is the facility on the location i #
        # Creates a list decision with the given length. A list is an ordered
        # collection of integers within a domain [0, n-1].
        p = model.list(n)


        # The list must be complete
        model.constraint(model.eq(model.count(p), n))

        # Create B as an array to be accessed by an at operator
        array_B = model.array(model.array(B[i]) for i in range(n))

        # Minimize the sum of product distance*flow
        obj = model.sum(A[i][j] * model.at(array_B, p[i], p[j]) for j in range(n) for i in range(n))
        model.minimize(obj)

        model.close()

        #
        # Parameterizes the solver
        #

        ls.param.time_limit = 300
        ls.solve()

        #
        # Writes the solution in a file with the following format:
        #  - n objValue
        #  - permutation p
        #

        with open(results_file, 'w') as outfile:
            outfile.write("%d objective value:%d\n" % (n, obj.value))
            for i in range(n):
                outfile.write("%i :d- value:%d " % (i, p.value[i]))
            outfile.write("\n")


if __name__ == '__main__':
    main(instance_file='instances//esc32a.dat',
         results_file='results.txt')
