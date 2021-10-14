/********** Toy.java **********/

import localsolver.*;

public class Toy {

    public static void main(String [] args) {
        int[] weights = {10, 60, 30, 40, 30, 20, 20, 2};
        int[] values = {1, 10, 15, 40, 60, 90, 100, 15};

        // Declares the optimization model.        
        final LocalSolver localsolver = new LocalSolver();
        LSModel model = localsolver.getModel();

        // 0-1 decisions
        LSExpression[] x = new LSExpression[8];
        for (int i = 0; i < 8; i++) {
            x[i] = model.boolVar();
        }

        // knapsackWeight <- 10*x0 + 60*x1 + 30*x2 + 40*x3 + 30*x4 + 20*x5 + 20*x6 + 2*x7;
        LSExpression knapsackWeight = model.sum();
        for (int i = 0; i < 8; i++) {
            knapsackWeight.addOperand(model.prod(weights[i], x[i]));
        }

        // knapsackWeight <= 102;
        model.constraint(model.leq(knapsackWeight, 102));

        // knapsackValue <- 1*x0 + 10*x1 + 15*x2 + 40*x3 + 60*x4 + 90*x5 + 100*x6 + 15*x7;
        LSExpression knapsackValue = model.sum();
        for (int i = 0; i < 8; i++) {
            knapsackValue.addOperand(model.prod(values[i], x[i]));
        }

        // maximize knapsackValue;
        model.maximize(knapsackValue);

        // close model, then solve
        model.close();

        // Parameterizes the solver. 
        localsolver.getParam().setTimeLimit(10);
        localsolver.solve();
    }
}

