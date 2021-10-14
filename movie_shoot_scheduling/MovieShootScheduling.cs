/********** MovieShootScheduling.cs **********/

using System;
using System.IO;
using localsolver;

public class MssInstance
{
    public int nbActors;
    public int nbScenes;
    public int nbLocations;
    public int nbPrecedences;
    public int[] actorCost;
    public int[] locationCost;
    public int[] sceneDuration;
    public int[] sceneLocation;
    public int[] nbWorkedDays;

    public bool[,] isActorInScene;
    public int[,] precedence;

    // Constructor
    public MssInstance(string fileName)
    {
        ReadInstance(fileName);
        ComputeNbWorkedDays();
    }

    /* Read instance data */
    void ReadInstance(string fileName)
    {
        using (StreamReader input = new StreamReader(fileName))
        {
            string[] line;
            nbActors = int.Parse(input.ReadLine());
            nbScenes = int.Parse(input.ReadLine());
            nbLocations = int.Parse(input.ReadLine());
            nbPrecedences = int.Parse(input.ReadLine());
            input.ReadLine();
            actorCost = new int[nbActors];
            locationCost = new int[nbLocations];
            sceneDuration = new int[nbScenes];
            sceneLocation = new int[nbScenes];
            isActorInScene = new bool[nbActors, nbScenes];
            precedence = new int[nbPrecedences, 2];

            line = input.ReadLine().Split();
            for (int j = 0; j < nbActors; ++j)
                actorCost[j] = int.Parse(line[j]);
            line = input.ReadLine().Split();
            for (int k = 0; k < nbLocations; ++k)
                locationCost[k] = int.Parse(line[k]);
            line = input.ReadLine().Split();
            for (int i = 0; i < nbScenes; ++i)
                sceneDuration[i] = int.Parse(line[i]);
            line = input.ReadLine().Split();
            for (int i = 0; i < nbScenes; ++i)
                sceneLocation[i] = int.Parse(line[i]);
            input.ReadLine();
            for (int j = 0; j < nbActors; ++j)
            {
                line = input.ReadLine().Split();
                for (int i = 0; i < nbScenes; ++i)
                    isActorInScene[j, i] = Convert.ToBoolean(int.Parse(line[i]));
            }
            input.ReadLine();
            for (int p = 0; p < nbPrecedences; ++p)
            {
                line = input.ReadLine().Split();
                for (int i = 0; i < 2; ++i)
                    precedence[p, i] = int.Parse(line[i]);
            }
        }
    }

    private void ComputeNbWorkedDays()
    {
        nbWorkedDays = new int[nbActors];
        for (int j = 0; j < nbActors; ++j)
        {
            nbWorkedDays[j] = 0;
            for (int i = 0; i < nbScenes; ++i)
            {
                if (isActorInScene[j, i])
                {
                    nbWorkedDays[j] += sceneDuration[i];
                }
            }
        }
    }
}

/* External function */
public class CostFunction
{
    MssInstance instance;

    // To maintain thread-safety property, ThreadStatic is used
    // here. Each thread must have have independant following variables.

    // Number of visits per location (group of successive shoots)
    [ThreadStatic]
    static int[] nbLocationVisits;

    // First day of work for each actor
    [ThreadStatic]
    static int[] actorFirstDay;

    // Last day of work for each actor
    [ThreadStatic]
    static int[] actorLastDay;

    // Constructor
    public CostFunction(MssInstance instance)
    {
      this.instance = instance;
    }

    public long Call(LSExternalArgumentValues argumentValues)
    {
        LSCollection shootOrder = argumentValues.GetCollectionValue(0);
        int shootOrderLength = shootOrder.Count();
        if (shootOrderLength < instance.nbScenes)
        {
            // Infeasible solution if some shoots are missing
            return Int32.MaxValue;
        }

        InitStaticVectors();
        ResetStaticVectors();
        long[] shootOrderArray = new long[shootOrderLength];
        shootOrder.CopyTo(shootOrderArray);

        int locationExtraCost = ComputeLocationCost(shootOrderArray);
        int actorExtraCost = ComputeActorCost(shootOrderArray);
        return locationExtraCost + actorExtraCost;
    }

    private int ComputeLocationCost(long[] shootOrderArray)
    {
        int previousLocation = -1;
        for (int i = 0; i < instance.nbScenes; ++i)
        {
            int currentLocation = instance.sceneLocation[shootOrderArray[i]];
            // When we change location, we increment the number of shoots of the new location
            if (previousLocation != currentLocation)
            {
                nbLocationVisits[currentLocation] += 1;
                previousLocation = currentLocation;
            }
        }
        int locationExtraCost = 0;
        for (int k = 0; k < instance.nbLocations; ++k)
        {
            locationExtraCost += (nbLocationVisits[k] - 1) * instance.locationCost[k];
        }
        return locationExtraCost;
    }

    private int ComputeActorCost(long[] shootOrderArray)
    {
        // Compute first and last days of work for each actor
        for (int j = 0; j < instance.nbActors; ++j)
        {
            bool hasActorStartedWorking = false;
            int startDayOfScene = 0;
            for (int i = 0; i < instance.nbScenes; ++i)
            {
                int currentScene = Convert.ToInt32(shootOrderArray[i]);
                int endDayOfScene = startDayOfScene + instance.sceneDuration[currentScene] - 1;
                if (instance.isActorInScene[j, currentScene])
                {
                    actorLastDay[j] = endDayOfScene;
                    if (!(hasActorStartedWorking))
                    {
                        hasActorStartedWorking = true;
                        actorFirstDay[j] = startDayOfScene;
                    }
                }
                // The next scene begins the day after the end of the current one
                startDayOfScene = endDayOfScene + 1;
            }
        }

        // Compute actor extra cost due to days paid but not worked
        int actorExtraCost = 0;
        for (int j = 0; j < instance.nbActors; ++j)
        {
            int nbPaidDays = actorLastDay[j] - actorFirstDay[j] + 1;
            actorExtraCost += (nbPaidDays - instance.nbWorkedDays[j]) * instance.actorCost[j];
        }
        return actorExtraCost;
    }

    void InitStaticVectors()
    {
        if (nbLocationVisits == null) nbLocationVisits = new int[instance.nbLocations];
        if (actorFirstDay == null) actorFirstDay = new int[instance.nbActors];
        if (actorLastDay == null) actorLastDay = new int[instance.nbActors];
    }

    void ResetStaticVectors()
    {
        for (int k = 0; k < instance.nbLocations; ++k)
        {
            nbLocationVisits[k] = 0;
        }
        for (int j = 0; j < instance.nbActors; ++j)
        {
            actorFirstDay[j] = 0;
            actorLastDay[j] = 0;
        }
    }
}

public class MovieShootScheduling : IDisposable
{
    // LocalSolver
    LocalSolver localsolver;

    // Instance data
    MssInstance instance;

    // Decision variable
    LSExpression shootOrder;

    // Objective
    LSExpression callCostFunc;

     // Constructor
    public MovieShootScheduling(MssInstance instance)
    {
        this.localsolver = new LocalSolver();
        this.instance = instance;
    }

    public void Dispose()
    {
        if (localsolver != null)
            localsolver.Dispose();
    }

    void Solve(int limit)
    {
        // Declare the optimization model
        LSModel model = localsolver.GetModel();

        // A list variable: shootOrder[i] is the index of the ith scene to be shot
        shootOrder = model.List(instance.nbScenes);

        // All shoots must be scheduled
        model.Constraint(model.Count(shootOrder) == instance.nbScenes);

       // Constraint of precedence between scenes
       for (int p = 0; p < instance.nbPrecedences; ++p)
            model.Constraint(model.IndexOf(shootOrder, instance.precedence[p, 0])
                            < model.IndexOf(shootOrder, instance.precedence[p, 1]));

        // Minimize external function
        CostFunction costObject = new CostFunction(instance);
        LSIntExternalFunction func = new LSIntExternalFunction(costObject.Call);
        LSExpression costFunc = model.CreateIntExternalFunction(func);
        costFunc.GetExternalContext().SetIntLowerBound(0);
        callCostFunc = model.Call(costFunc, shootOrder);
        model.Minimize(callCostFunc);

        model.Close();

        // Parameterize the solver
        localsolver.GetParam().SetTimeLimit(limit);

        localsolver.Solve();
    }

    /* Write the solution in a file in the following format:
    * - 1st line: value of the objective;
    * - 2nd line: for each i, the index of the i-th scene to be shot. */
    void WriteSolution(string fileName)
    {
        using (StreamWriter output = new StreamWriter(fileName))
        {
            output.WriteLine(callCostFunc.GetIntValue());
            LSCollection shootOrderCollection = shootOrder.GetCollectionValue();
            for (int i = 0; i < instance.nbScenes; ++i)
                output.Write(shootOrderCollection.Get(i) + " ");
            output.WriteLine();
        }
    }

    public static void Main(string[] args)
    {
        if (args.Length < 1)
        {
            Console.WriteLine("Usage: MovieShootScheduling inputFile [solFile] [timeLimit]");
            Environment.Exit(1);
        }
        string instanceFile = args[0];
        string outputFile = args.Length > 1 ? args[1] : null;
        string strTimeLimit = args.Length > 2 ? args[2] : "20";
        MssInstance instance = new MssInstance(instanceFile);
        using (MovieShootScheduling model = new MovieShootScheduling(instance))
        {
            model.Solve(int.Parse(strTimeLimit));
            if (outputFile != null)
                model.WriteSolution(outputFile);
        }
    }
}
