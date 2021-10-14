/********** RevenueManagement.cs **********/

using System;
using System.IO;
using System.Collections.Generic;
using localsolver;

public class RevenueManagement : IDisposable
{
    public class EvaluatedPoint
    {
        private int[] point;
        private double value;

        public EvaluatedPoint(int[] point, double value)
        {
            this.point = point;
            this.value = value;
        }

        public int GetPoint(int index) {
            return point[index];
        }

        public double GetValue() {
            return value;
        }
    }

    /* Black-box function */
    public class RevenueManagementFunction
    {
        private int seed;
        private const int nbPeriods = 3;
        private const int purchasePrice = 80;
        private const int nbSimulations = (int) 1e6;
        private readonly int[] prices = {100, 300, 400};
        private readonly int[] meanDemands = {50, 20, 30};
        private List<EvaluatedPoint> evaluatedPoints = new List<EvaluatedPoint>();

        public RevenueManagementFunction(int seed)
        {
            this.seed = seed;
            int[] point = {100, 50, 30};
            evaluatedPoints.Add(new EvaluatedPoint(point, 4740.99));
        }

        public double Call(LSBlackBoxArgumentValues argumentValues)
        {
            // Initial quantity purchased
            int nbUnitsPurchased = (int) argumentValues.GetIntValue(0);
            // Number of units that should be left for future periods
            int[] nbUnitsReserved = new int[nbPeriods];
            for (int j = 0; j < nbPeriods - 1; j++)
            {
                nbUnitsReserved[j] = (int) argumentValues.GetIntValue(j+1);
            }
            nbUnitsReserved[nbPeriods - 1] = 0;
            // Sets seed for reproducibility
            Random rng = new Random(seed);
            // Creates distribution
            double[] X = new double[nbSimulations];
            for (int i = 0; i < nbSimulations; i++)
            {
                X[i] = GammaSample(rng);
            }
            double[,] Y = new double[nbSimulations, nbPeriods];
            for (int i = 0; i < nbSimulations; i++)
            {
                for (int j = 0; j < nbPeriods; j++)
                {
                    Y[i,j] = ExponentialSample(rng);
                }
            }

            // Runs simulations
            double sumProfit = 0;
            for (int i = 0; i < nbSimulations; i++)
            {
                int remainingCapacity = nbUnitsPurchased;
                for (int j = 0; j < nbPeriods; j++)
                {
                    // Generates demand for period j
                    int demand = (int) (meanDemands[j] * X[i] * Y[i,j]);
                    int nbUnitsSold = Math.Min(Math.Max(remainingCapacity - nbUnitsReserved[j],
                            0), demand);
                    remainingCapacity = remainingCapacity - nbUnitsSold;
                    sumProfit += prices[j] * nbUnitsSold;
                }
            }
            // Calculates mean revenue
            double meanProfit = sumProfit / nbSimulations;
            double meanRevenue = meanProfit - purchasePrice * nbUnitsPurchased;

            return meanRevenue;
        }

        private static double ExponentialSample(Random rng, double rateParam = 1.0)
        {
            double u = rng.NextDouble();
            return Math.Log(1 - u) / (-rateParam);
        }

        private static double GammaSample(Random rng, double scaleParam = 1.0)
        {
            return ExponentialSample(rng, scaleParam);
        }

        public int GetNbPeriods()
        {
            return nbPeriods;
        }

        public List<EvaluatedPoint> GetEvaluatedPoints() {
            return evaluatedPoints;
        }
    }

    // Solver
    private LocalSolver localsolver;

    // LS Program variables
    private LSExpression[] variables;
    private LSExpression bbCall;

    public RevenueManagement()
    {
        localsolver = new LocalSolver();
    }

    public void Dispose()
    {
        if (localsolver != null)
            localsolver.Dispose();
    }

    public void Solve(int timeLimit, int evaluationLimit)
    {
        // Declares the optimization model
        LSModel model = localsolver.GetModel();

        // Generates data
        RevenueManagementFunction revenueManagement = new RevenueManagementFunction(1);
        int nbPeriods = revenueManagement.GetNbPeriods();
        // Declares decision variables
        variables = new LSExpression[nbPeriods];
        for (int i = 0; i < nbPeriods; i++)
        {
            variables[i] = model.Int(0, 100);
        }

        // Creates blackbox function
        LSDoubleBlackBoxFunction bbFunc = new LSDoubleBlackBoxFunction(revenueManagement.Call);
        LSExpression bbFuncExpr = model.DoubleBlackBoxFunction(bbFunc);
        // Calls function
        bbCall = model.Call(bbFuncExpr);
        for (int i = 0; i < nbPeriods; i++)
        {
            bbCall.AddOperand(variables[i]);
        }

        // Declares constraints
        for (int i = 1; i < nbPeriods; i++)
        {
            model.Constraint(variables[i] <= variables[i-1]);
        }

        // Maximizes function call
        model.Maximize(bbCall);

        // Sets lower bound
        LSBlackBoxContext context = bbFuncExpr.GetBlackBoxContext();
        context.SetLowerBound(0.0);

        model.Close();

        // Parametrizes the solver
        if (timeLimit != 0)
        {
            localsolver.GetParam().SetTimeLimit(timeLimit);
        }

        // Sets the maximum number of evaluations
        context.SetEvaluationLimit(evaluationLimit);

        // Adds evaluation points
        foreach (EvaluatedPoint evaluatedPoint in revenueManagement.GetEvaluatedPoints())
        {
            LSBlackBoxEvaluationPoint evaluationPoint = context.CreateEvaluationPoint();
            for (int i = 0; i < nbPeriods; i++)
            {
                evaluationPoint.AddArgument(evaluatedPoint.GetPoint(i));
            }
            evaluationPoint.SetReturnValue(evaluatedPoint.GetValue());
        }

        localsolver.Solve();
    }

    // Writes the solution in a file
    public void WriteSolution(string fileName)
    {
        using (StreamWriter output = new StreamWriter(fileName))
        {
            output.WriteLine("obj=" + bbCall.GetDoubleValue());
            output.WriteLine("b=" + variables[0].GetIntValue());
            for (int i = 1; i < variables.Length; i++) {
                output.WriteLine("r" + i + "=" + variables[i].GetIntValue());
            }
        }
    }

    public static void Main(string[] args)
    {
        string outputFile = args.Length > 0 ? args[0] : null;
        string strTimeLimit = args.Length > 1 ? args[1] : "0";
        string strEvaluationLimit = args.Length > 2 ? args[2] : "30";

        using (RevenueManagement model = new RevenueManagement())
        {
            model.Solve(int.Parse(strTimeLimit), int.Parse(strEvaluationLimit));
            if (outputFile != null)
                model.WriteSolution(outputFile);
        }
    }
}
