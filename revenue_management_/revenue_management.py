#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
    Revenue management

    A businessman wants to maximize the income from the sale of a product over a certain
    time horizon, split into several periods. At the beginning of the time horizon,
    he has to decide the total amount of product to buy. Then in each period he has
    to choose the number of units to sell, provided that the total number of units sold
    during the time horizon does not exceed the initial amount purchased. The price
    of the product increases over the periods, this means the businessman has to
    determine the number of units to reserve for customers who arrive later, because
    they will pay more. The later demand must therefore be considered to make a wise
    decision at each period. Since the demand for the product is stochastic, the
    businessman simulates each repartition of units a large number of times
    to get a robust estimate of his income.

    Program
    Parameters are fixed to the recommended values: 3 periods are used and the initial
    cost of the product is set to $80.

    The demand at each period t is defined by: D=μXY, where:

        Y has an exponential distribution with a rate parameter λ=1.
        X has a gamma distribution with a shape parameter k=1 and a scale parameter θ=1,
           which is equivalent to the standard exponential distribution.
        μ is the mean demand for this period.

    The distributions are implemented in each language.
    The prices and mean demands at each period are in the table below:

    Period    	1	2	3
    Price	    100	300	400
    Mean demand	50	20	30

    To have a robust estimate of the income, the simulation is realized a large number of times
    (1.000.000) using a Monte Carlo method. Each simulation takes several seconds to run,
    that’s why the next point to be evaluated has to be wisely chosen. A black-box function
    is thus used to compute the average income from the simulations.

    Three integer decision variables are declared. The first one corresponds to the initial
    quantity purchased at the beginning of the time horizon. The second determines the amount
    of product that has to be reserved for periods 2 and 3, and the third the amount of product
    available for period 3. The domains of these variables are all [0, 100]. To ensure the
    feasibility, each variable is constrained to be lesser or equal than the previous one.

    As the black-box function is provided by the user, LocalSolver cannot compute anything about it.
    It is then useful to parametrize it via the LSBlackBoxContext. In this example, the simulation
    will never return a negative value, because the prices at any periods are above the initial cost,
    and all decision variables are positive. The lower bound of the function is thus set to 0. The
    maximum number of evaluations is set to 30.

    For this simulation, an evaluation point was previously computed and its value was saved: the
    variables [100, 50, 30] generates a mean revenue of 4740.99. This point is added with a
    LSBlackBoxEvaluationPoint to warm start the solver.

    set PYTHONPATH=%LS_HOME%\bin\python
    python revenue_management.py


"""
import localsolver
import sys
import math
import random


class RevenueManagementFunction:

    def __init__(self, seed):
        self.nb_periods = 3
        self.prices = [100, 300, 400]
        self.mean_demands = [50, 20, 30]
        self.purchase_price = 80
        self.evaluated_points = [{
            "point": [100, 50, 30],
            "value": 4740.99
        }]
        self.nb_simulations = int(1e6)
        self.seed = seed

    # Black-box function
    def evaluate(self, argument_values):
        variables = [argument_values.get(i) for i in range(argument_values.count())]
        # Initial quantity purchased
        nb_units_purchased = variables[0]
        # Number of units that should be left for future periods
        nb_units_reserved = variables[1:] + [0]

        # Sets seed for reproducibility
        random.seed(self.seed)
        # Creates distribution
        X = [gamma_sample() for i in range(self.nb_simulations)]
        Y = [[exponential_sample() for i in range(self.nb_periods)]
             for j in range(self.nb_simulations)]

        # Runs simulations
        sum_profit = 0.0
        for i in range(self.nb_simulations):
            remaining_capacity = nb_units_purchased
            for j in range(self.nb_periods):
                # Generates demand for period j
                demand_j = int(self.mean_demands[j] * X[i] * Y[i][j])
                nb_units_sold = min(max(remaining_capacity - nb_units_reserved[j], 0),
                                    demand_j)
                remaining_capacity = remaining_capacity - nb_units_sold
                sum_profit += self.prices[j] * nb_units_sold

        # Calculates mean revenue
        mean_profit = sum_profit / self.nb_simulations
        mean_revenue = mean_profit - self.purchase_price * nb_units_purchased

        return mean_revenue


def exponential_sample(rate_param=1.0):
    u = random.random()
    return math.log(1 - u) / (-rate_param)


def gamma_sample(scale_param=1.0):
    return exponential_sample(scale_param)


def solve(evaluation_limit, time_limit, output_file):
    with localsolver.LocalSolver() as ls:
        model = ls.model

        # Generates data
        revenue_management = RevenueManagementFunction(1)
        nb_periods = revenue_management.nb_periods
        # Declares decision variables
        variables = [model.int(0, 100) for i in range(nb_periods)]

        # Creates blackbox function
        func_expr = model.create_double_blackbox_function(revenue_management.evaluate)
        # Calls function
        func_call = model.call(func_expr)
        func_call.add_operands(variables)

        # Declares constraints
        for i in range(1, nb_periods):
            model.constraint(variables[i] <= variables[i - 1])

        # Maximizes function call
        model.maximize(func_call)

        # Sets lower bound
        context = func_expr.blackbox_context
        context.lower_bound = 0.0

        model.close()

        # Parametrizes the solver
        if time_limit is not None:
            ls.param.time_limit = time_limit

        # Sets the maximum number of evaluations
        context.evaluation_limit = evaluation_limit

        # Adds evaluation points
        for evaluated_point in revenue_management.evaluated_points:
            evaluation_point = context.create_evaluation_point()
            for i in range(nb_periods):
                evaluation_point.add_argument(evaluated_point["point"][i])
            evaluation_point.set_return_value(evaluated_point["value"])

        ls.solve()

        # Writes the solution in a file
        if output_file is not None:
            with open(output_file, 'w') as f:
                f.write("obj=%f\n" % func_call.value)
                f.write("b=%f\n" % variables[0].value)
                for i in range(1, nb_periods):
                    f.write("r%f=%f\n" % (i + 1, variables[i].value))


if __name__ == '__main__':
    output_file = 'results'  # sys.argv[1] if len(sys.argv) > 1 else None
    time_limit = 120  # int(sys.argv[2]) if len(sys.argv) > 2 else None
    evaluation_limit = 30 #int(sys.argv[3]) if len(sys.argv) > 3 else 30

    solve(evaluation_limit, time_limit, output_file)
