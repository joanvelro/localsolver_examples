/********** Toy.cs **********/

using localsolver;

public class Toy
{
    public static void Main()
    {
        int[] weights = { 10, 60, 30, 40, 30, 20, 20, 2 };
        int[] values = { 1, 10, 15, 40, 60, 90, 100, 15 };

        using (LocalSolver localsolver = new LocalSolver())
        {
            // Declares the optimization model.
            LSModel model = localsolver.GetModel();

            // 0-1 decisions
            LSExpression[] x = new LSExpression[8];
            for (int i = 0; i < 8; i++)
                x[i] = model.Bool();

            // knapsackWeight <- 10*x0 + 60*x1 + 30*x2 + 40*x3 + 30*x4 + 20*x5 + 20*x6 + 2*x7;
            LSExpression knapsackWeight = model.Sum();
            for (int i = 0; i < 8; i++)
                knapsackWeight.AddOperand(weights[i] * x[i]);

            // knapsackWeight <= 102;    
            model.Constraint(knapsackWeight <= 102);

            // knapsackValue <- 1*x0 + 10*x1 + 15*x2 + 40*x3 + 60*x4 + 90*x5 + 100*x6 + 15*x7;
            LSExpression knapsackValue = model.Sum();
            for (int i = 0; i < 8; i++)
                knapsackValue.AddOperand(values[i] * x[i]);

            // maximize knapsackValue;
            model.Maximize(knapsackValue);

            // close the model before solving it
            model.Close();

            // Parameterizes the solver.
            localsolver.GetParam().SetTimeLimit(10);
            localsolver.Solve();
        }
    }
}

