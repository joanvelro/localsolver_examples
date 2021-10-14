/********** MovieShootScheduling.java **********/

import java.util.Scanner;
import java.io.*;
import localsolver.*;

public class MovieShootScheduling {

    private static class MssInstance {

        int nbActors;
        int nbScenes;
        int nbLocations;
        int nbPrecedences;
        int[] actorCost;
        int[] locationCost;
        int[] sceneDuration;
        int[] sceneLocation;
        int[] nbWorkedDays;

        int[][] precedences;
        boolean[][] isActorInScene;


        /* Constructor */
        private MssInstance(String fileName) throws IOException {
            readInput(fileName);
            computeNbWorkedDays();
        }

        /* Read instance data */
        private void readInput(String fileName) throws IOException {
            try (Scanner input = new Scanner(new File(fileName))) {
                nbActors = input.nextInt();
                nbScenes = input.nextInt();
                nbLocations = input.nextInt();
                nbPrecedences = input.nextInt();
                actorCost = new int[nbActors];
                locationCost = new int[nbLocations];
                sceneDuration = new int[nbScenes];
                sceneLocation = new int[nbScenes];
                isActorInScene = new boolean[nbActors][nbScenes];
                precedences = new int[nbPrecedences][2];

                for (int j = 0; j < nbActors; j++)
                    actorCost[j] = input.nextInt();
                for (int k = 0; k < nbLocations; k++)
                    locationCost[k] = input.nextInt();
                for (int i = 0; i < nbScenes; i++)
                    sceneDuration[i] = input.nextInt();
                for (int i = 0; i < nbScenes; i++)
                    sceneLocation[i] = input.nextInt();
                for (int j = 0; j < nbActors; j++) {
                    for (int i = 0; i < nbScenes; i++) {
                        int tmp = input.nextInt();
                        isActorInScene[j][i] = (tmp == 1);
                    }
                }
                for (int p = 0; p < nbPrecedences; p++) {
                    for (int i = 0; i < 2; i++) {
                        precedences[p][i] = input.nextInt();
                    }
                }
            }
        }

        private void computeNbWorkedDays() {
            nbWorkedDays = new int[nbActors];
            for (int j = 0; j < nbActors; ++j) {
                nbWorkedDays[j] = 0;
                for (int i = 0; i < nbScenes; ++i) {
                    if (isActorInScene[j][i]) {
                        nbWorkedDays[j] += sceneDuration[i];
                    }
                }
            }
        }
    }

    /* External function */
    private static class CostFunction implements LSIntExternalFunction {

        private final MssInstance instance;

        // To maintain thread-safety property, ThreadLocal is used here.
        // Each thread must have independant following variables.

        // Number of visits per location (group of successive shoots)
        private ThreadLocal<int[]> nbLocationVisits;

        // First day of work for each actor
        private ThreadLocal<int[]> actorFirstDay;

        // Last day of work for each actor
        private ThreadLocal<int[]> actorLastDay;

        /* Constructor */
        private CostFunction(MssInstance instance) {
            this.instance = instance;
            this.nbLocationVisits = ThreadLocal.withInitial(() -> new int[instance.nbLocations]);
            this.actorFirstDay = ThreadLocal.withInitial(() -> new int[instance.nbActors]);
            this.actorLastDay = ThreadLocal.withInitial(() -> new int[instance.nbActors]);
        }

        @Override
        public long call(LSExternalArgumentValues argumentValues) {
            LSCollection shootOrder = argumentValues.getCollectionValue(0);
            int shootOrderLength = shootOrder.count();
            if (shootOrderLength < instance.nbScenes) {
                // Infeasible solution if some shoots are missing
                return Integer.MAX_VALUE;
            }

            resetVectors();
            long[] shootOrderArray = new long[shootOrderLength];
            shootOrder.copyTo(shootOrderArray);

            int locationExtraCost = computeLocationCost(shootOrderArray);
            int actorExtraCost = computeActorCost(shootOrderArray);
            return locationExtraCost + actorExtraCost;
        }

        private int computeLocationCost(long[] shootOrderArray) {
            int previousLocation = -1;
            for (int i = 0; i < instance.nbScenes; i++) {
                int currentLocation = instance.sceneLocation[(int) shootOrderArray[i]];
                // When we change location, we increment the number of visits of the new location
                if (previousLocation != currentLocation) {
                    nbLocationVisits.get()[currentLocation] += 1;
                    previousLocation = currentLocation;
                }
            }
            int locationExtraCost = 0;
            for (int k = 0; k < instance.nbLocations; ++k) {
                locationExtraCost += (nbLocationVisits.get()[k] - 1) * instance.locationCost[k];
            }
            return locationExtraCost;
        }

        private int computeActorCost(long[] shootOrderArray) {
            // Compute first and last days of work for each actor
            for (int j = 0; j < instance.nbActors; ++j) {
                boolean hasActorStartedWorking = false;
                int startDayOfScene = 0;
                for (int i = 0; i < instance.nbScenes; ++i) {
                    int currentScene = (int) shootOrderArray[i];
                    int endDayOfScene = startDayOfScene + instance.sceneDuration[currentScene] - 1;
                    if (instance.isActorInScene[j][currentScene]) {
                        actorLastDay.get()[j] = endDayOfScene;
                        if (!hasActorStartedWorking) {
                            hasActorStartedWorking = true;
                            actorFirstDay.get()[j] = startDayOfScene;
                        }
                    }
                    // The next scene begins the day after the end of the current one
                    startDayOfScene = endDayOfScene + 1;
                }
            }

            // Compute actor extra cost due to days paid but not worked
            int actorExtraCost = 0;
            for (int j = 0; j < instance.nbActors; ++j) {
                int nbPaidDays = actorLastDay.get()[j] - actorFirstDay.get()[j] + 1;
                actorExtraCost += (nbPaidDays - instance.nbWorkedDays[j]) * instance.actorCost[j];
            }
            return actorExtraCost;
        }

        private void resetVectors() {
            for (int j = 0; j < instance.nbActors; ++j) {
                actorFirstDay.get()[j] = 0;
                actorLastDay.get()[j] = 0;
            }
            for (int k = 0; k < instance.nbLocations; ++k) {
                nbLocationVisits.get()[k] = 0;
            }
        }
    }

    private static class MSSProblem {

        // LocalSolver
        private final LocalSolver localsolver;

        // Instance data
        private final MssInstance instance;

        // Decision variable
        private LSExpression shootOrder;

        // Objective
        private LSExpression callCostFunc;

        // Constructor
        private MSSProblem(LocalSolver localsolver, MssInstance instance) {
            this.localsolver = localsolver;
            this.instance = instance;
        }

        private void solve(int limit) {
            // Declare the optimization model
            LSModel model = localsolver.getModel();

            // A list variable: shootOrder[i] is the index of the i-th scene to be shot
            shootOrder = model.listVar(instance.nbScenes);

            // Every scene must be scheduled
            model.constraint(model.eq(model.count(shootOrder), instance.nbScenes));

            // Constraint of precedence between scenes
            for (int p = 0; p < instance.nbPrecedences; ++p)
                model.constraint(model.lt(model.indexOf(shootOrder, instance.precedences[p][0]),
                        model.indexOf(shootOrder, instance.precedences[p][1])));

            // Minimize external function
            CostFunction costObject = new CostFunction(instance);
            LSExpression costFunc = model.createIntExternalFunction(costObject);
            costFunc.getExternalContext().setLowerBound(0);
            callCostFunc = model.call(costFunc, shootOrder);
            model.minimize(callCostFunc);

            model.close();

            // Parameterize the solver
            localsolver.getParam().setTimeLimit(limit);

            localsolver.solve();
        }

        /* Write the solution in a file in the following format:
         * - 1st line: value of the objective;
         * - 2nd line: for each i, the index of the i-th scene to be shot. */
        void writeSolution(String fileName) throws IOException {
            try (PrintWriter output = new PrintWriter(new FileWriter(fileName))) {
                output.println(callCostFunc.getIntValue());
                LSCollection shootOrderCollection = shootOrder.getCollectionValue();
                for (int i = 0; i < instance.nbScenes; ++i) {
                    output.print(shootOrderCollection.get(i) + " ");
                }
                output.println();
            }
        }
    }

    public static void main(String[] args) {
        if (args.length < 1) {
            System.err.println("Usage: MovieShootScheduling inputFile [outputFile] [timeLimit]");
            System.exit(1);
        }

        String instanceFile = args[0];
        String outputFile = args.length > 1 ? args[1] : null;
        String strTimeLimit = args.length > 2 ? args[2] : "5";
        try (LocalSolver localsolver = new LocalSolver()) {
            MssInstance instance = new MssInstance(instanceFile);
            MSSProblem model = new MSSProblem(localsolver, instance);
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
