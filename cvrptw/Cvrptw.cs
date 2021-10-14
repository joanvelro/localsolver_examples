/********** Cvrptw.cs **********/

using System;
using System.IO;
using System.Collections.Generic;
using localsolver;

public class Cvrptw : IDisposable
{
    // Solver
    LocalSolver localsolver;

    // Number of customers (= number of nodes minus 1)
    int nbCustomers;

    // Capacity of the trucks
    int truckCapacity;

    // Latest allowed arrival to depot
    int maxHorizon;

    // Demand on each node
    List<int> demands;

    // Earliest arrival on each node
    List<int> earliestStart;

    // Latest departure from each node
    List<int> latestEnd;

    // Service time on each node
    List<int> serviceTime;

    // Distance matrix between customers
    double[][] distanceMatrix;

    // Distances between customers and warehouse
    double[] distanceWarehouses;

    // Number of trucks
    int nbTrucks;

    // Decision variables
    LSExpression[] customersSequences;

    // Are the trucks actually used
    LSExpression[] trucksUsed;

    // Distance traveled by each truck
    LSExpression[] routeDistances;

    // End time array for each truck
    LSExpression[] endTime;

    // Home lateness for each truck
    LSExpression[] homeLateness;

    // Cumulated Lateness for each truck
    LSExpression[] lateness;

    // Cumulated lateness in the solution (must be 0 for the solution to be valid)
    LSExpression totalLateness;

    // Number of trucks used in the solution
    LSExpression nbTrucksUsed;

    // Distance traveled by all the trucks
    LSExpression totalDistance;

    public Cvrptw()
    {
        localsolver = new LocalSolver();
    }

    // Reads instance data.
    void ReadInstance(string fileName)
    {
        ReadInputCvrptw(fileName);
    }

    public void Dispose()
    {
        if (localsolver != null)
            localsolver.Dispose();
    }

    void Solve(int limit)
    {
        // Declares the optimization model.
        LSModel model = localsolver.GetModel();

        trucksUsed = new LSExpression[nbTrucks];
        customersSequences = new LSExpression[nbTrucks];
        routeDistances = new LSExpression[nbTrucks];
        endTime = new LSExpression[nbTrucks];
        homeLateness = new LSExpression[nbTrucks];
        lateness = new LSExpression[nbTrucks];


        // Sequence of customers visited by each truck.
        for (int k = 0; k < nbTrucks; k++)
            customersSequences[k] = model.List(nbCustomers);

        // All customers must be visited by the trucks
        model.Constraint(model.Partition(customersSequences));

        // Create demands and distances as arrays to be able to access it with an "at" operator
        LSExpression demandsArray = model.Array(demands);
        LSExpression earliestArray = model.Array(earliestStart);
        LSExpression latestArray = model.Array(latestEnd);
        LSExpression serviceArray = model.Array(serviceTime);

        LSExpression distanceWarehouseArray = model.Array(distanceWarehouses);
        LSExpression distanceArray = model.Array(distanceMatrix);

        for (int k = 0; k < nbTrucks; k++)
        {
            LSExpression sequence = customersSequences[k];
            LSExpression c = model.Count(sequence);

            // A truck is used if it visits at least one customer
            trucksUsed[k] = c > 0;

            // The quantity needed in each route must not exceed the truck capacity
            LSExpression demandSelector = model.LambdaFunction(i => demandsArray[sequence[i]]);
            LSExpression routeQuantity = model.Sum(model.Range(0, c), demandSelector);
            model.Constraint(routeQuantity <= truckCapacity);

            // Distance traveled by truck k
            LSExpression distSelector = model.LambdaFunction(i => distanceArray[sequence[i - 1], sequence[i]]);
            routeDistances[k] = model.Sum(model.Range(1, c), distSelector)
                                + model.If(c > 0, distanceWarehouseArray[sequence[0]] + distanceWarehouseArray[sequence[c - 1]], 0);

            //End of each visit
            LSExpression endSelector = model.LambdaFunction((i, prev) => model.Max(earliestArray[sequence[i]],
                          model.If(i == 0,
                              distanceWarehouseArray[sequence[0]],
                              prev + distanceArray[sequence[i-1], sequence[i]])) +
                            serviceArray[sequence[i]]);

            endTime[k] = model.Array(model.Range(0, c), endSelector);

            // Arriving home after max_horizon
            homeLateness[k] = model.If(trucksUsed[k],
                                model.Max(0, endTime[k][c-1] + distanceWarehouseArray[sequence[c-1]] - maxHorizon),
                                0);

            //completing visit after latest_end
            LSExpression lateSelector = model.LambdaFunction(i => model.Max(endTime[k][i] - latestArray[sequence[i]], 0));
            lateness[k] = homeLateness[k] + model.Sum(model.Range(0, c), lateSelector);
        }

        totalLateness = model.Sum(lateness);
        nbTrucksUsed = model.Sum(trucksUsed);
        totalDistance = model.Round(100*model.Sum(routeDistances))/100;

        // Objective: minimize the number of trucks used, then minimize the distance traveled
        model.Minimize(totalLateness);
        model.Minimize(nbTrucksUsed);
        model.Minimize(totalDistance);

        model.Close();

        // Parameterizes the solver.
        localsolver.GetParam().SetTimeLimit(limit);

        localsolver.Solve();
    }

    // Writes the solution in a file with the following format:
    //  - number of trucks used and total distance
    //  - for each truck the nodes visited (omitting the start/end at the depot)
    void WriteSolution(string fileName)
    {
        using (StreamWriter output = new StreamWriter(fileName))
        {
            output.WriteLine(nbTrucksUsed.GetValue() + " " + totalDistance.GetDoubleValue());
            for (int k = 0; k < nbTrucks; k++)
            {
                if (trucksUsed[k].GetValue() != 1) continue;
                // Values in sequence are in [0..nbCustomers-1]. +2 is to put it back in [2..nbCustomers+1]
                // as in the data files (1 being the depot)
                LSCollection customersCollection = customersSequences[k].GetCollectionValue();
                for (int i = 0; i < customersCollection.Count(); i++)
                {
                    output.Write((customersCollection[i] + 2) + " ");
                }
                output.WriteLine();
            }
        }
    }

    public static void Main(string[] args)
    {
        if (args.Length < 1)
        {
            Console.WriteLine("Usage: Cvrptw inputFile [solFile] [timeLimit]");
            Environment.Exit(1);
        }
        string instanceFile = args[0];
        string outputFile = args.Length > 1 ? args[1] : null;
        string strTimeLimit = args.Length > 2 ? args[2] : "20";

        using (Cvrptw model = new Cvrptw())
        {
            model.ReadInstance(instanceFile);
            model.Solve(int.Parse(strTimeLimit));
            if (outputFile != null)
                model.WriteSolution(outputFile);
        }
    }

    private string[] SplitInput(StreamReader input) {
        string line = input.ReadLine();
        if (line == null) return new string[0];
        return line.Split(new [] {' '}, StringSplitOptions.RemoveEmptyEntries);
    }

    // The input files follow the "Solomon" format.
    private void ReadInputCvrptw(string fileName)
    {
        using (StreamReader input = new StreamReader(fileName))
        {
            string[] splitted;

            input.ReadLine();
            input.ReadLine();
            input.ReadLine();
            input.ReadLine();

            splitted = SplitInput(input);
            nbTrucks = int.Parse(splitted[0]);
            truckCapacity = int.Parse(splitted[1]);

            input.ReadLine();
            input.ReadLine();
            input.ReadLine();
            input.ReadLine();

            splitted = SplitInput(input);
            int depotX = int.Parse(splitted[1]);
            int depotY = int.Parse(splitted[2]);
            maxHorizon = int.Parse(splitted[5]);

            List<int> customersX = new List<int>();
            List<int> customersY = new List<int>();
            demands = new List<int>();
            earliestStart = new List<int>();
            latestEnd = new List<int>();
            serviceTime = new List<int>();

            while(!input.EndOfStream)
            {
                splitted = SplitInput(input);
                if (splitted.Length < 7) break;
                customersX.Add(int.Parse(splitted[1]));
                customersY.Add(int.Parse(splitted[2]));
                demands.Add(int.Parse(splitted[3]));
                int ready = int.Parse(splitted[4]);
                int due = int.Parse(splitted[5]);
                int service = int.Parse(splitted[6]);

                earliestStart.Add(ready);
                latestEnd.Add(due+service);//in input files due date is meant as latest start time
                serviceTime.Add(service);
            }

            nbCustomers = customersX.Count;

            ComputeDistanceMatrix(depotX, depotY, customersX, customersY);
        }
    }

    // Computes the distance matrix
    private void ComputeDistanceMatrix(int depotX, int depotY, List<int> customersX, List<int> customersY)
    {
        distanceMatrix = new double[nbCustomers][];
        for (int i = 0; i < nbCustomers; i++)
            distanceMatrix[i] = new double[nbCustomers];

        for (int i = 0; i < nbCustomers; i++)
        {
            distanceMatrix[i][i] = 0;
            for (int j = i + 1; j < nbCustomers; j++)
            {
                double dist = ComputeDist(customersX[i], customersX[j], customersY[i], customersY[j]);
                distanceMatrix[i][j] = dist;
                distanceMatrix[j][i] = dist;
            }
        }

        distanceWarehouses = new double[nbCustomers];
        for (int i = 0; i < nbCustomers; ++i) {
            distanceWarehouses[i] = ComputeDist(depotX, customersX[i], depotY, customersY[i]);
        }
    }

    private double ComputeDist(int xi, int xj, int yi, int yj)
    {
        return Math.Sqrt(Math.Pow(xi - xj, 2) + Math.Pow(yi - yj, 2));
    }

}
