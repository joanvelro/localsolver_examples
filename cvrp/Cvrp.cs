/********** Cvrp.cs **********/

using System;
using System.IO;
using localsolver;

public class Cvrp : IDisposable
{
    // Solver
    LocalSolver localsolver;

    // Number of customers (= number of nodes minus 1)
    int nbCustomers;

    // Capacity of the trucks
    int truckCapacity;

    // Demand on each customer
    long[] demands;

    // Distance matrix between customers
    long[][] distanceMatrix;

    // Distances between customers and warehouse
    long[] distanceWarehouses;

    // Number of trucks
    int nbTrucks;

    // Decision variables
    LSExpression[] customersSequences;

    // Are the trucks actually used
    LSExpression[] trucksUsed;

    // Distance traveled by each truck
    LSExpression[] routeDistances;

    // Number of trucks used in the solution
    LSExpression nbTrucksUsed;

    // Distance traveled by all the trucks
    LSExpression totalDistance;

    public Cvrp(string strNbTrucks)
    {
        localsolver = new LocalSolver();
        nbTrucks = int.Parse(strNbTrucks);
    }

    // Reads instance data.
    void ReadInstance(string fileName)
    {
        ReadInputCvrp(fileName);

        // The number of trucks is usually given in the name of the file
        // nbTrucks can also be given in command line
        if (nbTrucks == 0) nbTrucks = GetNbTrucks(fileName);
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

        // Sequence of customers visited by each truck.
        for (int k = 0; k < nbTrucks; k++)
            customersSequences[k] = model.List(nbCustomers);

        // All customers must be visited by the trucks
        model.Constraint(model.Partition(customersSequences));

        // Create demands and distances as arrays to be able to access it with an "at" operator
        LSExpression demandsArray = model.Array(demands);
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
        }

        nbTrucksUsed = model.Sum(trucksUsed);
        totalDistance = model.Sum(routeDistances);

        // Objective: minimize the number of trucks used, then minimize the distance traveled
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
            output.WriteLine(nbTrucksUsed.GetValue() + " " + totalDistance.GetValue());
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
            Console.WriteLine("Usage: Cvrp inputFile [solFile] [timeLimit] [nbTrucks]");
            Environment.Exit(1);
        }
        string instanceFile = args[0];
        string outputFile = args.Length > 1 ? args[1] : null;
        string strTimeLimit = args.Length > 2 ? args[2] : "20";
        string strNbTrucks = args.Length > 3 ? args[3] : "0";

        using (Cvrp model = new Cvrp(strNbTrucks))
        {
            model.ReadInstance(instanceFile);
            model.Solve(int.Parse(strTimeLimit));
            if (outputFile != null)
                model.WriteSolution(outputFile);
        }
    }

    // The input files follow the "Augerat" format.
    private void ReadInputCvrp(string fileName)
    {
        using (StreamReader input = new StreamReader(fileName))
        {
            int nbNodes = 0;
            string[] splitted;
            while (true)
            {
                splitted = input.ReadLine().Split(':');
                if (splitted[0].Contains("DIMENSION"))
                {
                    nbNodes = int.Parse(splitted[1]);
                    nbCustomers = nbNodes - 1;
                }
                else if (splitted[0].Contains("CAPACITY"))
                {
                    truckCapacity = int.Parse(splitted[1]);
                }
                else if (splitted[0].Contains("EDGE_WEIGHT_TYPE"))
                {
                    if (!splitted[1].Trim().Equals("EUC_2D"))
                        throw new Exception("Edge Weight Type " + splitted[1] + " is not supported (only EUC_2D)");
                }
                else if (splitted[0].Contains("NODE_COORD_SECTION"))
                {
                    break;
                }
            }
            int[] customersX = new int[nbCustomers];
            int[] customersY = new int[nbCustomers];
            int depotX = 0, depotY = 0;
            for (int n = 1; n <= nbNodes; n++)
            {
                splitted = input.ReadLine().Split((char[])null, StringSplitOptions.RemoveEmptyEntries);
                if (int.Parse(splitted[0]) != n)
                    throw new Exception("Unexpected index");
                if (n == 1) {
                    depotX = int.Parse(splitted[1]); 
                    depotY = int.Parse(splitted[2]); 
                } else {
                    // -2 because orginal customer indices are in 2..nbNodes 
                    customersX[n-2] = int.Parse(splitted[1]);
                    customersY[n-2] = int.Parse(splitted[2]);
                }    
            }

            ComputeDistanceMatrix(depotX, depotY, customersX, customersY);

            splitted = input.ReadLine().Split(':');
            if (!splitted[0].Contains("DEMAND_SECTION"))
                throw new Exception("Expected keyword DEMAND_SECTION");

            demands = new long[nbCustomers];
            for (int n = 1; n <= nbNodes; n++)
            {
                splitted = input.ReadLine().Split((char[])null, StringSplitOptions.RemoveEmptyEntries);
                if (int.Parse(splitted[0]) != n)
                    throw new Exception("Unexpected index");
                var demand = int.Parse(splitted[1]);
                if (n == 1) {
                    if (demand != 0) throw new Exception("Warehouse demand is supposed to be 0");
                } else {
                    // -2 because orginal customer indices are in 2..nbNodes 
                    demands[n-2] = demand;
                }
            }

            splitted = input.ReadLine().Split(':');
            if (!splitted[0].Contains("DEPOT_SECTION"))
                throw new Exception("Expected keyword DEPOT_SECTION");

            int warehouseId = int.Parse(input.ReadLine());
            if (warehouseId != 1)
                throw new Exception("Warehouse id is supposed to be 1");

            int endOfDepotSection = int.Parse(input.ReadLine());
            if (endOfDepotSection != -1)
                throw new Exception("Expecting only one warehouse, more than one found");
        }
    }

    // Computes the distance matrix
    private void ComputeDistanceMatrix(int depotX, int depotY, int[] customersX, int[] customersY)
    {
        distanceMatrix = new long[nbCustomers][];
        for (int i = 0; i < nbCustomers; i++)
            distanceMatrix[i] = new long[nbCustomers];

        for (int i = 0; i < nbCustomers; i++)
        {
            distanceMatrix[i][i] = 0;
            for (int j = i + 1; j < nbCustomers; j++)
            {
                long dist = ComputeDist(customersX[i], customersX[j], customersY[i], customersY[j]);
                distanceMatrix[i][j] = dist;
                distanceMatrix[j][i] = dist;
            }
        }

        distanceWarehouses = new long[nbCustomers];
        for (int i = 0; i < nbCustomers; ++i) {
            distanceWarehouses[i] = ComputeDist(depotX, customersX[i], depotY, customersY[i]);
        }
    }

    private long ComputeDist(int xi, int xj, int yi, int yj)
    {
        double exactDist = Math.Sqrt(Math.Pow(xi - xj, 2) + Math.Pow(yi - yj, 2));
        return Convert.ToInt64(Math.Round(exactDist));
    }

    private int GetNbTrucks(string fileName)
    {
        string[] splitted = fileName.Split(new[] { '-', 'k' }, StringSplitOptions.RemoveEmptyEntries);
        if (splitted.Length >= 2)
        {
            string toSplit = splitted[splitted.Length - 1];
            splitted = toSplit.Split(new[] { '.' }, StringSplitOptions.RemoveEmptyEntries);
            return int.Parse(splitted[0]);
        }

        throw new Exception("Error: nbTrucks could not be read from the file name. Enter it from the command line");
    }
}
