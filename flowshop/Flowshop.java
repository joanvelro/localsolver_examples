/********** Flowshop.java **********/

import java.util.*;
import java.io.*;
import localsolver.*;

public class Flowshop {
    // Number of jobs
    private int nbJobs;

    // Number of machines
    private int nbMachines;

    // Initial seed used to generate the instance
    private long initialSeed;

    // Upper bound
    private int upperBound;

    // Lower bound
    private int lowerBound;

    // Processing time
    private long[][] processingTime;

    // LocalSolver
    private final LocalSolver localsolver;

    // Decision variable
    private LSExpression jobs;

    // Objective
    private LSExpression makespan;

    private Flowshop(LocalSolver localsolver) {
        this.localsolver = localsolver;
    }

    // Reads instance data.
    private void readInstance(String fileName) throws IOException {
        try (Scanner input = new Scanner(new File(fileName))) {
            nbJobs = input.nextInt();
            nbMachines = input.nextInt();
            initialSeed = input.nextInt();
            upperBound = input.nextInt();
            lowerBound = input.nextInt();

            processingTime = new long[nbMachines][nbJobs];
            for (int m = 0; m < nbMachines; m++) {
                for (int j = 0; j < nbJobs; j++) {
                    processingTime[m][j] = input.nextInt();
                }
            }
        }
    }

    private void solve(int limit) {
        // Declares the optimization model.
        LSModel model = localsolver.getModel();

        // Permutation of jobs
        jobs = model.listVar(nbJobs);

        // All jobs have to be assigned
        model.constraint(model.eq(model.count(jobs), nbJobs));

        // For each machine create proccessingTime[m] as an array to be able to access it
        // with an 'at' operator
        LSExpression[] processingTimeArray = new LSExpression[nbMachines];
        for (int m = 0; m < nbMachines; m++) {
            processingTimeArray[m] = model.array(processingTime[m]);
        }

        // On machine 0, the jth job ends on the time it took to be processed after 
        // the end of the previous job
        LSExpression[] end = new LSExpression[nbJobs];
        LSExpression firstEndSelector = model.lambdaFunction((i, prev) -> model.sum(
                    prev, model.at(processingTimeArray[0], model.at(jobs, i))));
        end[0] = model.array(model.range(0, nbJobs), firstEndSelector);

        // The jth job on machine m starts when it has been processed by machine n-1
        // AND when job j-1 has been processed on machine m. It ends after it has been processed.
        for (int m = 1; m < nbMachines; ++m)
        {
            final int mL = m;
            LSExpression endSelector = model.lambdaFunction((i, prev) -> model.sum(
                    model.max(prev, model.at(end[mL - 1], i)),
                    model.at(processingTimeArray[mL], model.at(jobs, i))));
            end[m] = model.array(model.range(0, nbJobs), endSelector);
        }

        // Minimize the makespan: end of the last job on the last machine
        makespan = model.at(end[nbMachines - 1], nbJobs - 1);
        model.minimize(makespan);
        model.close();

        // Parameterizes the solver.
        localsolver.getParam().setTimeLimit(limit);

        localsolver.solve();
    }

    // Writes the solution in a file
    private void writeSolution(String fileName) throws IOException {
        try (PrintWriter output = new PrintWriter(fileName)) {
            output.println(makespan.getValue());
            LSCollection jobsCollection = jobs.getCollectionValue();
            for (int j = 0; j < nbJobs; j++) {
                output.print(jobsCollection.get(j) + " ");
            }
            output.println();
        }
    }

    public static void main(String[] args) {
        if (args.length < 1) {
            System.err.println("Usage: java Flowshop inputFile [outputFile] [timeLimit]");
            System.exit(1);
        }

        String instanceFile = args[0];
        String outputFile = args.length > 1 ? args[1] : null;
        String strTimeLimit = args.length > 2 ? args[2] : "20";

         try (LocalSolver localsolver = new LocalSolver()) {
            Flowshop model = new Flowshop(localsolver);
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
