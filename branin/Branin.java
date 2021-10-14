/********** Branin.java **********/

import java.io.*;
import localsolver.*;

public class Branin {
    // Parameters of the function
    private static final double PI = 3.14159265359;
    private static final int a = 1;
    private static final double b = 5.1 / (4 * Math.pow(PI, 2));
    private static final double c = 5 / PI;
    private static final int r = 6;
    private static final int s = 10;
    private static final double t = 1 / (8 * PI);

    // Solver
    private final LocalSolver localsolver;

    // LS Program variables.
    private LSExpression x1;
    private LSExpression x2;

    private Branin(LocalSolver localsolver) {
        this.localsolver = localsolver;
    }

    // Declares the optimization model.
    private void solve(int limit) {
        LSModel model = localsolver.getModel();

        // numerical decisions
        x1 = model.floatVar(-5, 10);
        x2 = model.floatVar(0, 15);

        // f = a(x2 - b*x1^2 + c*x1 - r)^2 + s(1-t)cos(x1) + s
        LSExpression f = model.sum();

        // f1 = x2 - b*x1^2 + c*x1 - r
        LSExpression f1 = model.sum();
        f1.addOperand(x2);
        f1.addOperand(model.prod(-b, model.pow(x1, 2)));
        f1.addOperand(model.prod(c, x1));
        f1.addOperand(-r);

        // f = a*f1^2 + s(1-t)cos(x1) + s
        f.addOperand(model.prod(a, model.pow(f1, 2)));
        f.addOperand(model.prod(s * (1 - t), model.cos(x1)));
        f.addOperand(s);

        // minimize f
        model.minimize(f);

        // close model, then solve
        model.close();

        // Parameterizes the solver.
        localsolver.getParam().setTimeLimit(limit);

        localsolver.solve();
    }

    // Writes the solution in a file
    private void writeSolution(String fileName) throws IOException {
        try (PrintWriter output = new PrintWriter(fileName)) {
            output.println("x1=" + x1.getDoubleValue());
            output.println("x2=" + x2.getDoubleValue());
        }
    }

    public static void main(String[] args) {
        String outputFile = args.length > 0 ? args[0] : null;
        String strTimeLimit = args.length > 1 ? args[1] : "6";

         try (LocalSolver localsolver = new LocalSolver()) {
            Branin model = new Branin(localsolver);
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
