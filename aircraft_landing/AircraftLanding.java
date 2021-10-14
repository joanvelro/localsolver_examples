/********** AircraftLanding.java **********/

import java.util.*;
import java.io.*;
import localsolver.*;

public class AircraftLanding {

    // Data from the problem
    private int nbPlanes;
    private int[] earliestTime;
    private int[] targetTime;
    private int[] latestTime;
    private float[] earlinessCost;
    private float[] latenessCost;
    private int[][] separationTime;

    // LocalSolver
    private final LocalSolver localsolver;

    // Decision variables
    private LSExpression landingOrder;
    private LSExpression[] preferredTime;

    // Landing time for each plane
    private LSExpression landingTime;

    // Objective
    private LSExpression totalCost;

    private AircraftLanding(LocalSolver localsolver) {
        this.localsolver = localsolver;
    }

    /* Read instance data. */
    private void readInstance(String fileName) throws IOException {
        try (Scanner input = new Scanner(new File(fileName))) {
            nbPlanes = input.nextInt();
            input.nextInt(); // Skip freezeTime value

            earliestTime = new int[nbPlanes];
            targetTime = new int[nbPlanes];
            latestTime = new int[nbPlanes];
            earlinessCost = new float[nbPlanes];
            latenessCost = new float[nbPlanes];
            separationTime = new int[nbPlanes][nbPlanes];

            for (int p = 0; p < nbPlanes; p++) {
                input.nextInt(); // Skip appearanceTime values
                earliestTime[p] = input.nextInt();
                targetTime[p] = input.nextInt();
                latestTime[p] = input.nextInt();
                earlinessCost[p] = Float.parseFloat(input.next());
                latenessCost[p] = Float.parseFloat(input.next());
                for (int pp = 0; pp < nbPlanes; pp++) {
                    separationTime[p][pp] = input.nextInt();
                }
            }
        }
    }

    private LSExpression getMinLandingTime(LSExpression p, LSExpression prev, LSExpression separationTimeArray, LSModel model) {
        LSExpression planeIndex = model.at(landingOrder, p);
        LSExpression previousPlaneIndex = model.at(landingOrder, model.sub(p, 1));
        return model.iif(model.gt(p, 0),
                         model.sum(prev, model.at(separationTimeArray, previousPlaneIndex, planeIndex)),
                         0);
    }

    private void solve(int limit) {
        // Declare the optimization model
        LSModel model = localsolver.getModel();

        // A list variable: landingOrder[i] is the index of the ith plane to land
        landingOrder = model.listVar(nbPlanes);

        // All planes must be scheduled
        model.constraint(model.eq(model.count(landingOrder), nbPlanes));

        // Create LocalSolver arrays in order to be able to access them with "at" operators
        LSExpression targetTimeArray = model.array(targetTime);
        LSExpression latestTimeArray = model.array(latestTime);
        LSExpression earlinessCostArray = model.array(earlinessCost);
        LSExpression latenessCostArray = model.array(latenessCost);
        LSExpression separationTimeArray = model.array(separationTime);

        // Int variables: preferred time for each plane
        preferredTime = new LSExpression[nbPlanes];
        for (int p = 0; p < nbPlanes; ++p) {
            preferredTime[p] = model.intVar(earliestTime[p], targetTime[p]);
        }
        LSExpression preferredTimeArray = model.array(preferredTime);

        // Landing time for each plane
        LSExpression landingTimeSelector = model.lambdaFunction((p, prev) ->
                                           model.max(model.at(preferredTimeArray, model.at(landingOrder, p)),
                                                     getMinLandingTime(p, prev, separationTimeArray, model)));
        landingTime = model.array(model.range(0, nbPlanes), landingTimeSelector);

        // Landing times must respect the separation time with every previous plane.
        for (int p = 1; p < nbPlanes; ++p) {
            LSExpression lastSeparationEnd = model.max();
            for (int previousPlane = 0; previousPlane < p; ++previousPlane) {
                lastSeparationEnd.addOperand(model.sum(model.at(landingTime, previousPlane),
                                  model.at(separationTimeArray, model.at(landingOrder, previousPlane), model.at(landingOrder, p))));
            }
            model.constraint(model.geq(model.at(landingTime, p), lastSeparationEnd));
        }

        totalCost = model.sum();
        for (int p = 0; p < nbPlanes; ++p) {
            LSExpression planeIndex = model.at(landingOrder, p);

            // Constraint on latest landing time
            model.addConstraint(model.leq(model.at(landingTime, p), model.at(latestTimeArray, planeIndex)));

            // Cost for each plane
            LSExpression unitCost = model.iif(model.lt(model.at(landingTime, p), model.at(targetTimeArray, planeIndex)),
                                              model.at(earlinessCostArray, planeIndex),
                                              model.at(latenessCostArray, planeIndex));
            LSExpression differenceToTargetTime = model.abs(model.sub(model.at(landingTime, p), model.at(targetTimeArray, planeIndex)));
            totalCost.addOperand(model.prod(unitCost, differenceToTargetTime));
        }

        // Minimize the total cost
        model.minimize(totalCost);

        model.close();

        // Parameterize the solver
        localsolver.getParam().setTimeLimit(limit);

        localsolver.solve();
    }

    /* Write the solution in a file */
    private void writeSolution(String fileName) throws IOException {
        try (PrintWriter output = new PrintWriter(new FileWriter(fileName))) {
            output.println(totalCost.getDoubleValue());
            LSCollection landingOrderCollection = landingOrder.getCollectionValue();
            for (int i = 0; i < nbPlanes; i++) {
                output.print(landingOrderCollection.get(i) + " ");
            }
            output.println();
        }
    }

    public static void main(String[] args) {
        if (args.length < 1) {
            System.err.println("Usage: AircraftLanding inputFile [outputFile] [timeLimit]");
            System.exit(1);
        }

        String instanceFile = args[0];
        String outputFile = args.length > 1 ? args[1] : null;
        String strTimeLimit = args.length > 2 ? args[2] : "20";
        try (LocalSolver localsolver = new LocalSolver()) {
            AircraftLanding model = new AircraftLanding(localsolver);
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
