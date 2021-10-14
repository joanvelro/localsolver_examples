/********** CarSequencing.cs **********/

using System;
using System.IO;
using localsolver;

public class CarSequencing : IDisposable
{
    // Number of vehicles
    int nbPositions;

    // Number of options. 
    int nbOptions;

    // Number of classes. 
    int nbClasses;

    // Options properties. 
    int[] maxCarsPerWindow;
    int[] windowSize;

    // Classes properties. 
    int[] nbCars;
    bool[][] options;

    // Solver. 
    LocalSolver localsolver;

    // LS Program variables. 
    LSExpression[][] classOnPos;

    // Objective.
    LSExpression totalViolations;

    public CarSequencing()
    {
        localsolver = new LocalSolver();
    }

    // Reads instance data.
    void ReadInstance(string fileName)
    {
        using (StreamReader input = new StreamReader(fileName))
        {
            string[] splitted = input.ReadLine().Split(' ');
            nbPositions = int.Parse(splitted[0]);
            nbOptions = int.Parse(splitted[1]);
            nbClasses = int.Parse(splitted[2]);

            splitted = input.ReadLine().Split(' ');

            maxCarsPerWindow = new int[nbOptions];

            for (int o = 0; o < nbOptions; o++)
                maxCarsPerWindow[o] = int.Parse(splitted[o]);

            splitted = input.ReadLine().Split(' ');

            windowSize = new int[nbOptions];

            for (int o = 0; o < nbOptions; o++)
                windowSize[o] = int.Parse(splitted[o]);

            options = new bool[nbClasses][];
            nbCars = new int[nbClasses];

            for (int c = 0; c < nbClasses; c++)
            {
                splitted = input.ReadLine().Split(' ');
                nbCars[c] = int.Parse(splitted[1]);
                options[c] = new bool[nbOptions];
                for (int o = 0; o < nbOptions; o++)
                {
                    int v = int.Parse(splitted[o + 2]);
                    options[c][o] = (v == 1);
                }
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
        localsolver = new LocalSolver();

        // Declares the optimization model.
        LSModel model = localsolver.GetModel();

        // classOnPos[c][p] = 1 if class c is at position p, and 0 otherwise
        classOnPos = new LSExpression[nbClasses][];
        for (int c = 0; c < nbClasses; c++)
        {
            classOnPos[c] = new LSExpression[nbPositions];
            for (int p = 0; p < nbPositions; p++)
            {
                classOnPos[c][p] = model.Bool();
            }
        }

        // All cars of class c are assigned to positions
        for (int c = 0; c < nbClasses; c++)
        {
            LSExpression nbCarsFromClass = model.Sum(classOnPos[c]);
            model.Constraint(nbCarsFromClass == nbCars[c]);
        }

        // One car assigned to each position p
        for (int p = 0; p < nbPositions; p++)
        {
            LSExpression nbCarsOnPos = model.Sum();
            for (int c = 0; c < nbClasses; c++)
            {
                nbCarsOnPos.AddOperand(classOnPos[c][p]);
            }
            model.AddConstraint(nbCarsOnPos == 1);
        }

        // optionsOnPos[o][p] = 1 if option o appears at position p, and 0 otherwise
        LSExpression[][] optionsOnPos = new LSExpression[nbOptions][];
        for (int o = 0; o < nbOptions; o++)
        {
            optionsOnPos[o] = new LSExpression[nbPositions];
            for (int p = 0; p < nbPositions; p++)
            {
                optionsOnPos[o][p] = model.Or();
                for (int c = 0; c < nbClasses; c++)
                {
                    if (options[c][o]) optionsOnPos[o][p].AddOperand(classOnPos[c][p]);
                }
            }
        }

        // Number of cars with option o in each window
        LSExpression[][] nbCarsWindows = new LSExpression[nbOptions][];
        for (int o = 0; o < nbOptions; o++)
        {
            nbCarsWindows[o] = new LSExpression[nbPositions - windowSize[o] + 1];
            for (int j = 0; j < nbPositions - windowSize[o] + 1; j++)
            {
                nbCarsWindows[o][j] = model.Sum();
                for (int k = 0; k < windowSize[o]; k++)
                {
                    nbCarsWindows[o][j].AddOperand(optionsOnPos[o][j + k]);
                }
            }
        }

        // Number of violations of option o capacity in each window
        LSExpression[][] nbViolationsWindows = new LSExpression[nbOptions][];
        for (int o = 0; o < nbOptions; o++)
        {
            nbViolationsWindows[o] = new LSExpression[nbPositions - windowSize[o] + 1];
            for (int j = 0; j < nbPositions - windowSize[o] + 1; j++)
            {
                nbViolationsWindows[o][j] = model.Max(0, nbCarsWindows[o][j] - maxCarsPerWindow[o]);
            }
        }

        // Minimize the sum of violations for all options and all windows
        totalViolations = model.Sum();
        for (int o = 0; o < nbOptions; o++)
        {
            totalViolations.AddOperands(nbViolationsWindows[o]);
        }

        model.Minimize(totalViolations);
        model.Close();

        // Parameterizes the solver.
        localsolver.GetParam().SetTimeLimit(limit);

        localsolver.Solve();
    }

    // Writes the solution in a file following the following format: 
    // - 1st line: value of the objective;
    // - 2nd line: for each position p, index of class at positions p.
    void WriteSolution(string fileName)
    {
        using (StreamWriter output = new StreamWriter(fileName))
        {
            output.WriteLine(totalViolations.GetValue());
            for (int p = 0; p < nbPositions; p++)
            {
                for (int c = 0; c < nbClasses; c++)
                {
                    if (classOnPos[c][p].GetValue() == 1)
                    {
                        output.Write(c + " ");
                        break;
                    }
                }
            }
            output.WriteLine();
        }
    }

    public static void Main(string[] args)
    {
        if (args.Length < 1)
        {
            Console.WriteLine("Usage: CarSequencing inputFile [outputFile] [timeLimit]");
            Environment.Exit(1);
        }

        string instanceFile = args[0];
        string outputFile = args.Length > 1 ? args[1] : null;
        string strTimeLimit = args.Length > 2 ? args[2] : "60";

        using (CarSequencing model = new CarSequencing())
        {
            model.ReadInstance(instanceFile);
            model.Solve(int.Parse(strTimeLimit));
            if (outputFile != null)
                model.WriteSolution(outputFile);
        }
    }
}

