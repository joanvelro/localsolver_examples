/********** Facilitylocation.cs **********/

using System;
using System.IO;
using System.Collections.Generic;
using localsolver;

public class Facilitylocation : IDisposable
{
    // Number of locations
    int N;

    // Number of edges between locations
    int E;

    // Size of the subset S of facilities
    int p;

    // Weight matrix of the shortest path beween locations
    int[][] w;

    // Maximum distance between two locations
    int wmax;

    // LocalSolver
    LocalSolver localsolver;

    // Decision variables
    LSExpression[] x;

    // Objective
    LSExpression totalCost;

    // List of facilities
    List<int> solution;

    public Facilitylocation()
    {
        localsolver = new LocalSolver();
    }

    // Reads instance data
    public void ReadInstance(string fileName)
    {
        using (StreamReader input = new StreamReader(fileName))
        {
            var tokens = input.ReadLine().Split(' ');
            N = int.Parse(tokens[0]);
            E = int.Parse(tokens[1]);
            p = int.Parse(tokens[2]);

            w = new int[N][];

            wmax = 0;

            for (int i = 0; i < N; i++)
            {
                tokens = input.ReadLine().Split(' ');
                w[i] = new int[N];
                for (int j = 0; j < N; j++)
                {
                    w[i][j] = int.Parse(tokens[j]);
                    if (w[i][j] > wmax)
                        wmax = w[i][j];
                }
            }
        }
    }

    public void Dispose()
    {
        if (localsolver != null)
            localsolver.Dispose();
    }

    // Declares the optimization model
    public void Solve(int limit)
    {
        localsolver = new LocalSolver();
        LSModel model = localsolver.GetModel();
        x = new LSExpression[N];

        // One variable for each location : 1 if facility, 0 otherwise
        for (int i = 0; i < N; i++)
            x[i] = model.Bool();

        // No more than p locations are selected to be facilities
        LSExpression openedLocations = model.Sum(x);
        model.Constraint(openedLocations <= p);

        // Costs between location i and j is w[i][j] if j is a facility or 2*wmax if not
        LSExpression[][] costs = new LSExpression[N][];
        for (int i = 0; i < N; i++)
        {
            costs[i] = new LSExpression[N]; 
            for (int j = 0; j < N; j++)
            {
                costs[i][j] = model.If(x[j], w[i][j], 2 * wmax);
            }
        }

        // Cost between location i and the closest facility
        LSExpression[] cost = new LSExpression[N];
        for (int i = 0; i < N; i++)
            cost[i] = model.Min(costs[i]);

        // Minimize the total cost.
        totalCost = model.Sum(cost);
        model.Minimize(totalCost);

        model.Close();

        // Parameterizes the solver
        localsolver.GetParam().SetTimeLimit(limit);
        localsolver.Solve();

        solution = new List<int>();
        for (int i = 0; i < N; i++)
            if (x[i].GetValue() == 1)
                solution.Add(i);
    }

    // Writes the solution in a file following the following format: 
    // - value of the objective
    // - indices of the facilities (between 0 and N-1)
    public void WriteSolution(string fileName)
    {
        using (StreamWriter output = new StreamWriter(fileName))
        {
            output.WriteLine(totalCost.GetValue());
            for (int i = 0; i < solution.Count; ++i)
                output.Write(solution[i] + " ");
            output.WriteLine();
        }
    }

    public static void Main(string[] args)
    {
        if (args.Length < 1)
        {
            Console.WriteLine("Usage: Facilitylocation inputFile [outputFile] [timeLimit]");
            Environment.Exit(1);
        }
        string instanceFile = args[0];
        string outputFile = args.Length > 1 ? args[1] : null;
        string strTimeLimit = args.Length > 2 ? args[2] : "20";

        using (Facilitylocation model = new Facilitylocation())
        {
            model.ReadInstance(instanceFile);
            model.Solve(int.Parse(strTimeLimit));
            if (outputFile != null)
                model.WriteSolution(outputFile);
        }
    }
}
