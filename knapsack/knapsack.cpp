//********* knapsack.cpp *********

#include <iostream>
#include <fstream>
#include <vector>
#include "localsolver.h"

using namespace localsolver;
using namespace std;

class Knapsack {
public:
    // Number of items. 
    int nbItems;

    // Items properties. 
    vector<lsint> weights;
    vector<lsint> values;

    // Knapsack bound 
    lsint knapsackBound;
    
    // LocalSolver. 
    LocalSolver localsolver;

    // Decision variables. 
    vector<LSExpression> x;

    // Objective. 
    LSExpression knapsackValue;

    // Solution (items in the knapsack). 
    vector<int> solution;

    // Reads instance data. 
    void readInstance(const string& fileName) {
        ifstream infile;
        infile.exceptions(ifstream::failbit | ifstream::badbit);
        infile.open(fileName.c_str());

        infile >> nbItems;

        weights.resize(nbItems);
        for (int i = 0; i < nbItems; i++)
            infile >> weights[i];

        values.resize(nbItems);
        for (int i = 0; i < nbItems; i++)
            infile >> values[i];
    
        infile >> knapsackBound;   
    }

    void solve(int limit) {
        // Declares the optimization model. 
        LSModel model = localsolver.getModel();

        // Decision variables x[i] 
        x.resize(nbItems);
        for (int i = 0; i < nbItems; i++) {
            x[i] = model.boolVar();
        }

        // Weight constraint
        LSExpression knapsackWeight = model.sum();
        for (int i = 0; i < nbItems; i++) {
            LSExpression itemWeight = x[i]*weights[i];
            knapsackWeight += itemWeight;
        }
        model.constraint(knapsackWeight <= knapsackBound);
    
        // Maximize value
        knapsackValue = model.sum();
        for (int i = 0; i < nbItems; i++) {
            LSExpression itemValue = x[i]*values[i];
            knapsackValue += itemValue;
        }
        model.maximize(knapsackValue);
        model.close();

        // Parameterizes the solver. 
        localsolver.getParam().setTimeLimit(limit);

        localsolver.solve();

        solution.clear();
        for (int i = 0; i < nbItems; ++i)
            if (x[i].getValue() == 1) 
                solution.push_back(i);
    }

    // Writes the solution in a file 
    void writeSolution(const string& fileName) {
        ofstream outfile;
        outfile.exceptions(ofstream::failbit | ofstream::badbit);
        outfile.open(fileName.c_str());

        outfile << knapsackValue.getValue() << endl;
        for (unsigned int i = 0; i < solution.size(); ++i)
            outfile << solution[i] << " ";
        outfile << endl;
    }
};

int main(int argc, char** argv) {
    if (argc < 2) {
        cerr << "Usage: knapsack inputFile [outputFile] [timeLimit]" << endl;
        return 1;
    }

    const char* instanceFile = argv[1];
    const char* solFile = argc > 2 ? argv[2] : NULL;
    const char* strTimeLimit = argc > 3 ? argv[3] : "20";

    try {
        Knapsack model;
        model.readInstance(instanceFile);
        model.solve(atoi(strTimeLimit));
        if (solFile != NULL) model.writeSolution(solFile);
        return 0;
    } catch (const exception& e) {
        cerr << "An error occurred: " << e.what() << endl;
        return 1;
    }
}

