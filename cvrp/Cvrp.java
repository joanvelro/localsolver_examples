/********** Cvrp.java **********/

import java.util.*;
import java.io.*;
import localsolver.*;

public class Cvrp {
    // Solver
    private final LocalSolver localsolver;

    // Number of customers (= number of nodes minus 1)
    int nbCustomers;

    // Capacity of the trucks
    private int truckCapacity;

    // Demand on each node
    private long[] demands;

    // Distance matrix
    private long[][] distanceMatrix;
    
    // Distances between customers and warehouse
    private long[] distanceWarehouses;

    // Number of trucks
    private int nbTrucks;

    // Decision variables
    private LSExpression[] customersSequences;

    // Are the trucks actually used
    private LSExpression[] trucksUsed;
    
    // Distance traveled by each truck
    LSExpression[] routeDistances;

    // Number of trucks used in the solution
    private LSExpression nbTrucksUsed;

    // Distance traveled by all the trucks
    private LSExpression totalDistance;

    private Cvrp(LocalSolver localsolver) {
        this.localsolver = localsolver;
    }

    private void solve(int limit) {
        // Declares the optimization model.
        LSModel model = localsolver.getModel();

        trucksUsed = new LSExpression[nbTrucks];
        customersSequences = new LSExpression[nbTrucks];
        routeDistances = new LSExpression[nbTrucks];

        // Sequence of customers visited by each truck.
        for (int k = 0; k < nbTrucks; k++)
            customersSequences[k] = model.listVar(nbCustomers);

        // All customers must be visited by the trucks
        model.constraint(model.partition(customersSequences));

        // Create demands and distances as arrays to be able to access it with an "at" operator
        LSExpression demandsArray = model.array(demands);
        LSExpression distanceWarehouseArray = model.array(distanceWarehouses);
        LSExpression distanceArray = model.array(distanceMatrix);

        for (int k = 0; k < nbTrucks; k++) {
            LSExpression sequence = customersSequences[k];
            LSExpression c = model.count(sequence);

            // A truck is used if it visits at least one customer
            trucksUsed[k] = model.gt(c, 0);

            // The quantity needed in each route must not exceed the truck capacity
            LSExpression demandSelector = model.lambdaFunction(i -> model.at(demandsArray, model.at(sequence, i)));
            LSExpression routeQuantity = model.sum(model.range(0, c), demandSelector);
            model.constraint(model.leq(routeQuantity, truckCapacity));

            // Distance traveled by truck k
            LSExpression distSelector = model.lambdaFunction(i -> model.at(
                        distanceArray,
                        model.at(sequence, model.sub(i, 1)),
                        model.at(sequence, i)));
            routeDistances[k] = model.sum(model.sum(model.range(1, c), distSelector),
                                    model.iif(model.gt(c, 0), model.sum(
                                        model.at(distanceWarehouseArray, model.at(sequence, 0)),
                                        model.at(distanceWarehouseArray, model.at(sequence, model.sub(c, 1)))),  0));
        }

        nbTrucksUsed = model.sum(trucksUsed);
        totalDistance = model.sum(routeDistances);

        // Objective: minimize the number of trucks used, then minimize the distance traveled
        model.minimize(nbTrucksUsed);
        model.minimize(totalDistance);

        model.close();

        // Parameterizes the solver.
        localsolver.getParam().setTimeLimit(limit);

        localsolver.solve();
    }

    // Writes the solution in a file with the following format:
    // - number of trucks used and total distance
    // - for each truck the nodes visited (omitting the start/end at the depot)
    private void writeSolution(String fileName) throws IOException {
        try (PrintWriter output = new PrintWriter(fileName)) {
            output.println(nbTrucksUsed.getValue() + " " + totalDistance.getValue());
            for (int k = 0; k < nbTrucks; k++) {
                if (trucksUsed[k].getValue() != 1) continue;
                // Values in sequence are in [0..nbCustomers-1]. +2 is to put it back in [2..nbCustomers+1]
                // as in the data files (1 being the depot)
                LSCollection customersCollection = customersSequences[k].getCollectionValue();
                for (int i = 0; i < customersCollection.count(); i++) {
                    output.print((customersCollection.get(i) + 2) + " ");
                }
                output.println();
            }
        }
    }

    // The input files follow the "Augerat" format.
    private void readInstance(int customNbTrucks, String fileName) throws IOException {
        // The number of trucks is usually given in the name of the file
        // nbTrucks can also be given in command line
        nbTrucks = customNbTrucks <= 0 ? extractNbTrucksFromFileName(fileName) : customNbTrucks;

        if (nbTrucks <= 0) {
            throw new RuntimeException("Error: nbTrucks is incorrect or could not be read from the file name. "
                    + "Enter a strictly positive number from the command line");
        }

        try (Scanner input = new Scanner(new File(fileName))) {
            int nbNodes = 0;
            String[] splitted;
            while (true) {
                splitted = input.nextLine().split(":");
                if (splitted[0].contains("DIMENSION")) {
                    nbNodes = Integer.parseInt(splitted[1].trim());
                    nbCustomers = nbNodes - 1;
                } else if (splitted[0].contains("CAPACITY")) {
                    truckCapacity = Integer.parseInt(splitted[1].trim());
                } else if (splitted[0].contains("EDGE_WEIGHT_TYPE")) {
                    if (splitted[1].trim().compareTo("EUC_2D") != 0) {
                        throw new RuntimeException("Edge Weight Type " + splitted[1] + " is not supported (only EUC_2D)");
                    }
                } else if (splitted[0].contains("NODE_COORD_SECTION")) {
                    break;
                }
            }

            int[] customersX = new int[nbCustomers];
            int[] customersY = new int[nbCustomers];
            int depotX = 0, depotY = 0;
            for (int n = 1; n <= nbNodes; n++) {
                int id = input.nextInt();
                if (id != n) throw new IOException("Unexpected index");
                if (n == 1) {
                    depotX = input.nextInt(); 
                    depotY = input.nextInt();  
                } else {
                    // -2 because orginal customer indices are in 2..nbNodes 
                    customersX[n - 2] = input.nextInt(); 
                    customersY[n - 2] = input.nextInt(); 
                }    
            }

            computeDistanceMatrix(depotX, depotY, customersX, customersY);;

            splitted = input.nextLine().split(":"); // End the last line
            splitted = input.nextLine().split(":");
            if (!splitted[0].contains("DEMAND_SECTION")) {
                throw new RuntimeException("Expected keyword DEMAND_SECTION");
            }

            demands = new long[nbCustomers];
            for (int n = 1; n <= nbNodes; n++) {
                int id = input.nextInt();
                if (id != n) throw new IOException("Unexpected index");
                int demand = input.nextInt();
                if (n == 1) {
                    if (demand != 0) throw new IOException("Warehouse demand is supposed to be 0");
                } else {
                    // -2 because orginal customer indices are in 2..nbNodes 
                    demands[n - 2] = demand;
                }
            }

            splitted = input.nextLine().split(":"); // End the last line
            splitted = input.nextLine().split(":");
            if (!splitted[0].contains("DEPOT_SECTION")) {
                throw new RuntimeException("Expected keyword DEPOT_SECTION");
            }

            int warehouseId = input.nextInt();
            if (warehouseId != 1) throw new IOException("Warehouse id is supposed to be 1");

            int endOfDepotSection = input.nextInt();
            if (endOfDepotSection != -1) {
                throw new RuntimeException("Expecting only one warehouse, more than one found");
            }
        }
    }

    // Computes the distance matrix
    private void computeDistanceMatrix(int depotX, int depotY, int[] customersX, int[] customersY) {
        distanceMatrix = new long[nbCustomers][nbCustomers];
        for (int i = 0; i < nbCustomers; i++) {
            distanceMatrix[i][i] = 0;
            for (int j = i + 1; j < nbCustomers; j++) {
                long dist = computeDist(customersX[i], customersX[j], customersY[i], customersY[j]);
                distanceMatrix[i][j] = dist;
                distanceMatrix[j][i] = dist;
            }
        }
        
        distanceWarehouses = new long[nbCustomers];
        for (int i = 0; i < nbCustomers; ++i) {
            distanceWarehouses[i] = computeDist(depotX, customersX[i], depotY, customersY[i]);
        }
    }

    private long computeDist(int xi, int xj, int yi, int yj) {
        double exactDist = Math.sqrt(Math.pow(xi - xj, 2) + Math.pow(yi - yj, 2));
        return Math.round(exactDist);
    }

    private int extractNbTrucksFromFileName(String fileName) {
        int begin = fileName.lastIndexOf("-k");
        if (begin != -1) {
            int end = fileName.indexOf(".", begin + 2);
            return Integer.parseInt(fileName.substring(begin + 2, end));
        } else {
            return -1;
        }
    }

    public static void main(String[] args) {
        if (args.length < 1) {
            System.err.println("Usage: java Cvrp inputFile [outputFile] [timeLimit] [nbTrucks]");
            System.exit(1);
        }

        try (LocalSolver localsolver = new LocalSolver()) {
            String instanceFile = args[0];
            String outputFile = args.length > 1 ? args[1] : null;
            String strTimeLimit = args.length > 2 ? args[2] : "20";
            String strNbTrucks = args.length > 3 ? args[3] : "0";

            Cvrp model = new Cvrp(localsolver);
            model.readInstance(Integer.parseInt(strNbTrucks), instanceFile);
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
