/********** BinPacking.cs **********/

using System;
using System.IO;
using System.Linq;
using localsolver;

public class BinPacking : IDisposable
{
    // Number of items
    int nbItems;

    // Capacity of each bin
    int binCapacity;

    // Maximum number of bins
    int nbMaxBins;

    // Minimum number of bins
    int nbMinBins;

    // Weight of each item
    long[] itemWeights;

    // LocalSolver
    LocalSolver localsolver;

    // Decision variables
    LSExpression[] bins;

    // Weight of each bin in the solution
    LSExpression[] binWeights;

    // Whether the bin is used in the solution
    LSExpression[] binsUsed;

    // Objective
    LSExpression totalBinsUsed;

    public BinPacking()
    {
        localsolver = new LocalSolver();
    }

    // Reads instance data. 
    void ReadInstance(string fileName)
    {
        using (StreamReader input = new StreamReader(fileName))
        {
            nbItems = int.Parse(input.ReadLine());
            binCapacity = int.Parse(input.ReadLine());

            itemWeights = new long[nbItems];
            for (int i = 0; i < nbItems; i++) {
                itemWeights[i] = int.Parse(input.ReadLine());
            }

            nbMinBins = (int) Math.Ceiling((double) itemWeights.Sum() / binCapacity);
            nbMaxBins = Math.Min(2 * nbMinBins, nbItems);
        }
    }

    public void Dispose()
    {
        if (localsolver != null)
            localsolver.Dispose();
    }

    void Solve(int limit)
    {
        // Declares the optimization model.
        LSModel model = localsolver.GetModel();

        bins = new LSExpression[nbMaxBins]; 
        binWeights = new LSExpression[nbMaxBins]; 
        binsUsed = new LSExpression[nbMaxBins]; 

        // Set decisions: bin[k] represents the items in bin k
        for (int k = 0; k < nbMaxBins; ++k) {
            bins[k] = model.Set(nbItems);
        }

        // Each item must be in one bin and one bin only
        model.Constraint(model.Partition(bins));

        // Create an array and a function to retrieve the item's weight
        LSExpression weightArray = model.Array(itemWeights);
        LSExpression weightSelector = model.LambdaFunction(i => weightArray[i]);

        for (int k = 0; k < nbMaxBins; ++k) {
            // Weight constraint for each bin
            binWeights[k] = model.Sum(bins[k], weightSelector);
            model.Constraint(binWeights[k] <= binCapacity);

            // Bin k is used if at least one item is in it
            binsUsed[k] = model.Count(bins[k]) > 0;
        }

        // Count the used bins
        totalBinsUsed = model.Sum(binsUsed);

        // Minimize the number of used bins
        model.Minimize(totalBinsUsed);

        model.Close();

        // Parameterizes the solver.
        localsolver.GetParam().SetTimeLimit(limit);

        // Stop the search if the lower threshold is reached
        localsolver.GetParam().SetObjectiveThreshold(0, nbMinBins);

        localsolver.Solve();
    }

    // Writes the solution in a file
    void WriteSolution(string fileName)
    {
        using (StreamWriter output = new StreamWriter(fileName))
        {
            for (int k = 0; k < nbMaxBins; ++k) {
                if (binsUsed[k].GetValue() != 0) {
                    output.Write("Bin weight: " + binWeights[k].GetValue() + " | Items: ");
                    LSCollection binCollection = bins[k].GetCollectionValue();
                    for (int i = 0; i < binCollection.Count(); ++i) {
                        output.Write(binCollection[i] + " ");
                    }
                    output.WriteLine();
                }
            }
        }
    }

    public static void Main(string[] args)
    {
        if (args.Length < 1)
        {
            Console.WriteLine("Usage: BinPacking inputFile [solFile] [timeLimit]");
            Environment.Exit(1);
        }
        string instanceFile = args[0];
        string outputFile = args.Length > 1 ? args[1] : null;
        string strTimeLimit = args.Length > 2 ? args[2] : "5";

        using (BinPacking model = new BinPacking())
        {
            model.ReadInstance(instanceFile);
            model.Solve(int.Parse(strTimeLimit));
            if (outputFile != null)
                model.WriteSolution(outputFile);
        }
    }
}
