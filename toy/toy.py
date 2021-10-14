########## toy.py ##########

import localsolver

with localsolver.LocalSolver() as ls:
    weights = [10, 60, 30, 40, 30, 20, 20, 2]
    values = [1, 10, 15, 40, 60, 90, 100, 15]
    knapsack_bound = 102

    #
    # Declares the optimization model
    # 
    model = ls.model

    # 0-1 decisions
    x = [model.bool() for i in range(8)]

    # weight constraint
    knapsack_weight = model.sum(weights[i]*x[i] for i in range(8))
    model.constraint(knapsack_weight <= knapsack_bound)

    # maximize value
    knapsack_value = model.sum(values[i]*x[i] for i in range(8))
    model.maximize(knapsack_value)

    model.close()

    #
    # Parameterizes the solver
    #
    ls.param.time_limit = 10

    ls.solve()

