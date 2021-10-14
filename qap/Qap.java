/********** Qap.java **********/

import java.util.*;
import java.io.*;
import localsolver.*;

public class Qap {
    // Number of points
    private int n;

    // Distance between locations
    private int[][] A;
    // Flow between facilites
    private long[][] B;

    // Solver.
    private final LocalSolver localsolver;

    // LS Program variables
    private LSExpression p;

    // Objective
    private LSExpression obj;

    private Qap(LocalSolver localsolver) {
        this.localsolver = localsolver;
    }

    // Reads instance data
    private void readInstance(String fileName) throws IOException {
        try (Scanner input = new Scanner(new File(fileName))) {
            n = input.nextInt();

            A = new int[n][n];
            for (int i = 0; i < n; i++) {
                for (int j = 0; j < n; j++) {
                    A[i][j] = input.nextInt();
                }
            }

            B = new long[n][n];
            for (int i = 0; i < n; i++) {
                for (int j = 0; j < n; j++) {
                    B[i][j] = input.nextInt();
                }
            }
        }
    }

    private void solve(int limit) {
        // Declares the optimization model
        LSModel model = localsolver.getModel();

        // Permutation such that p[i] is the facility on the location i
        p = model.listVar(n);
        // [] operator is not overloaded, so we create a LSExpression array for easier access
        // of the elements of the permitation (instead of creating an at operator by hand
        // everytime we want to access an element in the list)
        LSExpression[] pElements = new LSExpression[n];
        for (int i = 0; i < n; i++) {
            pElements[i] = model.at(p, i);
        }

        // The list must be complete
        model.constraint(model.eq(model.count(p), n));

        // Create B as an array to be accessed by an at operator
        LSExpression arrayB = model.array(B);

        // Minimize the sum of product distance*flow
        obj = model.sum();
        for (int i = 0; i < n; i++) {
            for (int j = 0; j < n; j++) {
                LSExpression prod = model.prod();
                prod.addOperand(A[i][j]);
                prod.addOperand(model.at(arrayB, pElements[i], pElements[j]));
                obj.addOperand(prod);
            }
        }
        model.minimize(obj);

        model.close();

        // Parameterizes the solver.
        localsolver.getParam().setTimeLimit(limit);
        localsolver.solve();
    }

    // Writes the solution in a file with the following format:
    // - n objValue
    // - permutation p
    private void writeSolution(String fileName) throws IOException {
        try (PrintWriter output = new PrintWriter(fileName)) {
            output.println(n + " " + obj.getValue());
            LSCollection pCollection = p.getCollectionValue();
            for (int i = 0; i < n; i++)
                output.print(pCollection.get(i) + " ");
            output.println();
        }
    }

    public static void main(String[] args) {
        if (args.length < 1) {
            System.out.println("Usage: java Qap inputFile [outputFile] [timeLimit]");
            System.exit(1);
        }

        String instanceFile = args[0];
        String outputFile = args.length > 1 ? args[1] : null;
        String strTimeLimit = args.length > 2 ? args[2] : "300";

        try (LocalSolver localsolver = new LocalSolver()) {
            Qap model = new Qap(localsolver);
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
