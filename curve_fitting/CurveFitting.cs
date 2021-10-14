/********** CurveFitting.cs **********/

using System;
using System.IO;
using System.Collections.Generic;
using System.Globalization;
using localsolver;

public class CurveFitting : IDisposable
{
    // Number of observations
    int nbObservations;

    // Inputs and Outputs
    double[] inputs;
    double[] outputs;

    // Solver
    LocalSolver localsolver;

    // Decision variables (parameters of the mapping function)
    LSExpression a, b, c, d;

    // Objective (square error)
    LSExpression squareError;

    public CurveFitting()
    {
        localsolver = new LocalSolver();
    }

    // Reads instance data
    void ReadInstance(string fileName)
    {
        using (StreamReader input = new StreamReader(fileName))
        {
            nbObservations = int.Parse(input.ReadLine());
            inputs = new double[nbObservations];
            outputs = new double[nbObservations];

            for (int i = 0; i < nbObservations; i++)
            {
                string[] splittedObs = input.ReadLine().Split(' ');
                inputs[i] = double.Parse(splittedObs[0], CultureInfo.InvariantCulture);
                outputs[i] = double.Parse(splittedObs[1], CultureInfo.InvariantCulture);
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

        // Decision variables
        a = model.Float(-100, 100);
        b = model.Float(-100, 100);
        c = model.Float(-100, 100);
        d = model.Float(-100, 100);

        // Minimize square error
        squareError = model.Sum();
        for (int i = 0; i < nbObservations; i++)
        {
            LSExpression prediction = a * model.Sin(b - inputs[i]) + c * Math.Pow(inputs[i], 2) + d;
            LSExpression error = model.Pow(prediction - outputs[i], 2);
            squareError.AddOperand(error);
        }
        model.Minimize(squareError);
        model.Close();

        // Parameterizes the solver
        localsolver.GetParam().SetTimeLimit(limit);

        localsolver.Solve();
    }

    // Writes the solution in a file
    void WriteSolution(string fileName)
    {
        using (StreamWriter output = new StreamWriter(fileName))
        {
            output.WriteLine("Optimal mapping function");
            output.WriteLine("a = " + a.GetDoubleValue());
            output.WriteLine("b = " + b.GetDoubleValue());
            output.WriteLine("c = " + c.GetDoubleValue());
            output.WriteLine("d = " + d.GetDoubleValue());
        }
    }

    public static void Main(string[] args)
    {
        if (args.Length < 1)
        {
            Console.WriteLine("Usage: CurveFitting inputFile [solFile] [timeLimit]");
            Environment.Exit(1);
        }
        string instanceFile = args[0];
        string outputFile = args.Length > 1 ? args[1] : null;
        string strTimeLimit = args.Length > 2 ? args[2] : "3";

        using (CurveFitting model = new CurveFitting())
        {
            model.ReadInstance(instanceFile);
            model.Solve(int.Parse(strTimeLimit));
            if (outputFile != null)
                model.WriteSolution(outputFile);
        }
    }
}