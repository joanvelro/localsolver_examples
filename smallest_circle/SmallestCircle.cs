/********** SmallestCircle.cs **********/

using System;
using System.IO;
using localsolver;

public class SmallestCircle : IDisposable
{
    // Number of points
    int nbPoints;

    // Point coordinates
    double[] coordX;
    double[] coordY;

    // Minimum and maximum value of the coordinates of the points
    double minX;
    double minY;
    double maxX;
    double maxY;

    // Solver
    LocalSolver localsolver;

    // LS Program variables
    LSExpression x;
    LSExpression y;

    // Objective
    LSExpression r;

    public SmallestCircle()
    {
        localsolver = new LocalSolver();
    }

    // Reads instance data
    public void ReadInstance(string fileName)
    {
        using (StreamReader input = new StreamReader(fileName))
        {
            nbPoints = int.Parse(input.ReadLine());
            coordX = new double[nbPoints];
            coordY = new double[nbPoints];

            string[] splittedCoord = input.ReadLine().Split(' ');
            coordX[0] = int.Parse(splittedCoord[0]);
            coordY[0] = int.Parse(splittedCoord[1]);

            minX = coordX[0];
            maxX = coordX[0];
            minY = coordY[0];
            maxY = coordY[0];

            for (int i = 1; i < nbPoints; i++)
            {
                splittedCoord = input.ReadLine().Split(' ');
                coordX[i] = int.Parse(splittedCoord[0]);
                coordY[i] = int.Parse(splittedCoord[1]);

                minX = Math.Min(coordX[i], minX);
                maxX = Math.Max(coordX[i], maxX);
                minY = Math.Min(coordY[i], minY);
                maxY = Math.Max(coordY[i], maxY);
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

        // Numerical decisions
        x = model.Float(minX, maxX);
        y = model.Float(minY, maxY);

        // Distance between the origin and the point i
        LSExpression[] radius = new LSExpression[nbPoints];
        for (int i = 0; i < nbPoints; i++)
        {
            radius[i] = model.Pow(x - coordX[i], 2) + model.Pow(y - coordY[i], 2);
        }

        // Minimize the radius r        
        r = model.Sqrt(model.Max(radius));

        model.Minimize(r);
        model.Close();

        // Parameterizes the solver.
        localsolver.GetParam().SetTimeLimit(limit);

        localsolver.Solve();
    }

    // Writes the solution in a file
    public void WriteSolution(string fileName)
    {
        using (StreamWriter output = new StreamWriter(fileName))
        {
            output.WriteLine("x=" + x.GetDoubleValue());
            output.WriteLine("y=" + y.GetDoubleValue());
            output.WriteLine("r=" + r.GetDoubleValue());
        }
    }

    public static void Main(string[] args)
    {
        if (args.Length < 1)
        {
            Console.WriteLine("Usage: SmallestCircle inputFile [outputFile] [timeLimit]");
            Environment.Exit(1);
        }

        string instanceFile = args[0];
        string outputFile = args.Length > 1 ? args[1] : null;
        string strTimeLimit = args.Length > 2 ? args[2] : "6";

        using (SmallestCircle model = new SmallestCircle())
        {
            model.ReadInstance(instanceFile);
            model.Solve(int.Parse(strTimeLimit));
            if (outputFile != null)
                model.WriteSolution(outputFile);
        }
    }
}
