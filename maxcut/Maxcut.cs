/********** Maxcut.cs **********/

using System;
using System.IO;
using localsolver;

public class Maxcut : IDisposable
{
    // Number of vertices
    int n;

    // Number of edges
    int m;

    // Origin of each edge
    int[] origin;

    // Destination of each edge
    int[] dest;

    // Weight of each edge
    int[] w;

    // Solver
    LocalSolver localsolver;

    // True if vertex x[i] is on the right side of the cut, false if it is on the left side of the cut
    LSExpression[] x;

    // Objective
    LSExpression cutWeight;

    public Maxcut()
    {
        localsolver = new LocalSolver();
    }


    // Reads instance data.
    public void ReadInstance(string fileName)
    {
        using (StreamReader input = new StreamReader(fileName))
        {
            var tokens = input.ReadLine().Split(' ');
            n = int.Parse(tokens[0]);
            m = int.Parse(tokens[1]);

            origin = new int[m];
            dest = new int[m];
            w = new int[m];

            for (int e = 0; e < m; e++)
            {
                tokens = input.ReadLine().Split(' ');
                origin[e] = int.Parse(tokens[0]);
                dest[e] = int.Parse(tokens[1]);
                w[e] = int.Parse(tokens[2]);
            }
        }
    }

    public void Dispose()
    {
        if (localsolver != null)
            localsolver.Dispose();
    }

    public void Solve(int limit)
    {
        // Declares the optimization model.
        LSModel model = localsolver.GetModel();

        // Decision variables x[i]
        x = new LSExpression[n];
        for (int i = 0; i < n; i++)
        {
            x[i] = model.Bool();
        }

        // incut[e] is true if its endpoints are in different class of the partition
        // Note: the indices start at 1 in the instances
        LSExpression[] incut = new LSExpression[m];
        for (int e = 0; e < m; e++)
        {
            incut[e] = model.Neq(x[origin[e] - 1], x[dest[e] - 1]);
        }

        // Size of the cut
        cutWeight = model.Sum();
        for (int e = 0; e < m; e++)
        {
            cutWeight.AddOperand(w[e] * incut[e]);
        }
        model.Maximize(cutWeight);

        model.Close();

        // Parameterizes the solver.
        localsolver.GetParam().SetTimeLimit(limit);
        localsolver.Solve();

    }

    // Writes the solution in a file following the following format: 
    //  - objective value
    //  - each line contains a vertex number and its subset (1 for S, 0 for V-S) */
    public void WriteSolution(string fileName)
    {
        using (StreamWriter output = new StreamWriter(fileName))
        {
            output.WriteLine(cutWeight.GetValue());
            for (int i = 0; i < n; ++i)
                output.WriteLine((i + 1) + " " + x[i].GetValue());
        }
    }

    public static void Main(string[] args)
    {
        if (args.Length < 1)
        {
            Console.WriteLine("Usage: Maxcut inputFile [solFile] [timeLimit]");
            Environment.Exit(1);
        }
        string instanceFile = args[0];
        string outputFile = args.Length > 1 ? args[1] : null;
        string strTimeLimit = args.Length > 2 ? args[2] : "10";

        using (Maxcut model = new Maxcut())
        {
            model.ReadInstance(instanceFile);
            model.Solve(int.Parse(strTimeLimit));
            if (outputFile != null)
                model.WriteSolution(outputFile);
        }
    }
}
