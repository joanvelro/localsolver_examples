/********** BinPacking.java **********/

import java.util.*;
import java.io.*;
import localsolver.*;

public class BinPacking {
    // Number of items
    private int nbItems;

    // Capacity of each bin
    private int binCapacity;

    // Maximum number of bins
    private int nbMaxBins;

    // Minimum number of bins
    private int nbMinBins;

    // Weight of each item
    private long[] itemWeights;

    // LocalSolver
    private final LocalSolver localsolver;

    // Decision variables
    private LSExpression[] bins;

    // Weight of each bin in the solution
    private LSExpression[] binWeights;

    // Whether the bin is used in the solution
    private LSExpression[] binsUsed;

    // Objective
    private LSExpression totalBinsUsed;

    private BinPacking(LocalSolver localsolver) {
        this.localsolver = localsolver;
    }

    // Reads instance data.
    private void readInstance(String fileName) throws IOException {
        try (Scanner input = new Scanner(new File(fileName))) {
            nbItems = input.nextInt();
            binCapacity = input.nextInt();

            itemWeights = new long[nbItems];
            for (int i = 0; i < nbItems; i++) {
                itemWeights[i] = input.nextInt();
            }

            long sumWeights = 0;
            for (int i = 0; i < nbItems; i++) {
                sumWeights += itemWeights[i];
            }

            nbMinBins = (int) Math.ceil((double) sumWeights / binCapacity);
            nbMaxBins = Math.min(2 * nbMinBins, nbItems);
        }
    }

    private void solve(int limit) {
        // Declares the optimization model.
        LSModel model = localsolver.getModel();

        bins = new LSExpression[nbMaxBins];
        binWeights = new LSExpression[nbMaxBins];
        binsUsed = new LSExpression[nbMaxBins];

        // Set decisions: bins[k] represents the items in bin k
        for (int k = 0; k < nbMaxBins; ++k) {
            bins[k] = model.setVar(nbItems);
        }

        // Each item must be in one bin and one bin only
        model.constraint(model.partition(bins));

        // Create an array and a lambda function to retrieve the item's weight
        LSExpression weightArray = model.array(itemWeights);
        LSExpression weightSelector = model.lambdaFunction(i -> model.at(weightArray, i));

        for (int k = 0; k < nbMaxBins; ++k) {
            // Weight constraint for each bin
            binWeights[k] = model.sum(bins[k], weightSelector);
            model.constraint(model.leq(binWeights[k], binCapacity));

            // Bin k is used if at least one item is in it
            binsUsed[k] = model.gt(model.count(bins[k]), 0);
        }

        // Count the used bins
        totalBinsUsed = model.sum(binsUsed);

        // Minimize the number of used bins
        model.minimize(totalBinsUsed);
        model.close();

        // Parameterizes the solver.
        localsolver.getParam().setTimeLimit(limit);

        // Stop the search if the lower threshold is reached
        localsolver.getParam().setObjectiveThreshold(0, nbMinBins);

        localsolver.solve();
    }

    // Writes the solution in a file
    private void writeSolution(String fileName) throws IOException {
        try (PrintWriter output = new PrintWriter(fileName)) {
            for (int k = 0; k < nbMaxBins; ++k) {
                if (binsUsed[k].getValue() != 0) {
                    output.print("Bin weight: " + binWeights[k].getValue() + " | Items: ");
                    LSCollection binCollection = bins[k].getCollectionValue();
                    for (int i = 0; i < binCollection.count(); ++i) {
                        output.print(binCollection.get(i) + " ");
                    }
                    output.println();
                }
            }
        }
    }

    public static void main(String[] args) {
        if (args.length < 1) {
            System.err.println("Usage: java BinPacking inputFile [outputFile] [timeLimit]");
            System.exit(1);
        }

        String instanceFile = args[0];
        String outputFile = args.length > 1 ? args[1] : null;
        String strTimeLimit = args.length > 2 ? args[2] : "20";

        try (LocalSolver localsolver = new LocalSolver()) {
            BinPacking model = new BinPacking(localsolver);
            model.readInstance(instanceFile);
            model.solve(Integer.parseInt(strTimeLimit));
            if (outputFile != null) {
                model.writeSolution(outputFile);
            }
        } catch (Exception ex) {
            System.err.println(ex);
            ex.printStackTrace();
            System.exit(1);
        }
    }
}
