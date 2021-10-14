/********** assembly_line_balancing.cpp **********/

#include <iostream>
#include <fstream>
#include <vector>
#include "localsolver.h"

using namespace localsolver;
using namespace std;

class ALBInstance {
public:
    int nbTasks;
    int nbMaxStations;
    int cycleTime;
    string to_throw;
    vector<int> processingTime;
    vector<vector<int>> successors;

    /* Read instance data */
    void readInstance(const string& fileName) {
        ifstream infile;
        infile.exceptions(ifstream::failbit | ifstream::badbit);
        infile.open(fileName.c_str());

        for (int i = 0; i < 3; ++i)
            infile >> to_throw;

        // Read number of tasks
        infile >> nbTasks;
        nbMaxStations = nbTasks;
        processingTime.resize(nbTasks);
        successors.resize(nbTasks);
        for (int i = 0; i < 2; ++i)
            infile >> to_throw;

        // Read the cycle time limit
        infile >> cycleTime;
        for (int i = 0; i < 5; ++i)
            infile >> to_throw;

        // Read the processing times
        for (int i = 0; i < nbTasks; ++i) {
            int task;
            infile >> task;
            infile >> processingTime[task - 1];
        }
        for (int i = 0; i < 2; ++i)
            infile >> to_throw;

        // Read the successors' relations
        string delimiter = ",";
        while (infile.eof() != true) {
            string relation;
            infile >> relation;
            string predecessor = relation.substr(0, relation.find(delimiter));
            if(predecessor == relation)
                break;
            string successor = relation.substr(relation.find(delimiter)+1, relation.size());
            successors[stoi(predecessor)-1].push_back(stoi(successor)-1);
        }
        infile.close();
    }

    ALBInstance(const string& fileName) {
        readInstance(fileName);
    }
};

class AssemblyLineBalancing {
private:
    // LocalSolver
    LocalSolver localsolver;

    // Instance data
    const ALBInstance* instance;

    // Decision variables
    vector<LSExpression> station;

    // Intermediate expressions
    vector<LSExpression> timeInStation;
    vector<LSExpression> taskStation;

    // Objective
    LSExpression nbUsedStations;

public:
    // Constructor
    AssemblyLineBalancing(const ALBInstance* albi) : instance(albi) {
    }

    void solve(int limit) {
        // Declare the optimization model
        LSModel model = localsolver.getModel();

        // station[s] is the set of tasks assigned to station s
        station.resize(instance->nbMaxStations);
        LSExpression partition = model.partition();
        for(int s = 0; s < instance->nbMaxStations; ++s) {
            station[s] = model.setVar(instance->nbTasks);
            partition.addOperand(station[s]);
        }
        model.constraint(partition);

        // nbUsedStations is the total number of used stations
        nbUsedStations = model.sum();
        for (int s = 0; s < instance->nbMaxStations; ++s)
            nbUsedStations.addOperand((model.count(station[s]) > 0));

        // All stations must respect the cycleTime constraint
        timeInStation.resize(instance->nbMaxStations);
        LSExpression processingTimeArray = model.array(instance->processingTime.begin(), instance->processingTime.end());
        LSExpression timeSelector = model.lambdaFunction([&](LSExpression i) { return processingTimeArray[i]; });
        for (int s = 0; s < instance->nbMaxStations; ++s) {
            timeInStation[s] = model.sum(station[s], timeSelector);
            model.constraint(timeInStation[s] <= instance->cycleTime);
        }

        // The stations must respect the succession's order of the tasks
        taskStation.resize(instance->nbTasks);
        for (int i = 0; i < instance->nbTasks; ++i) {
            taskStation[i] = model.sum();
            for (int s = 0; s < instance->nbMaxStations; ++s)
                taskStation[i].addOperand(model.contains(station[s], i) * s);
        }
        for (int i = 0; i < instance->nbTasks; ++i)
            for (int j : instance->successors[i])
                model.constraint(taskStation[i] <= taskStation[j]);

        // Minimization of the number of active stations
        model.minimize(nbUsedStations);

        model.close();

        // Parametrize the solver
        localsolver.getParam().setTimeLimit(limit);
        // Initialize with a naive solution: each task belongs to one separate station
        // Note: nbTasks equals nbMaxStations
        for (int i = 0; i < instance->nbTasks; ++i)
            station[i].getCollectionValue().add(i);

        localsolver.solve();
    }

    /* Write the solution in a file following the format:
    * - 1st line: value of the objective
    * - 2nd line: number of tasks
    * - following lines: task's number, station's number */
    void writeSolution(const string& fileName) {
        ofstream outfile;
        outfile.exceptions(ofstream::failbit | ofstream::badbit);
        outfile.open(fileName.c_str());
        outfile << nbUsedStations.getIntValue() << endl;
        outfile << instance->nbTasks << endl;
        for (int i = 0; i < instance->nbTasks; ++i)
            outfile << i + 1 << "," << taskStation[i].getIntValue() + 1 << endl;
    }
};

int main(int argc, char** argv) {
    if (argc < 2) {
        cerr << "Usage: assembly_line_balancing inputFile [outputFile] [timeLimit]" << endl;
        return 1;
    }
    const char* instanceFile = argv[1];
    const char* solFile = argc > 2 ? argv[2] : NULL;
    const char* strTimeLimit = argc > 3 ? argv[3] : "20";
    ALBInstance instance(instanceFile);
    AssemblyLineBalancing model(&instance);
    try {
        model.solve(atoi(strTimeLimit));
        if (solFile != NULL) model.writeSolution(solFile);
        return 0;
    } catch (const exception& e) {
        cerr << "An error occurred: " << e.what() << endl;
        return 1;
    }
}
