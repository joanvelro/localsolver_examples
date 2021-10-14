/********** AircraftLanding.cs **********/

using System;
using System.IO;
using System.Globalization;
using localsolver;

public class AircraftLanding : IDisposable
{
    // Data from the problem
    private int nbPlanes;
    private int[] earliestTime;
    private int[] targetTime;
    private int[] latestTime;
    private float[] earlinessCost;
    private float[] latenessCost;
    private int[,] separationTime;

    // LocalSolver
    private readonly LocalSolver localsolver;

    // Decision variables
    private LSExpression landingOrder;
    private LSExpression[] preferredTime;

    // Landing time for each plane
    private LSExpression landingTime;

    // Objective
    private LSExpression totalCost;

    public AircraftLanding()
    {
        localsolver = new LocalSolver();
    }

    public void Dispose()
    {
        if (localsolver != null)
            localsolver.Dispose();
    }

    /* Read instance data */
    private void ReadInstance(string fileName)
    {
        using (StreamReader input = new StreamReader(fileName))
        {
            string[] firstLineSplitted = input.ReadLine().Split();
            nbPlanes = int.Parse(firstLineSplitted[1]);

            earliestTime = new int[nbPlanes];
            targetTime = new int[nbPlanes];
            latestTime = new int[nbPlanes];
            earlinessCost = new float[nbPlanes];
            latenessCost = new float[nbPlanes];
            separationTime = new int[nbPlanes, nbPlanes];

            for (int p = 0; p < nbPlanes; ++p)
            {
                string[] secondLineSplitted = input.ReadLine().Split();
                earliestTime[p] = int.Parse(secondLineSplitted[2]);
                targetTime[p] = int.Parse(secondLineSplitted[3]);
                latestTime[p] = int.Parse(secondLineSplitted[4]);
                earlinessCost[p] = float.Parse(secondLineSplitted[5], CultureInfo.InvariantCulture);
                latenessCost[p] = float.Parse(secondLineSplitted[6], CultureInfo.InvariantCulture);
                int pp = 0;

                while (pp < nbPlanes)
                {
                    string[] lineSplitted = input.ReadLine().Split(' ');
                    for (int i = 0; i < lineSplitted.Length; i++)
                    {
                        if (lineSplitted[i].Length > 0)
                        {
                            separationTime[p, pp] = int.Parse(lineSplitted[i]);
                            pp++;
                        }
                    }
                }
            }
        }
    }

    private LSExpression GetMinLandingTime(LSExpression p, LSExpression prev, LSModel model, LSExpression separationTimeArray)
    {
        return model.If(p>0,
                        prev + model.At(separationTimeArray, landingOrder[p-1], landingOrder[p]),
                        0);
    }

    private void Solve(int limit)
    {
        // Declare the optimization model
        LSModel model = localsolver.GetModel();

        // A list variable: landingOrder[i] is the index of the ith plane to land
        landingOrder = model.List(nbPlanes);

        // All planes must be scheduled
        model.Constraint(model.Count(landingOrder) == nbPlanes);

        // Create LocalSolver arrays in order to be able to access them with "at" operators
        LSExpression targetTimeArray = model.Array(targetTime);
        LSExpression latestTimeArray = model.Array(latestTime);
        LSExpression earlinessCostArray = model.Array(earlinessCost);
        LSExpression latenessCostArray = model.Array(latenessCost);
        LSExpression separationTimeArray = model.Array(separationTime);

        // Int variables: preferred time for each plane
        preferredTime = new LSExpression[nbPlanes];
        for (int p = 0; p < nbPlanes; ++p)
        {
            preferredTime[p] = model.Int(earliestTime[p], targetTime[p]);
        }
        LSExpression preferredTimeArray = model.Array(preferredTime);

        // Landing time for each plane
        LSExpression landingTimeSelector = model.LambdaFunction((p, prev) =>
                        model.Max(preferredTimeArray[landingOrder[p]], GetMinLandingTime(p, prev, model, separationTimeArray)));

        landingTime = model.Array(model.Range(0, nbPlanes), landingTimeSelector);

        // Landing times must respect the separation time with every previous plane.
        for (int p = 1; p < nbPlanes; ++p) {
            LSExpression lastSeparationEnd = model.Max();
            for (int previousPlane = 0; previousPlane < p; ++previousPlane) {
                lastSeparationEnd.AddOperand(landingTime[previousPlane]
                                + model.At(separationTimeArray, landingOrder[previousPlane], landingOrder[p]));
            }
            model.Constraint(landingTime[p] >= lastSeparationEnd);
        }

        totalCost = model.Sum();
        for (int p = 0; p < nbPlanes; ++p)
        {
            LSExpression planeIndex = landingOrder[p];

            // Constraint on latest landing time
            model.Constraint(landingTime[p] <= latestTimeArray[planeIndex]);

            // Cost for each plane
            LSExpression unitCost = model.If(landingTime[p] < targetTimeArray[planeIndex],
                                             earlinessCostArray[planeIndex],
                                             latenessCostArray[planeIndex]);
            LSExpression differenceToTargetTime = model.Abs(landingTime[p] - targetTimeArray[planeIndex]);
            totalCost.AddOperand(unitCost * differenceToTargetTime);
        }

        // Minimize the total cost
        model.Minimize(totalCost);

        model.Close();

        // Parameterize the solver
        localsolver.GetParam().SetTimeLimit(limit);

        localsolver.Solve();
    }

    /* Write the solution in a file */
    private void WriteSolution(string fileName)
    {
        using (StreamWriter output = new StreamWriter(fileName))
        {
            output.WriteLine(totalCost.GetDoubleValue());
            LSCollection landingOrderCollection = landingOrder.GetCollectionValue();
            for (int i = 0; i < nbPlanes; i++)
                output.Write(landingOrderCollection.Get(i) + " ");
            output.WriteLine();
        }
    }

    public static void Main(string[] args)
    {
        if (args.Length < 1)
        {
            Console.WriteLine("Usage: AircraftLanding inputFile [solFile] [timeLimit]");
            Environment.Exit(1);
        }
        string instanceFile = args[0];
        string outputFile = args.Length > 1 ? args[1] : null;
        string strTimeLimit = args.Length > 2 ? args[2] : "20";

        using (AircraftLanding model = new AircraftLanding())
        {
            model.ReadInstance(instanceFile);
            model.Solve(int.Parse(strTimeLimit));
            if (outputFile != null)
                model.WriteSolution(outputFile);
        }
    }
}
