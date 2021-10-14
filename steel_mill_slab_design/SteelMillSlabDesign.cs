/********** SteelMillSlabDesign.cs **********/

using System;
using System.IO;
using System.Collections.Generic;
using localsolver;

public class SteelMillSlabDesign : IDisposable
{
    // Number of available slabs
    int nbSlabs;

    // Number of orders
    int nbOrders;

    // Number of colors
    int nbColors;

    // Maximum number of colors per slab
    int nbColorsMaxSlab;

    // Maximum size of a slab
    int maxSize;

    // List of orders for each color
    List<int>[] ordersByColor;

    // Orders size
    int[] orders;

    // Steel waste computed for each content value
    long[] wasteForContent;

    // Solver.
    LocalSolver localsolver;

    // LS Program variables.
    LSExpression[,] x;

    // Objective
    LSExpression totalWastedSteel;

    public SteelMillSlabDesign()
    {
        localsolver = new LocalSolver();
    }

    public void Dispose()
    {
        if (localsolver != null)
            localsolver.Dispose();
    }

    // Reads instance data.
    void ReadInstance(string fileName)
    {
        using (StreamReader input = new StreamReader(fileName))
        {
            nbColorsMaxSlab = 2;
            string[] splitted = input.ReadLine().Split();
            int nbSlabSizes = int.Parse(splitted[0]);

            int[] slabSizes = new int[nbSlabSizes];
            for (int i = 0; i < nbSlabSizes; i++)
            {
                slabSizes[i] = int.Parse(splitted[i + 1]);
            }
            maxSize = slabSizes[nbSlabSizes - 1];

            nbColors = int.Parse(input.ReadLine());
            nbOrders = int.Parse(input.ReadLine());
            nbSlabs = nbOrders;

            ordersByColor = new List<int>[nbColors];
            for (int c = 0; c < nbColors; c++)
            {
                ordersByColor[c] = new List<int>();
            }
            orders = new int[nbOrders];
            int sumSizeOrders = 0;
            for (int o = 0; o < nbOrders; o++)
            {
                splitted = input.ReadLine().Split();
                orders[o] = int.Parse(splitted[0]);
                int c = int.Parse(splitted[1]);
                // Note: colors are in [1..nbColors]
                ordersByColor[c - 1].Add(o);
                sumSizeOrders += orders[o];
            }

            PreComputeWasteForContent(slabSizes, sumSizeOrders);
        }
    }

    // Computes the vector wasteForContent
    private void PreComputeWasteForContent(int[] slabSizes, int sumSizeOrders)
    {
        // No waste when a slab is empty.
        wasteForContent = new long[sumSizeOrders];

        int prevSize = 0;
        for (int i = 0; i < slabSizes.Length; i++)
        {
            int size = slabSizes[i];
            if (size < prevSize)
                throw new Exception("Slab sizes should be sorted in ascending order");

            for (int content = prevSize + 1; content < size; content++)
            {
                wasteForContent[content] = size - content;
            }
            prevSize = size;
        }
    }

    void Solve(int limit)
    {
        // Declares the optimization model.
        LSModel model = localsolver.GetModel();

        // x[o, s] = 1 if order o is assigned to slab s, 0 otherwise
        x = new LSExpression[nbOrders, nbSlabs];
        for (int o = 0; o < nbOrders; o++)
        {
            for (int s = 0; s < nbSlabs; s++)
            {
                x[o, s] = model.Bool();
            }
        }

        // Each order is assigned to a slab
        for (int o = 0; o < nbOrders; o++)
        {
            LSExpression nbSlabsAssigned = model.Sum();
            for (int s = 0; s < nbSlabs; s++)
            {
                nbSlabsAssigned.AddOperand(x[o, s]);
            }
            model.Constraint(nbSlabsAssigned == 1);
        }

        // The content of each slab must not exceed the maximum size of the slab
        LSExpression[] slabContent = new LSExpression[nbSlabs];
        for (int s = 0; s < nbSlabs; s++)
        {
            slabContent[s] = model.Sum();
            for (int o = 0; o < nbOrders; o++)
            {
                slabContent[s].AddOperand(orders[o] * x[o, s]);
            }
            model.Constraint(slabContent[s] <= maxSize);
        }

        // Create the LocalSolver array corresponding to the vector wasteForContent
        // (because "at" operators can only access LocalSolver arrays)
        LSExpression wasteForContentArray = model.Array(wasteForContent);

        // Wasted steel is computed according to the content of the slab
        LSExpression[] wastedSteel = new LSExpression[nbSlabs];
        for (int s = 0; s < nbSlabs; s++)
        {
            wastedSteel[s] = wasteForContentArray[slabContent[s]];
        }

        // color[c][s] = 1 if the color c in the slab s, 0 otherwise
        LSExpression[,] color = new LSExpression[nbColors, nbSlabs];
        for (int c = 0; c < nbColors; c++)
        {
            if (ordersByColor[c].Count == 0) continue;
            for (int s = 0; s < nbSlabs; s++)
            {
                color[c, s] = model.Or();
                for (int i = 0; i < ordersByColor[c].Count; i++)
                {
                    int o = ordersByColor[c][i];
                    color[c, s].AddOperand(x[o, s]);
                }
            }
        }

        // The number of colors per slab must not exceed a specified value
        for (int s = 0; s < nbSlabs; s++)
        {
            LSExpression nbColorsSlab = model.Sum();
            for (int c = 0; c < nbColors; c++)
            {
                if (ordersByColor[c].Count == 0) continue;
                nbColorsSlab.AddOperand(color[c, s]);
            }
            model.Constraint(nbColorsSlab <= nbColorsMaxSlab);
        }

        // Minimize the total wasted steel
        totalWastedSteel = model.Sum(wastedSteel);
        model.Minimize(totalWastedSteel);

        model.Close();

        // Parameterizes the solver.
        localsolver.GetParam().SetTimeLimit(limit);
        localsolver.GetParam().SetNbThreads(4);

        localsolver.Solve();
    }

    // Writes the solution in a file with the following format: 
    //  - total wasted steel
    //  - number of slabs used
    //  - for each slab used, the number of orders in the slab and the list of orders
    void WriteSolution(string fileName)
    {
        using (StreamWriter output = new StreamWriter(fileName))
        {
            output.WriteLine(totalWastedSteel.GetValue());
            int actualNbSlabs = 0;
            List<int>[] ordersBySlabs = new List<int>[nbSlabs];
            for (int s = 0; s < nbSlabs; s++)
            {
                ordersBySlabs[s] = new List<int>();
                for (int o = 0; o < nbOrders; o++)
                {
                    if (x[o, s].GetValue() == 1) ordersBySlabs[s].Add(o);
                }
                if (ordersBySlabs[s].Count > 0) actualNbSlabs++;
            }
            output.WriteLine(actualNbSlabs);

            for (int s = 0; s < nbSlabs; s++)
            {
                int nbOrdersInSlab = ordersBySlabs[s].Count;
                if (nbOrdersInSlab == 0) continue;
                output.Write(nbOrdersInSlab + " ");
                for (int i = 0; i < nbOrdersInSlab; i++)
                {
                    output.Write(ordersBySlabs[s][i] + " ");
                }
                output.WriteLine();
            }
        }
    }

    public static void Main(string[] args)
    {
        if (args.Length < 1)
        {
            Console.WriteLine("Usage: SteelMillSlabDesign inputFile [outputFile] [timeLimit]");
            Environment.Exit(1);
        }

        string instanceFile = args[0];
        string outputFile = args.Length > 1 ? args[1] : null;
        string strTimeLimit = args.Length > 2 ? args[2] : "60";

        using (SteelMillSlabDesign model = new SteelMillSlabDesign())
        {
            model.ReadInstance(instanceFile);
            model.Solve(int.Parse(strTimeLimit));
            if (outputFile != null)
                model.WriteSolution(outputFile);
        }
    }
}

