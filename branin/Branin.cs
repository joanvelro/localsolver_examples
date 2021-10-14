/********** Branin.cs **********/

using System;
using System.IO;
using localsolver;

public class Branin : IDisposable
{
    // Solver
    private LocalSolver localsolver;

    // LS Program variables
    private LSExpression x1;
    private LSExpression x2;

    public Branin()
    {
        localsolver = new LocalSolver();
    }

    public void Dispose()
    {
        if (localsolver != null)
            localsolver.Dispose();
    }

    public void Solve(int limit)
    {
        // Parameters of the function
        double PI = 3.14159265359;
        double a = 1;
        double b = 5.1 / (4 * Math.Pow(PI, 2.0));
        double c = 5 / PI;
        double r = 6;
        double s = 10;
        double t = 1 / (8 * PI);

        // Declares the optimization model
        LSModel model = localsolver.GetModel();

        // Numerical decisions
        x1 = model.Float(-5, 10);
        x2 = model.Float(0, 15);

        // f = a(x2 - b*x1^2 + c*x1 - r)^2 + s(1-t)cos(x1) + s
        LSExpression f = a * model.Pow(x2 - b * model.Pow(x1, 2) + c * x1 - r, 2) + s * (1 - t) * model.Cos(x1) + s;

        // Minimize f
        model.Minimize(f);
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
            output.WriteLine("x1=" + x1.GetDoubleValue());
            output.WriteLine("x2=" + x2.GetDoubleValue());
        }
    }

    public static void Main(string[] args)
    {
        string outputFile = args.Length > 0 ? args[0] : null;
        string strTimeLimit = args.Length > 1 ? args[1] : "6";

        using (Branin model = new Branin())
        {
            model.Solve(int.Parse(strTimeLimit));
            if (outputFile != null)
                model.WriteSolution(outputFile);
        }
    }
}
