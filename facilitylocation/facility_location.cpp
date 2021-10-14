//********* facility_location.cpp *********

#include <iostream>
#include <sstream>
#include <fstream>
#include <vector>
#include "localsolver.h"

using namespace localsolver;
using namespace std;


class Facilitylocation {
public:
    // Number of locations
    lsint N;

    // Number of edges between locations 
    lsint E;

    // Size of the subset S of facilities 
    lsint p;

    // Weight matrix of the shortest path between locations 
    vector<vector<lsint> > w;

    // Maximum distance between two locations 
    lsint wmax;

    // LocalSolver 
    LocalSolver localsolver;

    // Decisions variables 
    vector<LSExpression> x;
    
    // Objective 
    LSExpression totalCost;

    // Vector of facilities 
    vector<int> solution;

    // Reads instance data 
    void readInstance(const string & fileName) {
        ifstream infile;
        infile.exceptions(ifstream::failbit | ifstream::badbit);
        infile.open(fileName.c_str());

        infile >> N;
        infile >> E;
        infile >> p;

        w.resize(N);
        wmax = 0;
        for (int i = 0; i < N; i++) {
            w[i].resize(N);
            for (int j = 0; j < N; j++) {
                infile >> w[i][j];
                if (w[i][j] > wmax) {
                    wmax = w[i][j];
                }
            }
        }
    }

    // Declares the optimization model 
    void solve(int limit) {
        LSModel m = localsolver.getModel();

        // One variable for each location : 1 if facility, 0 otherwise
        x.resize(N);
        for (int i = 0; i < N; i++)
            x[i] = m.boolVar();
    
        // No more than p locations are selected to be facilities
        LSExpression openedLocations = m.sum(x.begin(), x.end());
        m.constraint(openedLocations <= p);

        // Costs between location i and j is w[i][j] if j is a facility or 2*wmax if not
        vector<vector<LSExpression> > costs(N);
        for (int i = 0; i < N; i++) {
            costs[i].resize(N);
            for (int j = 0; j < N; j++) {
                costs[i][j] = m.iif(x[j], w[i][j], 2*wmax);
            }
        }
        
        // Cost between location i and the closest facility
        vector<LSExpression> cost(N);
        for (int i = 0; i < N; i++) {
            cost[i] = m.min(costs[i].begin(), costs[i].end());
        }
        
        // Minimize the total cost
        totalCost = m.sum(cost.begin(), cost.end());
        m.minimize(totalCost);
        m.close();
        
        // Parameterizes the solver
        localsolver.getParam().setTimeLimit(limit);
        localsolver.solve();

        solution.clear();
        for (int i = 0; i < N; i++) {
            if (x[i].getValue() == 1) {
                solution.push_back(i);
            }
        }
    }

    // Writes the solution in a file following the following format:
    // each line contains the index of a facility (between 0 and N-1)
    void writeSolution(const string& fileName) {
        ofstream outfile;
        outfile.exceptions(ofstream::failbit | ofstream::badbit);
        outfile.open(fileName.c_str());

        outfile << totalCost.getValue() << endl;
        for (int i = 0; i < solution.size(); i++)
            outfile << solution[i] << " ";
        outfile << endl;
    }
};


int main(int argc, char** argv) {
    if (argc < 2) {
        cerr << "Usage: facility_location inputFile [outputFile] [timeLimit] " << endl;
        return 1;
    }

    const char* instanceFile = argv[1];
    const char* solFile = argc > 2 ? argv[2] : NULL;
    const char* strTimeLimit = argc > 3 ? argv[3] : "20";

    try {
        Facilitylocation model;
        model.readInstance(instanceFile);
        model.solve(atoi(strTimeLimit));
        if (solFile != NULL) model.writeSolution(solFile);
        return 0;
    } catch (const exception& e) {
        cerr << "An error occurred: " << e.what() << endl;
        return 1;
    }
}
