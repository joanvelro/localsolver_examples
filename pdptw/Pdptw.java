/********** Pdptw.java **********/

import java.util.*;
import java.io.*;
import localsolver.*;

public class Pdptw {
    // Solver
    private final LocalSolver localsolver;

    // Number of customers
    int nbCustomers;

    // Capacity of the trucks
    private int truckCapacity;

    // Latest allowed arrival to depot
    int maxHorizon;

    // Demand on each node
    List<Integer> demands;

    // Earliest arrival on each node
    List<Integer> earliestStart;

    // Latest departure from each node
    List<Integer> latestEnd;

    // Service time on each node
    List<Integer> serviceTime;

    // Index for pick up for each node
    List<Integer> pickUpIndex;

    // Index for delivery for each node
    List<Integer> deliveryIndex;

    // Distance matrix between customers
    private double[][] distanceMatrix;

    // Distances between customers and warehouse
    private double[] distanceWarehouses;

    // Number of trucks
    private int nbTrucks;

    // Decision variables
    private LSExpression[] customersSequences;

    // Are the trucks actually used
    private LSExpression[] trucksUsed;

    // Distance traveled by each truck
    private LSExpression[] routeDistances;

    // End time array for each truck
    private LSExpression[] endTime;

    // Home lateness for each truck
    private LSExpression[] homeLateness;

    // Cumulated Lateness for each truck
    private LSExpression[] lateness;

    // Cumulated lateness in the solution (must be 0 for the solution to be valid)
    private LSExpression totalLateness;

    // Number of trucks used in the solution
    private LSExpression nbTrucksUsed;

    // Distance traveled by all the trucks
    private LSExpression totalDistance;

    private Pdptw() {
        localsolver = new LocalSolver();
    }

    // Reads instance data
    private void readInstance(String fileName) throws IOException {
        readInputPdptw(fileName);
    }

    private void solve(int limit) {
        // Declares the optimization model
        LSModel model = localsolver.getModel();

        trucksUsed = new LSExpression[nbTrucks];
        customersSequences = new LSExpression[nbTrucks];
        routeDistances = new LSExpression[nbTrucks];
        endTime = new LSExpression[nbTrucks];
        homeLateness = new LSExpression[nbTrucks];
        lateness = new LSExpression[nbTrucks];

        // Sequence of customers visited by each truck
        for (int k = 0; k < nbTrucks; k++)
            customersSequences[k] = model.listVar(nbCustomers);

        // All customers must be visited by the trucks
        model.constraint(model.partition(customersSequences));

        // Create demands and distances as arrays to be able to access them with an "at" operator
        LSExpression demandsArray = model.array(demands);
        LSExpression earliestArray = model.array(earliestStart);
        LSExpression latestArray = model.array(latestEnd);
        LSExpression serviceArray = model.array(serviceTime);

        LSExpression distanceWarehouseArray = model.array(distanceWarehouses);
        LSExpression distanceArray = model.array(distanceMatrix);

        for (int k = 0; k < nbTrucks; k++)
        {
            LSExpression sequence = customersSequences[k];
            LSExpression c = model.count(sequence);

            // A truck is used if it visits at least one customer
            trucksUsed[k] = model.gt(c, 0);

            // The quantity needed in each route must not exceed the truck capacity at any point in the sequence
            LSExpression demandCumulator = model.lambdaFunction((i, prev) -> model.sum(prev, model.at(demandsArray, model.at(sequence, i))));
            LSExpression routeQuantity = model.array(model.range(0, c), demandCumulator);

            LSExpression quantityChecker = model.lambdaFunction(i -> model.leq(model.at(routeQuantity, i), truckCapacity));
            model.constraint(model.and(model.range(0, c), quantityChecker));

            // Pickups and deliveries
            for (int i = 0; i < nbCustomers; i++) {
                if (pickUpIndex.get(i) == -1) {
                    model.constraint(model.eq(model.contains(sequence, i), model.contains(sequence, deliveryIndex.get(i))));
                    model.constraint(model.leq(model.indexOf(sequence, i), model.indexOf(sequence, deliveryIndex.get(i))));
                }
            }

            // Distance traveled by truck k
            LSExpression distSelector = model.lambdaFunction(i -> model.at(
                        distanceArray,
                        model.at(sequence, model.sub(i, 1)),
                        model.at(sequence, i)));
            routeDistances[k] = model.sum(model.sum(model.range(1, c), distSelector),
                                    model.iif(model.gt(c, 0), model.sum(
                                        model.at(distanceWarehouseArray, model.at(sequence, 0)),
                                        model.at(distanceWarehouseArray, model.at(sequence, model.sub(c, 1)))), 0));

            // End of each visit
            LSExpression endSelector = model.lambdaFunction((i, prev) -> model.sum(
                         model.max(model.at(earliestArray, model.at(sequence, i)),
                          model.sum(model.iif(model.eq(i, 0),
                              model.at(distanceWarehouseArray, model.at(sequence, 0)),
                              model.sum(prev, model.at(distanceArray, model.at(sequence, model.sub(i, 1)), model.at(sequence, i)))))),
                            model.at(serviceArray, model.at(sequence, i))));

            endTime[k] = model.array(model.range(0, c), endSelector);

            LSExpression theEnd = endTime[k];

            // Arriving home after max_horizon
            homeLateness[k] = model.iif(trucksUsed[k],
                                model.max(0, model.sum(model.at(theEnd, model.sub(c, 1)),
                                                   model.sub(model.at(distanceWarehouseArray, model.at(sequence, model.sub(c, 1))) , maxHorizon))),
                                0);

            // Completing visit after latest_end
            LSExpression lateSelector = model.lambdaFunction(i -> model.max(model.sub(model.at(theEnd, i), model.at(latestArray, model.at(sequence, i))), 0));
            lateness[k] = model.sum(homeLateness[k], model.sum(model.range(0, c), lateSelector));
        }


        totalLateness = model.sum(lateness);
        nbTrucksUsed = model.sum(trucksUsed);
        totalDistance = model.div(model.round(model.prod(100, model.sum(routeDistances))), 100);

        // Objective: minimize the number of trucks used, then minimize the distance traveled
        model.minimize(totalLateness);
        model.minimize(nbTrucksUsed);
        model.minimize(totalDistance);

        model.close();

        // Parameterizes the solver
        localsolver.getParam().setTimeLimit(limit);

        localsolver.solve();
    }

    // Writes the solution in a file with the following format:
    // - number of trucks used and total distance
    // - for each truck the nodes visited (omitting the start/end at the depot)
    private void writeSolution(String fileName) throws IOException {
        try (PrintWriter output = new PrintWriter(fileName)) {
            output.println(nbTrucksUsed.getValue() + " " + totalDistance.getDoubleValue());
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

    // The input files follow the "Li & Lim" format
    private void readInputPdptw(String fileName) throws IOException {
        try (Scanner input = new Scanner(new File(fileName))) {
            int nbNodes = 0;
            int dump = 0;

            nbTrucks = input.nextInt();
            truckCapacity = input.nextInt();
            dump = input.nextInt();

            dump = input.nextInt();
            int depotX = input.nextInt();
            int depotY = input.nextInt();
            dump = input.nextInt();
            dump = input.nextInt();
            maxHorizon = input.nextInt();
            dump = input.nextInt();
            dump = input.nextInt();
            dump = input.nextInt();

            List<Integer> customersX = new ArrayList<Integer>();
            List<Integer> customersY = new ArrayList<Integer>();
            demands = new ArrayList<Integer>();
            earliestStart = new ArrayList<Integer>();
            latestEnd = new ArrayList<Integer>();
            serviceTime = new ArrayList<Integer>();
            pickUpIndex = new ArrayList<Integer>();
            deliveryIndex = new ArrayList<Integer>();

            while (input.hasNextInt()) {
                dump = input.nextInt();
                int cx = input.nextInt();
                int cy = input.nextInt();
                int demand = input.nextInt();
                int ready = input.nextInt();
                int due = input.nextInt();
                int service = input.nextInt();
                int pick = input.nextInt();
                int delivery = input.nextInt();

                customersX.add(cx);
                customersY.add(cy);
                demands.add(demand);
                earliestStart.add(ready);
                latestEnd.add(due+service); // in input files due date is meant as latest start time
                serviceTime.add(service);
                pickUpIndex.add(pick - 1);
                deliveryIndex.add(delivery - 1);
            }

            nbCustomers = customersX.size();

            computeDistanceMatrix(depotX, depotY, customersX, customersY);

        }
    }

    // Computes the distance matrix
    private void computeDistanceMatrix(int depotX, int depotY, List<Integer> customersX, List<Integer> customersY) {
        distanceMatrix = new double[nbCustomers][nbCustomers];
        for (int i = 0; i < nbCustomers; i++) {
            distanceMatrix[i][i] = 0;
            for (int j = i + 1; j < nbCustomers; j++) {
                double dist = computeDist(customersX.get(i), customersX.get(j), customersY.get(i), customersY.get(j));
                distanceMatrix[i][j] = dist;
                distanceMatrix[j][i] = dist;
            }
        }

        distanceWarehouses = new double[nbCustomers];
        for (int i = 0; i < nbCustomers; ++i) {
            distanceWarehouses[i] = computeDist(depotX, customersX.get(i), depotY, customersY.get(i));
        }
    }

    private double computeDist(int xi, int xj, int yi, int yj) {
        return Math.sqrt(Math.pow(xi - xj, 2) + Math.pow(yi - yj, 2));
    }


    public static void main(String[] args) {
        if (args.length < 1) {
            System.err.println("Usage: java Pdptw inputFile [outputFile] [timeLimit]");
            System.exit(1);
        }

        try {
            String instanceFile = args[0];
            String outputFile = args.length > 1 ? args[1] : null;
            String strTimeLimit = args.length > 2 ? args[2] : "20";

            Pdptw model = new Pdptw();
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
