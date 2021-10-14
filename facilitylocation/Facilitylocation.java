/********** Facilitylocation.java **********/

import java.util.*;
import java.io.*;
import localsolver.*;

public class Facilitylocation {
    // Number of locations
    private int N;

    // Number of edges between locations
    private int E;

    // Size of the subset S of facilities
    private int p;

    // Weight matrix of the shortest path between locations
    private int[][] w;

    // Maximum distance between two locations
    private int wmax;

    // LocalSolver.
    private final LocalSolver localsolver;

    // Decisions variables
    private LSExpression[] x;

    // Objective
    private LSExpression totalCost;

    // List of selected locations
    private List<Integer> solution;

    private Facilitylocation(LocalSolver localsolver) {
        this.localsolver = localsolver;
    }

    // Reads instance data
    private void readInstance(String fileName) throws IOException {
        try (Scanner input = new Scanner(new File(fileName))) {
            N = input.nextInt();
            E = input.nextInt();
            p = input.nextInt();

            w = new int[N][N];
            wmax = 0;
            for (int i = 0; i < N; i++) {
                for (int j = 0; j < N; j++) {
                    w[i][j] = input.nextInt();
                    if (w[i][j] > wmax)
                        wmax = w[i][j];
                }
            }
        }
    }

    // Declares the optimization model
    private void solve(int limit) {
        LSModel model = localsolver.getModel();

        // One variable for each location : 1 if facility, 0 otherwise
        x = new LSExpression[N];
        for (int i = 0; i < N; i++) {
            x[i] = model.boolVar();
        }

        // No more than p locations are selected to be facilities
        LSExpression openedLocations = model.sum(x);
        model.constraint(model.leq(openedLocations, p));

        // Costs between location i and j is w[i][j] if j is a facility or 2*wmax if not
        LSExpression[][] costs = new LSExpression[N][N];
        for (int i = 0; i < N; i++) {
            for (int j = 0; j < N; j++) {
                costs[i][j] = model.iif(x[j], w[i][j], 2 * wmax);
            }
        }

        // Cost between location i and the closest facility
        LSExpression[] cost = new LSExpression[N];
        for (int i = 0; i < N; i++) {
            cost[i] = model.min(costs[i]);
        }

        // Minimize the total cost
        totalCost = model.sum(cost);
        model.minimize(totalCost);

        model.close();

        // Parameterizes the solver
        localsolver.getParam().setTimeLimit(limit);
        localsolver.solve();

        solution = new ArrayList<Integer>();
        for (int i = 0; i < N; i++) {
            if (x[i].getValue() == 1)
                solution.add(i);
        }
    }

    // Writes the solution in a file following the following format:
    // - value of the objective
    // - indices of the facilities (between 0 and N-1) */
    private void writeSolution(String fileName) throws IOException {
        try (PrintWriter output = new PrintWriter(fileName)) {
            output.println(totalCost.getValue());
            for (int i = 0; i < solution.size(); i++) {
                output.print(solution.get(i) + " ");
            }
            output.println();
        }
    }

    public static void main(String[] args) {
        if (args.length < 1) {
            System.err.println("Usage: java Facilitylocation inputFile [outputFile] [timeLimit]");
            System.exit(1);
        }

        String instanceFile = args[0];
        String outputFile = args.length > 1 ? args[1] : null;
        String strTimeLimit = args.length > 2 ? args[2] : "10";

        try (LocalSolver localsolver = new LocalSolver()) {
            Facilitylocation model = new Facilitylocation(localsolver);
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
