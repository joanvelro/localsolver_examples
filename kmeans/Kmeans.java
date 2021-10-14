/********** Kmeans.java **********/

import java.util.*;
import java.io.*;
import localsolver.*;

public class Kmeans {
    // Data properties
    private int nbObservations;
    private int nbDimensions;
    private int k;

    private double[][] coordinates;
    private String[] initialClusters;

    // Solver.
    private final LocalSolver localsolver;

    // Decisions.
    private LSExpression[] clusters;

    // Objective.
    private LSExpression obj;

    private Kmeans(LocalSolver localsolver) {
        this.localsolver = localsolver;
    }

    // Reads instance data
    private void readInstance(int k, String fileName) throws IOException {
        try (Scanner input = new Scanner(new File(fileName))) {
            input.useLocale(Locale.ROOT);

            nbObservations = input.nextInt();
            nbDimensions = input.nextInt();

            this.k = k;
            coordinates = new double[nbObservations][nbDimensions];
            initialClusters = new String[nbObservations];
            for (int o = 0; o < nbObservations; o++) {
                for (int d = 0; d < nbDimensions; d++) {
                    coordinates[o][d] = input.nextDouble();
                }
                initialClusters[o] = input.next();
            }
        }
    }

    private void solve(int limit) {
        // Declares the optimization model.
        LSModel model = localsolver.getModel();

        // Set decisions: clusters[c] represents the points in cluster c
        clusters = new LSExpression[k];
        for (int c = 0; c < k; c++) {
            clusters[c] = model.setVar(nbObservations);
        }

        // Each point must be in one cluster and one cluster only
        model.constraint(model.partition(clusters));

        // Coordinates of points
        LSExpression coordinatesArray = model.array(coordinates);
        
        // Compute variances
        LSExpression[] variances = new LSExpression[k];
        for (int c = 0; c < k; c++) {
            LSExpression cluster = clusters[c];
            LSExpression size = model.count(cluster);

            // Compute the centroid of the cluster
            LSExpression centroid = model.array();
            for (int d = 0; d < nbDimensions; d++) {
                LSExpression vExpr = model.createConstant(d);
                LSExpression coordinateSelector = model.lambdaFunction(
                    o -> model.at(coordinatesArray, o, vExpr));
                centroid.addOperand(model.iif(model.eq(size, 0), 0,
                    model.div(model.sum(cluster, coordinateSelector), size)));
            }

            // Compute the variance of the cluster
            LSExpression variance = model.sum();
            for (int d = 0; d < nbDimensions; d++) {
                LSExpression vExpr = model.createConstant(d);
                LSExpression dimensionVarianceSelector = model.lambdaFunction(
                    o -> model.pow(model.sub(model.at(coordinatesArray, o, vExpr),
                                   model.at(centroid, vExpr)), 2)
                    );
                LSExpression dimensionVariance = model.sum(cluster,
                    dimensionVarianceSelector);
                variance.addOperand(dimensionVariance);
            }
            variances[c] = variance;
        }

        // Minimize the total variance
        obj = model.sum(variances);
        model.minimize(obj);

        model.close();

        // Parameterizes the solver.
        localsolver.getParam().setTimeLimit(limit);

        localsolver.solve();
    }

    // Writes the solution in a file in the following format:
    // - objective value
    // - k
    // - for each cluster, a line with the elements in the cluster (separated by spaces)
    private void writeSolution(String fileName) throws IOException {
        try (PrintWriter output = new PrintWriter(fileName)) {
            output.println(obj.getDoubleValue());
            output.println(k);
            for (int c = 0; c < k; c++) {
                LSCollection clusterCollection = clusters[c].getCollectionValue();
                for (int i = 0; i < clusterCollection.count(); i++) {
                    output.print(clusterCollection.get(i) + " ");
                }
                output.println();
            }
        }
    }

    public static void main(String[] args) {
        if (args.length < 1) {
            System.err.println("Usage: java Kmeans inputFile [outputFile] [timeLimit] [k value]");
            System.exit(1);
        }

        String instanceFile = args[0];
        String outputFile = args.length > 1 ? args[1] : null;
        String strTimeLimit = args.length > 2 ? args[2] : "5";
        String k = args.length > 3 ? args[3] : "2";

        try (LocalSolver localsolver = new LocalSolver()) {
            Kmeans model = new Kmeans(localsolver);
            model.readInstance(Integer.parseInt(k), instanceFile);
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
