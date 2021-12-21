#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
    The Quadratic Assignment Problem (QAP) is a fundamental combinatorial problem in the branch
    of optimization and operations research. It has emerged from facility location applications
    and models the following real-life problem. You are given a set of n facilities and a set of
    n locations. A distance is specified for each pair of locations, and a flow (or weight) is
    specified for each pair of facilities (e.g. the amount of supplies transported between the pair).
    The problem is to assign each facility to one location with the goal of minimizing the sum of
    the distances multiplied by the corresponding flows. Intuitively, the cost function encourages
    factories with high flows between each other to be placed close together. The problem statement
    resembles that of the assignment problem, except that the cost function is expressed in terms
    of quadratic inequalities, hence the name. For more details, we invite the reader to have a
    look at the QAPLIB webpage.

    Data
    Instance files are from the QAPLIB.

    The format of the data is as follows:

    Number of points
    Matrix A: distance between each location
    Matrix B: flow between each facility

    Program
    Using LocalSolver’s non-linear operators, modeling the problem is really straightforward
    (no linearization required). It is not even necessary to introduce a quadratic number of
    decision variables x[f][l]. Indeed, we are considering a permutation of all facilities,
    which can be modeled directly in LocalSolver with a single list variable. The only constraint
    is for the list to contain all the facilities. As for the objective, it is the sum,
    for each pair of locations (l1,l2), of the product between the distance between l1 and l2
    and the flow between the factory on l1 and the factory on l2. This is written with “at”
    operators that can retrieve a member of an array indexed by an expression (see this page
    for more information about the “at” operator).

    obj <- sum[i in 0..n-1][j in 0..n-1]( A[i][j] * B[p[i]][p[j]]);
    With such a compact model, instances with thousands of points can be tackled with no
    resource issues.

    You can find below this model for each language.
    You can also have a look at a performance comparison of LocalSolver against MIP solvers on
    this Quadratic Assignment Problem.

    linux: export PYTHONPATH=/opt/localsolver_10_0/bin/python
    windows: set PYTHONPATH=%LS_HOME%\bin\python

    linux: python qap.py instances/esc32a.dat results.txt 300
    windows: python qap.py instances\esc32a.dat results.txt 300

"""

import localsolver
import sys


# if len(sys.argv) < 2:
#    print("Usage: python qap.py inputFile [outputFile] [timeLimit]")
#    sys.exit(1)


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
