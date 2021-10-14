/********** Knapsack.java **********/

import java.util.*;
import java.io.*;
import localsolver.*;

public class Knapsack {
    // Number of items. 
    private int nbItems;

    // Items properties. 
    private int[] weights;
    private int[] values;

    // Knapsack bound 
    private int knapsackBound;

    // Solver. 
    private final LocalSolver localsolver;

    // LS Program variables. 
    private LSExpression[] x;

    // Objective. 
    private LSExpression knapsackValue;
    
    // Solutions (classes at each position). 
    private List<Integer> solutions;

    private Knapsack(LocalSolver localsolver) {
        this.localsolver = localsolver;
    }

    // Reads instance data. 
    private void readInstance(String fileName) throws IOException {
        try (Scanner input = new Scanner(new File(fileName))) {
            nbItems = input.nextInt();

            weights = new int[nbItems];
            for (int i = 0; i < nbItems; i++) {
                weights[i] = input.nextInt();
            }

            values = new int[nbItems];
            for (int i = 0; i < nbItems; i++) {
                values[i] = input.nextInt();
            }
        
            knapsackBound = input.nextInt();
        }
    }

    private void solve(int limit) {
        // Declares the optimization model. 
        LSModel model = localsolver.getModel();

        // boolean variables x[i]
        x = new LSExpression[nbItems];
        for (int i = 0; i < nbItems; i++) {
            x[i] = model.boolVar();
        }

        // weight constraint
        LSExpression knapsackWeight = model.sum();
        for (int i = 0; i < nbItems; i++) {
            LSExpression itemWeight = model.prod(x[i], weights[i]);
            knapsackWeight.addOperand(itemWeight);
        }        
        model.constraint(model.leq(knapsackWeight, knapsackBound));

        // maximize value
        knapsackValue = model.sum();
        for (int i = 0; i < nbItems; i++) {
            LSExpression itemValue = model.prod(x[i], values[i]);
            knapsackValue.addOperand(itemValue);
        }
    
        model.maximize(knapsackValue);
        model.close();

        // Parameterizes the solver. 
        localsolver.getParam().setTimeLimit(limit);

        localsolver.solve();

        solutions = new ArrayList<Integer>();
        for (int i = 0; i < nbItems; i++) 
            if (x[i].getValue() == 1) 
        solutions.add(i);         
    }

    // Writes the solution in a file 
    private void writeSolution(String fileName) throws IOException {
        try (PrintWriter output = new PrintWriter(fileName)) {
            output.println(knapsackValue.getValue());
            for (int i = 0; i < solutions.size(); ++i) 
                output.print(solutions.get(i) + " ");
            output.println();
        }
    }
    
     public static void main(String[] args) {
        if (args.length < 1) {
            System.err.println("Usage: java Knapsack inputFile [outputFile] [timeLimit]");
            System.exit(1);
        }

        String instanceFile = args[0];
        String outputFile = args.length > 1 ? args[1] : null;
        String strTimeLimit = args.length > 2 ? args[2] : "20";

         try (LocalSolver localsolver = new LocalSolver()) {
            Knapsack model = new Knapsack(localsolver);
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
