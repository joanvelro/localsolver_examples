#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
   Simple Transport problem

   This problem finds a least cost shipping schedule that meets
    requirements at markets and supplies at factories.


    Dantzig, G B, Chapter 3.3. In Linear Programming and Extensions.
    Princeton University Press, Princeton, New Jersey, 1963.

    This formulation is described in detail in:
    Rosenthal, R E, Chapter 2: A GAMS Tutorial. In GAMS: A User's Guide.
    The Scientific Press, Redwood City, California, 1988.

    The line numbers will not match those in the book because of these
    comments.

    * Single product
    * single freight

    Keywords: linear programming, transportation problem, scheduling

"""

import localsolver
from timeit import default_timer as timer

# start time


# Sets
# plants
plants = ['seatle', 'san-diego']
# markets
markets = ['new-york', 'chicago', 'topeka']

# ::: Parameters :::

# capacity of plants
capacity = {'seatle': 350,
            'san-diego': 600}

# demand at markets
demand = {'new-york': 325,
          'chicago': 200,
          'topeka': 375}

# distance in  miles
distances = {('seatle', 'new-york'): 2500,
             ('seatle', 'chicago'): 1700,
             ('seatle', 'topeka'): 1800,
             ('san-diego', 'new-york'): 2500,
             ('san-diego', 'chicago'): 1800,
             ('san-diego', 'topeka'): 1400
             }

freight = 90  # freight in dollars per case per thousand miles $/1000 miles


start = timer()

with localsolver.LocalSolver() as ls:
    #
    # Declares the optimization model
    #
    model = ls.model

    # transport cost in $/ s
    costs = distances
    for key in costs:
        costs[key] = int(costs.get(key) * freight / 1000)

    # =================
    # ::: Variables :::
    # =================

    # shipment quantities in cases
    x_max = 1000000
    x = [[model.int(0, x_max) for i in range(len(plants))] for j in range(len(markets))]

    # ====================
    # ::: Constraints :::
    # ====================

    # # Not surpass capacity

    try:
        for i in range(0, len(plants)):
            model.constraint(model.sum(x[j][i] for j in range(len(markets))) <= capacity[plants[i]])
    except Exception as exception_msg:
        print('----> (!) Error in capacity constraint: {}'.format(str(exception_msg)))

    # demand

    try:
        for j in range(0, len(markets)):
            model.constraint(model.sum(x[j][i] for i in range(len(plants))) >= demand[markets[j]])
    except Exception as exception_msg:
        print('----> (!) Error in demand constraint: {}'.format(str(exception_msg)))

    # ========================
    # ::: Objective function :::
    # ========================
    try:
        OF = model.sum(x[j][i] * costs[(plants[i], markets[j])] for i in range(len(plants)) for j in range(len(markets)))
    except Exception as exception_msg:
        OF = 0
        print('----> (!) Error in objective function: {}'.format(str(exception_msg)))

    model.minimize(OF)

    model.close()

    initialization = True

    if initialization:
        x[0][0].value = 1456
        x[1][0].value = 1
        x[2][0].value = 16589

    # ::: model params :::

    # ls.param.time_limit = 5
    ls.param.iteration_limit = 300000

    # vervosity
    ls.param.verbosity = 1

    # ::: Solve model :::
    ls.solve()

    # ::: get solution  :::
    x_sol = {(plants[i], markets[j]): x[j][i].value for i in range(0, len(plants)) for j in range(0, len(markets))}
    total_cost = OF.value
    print('Total cost: {} $'.format(total_cost))
    print('Optimal solution')
    for i, j in x_sol.keys():
        print(' {}--{} : {} Tm'.format(i, j, x_sol[(i, j)]))


end = timer()
print('\nExecution time: {} s'.format(round(end - start, 4)))