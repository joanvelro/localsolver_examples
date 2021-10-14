//********* car_sequencing.cpp *********

#include <iostream>
#include <fstream>
#include <vector>
#include "localsolver.h"

using namespace localsolver;
using namespace std;

class CarSequencing {
public:
    // Number of vehicles. 
    int nbPositions;

    // Number of options. 
    int nbOptions;

    // Number of classes. 
    int nbClasses;

    // Options properties. 
    vector<lsint> maxCarsPerWindow;
    vector<lsint> windowSize;

    // Classes properties. 
    vector<lsint> nbCars;
    vector<vector<bool> > options;

    // Solver. 
    LocalSolver localsolver;

    // LS Program variables. 
    vector<vector<localsolver::LSExpression> > classOnPos;

    // Objective 
    LSExpression totalViolations;

    // Reads instance data. 
    void readInstance(const string& fileName) {
        ifstream infile;
        infile.exceptions(ifstream::failbit | ifstream::badbit);
        infile.open(fileName.c_str());

        infile >> nbPositions;
        infile >> nbOptions;
        infile >> nbClasses;

        maxCarsPerWindow.resize(nbOptions);
        for (int o = 0; o < nbOptions; o++)
            infile >> maxCarsPerWindow[o];

        windowSize.resize(nbOptions);
        for (int o = 0; o < nbOptions; o++)
            infile >> windowSize[o];

        options.resize(nbClasses);
        nbCars.resize(nbClasses);
        for (int c = 0; c < nbClasses; c++) {
            int ignored;
            infile >> ignored;
            infile >> nbCars[c];
            options[c].resize(nbOptions);
            for (int o = 0; o < nbOptions; o++) {
                int v;
                infile >> v;
                options[c][o] = (v == 1);
            }
        }
    }

    void solve(int limit) {
        // Declares the optimization model. 
        LSModel model = localsolver.getModel();

        // classOnPos[c][p] = 1 if class c is at position p, and 0 otherwise
        classOnPos.resize(nbClasses);
        for (int c = 0; c < nbClasses; c++) {
            classOnPos[c].resize(nbPositions);
            for (int p = 0; p < nbPositions; p++) {
                classOnPos[c][p] = model.boolVar();
            }
        }

        // All cars of class c are assigned to positions
        for (int c = 0; c < nbClasses; c++) {
            LSExpression nbCarsFromClass = model.sum(classOnPos[c].begin(), classOnPos[c].end());
            model.constraint(nbCarsFromClass == nbCars[c]);
        }

        // One car assigned to each position p
        for (int p = 0; p < nbPositions; p++) {
            LSExpression nbCarsOnPos = model.sum();
            for (int c = 0; c < nbClasses; c++) {
                nbCarsOnPos += classOnPos[c][p];
            }
            model.constraint(nbCarsOnPos == 1);
        }

        // optionsOnPos[o][p] = 1 if option o appears at position p, and 0 otherwise
        vector<vector<LSExpression> > optionsOnPos;
        optionsOnPos.resize(nbOptions);
        for (int o = 0; o < nbOptions; o++) {
            optionsOnPos[o].resize(nbPositions);
            for (int p = 0; p < nbPositions; p++) {
                optionsOnPos[o][p] = model.or_();
                for (int c = 0; c < nbClasses; c++) {
                    if (options[c][o]) optionsOnPos[o][p].addOperand(classOnPos[c][p]);
                }
            }
        }

        // Number of cars with option o in each window
        vector<vector<LSExpression> > nbCarsWindows;
        nbCarsWindows.resize(nbOptions);
        for (int o = 0; o < nbOptions; o++) {
            nbCarsWindows[o].resize(nbPositions - windowSize[o] + 1);
            for (int j = 0; j < nbPositions - windowSize[o] + 1; j++) {
                nbCarsWindows[o][j] = model.sum();
                for (int k = 0; k < windowSize[o]; k++) {
                    nbCarsWindows[o][j] += optionsOnPos[o][j + k];
                }
            }
        }

        // Number of violations of option o capacity in each window
        vector<vector<LSExpression> > nbViolationsWindows;
        nbViolationsWindows.resize(nbOptions);
        for (int o = 0; o < nbOptions; o++) {
            nbViolationsWindows[o].resize(nbPositions - windowSize[o] + 1);
            for (int j = 0; j < nbPositions - windowSize[o] + 1; j++) {
                nbViolationsWindows[o][j] = model.max(0, nbCarsWindows[o][j] - maxCarsPerWindow[o]);
            }
        }
        
        // Minimize the sum of violations for all options and all windows
        totalViolations = model.sum();
        for (int o = 0; o < nbOptions; o++) {
            totalViolations.addOperands(nbViolationsWindows[o].begin(), nbViolationsWindows[o].end());
        }

        model.minimize(totalViolations);
        model.close();

        // Parameterizes the solver. 
        localsolver.getParam().setTimeLimit(limit);


        localsolver.solve();
    }

    // Writes the solution in a file following the following format: 
    // - 1st line: value of the objective;
    // - 2nd line: for each position p, index of class at positions p.
    void writeSolution(const string& fileName) {
        ofstream outfile;
        outfile.exceptions(ofstream::failbit | ofstream::badbit);
        outfile.open(fileName.c_str());

        outfile << totalViolations.getValue() << endl;
        for (int p = 0; p < nbPositions; p++) {
            for (int c = 0; c < nbClasses; c++) {
                if (classOnPos[c][p].getValue() == 1) {
                    outfile << c << " ";
                    break;
                }
            }
        }
        outfile << endl;
    }
};

int main(int argc, char** argv) {
    if (argc < 2) {
        cerr << "Usage: car_sequencing inputFile [outputFile] [timeLimit]" << endl;
        return 1;
    }

    const char* instanceFile = argv[1];
    const char* outputFile = argc >= 3 ? argv[2] : NULL;
    const char* strTimeLimit = argc >= 4 ? argv[3] : "60";

    try {
        CarSequencing model;
        model.readInstance(instanceFile);
        model.solve(atoi(strTimeLimit));
        if (outputFile != NULL) model.writeSolution(outputFile);
        return 0;
    } catch (const exception& e) {
        cerr << "An error occurred: " << e.what() << endl;
        return 1;
    }
}

