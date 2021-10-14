/********** flowshop.cpp **********/

#include <iostream>
#include <fstream>
#include <vector>
#include "localsolver.h"

using namespace localsolver;
using namespace std;

class Flowshop {
public:
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
    vector<vector<lsint> > processingTime;

    // LocalSolver
    LocalSolver localsolver;

    // Decision variable
    LSExpression jobs;

    // Objective
    LSExpression makespan;

    // Reads instance data.
    void readInstance(const string& fileName) {
        ifstream infile;
        infile.exceptions(ifstream::failbit | ifstream::badbit);
        infile.open(fileName.c_str());

        infile >> nbJobs;
        infile >> nbMachines;
        infile >> initialSeed;
        infile >> upperBound;
        infile >> lowerBound;

        processingTime.resize(nbMachines);
        for (int m = 0; m < nbMachines; m++) {
            processingTime[m].resize(nbJobs);
            for (int j = 0; j < nbJobs; j++) {
                infile >> processingTime[m][j];
            }
        }
    }

    void solve(int limit) {
        // Declares the optimization model.
        LSModel model = localsolver.getModel();

        // Permutation of jobs
        jobs = model.listVar(nbJobs);

        // All jobs have to be assigned
        model.constraint(model.count(jobs) == nbJobs);

        // For each machine create proccessingTime[m] as an array to be able to access it 
        // with an 'at' operator
        vector<LSExpression> processingTimeArray(nbMachines);
        for (int m = 0; m < nbMachines; m++) {
            processingTimeArray[m] = model.array(processingTime[m].begin(), processingTime[m].end());
        }

        // On machine 0, the jth job ends on the time it took to be processed after
        // the end of the previous job
        vector<LSExpression> end(nbMachines);
        LSExpression firstEndSelector = model.createLambdaFunction([&](LSExpression i, LSExpression prev) {
            return prev + processingTimeArray[0][jobs[i]];
        });
        end[0] = model.array(model.range(0, nbJobs), firstEndSelector);

        // The jth job on machine m starts when it has been processed by machine n-1
        // AND when job j-1 has been processed on machine m. It ends after it has been processed.
        for (int m = 1; m < nbMachines; ++m) {
            int mL = m;
            LSExpression endSelector = model.createLambdaFunction([&](LSExpression i, LSExpression prev) {
                return model.max(prev, end[mL - 1][i]) + processingTimeArray[mL][jobs[i]];
            });
            end[m] = model.array(model.range(0, nbJobs), endSelector);
        }

        // Minimize the makespan: end of the last job on the last machine
        makespan = end[nbMachines - 1][nbJobs - 1];
        model.minimize(makespan);
        model.close();


        // Parameterizes the solver.
        localsolver.getParam().setTimeLimit(limit);

        localsolver.solve();
    }

    // Writes the solution in a file
    void writeSolution(const string& fileName) {
        ofstream outfile;
        outfile.exceptions(ofstream::failbit | ofstream::badbit);
        outfile.open(fileName.c_str());

        outfile << makespan.getValue() << endl;
        LSCollection jobsCollection = jobs.getCollectionValue();
        for (int j = 0; j < nbJobs; j++) {
            outfile << jobsCollection[j] << " ";
        }
        outfile << endl;
    }
};

int main(int argc, char** argv) {
    if (argc < 2) {
        cerr << "Usage: flowshop inputFile [outputFile] [timeLimit]" << endl;
        return 1;
    }

    const char* instanceFile = argv[1];
    const char* solFile = argc > 2 ? argv[2] : NULL;
    const char* strTimeLimit = argc > 3 ? argv[3] : "5";

    try {
        Flowshop model;
        model.readInstance(instanceFile);
        model.solve(atoi(strTimeLimit));
        if (solFile != NULL) model.writeSolution(solFile);
        return 0;
     } catch (const exception& e) {
        cerr << "An error occurred: " << e.what() << endl;
        return 1;
    }
}


