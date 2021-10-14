########## revenue_management.py ##########

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
            model.constraint(variables[i] <= variables[i-1])

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
                    f.write("r%f=%f\n" % (i+1, variables[i].value))

if __name__ == '__main__':
    output_file = sys.argv[1] if len(sys.argv) > 1 else None
    time_limit = int(sys.argv[2]) if len(sys.argv) > 2 else None
    evaluation_limit = int(sys.argv[3]) if len(sys.argv) > 3 else 30

    solve(evaluation_limit, time_limit, output_file)
