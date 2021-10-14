/********** CurveFitting.java **********/

import java.util.*;
import java.io.*;
import localsolver.*;

public class CurveFitting {
    // Number of observations
    private int nbObservations;

    // Inputs and Outputs
    private double[] inputs;
    private double[] outputs;

    // Solver
    private final LocalSolver localsolver;

    // Decision variables (parameters of the mapping function)
    private LSExpression a, b, c, d;

    // Objective (square error)
    private LSExpression squareError;

    private CurveFitting(LocalSolver localsolver) {
        this.localsolver = localsolver;
    }

    // Reads instance data
    private void readInstance(String fileName) throws IOException {
        try (Scanner input = new Scanner(new File(fileName))) {
            input.useLocale(Locale.ROOT);
            
            nbObservations = input.nextInt();

            inputs = new double[nbObservations];
            outputs = new double[nbObservations];
            for (int i = 0; i < nbObservations; i++) {
                inputs[i] = input.nextDouble();
                outputs[i] = input.nextDouble();
            }
        }
    }

    private void solve(int limit) {
        // Declares the optimization model
        LSModel model = localsolver.getModel();

        // Decision variables
        a = model.floatVar(-100, 100);
        b = model.floatVar(-100, 100);
        c = model.floatVar(-100, 100);
        d = model.floatVar(-100, 100);

        // Minimize square error
        squareError = model.sum();
        for (int i = 0; i < nbObservations; i++) {
            LSExpression prediction = model.sum(model.prod(a, model.sin(model.sub(b, inputs[i]))), model.prod(c, Math.pow(inputs[i], 2)), d);
            LSExpression error = model.pow(model.sub(prediction, outputs[i]), 2);
            squareError.addOperand(error);
        }
    
        model.minimize(squareError);
        model.close();

        // Parameterizes the solver
        localsolver.getParam().setTimeLimit(limit);

        localsolver.solve();       
    }

    // Writes the solution in a file 
    private void writeSolution(String fileName) throws IOException {
        try (PrintWriter output = new PrintWriter(fileName)) {
            output.println("Optimal mapping function");
            output.println("a = " + a.getDoubleValue());
            output.println("b = " + b.getDoubleValue());
            output.println("c = " + c.getDoubleValue());
            output.println("d = " + d.getDoubleValue());
        }
    }
    
     public static void main(String[] args) {
        if (args.length < 1) {
            System.err.println("Usage: java CurveFitting inputFile [outputFile] [timeLimit]");
            System.exit(1);
        }

        String instanceFile = args[0];
        String outputFile = args.length > 1 ? args[1] : null;
        String strTimeLimit = args.length > 2 ? args[2] : "3";

         try (LocalSolver localsolver = new LocalSolver()) {
            CurveFitting model = new CurveFitting(localsolver);
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