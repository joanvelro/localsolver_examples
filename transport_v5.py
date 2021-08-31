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

    * multiproduct
    * freights depends on products
    * multiperiod
    + demand change over periods

    Keywords: linear programming, transportation problem, scheduling

"""

import localsolver
from timeit import default_timer as timer
import pandas

# start time


start = timer()

with localsolver.LocalSolver() as ls:
    #
    # Declares the optimization model
    #
    model = ls.model

    # Sets
    # plants
    plants = ['factory-A', 'factory-B']
    # markets
    markets = ['market-1', 'market-2', 'market-3']
    # periods
    periods = ['T1', 'T2', 'T3']
    # products
    products = ['product-X', 'product-Y', 'product-Z']

    # ::: Parameters :::

    # capacity of plants
    capacity = {('factory-A', 'product-X'): 500,
                ('factory-A', 'product-Y'): 500,
                ('factory-A', 'product-Z'): 500,
                ('factory-B', 'product-X'): 500,
                ('factory-B', 'product-Y'): 500,
                ('factory-B', 'product-Z'): 500}

    # demand at markets
    demand = {('market-1', 'T1', 'product-X'): 20,
              ('market-1', 'T2', 'product-X'): 30,
              ('market-1', 'T3', 'product-X'): 0,
              ('market-1', 'T1', 'product-Y'): 60,
              ('market-1', 'T2', 'product-Y'): 45,
              ('market-1', 'T3', 'product-Y'): 5,
              ('market-1', 'T1', 'product-Z'): 0,
              ('market-1', 'T2', 'product-Z'): 25,
              ('market-1', 'T3', 'product-Z'): 55,
              ('market-2', 'T1', 'product-X'): 45,
              ('market-2', 'T2', 'product-X'): 50,
              ('market-2', 'T3', 'product-X'): 30,
              ('market-2', 'T1', 'product-Y'): 15,
              ('market-2', 'T2', 'product-Y'): 25,
              ('market-2', 'T3', 'product-Y'): 30,
              ('market-2', 'T1', 'product-Z'): 45,
              ('market-2', 'T2', 'product-Z'): 40,
              ('market-2', 'T3', 'product-Z'): 75,
              ('market-3', 'T1', 'product-X'): 45,
              ('market-3', 'T2', 'product-X'): 40,
              ('market-3', 'T3', 'product-X'): 30,
              ('market-3', 'T1', 'product-Y'): 45,
              ('market-3', 'T2', 'product-Y'): 45,
              ('market-3', 'T3', 'product-Y'): 45,
              ('market-3', 'T1', 'product-Z'): 30,
              ('market-3', 'T2', 'product-Z'): 35,
              ('market-3', 'T3', 'product-Z'): 90,
              }

    # distance in  miles
    distances = {('factory-A', 'market-1'): 2500,
                 ('factory-A', 'market-2'): 1700,
                 ('factory-A', 'market-3'): 1800,
                 ('factory-B', 'market-1'): 2500,
                 ('factory-B', 'market-2'): 1800,
                 ('factory-B', 'market-3'): 1400
                 }

    # transport cost in $/mile-ud from the plants
    freights = {('factory-A', 'product-X'): 95 / 1000,
                ('factory-A', 'product-Y'): 75 / 1000,
                ('factory-A', 'product-Z'): 115 / 1000,
                ('factory-B', 'product-X'): 85 / 1000,
                ('factory-B', 'product-Y'): 65 / 1000,
                ('factory-B', 'product-Z'): 145 / 1000}

    # =================
    # ::: Variables :::
    # =================

    # shipment quantities x(i,j,t,p)
    x_max = 1000
    try:
        x = [[[[model.int(0, x_max) for i in range(len(plants))] for j in range(len(markets))] for t in range(len(periods))] for p in range(len(products))]
    except Exception as exception_msg:
        print('----> (!) Error in defining decision variable: {}'.format(str(exception_msg)))

    # ====================
    # ::: Constraints :::
    # ====================

    # supply capacity
    if 1 == 1:
        try:
            for i in range(0, len(plants)):
                for p in range(0, len(products)):
                    model.constraint(model.sum(x[p][t][j][i] for j in range(len(markets)) for t in range(len(periods))) <= capacity[(plants[i], products[p])])
        except Exception as exception_msg:
            print('----> (!) Error in capacity constraint: {}'.format(str(exception_msg)))

    # demand
    if 1 == 1:
        try:
            for j in range(0, len(markets)):
                for t in range(0, len(periods)):
                    for p in range(0, len(products)):
                        model.constraint(model.sum(x[p][t][j][i] for i in range(0, len(plants))) >= demand[(markets[j], periods[t], products[p])])
        except Exception as exception_msg:
            print('----> (!) Error in demand constraint: {}'.format(str(exception_msg)))



    # ========================
    # ::: Objective function :::
    # ========================
    try:
        OF = model.sum(x[p][t][j][i] * distances[(plants[i], markets[j])] * freights[(plants[i], products[p])]
                       for i in range(len(plants))
                       for j in range(len(markets))
                       for t in range(len(periods))
                       for p in range(len(products))
                       )
    except Exception as exception_msg:
        OF = 0
        print('----> (!) Error in objective function: {}'.format(str(exception_msg)))

    model.minimize(OF)

    model.close()

    # ::: model params :::

    # ls.param.time_limit = 5
    ls.param.iteration_limit = 300000

    # vervosity
    ls.param.verbosity = 1

    # ::: Solve model :::
    ls.solve()

    # ::: get solution  :::
    x_sol = {(plants[i], markets[j], periods[t], products[p]): x[p][t][j][i].value
             for i in range(0, len(plants))
             for j in range(0, len(markets))
             for t in range(0, len(periods))
             for p in range(0, len(products))
             }
    total_cost = round(OF.value)
    total_demand = sum([demand[(i, t, p)] for i, t, p in demand.keys()])
    total_supply = sum([x_sol[(i, j, t, p)] for i, j, t, p in x_sol.keys()])
    print('Total cost: {} $'.format(total_cost))
    print('Total demand: {} ud'.format(total_demand))
    print('Total supply: {} ud'.format(total_supply))
    print('Marginal cost: {} $/ud'.format(round(total_cost / total_supply, 2)))
    print('Optimal solution')
    for i, j, t, p in x_sol.keys():
        print(' {}--{}--{}--{} : {} Tm'.format(i, j, t, p, x_sol[(i, j, t, p)]))

end = timer()
print('\nExecution time: {} s'.format(round(end - start, 4)))

# create dataframe results
results = pandas.DataFrame.from_dict(data=x_sol, orient='index')
results.reset_index(inplace=True)
results['plant'] = 0
results['market'] = 0
results['period'] = 0
results['product'] = 0
results['plant'] = results['index'].apply(lambda x: x[0])
results['market'] = results['index'].apply(lambda x: x[1])
results['period'] = results['index'].apply(lambda x: x[2])
results['product'] = results['index'].apply(lambda x: x[3])
results.rename(columns={0: 'quantity'}, inplace=True)
results.drop(columns=['index'], inplace=True)
results.sort_values(by=['plant', 'market', 'period'], ascending=True, inplace=True)
