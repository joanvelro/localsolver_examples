/********** kmeans.cs **********/

using System;
using System.IO;
using System.Globalization;
using localsolver;

public class Kmeans : IDisposable
{
    // Data properties
    int nbObservations;
    int nbDimensions;
    int k;

    double[][] coordinates;
    string[] initialClusters;

    // Solver.
    LocalSolver localsolver;

    // Decisions.
    LSExpression[] clusters;

    // Objective.
    LSExpression obj;

    public Kmeans(int k)
    {
        localsolver = new LocalSolver();
        this.k = k;
    }

    // Reads instance data 
    public void ReadInstance(string fileName)
    {
        using (StreamReader input = new StreamReader(fileName))
        {
            string[] splittedLine = input.ReadLine().Split();

            nbObservations = int.Parse(splittedLine[0]);
            nbDimensions = int.Parse(splittedLine[1]);

            coordinates = new double[nbObservations][];
            initialClusters = new string[nbObservations];
            for (int o = 0; o < nbObservations; o++)
            {
                splittedLine = input.ReadLine().Split();
                coordinates[o] = new double[nbDimensions];
                for (int d = 0; d < nbDimensions; d++)
                    coordinates[o][d] = double.Parse(splittedLine[d], 
                        CultureInfo.InvariantCulture);
                initialClusters[o] = splittedLine[nbDimensions];
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
        // Declares the optimization model
        LSModel model = localsolver.GetModel();

        // Set decisions: clusters[c] represents the points in cluster c
        clusters = new LSExpression[k];
        for (int c = 0; c < k; c++)
            clusters[c] = model.Set(nbObservations);

        // Each point must be in one cluster and one cluster only
        model.Constraint(model.Partition(clusters));

        // Coordinates of points
        LSExpression coordinatesArray = model.Array(coordinates);

        // Compute variances
        LSExpression[] variances = new LSExpression[k];
        for (int c = 0; c < k; c++) 
        {
            LSExpression cluster =  clusters[c];
            LSExpression size = model.Count(cluster);

            // Compute the centroid of the cluster
            LSExpression centroid = model.Array();
            for (int d = 0; d < nbDimensions; d++)
            {
                LSExpression coordinateSelector = model.LambdaFunction(
                    o => model.At(coordinatesArray, o, model.CreateConstant(d)));
                centroid.AddOperand(model.If(size == 0, 0,
                    model.Sum(cluster, coordinateSelector) / size));
            }

            // Compute the variance of the cluster
            LSExpression variance = model.Sum();
            for (int d = 0; d < nbDimensions; d++)
            {
                LSExpression dimensionVarianceSelector = model.LambdaFunction(
                    o => model.Pow(model.At(coordinatesArray, o, model.CreateConstant(d))
                                   - model.At(centroid, model.CreateConstant(d)), 2)
                    );
                LSExpression dimensionVariance = model.Sum(cluster, 
                    dimensionVarianceSelector);
                variance.AddOperand(dimensionVariance);
            }
            variances[c] = variance;
        }

        // Minimize the total variance
        obj = model.Sum(variances);
        model.Minimize(obj);

        model.Close();

        // Parameterizes the solver.
        localsolver.GetParam().SetTimeLimit(limit);

        localsolver.Solve();
    }

    // Writes the solution in a file in the following format:
    //  - objective value
    //  - k
    //  - for each cluster, a line with the elements in the cluster (separated by spaces)
    public void WriteSolution(string fileName)
    {
        using (StreamWriter output = new StreamWriter(fileName))
        {
            output.WriteLine(obj.GetDoubleValue());
            output.WriteLine(k);
            for (int c = 0; c < k; c++)
            {
                LSCollection clusterCollection = clusters[c].GetCollectionValue();
                for (int i = 0; i < clusterCollection.Count(); i++)
                    output.Write(clusterCollection[i] + " ");
                output.WriteLine();
            }
            output.Close();
        }
    }

    public static void Main(string[] args)
    {
        if (args.Length < 1)
        {
            Console.WriteLine("Usage: Kmeans inputFile [outputFile] [timeLimit] [k value]");
            Environment.Exit(1);
        }
        
        string instanceFile = args[0];
        string outputFile = args.Length > 1 ? args[1] : null;
        string strTimeLimit = args.Length > 2 ? args[2] : "5";
        string k = args.Length > 3 ? args[3] : "2";
        using (Kmeans model = new Kmeans(int.Parse(k)))
        {
            model.ReadInstance(instanceFile);
            model.Solve(int.Parse(strTimeLimit));
            if (outputFile != null)
            {
                model.WriteSolution(outputFile);
            }
        }
    }
}
