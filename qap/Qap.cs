/********** Qap.cs **********/

using System;
using System.IO;
using localsolver;

public class Qap : IDisposable
{
    // Number of points
    int n;

    // Distance between locations
    int[][] A;
    // Flow between facilites
    long[][] B;

    // Solver.
    LocalSolver localsolver;

    // LS Program variables
    LSExpression p;

    // Objective
    LSExpression obj;

    public Qap()
    {
        localsolver = new LocalSolver();
    }

    private int readInt(string[] splittedLine, ref int lastPosRead)
    {
        lastPosRead++;
        return int.Parse(splittedLine[lastPosRead]);
    }

    // Reads instance data
    void ReadInstance(string fileName)
    {
        string text = File.ReadAllText(fileName);
        string[] splitted = text.Split((char[])null, StringSplitOptions.RemoveEmptyEntries);
        int lastPosRead = -1;

        n = readInt(splitted, ref lastPosRead);

        A = new int[n][];
        for (int i = 0; i < n; i++)
        {
            A[i] = new int[n];
            for (int j = 0; j < n; j++)
            {
                A[i][j] = readInt(splitted, ref lastPosRead);
            }
        }

        B = new long[n][];
        for (int i = 0; i < n; i++)
        {
            B[i] = new long[n];
            for (int j = 0; j < n; j++)
            {
                B[i][j] = readInt(splitted, ref lastPosRead);
            }
        }
    }

    public void Dispose()
    {
        if (localsolver != null)
            localsolver.Dispose();
    }

    void Solve(int limit)
    {
        // Declares the optimization model
        LSModel model = localsolver.GetModel();

        // Permutation such that p[i] is the facility on the location i
        p = model.List(n);

        // The list must be complete
        model.Constraint(model.Count(p) == n);

        // Create B as an array to be accessed by an at operator
        LSExpression arrayB = model.Array(B);

        // Minimize the sum of product distance*flow
        obj = model.Sum();
        for (int i = 0; i < n; i++)
        {
            for (int j = 0; j < n; j++)
            {
                // arrayB[a, b] is a shortcut for accessing the multi-dimensional array
                // arrayB with an at operator. Same as model.At(arrayB, a, b)
                obj.AddOperand(A[i][j] * arrayB[p[i], p[j]]);
            }
        }
        model.Minimize(obj);

        model.Close();

        // Parameterizes the solver.
        localsolver.GetParam().SetTimeLimit(limit);

        localsolver.Solve();
    }

    // Writes the solution in a file with the following format:
    //  - n objValue
    //  - permutation p
    void WriteSolution(string fileName)
    {
        using (StreamWriter output = new StreamWriter(fileName))
        {
            output.WriteLine(n + " " + obj.GetValue());
            LSCollection pCollection = p.GetCollectionValue();
            for (int i = 0; i < n; i++)
            {
                output.Write(pCollection.Get(i) + " ");
            }
            output.WriteLine();
        }
    }


    public static void Main(string[] args)
    {
        if (args.Length < 1)
        {
            Console.WriteLine("Usage: Qap inputFile [solFile] [timeLimit]");
            Environment.Exit(1);
        }
        string instanceFile = args[0];
        string outputFile = args.Length > 1 ? args[1] : null;
        string strTimeLimit = args.Length > 2 ? args[2] : "300";

        using (Qap model = new Qap())
        {
            model.ReadInstance(instanceFile);
            model.Solve(int.Parse(strTimeLimit));
            if (outputFile != null)
                model.WriteSolution(outputFile);
        }
    }
}
