import localsolver
import sys

with localsolver.LocalSolver() as ls:
    tuples = [(1, 2, 8), (9, 10, 11), (50, 100, 0)]

    utilities = [50, 200, 1]
    weights = [5, 10, 1]

    x = {obj: ls.model.float(0, 1) for obj in tuples}

    total_weight = ls.model.sum(x[tuples[i]] * weights[i] for i in range(0, len(tuples)))
    ls.model.constraint(total_weight <= 123.0)

    total_utility = ls.model.sum(x[tuples[i]] * utilities[i] for i in range(0, len(tuples)))
    ls.model.maximize(total_utility)

    ls.model.close()
    ls.solve()

    tupleToPrint = (9, 10, 11)
    print(x[tupleToPrint].get_value())

    for (i, j, k) in tuples:
        print('x[({},{},{})]:{}'.format(i, j, k, x[(i, j, k)].get_value()))
