//********* curve_fitting.cpp *********

#include <iostream>
#include <fstream>
#include <vector>
#include "localsolver.h"

using namespace localsolver;
using namespace std;

class CurveFitting {
public:

    // Number of observations
    int nbObservations;

    // Inputs and Outputs
    vector<lsdouble> inputs;
    vector<lsdouble> outputs;
    
    // Solver
    LocalSolver localsolver;

    // Decision variables (parameters of the mapping function)
    LSExpression a, b, c, d;

    // Objective (square error)
    LSExpression squareError;

    // Reads instance data
    void readInstance(const string& fileName) {
        ifstream infile;
        infile.exceptions(ifstream::failbit | ifstream::badbit);
        infile.open(fileName.c_str());

        infile >> nbObservations;

        inputs.resize(nbObservations);
        outputs.resize(nbObservations);
        for (int i = 0; i < nbObservations; i++) {
            infile >> inputs[i];
            infile >> outputs[i]; 
        }
    }

    void solve(int limit) {
        // Declares the optimization model
        LSModel model = localsolver.getModel();

        // Decision variables
        a = model.floatVar(-100, 100);
        b = model.floatVar(-100, 100);
        c = model.floatVar(-100, 100);
        d = model.floatVar(-100, 100);
    
        // Minimize square error
        squareError = model.sum();
        for (int i = 0; i < nbObservations; i++) {
            LSExpression prediction = a * model.sin(b - inputs[i]) + c * pow(inputs[i], 2) + d;
            LSExpression error = model.pow(prediction - outputs[i], 2);
            squareError.addOperand(error);
        }
        model.minimize(squareError);
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
        outfile << "Optimal mapping function" << endl;
        outfile << "a = " << a.getDoubleValue() << endl;
        outfile << "b = " << b.getDoubleValue() << endl;
        outfile << "c = " << c.getDoubleValue() << endl;
        outfile << "d = " << d.getDoubleValue() << endl;
    }
};

int main(int argc, char** argv) {
    if (argc < 2) {
        cerr << "Usage: curve_fitting inputFile [outputFile] [timeLimit]" << endl;
        return 1;
    }

    const char* instanceFile = argv[1];
    const char* solFile = argc > 2 ? argv[2] : NULL;
    const char* strTimeLimit = argc > 3 ? argv[3] : "3";

    try {
        CurveFitting model;
        model.readInstance(instanceFile);
        model.solve(atoi(strTimeLimit));
        if (solFile != NULL) model.writeSolution(solFile);
        return 0;
    } catch (const exception& e) {
        cerr << "An error occurred: " << e.what() << endl;
        return 1;
    }
}