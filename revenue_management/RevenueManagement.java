
/********** RevenueManagement.java **********/

import java.io.*;
import java.lang.Math;
import java.util.ArrayList;
import java.util.List;
import java.util.Random;

import localsolver.*;

public class RevenueManagement {

    private static class EvaluatedPoint {
        private int[] point;
        private double value;

        public EvaluatedPoint(int[] point, double value) {
            this.point = point;
            this.value = value;
        }
    }

    /* Black-box function */
    private static class RevenueManagementFunction implements LSDoubleBlackBoxFunction {

        private int seed;
        private int nbPeriods = 3;
        private int purchasePrice = 80;
        private int nbSimulations = (int) 1e6;
        private int[] prices = {100, 300, 400};
        private int[] meanDemands = {50, 20, 30};
        private List<EvaluatedPoint> evaluatedPoints = new ArrayList<EvaluatedPoint>();

        public RevenueManagementFunction(int seed) {
            this.seed = seed;
            int[] point = {100, 50, 30};
            evaluatedPoints.add(new EvaluatedPoint(point, 4740.99));
        }

        @Override
        public double call(LSBlackBoxArgumentValues argumentValues) {
            // Initial quantity purchased
            int nbUnitsPurchased = (int) argumentValues.getIntValue(0);
            // Number of units that should be left for future periods
            int[] nbUnitsReserved = new int[nbPeriods];
            for (int j = 0; j < nbPeriods - 1; j++) {
                nbUnitsReserved[j] = (int) argumentValues.getIntValue(j+1);
            }
            nbUnitsReserved[nbPeriods - 1] = 0;

            // Sets seed for reproducibility
            Random rng = new Random(seed);
            // Creates distribution
            double rateParam = 1.0;
            double scaleParam = 1.0;
            double[] X = new double[nbSimulations];
            for (int i = 0; i < nbSimulations; i++) {
                X[i] = gammaSample(rng, rateParam);
            }
            double[][] Y = new double[nbSimulations][nbPeriods];
            for (int i = 0; i < nbSimulations; i++) {
                for (int j = 0; j < nbPeriods; j++) {
                    Y[i][j] = exponentialSample(rng, scaleParam);
                }
            }

            // Runs simulations
            double sumProfit = 0;
            for (int i = 0; i < nbSimulations; i++) {
                int remainingCapacity = nbUnitsPurchased;
                for (int j = 0; j < nbPeriods; j++) {
                    // Generates demand for period j
                    int demand = (int) (meanDemands[j] * X[i] * Y[i][j]);
                    int nbUnitsSold = Math.min(Math.max(remainingCapacity - nbUnitsReserved[j],
                            0), demand);
                    remainingCapacity = remainingCapacity - nbUnitsSold;
                    sumProfit += prices[j] * nbUnitsSold;
                }
            }
            // Calculates mean revenue
            double meanProfit = sumProfit / nbSimulations;
            double meanRevenue = meanProfit - purchasePrice * nbUnitsPurchased;

            return meanRevenue;
        }

        private static double exponentialSample(Random rng, double rateParam) {
            double u = rng.nextDouble();
            return Math.log(1 - u) / (-rateParam);
        }

        private static double gammaSample(Random rng, double scaleParam) {
            return exponentialSample(rng, scaleParam);
        }
    }

    // Solver
    private final LocalSolver localsolver;

    // LS Program variables
    private LSExpression[] variables;
    private LSExpression bbCall;

    private RevenueManagement(LocalSolver localsolver) {
        this.localsolver = localsolver;
    }

    // Declares the optimization model
    private void solve(int timeLimit, int evaluationLimit) {
        LSModel model = localsolver.getModel();

        // Generates data
        RevenueManagementFunction revenueManagement = new RevenueManagementFunction(1);
        int nbPeriods = revenueManagement.nbPeriods;
        // Declares decision variables
        variables = new LSExpression[nbPeriods];
        for (int i = 0; i < nbPeriods; i++) {
            variables[i] = model.intVar(0, 100);
        }

        // Creates blackbox function
        LSExpression bbFunc = model.doubleBlackBoxFunction(revenueManagement);
        // Calls function with operands
        bbCall = model.call(bbFunc);
        for (int i = 0; i < nbPeriods; i++) {
            bbCall.addOperand(variables[i]);
        }

        // Declares constraints
        for (int i = 1; i < nbPeriods; i++) {
            model.constraint(model.leq(variables[i], variables[i-1]));
        }

        // Maximizes function call
        model.maximize(bbCall);

        // Sets lower bound
        LSBlackBoxContext context = bbFunc.getBlackBoxContext();
        context.setLowerBound(0.0);

        model.close();

        // Parametrizes the solver
        if (timeLimit != 0) {
            localsolver.getParam().setTimeLimit(timeLimit);
        }

        // Sets the maximum number of evaluations
        context.setEvaluationLimit(evaluationLimit);

        // Adds evaluation points
        for (EvaluatedPoint evaluatedPoint : revenueManagement.evaluatedPoints) {
            LSBlackBoxEvaluationPoint evaluationPoint = context.createEvaluationPoint();
            for (int i = 0; i < nbPeriods; i++) {
                evaluationPoint.addArgument(evaluatedPoint.point[i]);
            }
            evaluationPoint.setReturnValue(evaluatedPoint.value);
        }

        localsolver.solve();
    }

    // Writes the solution in a file
    private void writeSolution(String fileName) throws IOException {
        try (PrintWriter output = new PrintWriter(fileName)) {
            output.println("obj=" + bbCall.getDoubleValue());
            output.println("b=" + variables[0].getIntValue());
            for (int i = 1; i < variables.length; i++) {
                output.println("r" + i + "=" + variables[i].getIntValue());
            }
        }
    }

    public static void main(String[] args) {
        String outputFile = args.length > 0 ? args[0] : null;
        String strTimeLimit = args.length > 1 ? args[1] : "0";
        String strEvaluationLimit = args.length > 2 ? args[2] : "30";

         try (LocalSolver localsolver = new LocalSolver()) {
            RevenueManagement model = new RevenueManagement(localsolver);
            model.solve(Integer.parseInt(strTimeLimit), Integer.parseInt(strEvaluationLimit));
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
