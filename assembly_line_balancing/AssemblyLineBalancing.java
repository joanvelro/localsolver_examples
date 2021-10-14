/********** AssemblyLineBalancing.java **********/

import java.util.*;
import java.io.*;
import localsolver.*;

public class AssemblyLineBalancing {

    private static class ALBInstance {
        int nbTasks;
        int nbMaxStations;
        int cycleTime;
        int[] processingTime;
        ArrayList<ArrayList<Integer>> successors;

        // Constructor
        private ALBInstance(String fileName) throws IOException {
            readInput(fileName);
        }

        // Read instance data
        private void readInput(String fileName) throws IOException {
            try (Scanner input = new Scanner(new File(fileName))) {

                input.nextLine();
                // Read number of tasks
                nbTasks = input.nextInt();
                nbMaxStations = nbTasks;
                processingTime = new int[nbTasks];
                successors = new ArrayList<ArrayList<Integer>>(nbTasks);
                for (int i = 0; i < nbTasks; i ++)
                    successors.add(i, new ArrayList<Integer>());
                for (int i = 0; i < 3; i++)
                    input.nextLine();

                // Read the cycle time limit
                cycleTime = input.nextInt();
                for (int i = 0; i < 7; ++i)
                    input.nextLine();

                // Read the processing times
                for (int i = 0; i < nbTasks; i++)
                    processingTime[input.nextInt()-1] = input.nextInt();
                for (int i = 0; i < 3; ++i)
                    input.nextLine();

                // Read the successors' relations
                String line = input.nextLine();
                while (!line.isEmpty()) {
                    String lineSplit[] = line.split(",");
                    int predecessor = Integer.parseInt(lineSplit[0]) -1;
                    int successor = Integer.parseInt(lineSplit[1]) -1;
                    successors.get(predecessor).add(successor);
                    line = input.nextLine();
                }
            }
        }
    }

    private static class ALBProblem {

        // LocalSolver
        private final LocalSolver localsolver;

        // Instance data
        private final ALBInstance instance;

        // Decision variables
        private LSExpression[] station;

        // Intermediate expressions
        private LSExpression[] timeInStation;
        private LSExpression[] taskStation;

        // Objective
        private LSExpression nbUsedStations;

        // Constructor
        private ALBProblem(LocalSolver localsolver, ALBInstance instance) {
            this.localsolver = localsolver;
            this.instance = instance;
        }

        private void solve(int limit) {
            // Declare the optimization model
            LSModel model = localsolver.getModel();

            // station[s] is the set of tasks assigned to station s
            station = new LSExpression[instance.nbMaxStations];
            LSExpression partition = model.partition();
            for (int s = 0; s < instance.nbMaxStations; s++) {
                station[s] = model.setVar(instance.nbTasks);
                partition.addOperand(station[s]);
            }
            model.constraint(partition);

            // nbUsedStations is the total number of used stations
            nbUsedStations = model.sum();
            for (int s = 0; s < instance.nbMaxStations; s++) {
                nbUsedStations.addOperand(model.gt(model.count(station[s]), 0));
            }

            // All stations must respect the cycleTime constraint
            timeInStation = new LSExpression[instance.nbMaxStations];
            LSExpression processingTimeArray = model.array(instance.processingTime);
            LSExpression timeSelector = model.lambdaFunction(i -> model.at(processingTimeArray, i));
            for (int s = 0; s < instance.nbMaxStations; s++) {
                timeInStation[s] = model.sum(station[s], timeSelector);
                model.constraint(model.leq(timeInStation[s], instance.cycleTime));
            }

            // The stations must respect the succession's order of the tasks
            taskStation = new LSExpression[instance.nbTasks];
            for (int i = 0; i < instance.nbTasks; i++) {
                taskStation[i] = model.sum();
                for (int s = 0; s < instance.nbMaxStations; s++) {
                    taskStation[i].addOperand(model.prod(model.contains(station[s], i), s));
                }
            }
            for (int i = 0; i < instance.nbTasks; i++) {
                ArrayList<Integer> successors_i = instance.successors.get(i);
                for (int j : successors_i) {
                    model.constraint(model.leq(taskStation[i], taskStation[j]));
                }
            }

            // Minimization of the number of active stations
            model.minimize(nbUsedStations);

            model.close();

            // Parametrize the solver
            localsolver.getParam().setTimeLimit(limit);
            // Initialize with a naive solution: each task belongs to one separate station
            // Note: nbTasks equals nbMaxStations
            for (int i = 0; i < instance.nbTasks; i++)
                station[i].getCollectionValue().add(i);

            localsolver.solve();
        }

        /* Write the solution in a file following the format:
        * - 1st line: value of the objective
        * - 2nd line: number of tasks
        * - following lines: task's number, station's number */
        void writeSolution(String fileName) throws IOException {
            try(PrintWriter output = new PrintWriter(new FileWriter(fileName))) {
                output.println(nbUsedStations.getIntValue());
                output.println(instance.nbTasks);
                for (int i = 0; i < instance.nbTasks; i++) {
                    output.print(i + 1);
                    output.print(",");
                    output.println(taskStation[i].getIntValue() + 1);
                }
            }
        }
    }
    public static void main(String [] args) {
        if (args.length < 1) {
            System.err.println("Usage: AssemblyLineBalancing inputFile [outputFile] [timeLimit]");
            System.exit(1);
        }

        String instanceFile = args[0];
        String outputFile = args.length > 1 ? args[1] : null;
        String strTimeLimit = args.length > 2 ? args[2] : "20";
        try (LocalSolver localsolver = new LocalSolver()) {
            ALBInstance instance = new ALBInstance(instanceFile);
            ALBProblem model = new ALBProblem(localsolver, instance);
            model.solve(Integer.parseInt(strTimeLimit));
            if (outputFile != null)
                model.writeSolution(outputFile);
        }
        catch (Exception ex) {
            System.err.println(ex);
            ex.printStackTrace();
            System.exit(1);
        }
    }
}
