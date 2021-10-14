/********** OptimalBucket.java **********/
import java.io.*;
import localsolver.*;

public class OptimalBucket {
    private static final double PI = 3.14159265359;

    // Solver.
    private final LocalSolver localsolver;

    // LS Program variables.
    private LSExpression R;
    private LSExpression r;
    private LSExpression h;

    private LSExpression surface;
    private LSExpression volume;

    private OptimalBucket(LocalSolver localsolver) {
        this.localsolver = localsolver;
    }

    private void solve(int limit) {
        // Declares the optimization model.
        LSModel model = localsolver.getModel();
        LSExpression piConst = model.createConstant(PI);

        // Numerical decisions
        R = model.floatVar(0, 1);
        r = model.floatVar(0, 1);
        h = model.floatVar(0, 1);

        // Surface related expressions
        // s1 = PI*r^2
        LSExpression s1 = model.prod(piConst, r, r);
        // s2 = (R - r)^2
        LSExpression s2 = model.pow(model.sub(R, r), 2);
        // s3 = h^2
        LSExpression s3 = model.pow(h, 2);
        // s4 = sqrt((R-r)^2 + h^2)
        LSExpression s4 = model.sqrt(model.sum(s2, s3));
        // s5 = R+r */
        LSExpression s5 = model.sum(R, r);
        // s6 = PI*(R + r)*sqrt((R - r)^2 + h^2)
        LSExpression s6 = model.prod(piConst, s5, s4);

        // surface = PI*r^2 + PI*(R+r)*sqrt((R - r)^2 + h^2)
        surface = model.sum(s1, s6);
        // Surface must not exceed the surface of the plain disc
        model.addConstraint(model.leq(surface, PI));

        // Volume related expressions
        // v1 = R^2
        LSExpression v1 = model.pow(R, 2);
        // v2 = R*r
        LSExpression v2 = model.prod(R, r);
        // v3 = r^2
        LSExpression v3 = model.pow(r, 2);

        // volume = PI*h/3*(R^2 + R*r + r^2)
        volume = model.prod(piConst, model.div(h, 3), model.sum(v1, v2, v3));

        // Maximize the volume
        model.maximize(volume);

        model.close();

        // Parameterizes the solver.
        localsolver.getParam().setTimeLimit(limit);

        localsolver.solve();
    }

    // Writes the solution in a file with the following format:
    // - surface and volume of the bucket
    // - values of R, r and h
    private void writeSolution(String fileName) throws IOException {
        try (PrintWriter output = new PrintWriter(fileName)) {
            output.println(surface.getDoubleValue() + " " + volume.getDoubleValue());
            output.println(R.getDoubleValue() + " " + r.getDoubleValue() + " " + h.getDoubleValue());
        }
    }

    public static void main(String[] args) {

        String outputFile = args.length > 0 ? args[0] : null;
        String strTimeLimit = args.length > 1 ? args[1] : "2";

         try (LocalSolver localsolver = new LocalSolver()) {
            OptimalBucket model = new OptimalBucket(localsolver);
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
