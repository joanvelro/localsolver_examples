/********** Tsp.java **********/

import java.util.*;
import java.io.*;
import localsolver.*;

public class Tsp {
    // Number of cities
    private int nbCities;

    // Vector of distance between two cities
    private long[][] distanceWeight;

    // LocalSolver.
    private final LocalSolver localsolver;

    // Decision variables.
    private LSExpression cities;

    // Objective
    private LSExpression obj;

    private Tsp(LocalSolver localsolver) {
        this.localsolver = localsolver;
    }

    // Reads instance data.
    private void readInstance(String fileName) throws IOException {
        try (Scanner input = new Scanner(new File(fileName))) {
            // The input files follow the TSPLib "explicit" format.
            String str = new String();
            String[] pch = new String[2];
            int i = 0;
            while (true) {
                str = input.nextLine();
                pch = str.split(":");
                if (pch[0].compareTo("DIMENSION")==0) {
                    nbCities = Integer.parseInt(pch[1].trim());
                    System.out.println("Number of cities = " + nbCities);
                } else if (pch[0].compareTo("EDGE_WEIGHT_SECTION")==0) {
                    break;
                }
            }

            // Distance from i to j
            distanceWeight = new long[nbCities][nbCities];
            for (i = 0; i < nbCities; i++) {
                for (int j = 0; j < nbCities; j++) {
                    distanceWeight[i][j] = input.nextInt();
                }
            }
        }
    }

    private void solve(int limit) {
        // Declares the optimization model.
        LSModel model = localsolver.getModel();

        // A list variable: cities[i] is the index of the ith city in the tour
        cities = model.listVar(nbCities);

        // All cities must be visited
        model.constraint(model.eq(model.count(cities), nbCities));

        // Create a LocalSolver array for the distance matrix in order to be able to
        // access it with "at" operators.
        LSExpression distanceArray = model.array(distanceWeight);

        // Minimize the total distance
        LSExpression distSelector = model.lambdaFunction(i -> model.at(distanceArray,
                                            model.at(cities, model.sub(i, 1)),
                                            model.at(cities, i)));
        obj = model.sum(
                model.sum(model.range(1, nbCities), distSelector),
                model.at(distanceArray, model.at(cities, nbCities - 1), model.at(cities, 0)));

        model.minimize(obj);
        model.close();

        // Parameterizes the solver.
        localsolver.getParam().setTimeLimit(limit);

        localsolver.solve();
    }

    // Writes the solution in a file
    void writeSolution(String fileName) throws IOException {
        try (PrintWriter output = new PrintWriter(new FileWriter(fileName))) {
            output.println(obj.getValue());
            LSCollection citiesCollection = cities.getCollectionValue();
            for (int i = 0; i < nbCities; i++) {
                output.print(citiesCollection.get(i) + " ");
            }
            output.println();
        }
    }

    public static void main(String[] args) {
        if (args.length < 1) {
            System.err.println("Usage: java Tsp inputFile [outputFile] [timeLimit]");
            System.exit(1);
        }

        String instanceFile = args[0];
        String outputFile = args.length > 1 ? args[1] : null;
        String strTimeLimit = args.length > 2 ? args[2] : "5";

        try (LocalSolver localsolver = new LocalSolver()) {
            Tsp model = new Tsp(localsolver);
            model.readInstance(instanceFile);
            model.solve(Integer.parseInt(strTimeLimit));
            if (outputFile != null) {
                model.writeSolution(outputFile);
            }
        } catch(Exception ex) {
            System.err.println(ex);
            ex.printStackTrace();
            System.exit(1);
        }
    }
}
