/********** SteelMillSlabDesign.java **********/

import java.util.*;
import java.io.*;
import localsolver.*;

public class SteelMillSlabDesign {
    // Number of available slabs
    private int nbSlabs;

    // Number of orders
    private int nbOrders;

    // Number of colors
    private int nbColors;

    // Maximum number of colors per slab
    private int nbColorsMaxSlab;

    // Maximum size of a slab
    private int maxSize;

    // List of orders for each color
    private ArrayList<ArrayList<Integer>> ordersByColor;

    // Orders size
    private int[] orders;

    // Steel waste computed for each content value
    private long[] wasteForContent;

    // Solver.
    private final LocalSolver localsolver;

    // LS Program variables.
    private LSExpression[][] x;

    // Objective
    private LSExpression totalWastedSteel;

    private SteelMillSlabDesign(LocalSolver localsolver) {
        this.localsolver = localsolver;
    }

    // Reads instance data.
    private void readInstance(String fileName) throws IOException {
        try (Scanner input = new Scanner(new File(fileName))) {
            nbColorsMaxSlab = 2;
            int nbSlabSizes = input.nextInt();

            int[] slabSizes = new int[nbSlabSizes];
            for (int i = 0; i < nbSlabSizes; i++) {
                slabSizes[i] = input.nextInt();
            }
            maxSize = slabSizes[nbSlabSizes - 1];

            nbColors = input.nextInt();
            nbOrders = input.nextInt();
            nbSlabs = nbOrders;

            ordersByColor = new ArrayList<ArrayList<Integer>>(nbColors);
            for (int c = 0; c < nbColors; c++) {
                ordersByColor.add(new ArrayList<Integer>());
            }
            orders = new int[nbOrders];
            int sumSizeOrders = 0;
            for (int o = 0; o < nbOrders; o++) {
                orders[o] = input.nextInt();
                int c = input.nextInt();
                // Note: colors are in [1..nbColors]
                ordersByColor.get(c - 1).add(o);
                sumSizeOrders += orders[o];
            }

            preComputeWasteForContent(slabSizes, sumSizeOrders);
        }
    }

    private void preComputeWasteForContent(int[] slabSizes, int sumSizeOrders) {
        
        wasteForContent = new long[sumSizeOrders];

        int prevSize = 0;
        for (int i = 0; i < slabSizes.length; i++) {
            int size = slabSizes[i];
            if (size < prevSize)
                throw new RuntimeException("Slab sizes should be sorted in ascending order");
            for (int content = prevSize + 1; content < size; content++) {
                wasteForContent[content] = size - content;
            }
            prevSize = size;
        }
    }

    private void solve(int limit) {
        // Declares the optimization model.
        LSModel model = localsolver.getModel();

        // x[o][s] = 1 if order o is assigned to slab s, 0 otherwise
        x = new LSExpression[nbOrders][nbSlabs];
        for (int o = 0; o < nbOrders; o++) {
            for (int s = 0; s < nbSlabs; s++) {
                x[o][s] = model.boolVar();
            }
        }

        // Each order is assigned to a slab
        for (int o = 0; o < nbOrders; o++) {
            LSExpression nbSlabsAssigned = model.sum(x[o]);
            model.constraint(model.eq(nbSlabsAssigned, 1));
        }

        // The content of each slab must not exceed the maximum size of the slab
        LSExpression[] slabContent = new LSExpression[nbSlabs];
        for (int s = 0; s < nbSlabs; s++) {
            slabContent[s] = model.sum();
            for (int o = 0; o < nbOrders; o++) {
                slabContent[s].addOperand(model.prod(orders[o], x[o][s]));
            }
            model.constraint(model.leq(slabContent[s], maxSize));
        }

        // Create the LocalSolver array corresponding to the vector wasteForContent
        // (because "at" operators can only access LocalSolver arrays)
        LSExpression wasteForContentArray = model.array(wasteForContent);

        // Wasted steel is computed according to the content of the slab
        LSExpression[] wastedSteel = new LSExpression[nbSlabs];
        for (int s = 0; s < nbSlabs; s++) {
            wastedSteel[s] = model.at(wasteForContentArray, slabContent[s]);
        }

        // color[c][s] = 1 if the color c in the slab s, 0 otherwise
        LSExpression[][] color = new LSExpression[nbColors][nbSlabs];
        for (int c = 0; c < nbColors; c++) {
            if (ordersByColor.get(c).size() == 0) continue;
            for (int s = 0; s < nbSlabs; s++) {
                color[c][s] = model.or();
                for (int i = 0; i < ordersByColor.get(c).size(); i++) {
                    int o = ordersByColor.get(c).get(i);
                    color[c][s].addOperand(x[o][s]);
                }
            }
        }

        // The number of colors per slab must not exceed a specified value
        for (int s = 0; s < nbSlabs; s++) {
            LSExpression nbColorsSlab = model.sum();
            for (int c = 0; c < nbColors; c++) {
                if (ordersByColor.get(c).size() == 0) continue;
                nbColorsSlab.addOperand(color[c][s]);
            }
            model.constraint(model.leq(nbColorsSlab, nbColorsMaxSlab));
        }

        // Minimize the total wasted steel
        totalWastedSteel = model.sum(wastedSteel);
        model.minimize(totalWastedSteel);

        model.close();

        // Parameterizes the solver.
        localsolver.getParam().setTimeLimit(limit);
        localsolver.getParam().setNbThreads(4);

        localsolver.solve();
    }

    // Writes the solution in a file with the following format:
    // - total wasted steel
    // - number of slabs used
    // - for each slab used, the number of orders in the slab and the list of orders
    private void writeSolution(String fileName) throws IOException {
        try (PrintWriter output = new PrintWriter(new FileWriter(fileName))) {
            output.println(totalWastedSteel.getValue());

            int actualNbSlabs = 0;
            ArrayList<ArrayList<Integer>> ordersBySlabs = new ArrayList<ArrayList<Integer>>(nbSlabs);
            for (int s = 0; s < nbSlabs; s++) {
                ordersBySlabs.add(new ArrayList<Integer>());
                for (int o = 0; o < nbOrders; o++) {
                    if (x[o][s].getValue() == 1)
                        ordersBySlabs.get(s).add(o);
                }
                if (ordersBySlabs.get(s).size() > 0)
                    actualNbSlabs++;
            }
            output.println(actualNbSlabs);

            for (int s = 0; s < nbSlabs; s++) {
                int nbOrdersInSlab = ordersBySlabs.get(s).size();
                if (nbOrdersInSlab == 0) continue;
                output.print(nbOrdersInSlab + " ");
                for (int i = 0; i < nbOrdersInSlab; i++) {
                    output.print(ordersBySlabs.get(s).get(i) + " ");
                }
                output.println();
            }
        }
    }

    public static void main(String[] args) {
        if (args.length < 1) {
            System.err.println("Usage: java SteelMillSlabDesign inputFile [outputFile] [timeLimit]");
            System.exit(1);
        }

        String instanceFile = args[0];
        String outputFile = args.length > 1 ? args[1] : null;
        String strTimeLimit = args.length > 2 ? args[2] : "60";

        try (LocalSolver localsolver = new LocalSolver()) {
            SteelMillSlabDesign model = new SteelMillSlabDesign(localsolver);
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
