/********** Maxcut.java **********/

import java.util.*;
import java.io.*;
import localsolver.*;

public class Maxcut {
    // LocalSolver
    private final LocalSolver localsolver;

    // Number of vertices
    private int n;

    // Number of edges
    private int m;

    // Origin of each edge
    private int[] origin;

    // Destination of each edge
    private int[] dest;

    // Weight of each edge
    private int[] w;

    // True if vertex x[i] is on the right side of the cut, false if it is on the left side of the cut
    private LSExpression[] x;

    // Objective
    private LSExpression cutWeight;

    private Maxcut(LocalSolver localsolver) {
        this.localsolver = localsolver;
    }

    // Reads instance data.
    private void readInstance(String fileName) throws IOException {
        try (Scanner input = new Scanner(new File(fileName))) {
            n = input.nextInt();
            m = input.nextInt();

            origin = new int[m];
            dest = new int[m];
            w = new int[m];
            for (int e = 0; e < m; e++) {
                origin[e] = input.nextInt();
                dest[e] = input.nextInt();
                w[e] = input.nextInt();
            }
        }
    }

    // Declares the optimization model.
    private void solve(int limit) {
        LSModel model = localsolver.getModel();

        // Decision variables x[i]
        x = new LSExpression[n];
        for (int i = 0; i < n; i++) {
            x[i] = model.boolVar();
        }

        // incut[e] is true if its endpoints are in different class of the partition
        // Note: the indices start at 1 in the instances
        LSExpression[] incut = new LSExpression[m];
        for (int e = 0; e < m; e++) {
            incut[e] = model.neq(x[origin[e] - 1], x[dest[e] - 1]);
        }

        // Size of the cut
        cutWeight = model.sum();
        for (int e = 0; e < m; e++) {
            cutWeight.addOperand(model.prod(w[e], incut[e]));
        }
        model.maximize(cutWeight);

        model.close();

        // Parameterizes the solver.
        localsolver.getParam().setTimeLimit(limit);
        localsolver.solve();
    }

    // Writes the solution in a file following the following format:
    // - objective value
    // - each line contains a vertex number and its subset (1 for S, 0 for V-S) */
    private void writeSolution(String fileName) throws IOException {
        try (PrintWriter output = new PrintWriter(fileName)) {
            output.println(cutWeight.getValue());
            // In the instances the indices start at 1
            for (int i = 0; i < n; i++) {
                output.println((i + 1) + " " + x[i].getValue());
            }
        }
    }

    public static void main(String[] args) {
        if (args.length < 1) {
            System.err.println("Usage: java Maxcut inputFile [outputFile] [timeLimit]");
            System.exit(1);
        }

        String instanceFile = args[0];
        String outputFile = args.length > 1 ? args[1] : null;
        String strTimeLimit = args.length > 2 ? args[2] : "10";

        try (LocalSolver localsolver = new LocalSolver()) {
            Maxcut model = new Maxcut(localsolver);
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
