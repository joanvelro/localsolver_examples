/********** Hosaki.cs **********/

using System;
using System.IO;
using localsolver;

public class Hosaki : IDisposable
{
    /* Black-box function */
    public class HosakiFunction {
        public double Call(LSBlackBoxArgumentValues argumentValues) {
            double x1 = argumentValues.GetDoubleValue(0);
            double x2 = argumentValues.GetDoubleValue(1);
            return (1 - 8*x1 + 7*x1*x1 - 7*Math.Pow(x1, 3)/3 + Math.Pow(x1, 4)/4) * x2*x2
                * Math.Exp(-x2);
        }
    }

    // Solver
    private LocalSolver localsolver;

    // LS Program variables
    private LSExpression x1;
    private LSExpression x2;
    private LSExpression bbCall;

    public Hosaki()
    {
        localsolver = new LocalSolver();
    }

    public void Dispose()
    {
        if (localsolver != null)
            localsolver.Dispose();
    }

    public void Solve(int evaluationLimit)
    {
        // Declares the optimization model
        LSModel model = localsolver.GetModel();

        // Numerical decisions
        x1 = model.Float(0, 5);
        x2 = model.Float(0, 6);

        // Creates and calls blackbox function
        HosakiFunction func = new HosakiFunction();
        LSDoubleBlackBoxFunction bbFunc = new LSDoubleBlackBoxFunction(func.Call);
        LSExpression bbFuncExpr = model.DoubleBlackBoxFunction(bbFunc);
        bbCall = model.Call(bbFuncExpr, x1, x2);

        // Minimizes function call
        model.Minimize(bbCall);
        model.Close();

        // Parameterizes the solver
        LSBlackBoxContext context = bbFuncExpr.GetBlackBoxContext();
        context.SetEvaluationLimit(evaluationLimit);

        localsolver.Solve();
    }

    // Writes the solution in a file
    public void WriteSolution(string fileName)
    {
        using (StreamWriter output = new StreamWriter(fileName))
        {
            output.WriteLine("obj=" + bbCall.GetDoubleValue());
            output.WriteLine("x1=" + x1.GetDoubleValue());
            output.WriteLine("x2=" + x2.GetDoubleValue());
        }
    }

    public static void Main(string[] args)
    {
        string outputFile = args.Length > 0 ? args[0] : null;
        string strEvaluationLimit = args.Length > 1 ? args[1] : "30";

        using (Hosaki model = new Hosaki())
        {
            model.Solve(int.Parse(strEvaluationLimit));
            if (outputFile != null)
                model.WriteSolution(outputFile);
        }
    }
}
