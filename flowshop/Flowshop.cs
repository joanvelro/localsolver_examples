/********** Flowshop.cs **********/

using System;
using System.IO;
using localsolver;

public class Flowshop : IDisposable
{
    // Number of jobs
    int nbJobs;

    // Number of machines
    int nbMachines;

    // Initial seed used to generate the instance
    long initialSeed;

    // Upper bound
    int upperBound;

    // Lower bound
    int lowerBound;

    // Processing time
    long[][] processingTime;

    // LocalSolver
    LocalSolver localsolver;

    // Decision variable
    LSExpression jobs;

    // Objective
    LSExpression makespan;

    public Flowshop()
    {
        localsolver = new LocalSolver();
    }

    // Reads instance data. 
    void ReadInstance(string fileName)
    {
        using (StreamReader input = new StreamReader(fileName))
        {
            string[] firstLineSplit = input.ReadLine().Split((char[])null, StringSplitOptions.RemoveEmptyEntries);
            nbJobs = int.Parse(firstLineSplit[0]);
            nbMachines = int.Parse(firstLineSplit[1]);
            initialSeed = int.Parse(firstLineSplit[2]);
            upperBound = int.Parse(firstLineSplit[3]);
            lowerBound = int.Parse(firstLineSplit[4]);

            string[] matrixText = input.ReadToEnd().Split((char[])null, StringSplitOptions.RemoveEmptyEntries);
            processingTime = new long[nbMachines][];
            for (int m = 0; m < nbMachines; m++)
            {
                processingTime[m] = new long[nbJobs];
                for (int j = 0; j < nbJobs; j++)
                {
                    processingTime[m][j] = long.Parse(matrixText[m * nbJobs + j]);
                }
            }
        }
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

        // Permutation of jobs
        jobs = model.List(nbJobs);

        // All jobs have to be assigned
        model.Constraint(model.Count(jobs) == nbJobs);

        // For each machine create proccessingTime[m] as an array to be able to access it 
        // with an 'at' operator
        LSExpression[] processingTimeArray = new LSExpression[nbMachines];
        for (int m = 0; m < nbMachines; m++)
            processingTimeArray[m] = model.Array(processingTime[m]);

        // On machine 0, the jth job ends on the time it took to be processed after 
        // the end of the previous job
        LSExpression[] end = new LSExpression[nbJobs];
        LSExpression firstEndSelector = model.LambdaFunction((i, prev) => prev + processingTimeArray[0][jobs[i]]);
        end[0] = model.Array(model.Range(0, nbJobs), firstEndSelector);

        // The jth job on machine m starts when it has been processed by machine n-1
        // AND when job j-1 has been processed on machine m. It ends after it has been processed.
        for (int m = 1; m < nbMachines; ++m)
        {
            LSExpression endSelector = model.LambdaFunction((i, prev) => model.Max(prev, end[m - 1][i]) + processingTimeArray[m][jobs[i]]);
            end[m] = model.Array(model.Range(0, nbJobs), endSelector);
        }

        // Minimize the makespan: end of the last job on the last machine
        makespan = end[nbMachines - 1][nbJobs - 1];
        model.Minimize(makespan);

        model.Close();

        // Parameterizes the solver.
        localsolver.GetParam().SetTimeLimit(limit);

        localsolver.Solve();
    }

    // Writes the solution in a file
    void WriteSolution(string fileName)
    {
        using (StreamWriter output = new StreamWriter(fileName))
        {
            output.WriteLine(makespan.GetValue());
            LSCollection jobsCollection = jobs.GetCollectionValue();
            for (int j = 0; j < nbJobs; j++)
            {
                output.Write(jobsCollection[j] + " ");
            }
            output.WriteLine();
        }
    }

    public static void Main(string[] args)
    {
        if (args.Length < 1)
        {
            Console.WriteLine("Usage: Flowshop inputFile [solFile] [timeLimit]");
            Environment.Exit(1);
        }
        string instanceFile = args[0];
        string outputFile = args.Length > 1 ? args[1] : null;
        string strTimeLimit = args.Length > 2 ? args[2] : "5";

        using (Flowshop model = new Flowshop())
        {
            model.ReadInstance(instanceFile);
            model.Solve(int.Parse(strTimeLimit));
            if (outputFile != null)
                model.WriteSolution(outputFile);
        }
    }
}
