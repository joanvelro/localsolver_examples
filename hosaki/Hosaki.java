/********** Hosaki.java **********/

import java.io.*;
import java.lang.Math;
import localsolver.*;

public class Hosaki {

    /* Black-box function */
    private static class HosakiFunction implements LSDoubleBlackBoxFunction {
        @Override
        public double call(LSBlackBoxArgumentValues argumentValues) {
            double x1 = argumentValues.getDoubleValue(0);
            double x2 = argumentValues.getDoubleValue(1);
            return (1 - 8*x1 + 7*x1*x1 - 7*Math.pow(x1, 3)/3 + Math.pow(x1, 4)/4)
                * x2*x2 * Math.exp(-x2);
        }
    }

    // Solver
    private final LocalSolver localsolver;

    // LS Program variables
    private LSExpression x1;
    private LSExpression x2;
    private LSExpression bbCall;

    private Hosaki(LocalSolver localsolver) {
        this.localsolver = localsolver;
    }

    // Declares the optimization model
    private void solve(int evaluationLimit) {
        LSModel model = localsolver.getModel();

        // Numerical decisions
        x1 = model.floatVar(0, 5);
        x2 = model.floatVar(0, 6);

        // Creates and calls blackbox function
        HosakiFunction function = new HosakiFunction();
        LSExpression bbFunc = model.doubleBlackBoxFunction(function);
        bbCall = model.call(bbFunc, x1, x2);

        // Minimizes function call
        model.minimize(bbCall);
        model.close();

        // Parameterizes the solver
        LSBlackBoxContext context = bbFunc.getBlackBoxContext();
        context.setEvaluationLimit(evaluationLimit);

        localsolver.solve();
    }

    // Writes the solution in a file
    private void writeSolution(String fileName) throws IOException {
        try (PrintWriter output = new PrintWriter(fileName)) {
            output.println("obj=" + bbCall.getDoubleValue());
            output.println("x1=" + x1.getDoubleValue());
            output.println("x2=" + x2.getDoubleValue());
        }
    }

    public static void main(String[] args) {
        String outputFile = args.length > 0 ? args[0] : null;
        String strEvaluationLimit = args.length > 1 ? args[1] : "30";

         try (LocalSolver localsolver = new LocalSolver()) {
            Hosaki model = new Hosaki(localsolver);
            model.solve(Integer.parseInt(strEvaluationLimit));
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
