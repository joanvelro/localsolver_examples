/********** AssemblyLineBalancing.cs **********/

using System;
using System.IO;
using System.Collections.Generic;
using localsolver;

public class ALBInstance
{
    public int nbTasks;
    public int nbMaxStations;
    public int cycleTime;
    public int[] processingTime;
    public List<int>[] successors;

    // Constructor
    public ALBInstance(string fileName)
    {
        ReadInstance(fileName);
    }

    /* Read instance data */
    void ReadInstance(string fileName)
    {
        using (StreamReader input = new StreamReader(fileName))
        {
            string[] line;
            input.ReadLine();

            // Read number of tasks
            nbTasks = int.Parse(input.ReadLine());
            nbMaxStations = nbTasks;
            processingTime = new int[nbTasks];
            successors = new List<int>[nbTasks];
            for (int i = 0; i < 2; ++i)
                input.ReadLine();

            // Read the cycle time limit
            cycleTime = int.Parse(input.ReadLine());
            for (int i = 0; i < 6; ++i)
                input.ReadLine();

            // Read the processing times
            for (int i = 0; i < nbTasks; ++i)
            {
                line = input.ReadLine().Split();
                processingTime[i] = int.Parse(line[1]);
            }
            for (int i = 0; i < 2; ++i)
                input.ReadLine();

            // Read the successors' relations
            while (true)
            {
                line = input.ReadLine().Split(',');
                if (line[0] == "")
                    break;
                int predecessor = int.Parse(line[0]) -1;
                int successor = int.Parse(line[1]) -1;
                if (successors[predecessor] == null)
                    successors[predecessor] = new List<int>();
                successors[predecessor].Add(successor);
            }
        }
    }
}

public class AssemblyLineBalancing : IDisposable
{
    // LocalSolver
    LocalSolver localsolver;

    // Instance data
    ALBInstance instance;

    // Decision variables
    LSExpression[] station;

    // Intermediate expressions
    LSExpression[] timeInStation;
    LSExpression[] taskStation;

    // Objective
    LSExpression nbUsedStations;

    // Constructor
    public AssemblyLineBalancing(ALBInstance instance)
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

        // station[s] is the set of tasks assigned to station s
        station = new LSExpression[instance.nbMaxStations];
        LSExpression partition = model.Partition();
        for (int s = 0; s < instance.nbMaxStations; ++s)
        {
            station[s] = model.Set(instance.nbTasks);
            partition.AddOperand(station[s]);
        }
        model.Constraint(partition);

        // nbUsedStations is the total number of used stations
        nbUsedStations = model.Sum();
        for (int s = 0; s < instance.nbMaxStations; ++s)
            nbUsedStations.AddOperand(model.Count(station[s]) > 0);

        // All stations must respect the cycleTime constraint
        timeInStation = new LSExpression[instance.nbMaxStations];
        LSExpression processingTimeArray = model.Array(instance.processingTime);
        LSExpression timeSelector = model.LambdaFunction(i => processingTimeArray[i]);
        for (int s = 0; s < instance.nbMaxStations; ++s)
        {
            timeInStation[s] = model.Sum(station[s], timeSelector);
            model.Constraint(timeInStation[s] <= instance.cycleTime);
        }

        // The stations must respect the succession's order of the tasks
        taskStation = new LSExpression[instance.nbTasks];
        for (int i = 0; i < instance.nbTasks; ++i)
        {
            taskStation[i] = model.Sum();
            for (int s = 0; s < instance.nbMaxStations; ++s)
                taskStation[i].AddOperand(model.Contains(station[s], i) * s);
        }
        for (int i = 0; i < instance.nbTasks; ++i)
            if(instance.successors[i] != null)
                foreach (int j in instance.successors[i])
                    model.Constraint(taskStation[i] <= taskStation[j]);

        // Minimization of the number of active stations
        model.Minimize(nbUsedStations);

        model.Close();

        // Parametrize the solver
        localsolver.GetParam().SetTimeLimit(limit);
        // Initialize with a naive solution: each task belongs to one separate station
        // Note: nbTasks equals nbMaxStations
        for (int i = 0; i < instance.nbTasks; ++i)
            station[i].GetCollectionValue().Add(i);

        localsolver.Solve();
    }

    /* Write the solution in a file following the format:
    * - 1st line: value of the objective
    * - 2nd line: number of tasks
    * - following lines: task's number, station's number */
    void WriteSolution(string fileName)
    {
        using (StreamWriter output = new StreamWriter(fileName))
        {
            output.WriteLine(nbUsedStations.GetIntValue());
            output.WriteLine(instance.nbTasks);
            for (int i = 0; i < instance.nbTasks; ++i)
            {
                output.Write(i + 1);
                output.Write(',');
                output.WriteLine(taskStation[i].GetIntValue() + 1);
            }
        }

    }

    public static void Main(string[] args)
    {
        if (args.Length < 1)
        {
            Console.WriteLine("Usage: AssemblyLineBalancing inputFile [solFile] [timeLimit]");
            Environment.Exit(1);
        }
        string instanceFile = args[0];
        string outputFile = args.Length > 1 ? args[1] : null;
        string strTimeLimit = args.Length > 2 ? args[2] : "20";
        ALBInstance instance = new ALBInstance(instanceFile);
        using (AssemblyLineBalancing model = new AssemblyLineBalancing(instance))
        {
            model.Solve(int.Parse(strTimeLimit));
            if (outputFile != null)
              model.WriteSolution(outputFile);
        }
    }
}
