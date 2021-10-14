/******** CarSequencing.java *********/

import java.util.*;
import java.io.*;
import localsolver.*;

public class CarSequencing {
    // Number of vehicles.
    private int nbPositions;

    // Number of options.
    private int nbOptions;

    // Number of classes.
    private int nbClasses;

    // Options properties.
    private int[] maxCarsPerWindow;
    private int[] windowSize;

    // Classes properties.
    private int[] nbCars;
    private boolean[][] options;

    // Solver.
    private final LocalSolver localsolver;

    // LS Program variables.
    private LSExpression[][] classOnPos;

    // Objective
    private LSExpression totalViolations;

    private CarSequencing(LocalSolver localsolver) {
        this.localsolver = localsolver;
    }

    // Reads instance data.
    private void readInstance(String fileName) throws IOException {
        try (Scanner input = new Scanner(new File(fileName))) {
            nbPositions = input.nextInt();
            nbOptions = input.nextInt();
            nbClasses = input.nextInt();

            maxCarsPerWindow = new int[nbOptions];
            for (int o = 0; o < nbOptions; o++) {
                maxCarsPerWindow[o] = input.nextInt();
            }

            windowSize = new int[nbOptions];
            for (int o = 0; o < nbOptions; o++) {
                windowSize[o] = input.nextInt();
            }

            options = new boolean[nbClasses][nbOptions];
            nbCars = new int[nbClasses];
            for (int c = 0; c < nbClasses; c++) {
                input.nextInt(); // skip
                nbCars[c] = input.nextInt();
                for (int o = 0; o < nbOptions; o++) {
                    int v = input.nextInt();
                    options[c][o] = (v == 1);
                }
            }
        }
    }

    private void solve(int limit) {
        // Declares the optimization model.
        LSModel model = localsolver.getModel();

        // classOnPos[c][p] = 1 if class c is at position p, and 0 otherwise
        classOnPos = new LSExpression[nbClasses][nbPositions];
        for (int c = 0; c < nbClasses; c++) {
            for (int p = 0; p < nbPositions; p++) {
                classOnPos[c][p] = model.boolVar();
            }
        }

        // All cars of class c are assigned to positions
        for (int c = 0; c < nbClasses; c++) {
            LSExpression nbCarsFromClass = model.sum(classOnPos[c]);
            model.constraint(model.eq(nbCarsFromClass, nbCars[c]));
        }

        // One car assigned to each position p
        for (int p = 0; p < nbPositions; p++) {
            LSExpression nbCarsOnPos = model.sum();
            for (int c = 0; c < nbClasses; c++) {
                nbCarsOnPos.addOperand(classOnPos[c][p]);
            }
            model.constraint(model.eq(nbCarsOnPos, 1));
        }

        // optionsOnPos[o][p] = 1 if option o appears at position p, and 0 otherwise
        LSExpression[][] optionsOnPos = new LSExpression[nbOptions][nbPositions];
        for (int o = 0; o < nbOptions; o++) {
            for (int p = 0; p < nbPositions; p++) {
                optionsOnPos[o][p] = model.or();
                for (int c = 0; c < nbClasses; c++) {
                    if (options[c][o])
                        optionsOnPos[o][p].addOperand(classOnPos[c][p]);
                }
            }
        }

        // Number of cars with option o in each window
        LSExpression[][] nbCarsWindows = new LSExpression[nbOptions][];
        for (int o = 0; o < nbOptions; o++) {
            nbCarsWindows[o] = new LSExpression[nbPositions - windowSize[o] + 1];
            for (int j = 0; j < nbPositions - windowSize[o] + 1; j++) {
                nbCarsWindows[o][j] = model.sum();
                for (int k = 0; k < windowSize[o]; k++) {
                    nbCarsWindows[o][j].addOperand(optionsOnPos[o][j + k]);
                }
            }
        }

        // Number of violations of option o capacity in each window
        LSExpression[][] nbViolationsWindows = new LSExpression[nbOptions][];
        for (int o = 0; o < nbOptions; o++) {
            nbViolationsWindows[o] = new LSExpression[nbPositions - windowSize[o] + 1];
            for (int j = 0; j < nbPositions - windowSize[o] + 1; j++) {
                LSExpression delta = model.sub(nbCarsWindows[o][j], maxCarsPerWindow[o]);
                nbViolationsWindows[o][j] = model.max(0, delta);
            }
        }

        // Minimize the sum of violations for all options and all windows
        totalViolations = model.sum();
        for (int o = 0; o < nbOptions; o++) {
            totalViolations.addOperands(nbViolationsWindows[o]);
        }

        model.minimize(totalViolations);
        model.close();

        // Parameterizes the solver.
        localsolver.getParam().setTimeLimit(limit);

        localsolver.solve();
    }

    // Writes the solution in a file following the following format:
    // - 1st line: value of the objective;
    // - 2nd line: for each position p, index of class at positions p.
    private void writeSolution(String fileName) throws IOException {
        try (PrintWriter output = new PrintWriter(fileName)) {
            output.println(totalViolations.getValue());
            for (int p = 0; p < nbPositions; p++) {
                for (int c = 0; c < nbClasses; c++) {
                    if (classOnPos[c][p].getValue() == 1) {
                        output.print(c + " ");
                        break;
                    }
                }
            }
            output.println();
        }
    }

    public static void main(String[] args) {
        if (args.length < 1) {
            System.err.println("Usage: java CarSequencing inputFile [outputFile] [timeLimit]");
            System.exit(1);
        }

        String instanceFile = args[0];
        String outputFile = args.length > 1 ? args[1] : null;
        String strTimeLimit = args.length > 2 ? args[2] : "60";

        try (LocalSolver localsolver = new LocalSolver()) {
            CarSequencing model = new CarSequencing(localsolver);
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
