/********** SmallesrCircle.java **********/

import java.util.*;
import java.io.*;
import localsolver.*;

public class SmallestCircle {
    // Number of points
    private int nbPoints;

    // Point coordinates
    private int[] coordX;
    private int[] coordY;

    // Minimum and maximum value of the coordinates of the points
    private int minX;
    private int minY;
    private int maxX;
    private int maxY;

    // Solver.
    private final LocalSolver localsolver;

    // LS Program variables
    private LSExpression x;
    private LSExpression y;

    // Objective i
    private LSExpression r;

    private SmallestCircle(LocalSolver localsolver) {
        this.localsolver = localsolver;
    }

    // Reads instance data
    private void readInstance(String fileName) throws IOException {
        try (Scanner input = new Scanner(new File(fileName))) {
            nbPoints = input.nextInt();

            coordX = new int[nbPoints];
            coordY = new int[nbPoints];

            coordX[0] = input.nextInt();
            coordY[0] = input.nextInt();
            minX = coordX[0];
            maxX = coordX[0];
            minY = coordY[0];
            maxY = coordY[0];

            for (int i = 1; i < nbPoints; i++) {
                coordX[i] = input.nextInt();
                coordY[i] = input.nextInt();
                minX = Math.min(coordX[i], minX);
                maxX = Math.max(coordX[i], maxX);
                minY = Math.min(coordY[i], minY);
                maxY = Math.max(coordY[i], maxY);
            }
        }
    }

    private void solve(int limit) {
        // Declares the optimization model.
        LSModel model = localsolver.getModel();

        // Numerical decisions
        x = model.floatVar(minX, maxX);
        y = model.floatVar(minY, maxY);

        // Distance between the origin and the point i
        LSExpression[] radius = new LSExpression[nbPoints];
        for (int i = 0; i < nbPoints; i++) {
            radius[i] = model.sum();
            radius[i].addOperand(model.pow(model.sub(x, coordX[i]), 2));
            radius[i].addOperand(model.pow(model.sub(y, coordY[i]), 2));
        }

        // Minimize the radius r
        r = model.sqrt(model.max(radius));

        model.minimize(r);
        model.close();

        // Parameterizes the solver.
        localsolver.getParam().setTimeLimit(limit);

        localsolver.solve();
    }

    // Writes the solution in a file
    private void writeSolution(String fileName) throws IOException {
        try (PrintWriter output = new PrintWriter(fileName)) {
            output.println("x=" + x.getDoubleValue());
            output.println("y=" + y.getDoubleValue());
            output.println("r=" + r.getDoubleValue());
        }
    }

    public static void main(String[] args) {
        if (args.length < 1) {
            System.err.println("Usage: java SmallestCircle inputFile [outputFile] [timeLimit]");
            System.exit(1);
        }

        String instanceFile = args[0];
        String outputFile = args.length > 1 ? args[1] : null;
        String strTimeLimit = args.length > 2 ? args[2] : "6";
        try (LocalSolver localsolver = new LocalSolver()) {
            SmallestCircle model = new SmallestCircle(localsolver);
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
