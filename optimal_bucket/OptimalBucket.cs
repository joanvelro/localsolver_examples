/********** optimal_bucket.cs **********/

using System;
using System.IO;
using localsolver;

public class OptimalBucket : IDisposable
{
    // Solver.
    LocalSolver localsolver;

    // LS Program variables.
    LSExpression R;
    LSExpression r;
    LSExpression h;

    LSExpression surface;
    LSExpression volume;

    public OptimalBucket()
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
        // Declares the optimization model.
        LSModel model = localsolver.GetModel();

        // Numerical decisions
        R = model.Float(0, 1);
        r = model.Float(0, 1);
        h = model.Float(0, 1);

        // Surface must not exceed the surface of the plain disc
        surface = Math.PI * model.Pow(r, 2) + Math.PI * (R + r) * model.Sqrt(model.Pow(R - r, 2) + model.Pow(h, 2));
        model.AddConstraint(surface <= Math.PI);

        // Maximize the volume
        volume = Math.PI * h / 3 * (model.Pow(R, 2) + R * r + model.Pow(r, 2));
        model.Maximize(volume);

        model.Close();

        // Parameterizes the solver.
        localsolver.GetParam().SetTimeLimit(limit);

        localsolver.Solve();
    }

    // Writes the solution in a file with the following format:
    //  - surface and volume of the bucket
    //  - values of R, r and h
    public void WriteSolution(string fileName)
    {
        using (StreamWriter output = new StreamWriter(fileName))
        {
            output.WriteLine(surface.GetDoubleValue() + " " + volume.GetDoubleValue());
            output.WriteLine(R.GetDoubleValue() + " " + r.GetDoubleValue() + " " + h.GetDoubleValue());
        }
    }

    public static void Main(string[] args)
    {

        string outputFile = args.Length > 0 ? args[0] : null;
        string strTimeLimit = args.Length > 1 ? args[1] : "2";

        using (OptimalBucket model = new OptimalBucket())
        {
            model.Solve(int.Parse(strTimeLimit));
            if (outputFile != null)
            {
                model.WriteSolution(outputFile);
            }
        }
    }
}
