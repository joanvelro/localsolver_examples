/********** Knapsack.cs **********/

using System;
using System.IO;
using System.Collections.Generic;
using localsolver;

public class Knapsack : IDisposable
{
    // Number of items
    int nbItems;

    // Items properties. 
    int[] weights;
    int[] values;

    // Knapsack bound.
    int knapsackBound;

    // Solver. 
    LocalSolver localsolver;

    // LS Program variables. 
    LSExpression[] x;

    // Objective.
    LSExpression knapsackValue;

    // Solutions    (items in the knapsack). 
    List<int> solutions;

    public Knapsack()
    {
        localsolver = new LocalSolver();
    }

    // Reads instance data.
    void ReadInstance(string fileName)
    {
        using (StreamReader input = new StreamReader(fileName))
        {
            nbItems = int.Parse(input.ReadLine());
            weights = new int[nbItems];
            values = new int[nbItems];

            string[] splittedWeights = input.ReadLine().Split(' ');
            if (splittedWeights.Length < nbItems)
                throw new Exception("Wrong number of item weights");

            for (int i = 0; i < nbItems; i++)
                weights[i] = int.Parse(splittedWeights[i]);

            string[] splittedValues = input.ReadLine().Split(' ');
            if (splittedValues.Length < nbItems)
                throw new Exception("Wrong number of item values");

            for (int i = 0; i < nbItems; i++)
                values[i] = int.Parse(splittedValues[i]);

            knapsackBound = int.Parse(input.ReadLine());
        }
    }

    public void Dispose()
    {
        if (localsolver != null)
            localsolver.Dispose();
    }

    void Solve(int limit)
    {
        // Declares the optimization model.
        LSModel model = localsolver.GetModel();

        // Decision variables x[i]
        x = new LSExpression[nbItems];
        for (int i = 0; i < nbItems; i++)
        {
            x[i] = model.Bool();
        }

        // weight constraint
        LSExpression knapsackWeight = model.Sum();
        for (int i = 0; i < nbItems; i++)
        {
            knapsackWeight.AddOperand(x[i] * weights[i]);
        }
        model.Constraint(knapsackWeight <= knapsackBound);

        // maximize value
        knapsackValue = model.Sum();
        for (int i = 0; i < nbItems; i++)
        {
            knapsackValue.AddOperand(x[i] * values[i]);
        }

        model.Maximize(knapsackValue);
        model.Close();

        // Parameterizes the solver.
        localsolver.GetParam().SetTimeLimit(limit);

        localsolver.Solve();

        solutions = new List<int>();
        for (int i = 0; i < nbItems; ++i)
        {
            if (x[i].GetValue() == 1) solutions.Add(i);
        }
    }

    // Writes the solution in a file
    void WriteSolution(string fileName)
    {
        using (StreamWriter output = new StreamWriter(fileName))
        {
            output.WriteLine(knapsackValue.GetValue());
            for (int i = 0; i < solutions.Count; ++i)
                output.Write(solutions[i] + " ");
            output.WriteLine();
        }
    }

    public static void Main(string[] args)
    {
        if (args.Length < 1)
        {
            Console.WriteLine("Usage: Knapsack inputFile [solFile] [timeLimit]");
            Environment.Exit(1);
        }
        string instanceFile = args[0];
        string outputFile = args.Length > 1 ? args[1] : null;
        string strTimeLimit = args.Length > 2 ? args[2] : "20";

        using (Knapsack model = new Knapsack())
        {
            model.ReadInstance(instanceFile);
            model.Solve(int.Parse(strTimeLimit));
            if (outputFile != null)
                model.WriteSolution(outputFile);
        }
    }
}
