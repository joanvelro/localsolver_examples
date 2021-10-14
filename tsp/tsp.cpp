/********** tsp.cpp **********/

#include <iostream>
#include <fstream>
#include <vector>
#include <string.h>
#include "localsolver.h"

using namespace localsolver;
using namespace std;

class Tsp {
public:
    // Number of cities
    int nbCities;

    // Vector of distance between two cities
    vector<vector<lsint> > distanceWeight;

    // LocalSolver.
    LocalSolver localsolver;

    // Decision variables.
    LSExpression cities;

    // Objective
    LSExpression obj;

    /* Reads instance data. */
    void readInstance(const string& fileName) {
        ifstream infile;
        infile.exceptions(ifstream::failbit | ifstream::badbit);
        infile.open(fileName.c_str());

        // The input files follow the TSPLib "explicit" format.
        string str;
        char * pch;
        char* line;

        while (true) {
            getline(infile, str);
            line = strdup(str.c_str());
            pch = strtok(line, " :");
            if (strcmp(pch, "DIMENSION") == 0) {
                getline(infile, str);
                line = strdup(str.c_str());
                pch = strtok(NULL, " :");
                nbCities = atoi(pch);
            } else if (strcmp(pch, "EDGE_WEIGHT_SECTION") == 0) {
                break;
            }
        }

        // Distance from i to j
        distanceWeight.resize(nbCities);
        for (int i = 0; i < nbCities; i++) {
            distanceWeight[i].resize(nbCities);
            for (int j = 0; j < nbCities; j++) {
                infile >> distanceWeight[i][j];
            }
        }
    }

    void solve(int limit) {
        // Declares the optimization model.
        LSModel model = localsolver.getModel();

        // A list variable: cities[i] is the index of the ith city in the tour
        cities = model.listVar(nbCities);

        // All cities must be visited
        model.constraint(model.count(cities) == nbCities);

        // Create a LocalSolver array for the distance matrix in order to be able to
        // access it with "at" operators.
        LSExpression distanceArray = model.array();
        for (int i = 0; i < nbCities; i++) {
            LSExpression row = model.array(distanceWeight[i].begin(), distanceWeight[i].end());
            distanceArray.addOperand(row);
        }

        // Minimize the total distance
        LSExpression distSelector = model.createLambdaFunction([&](LSExpression i) { return model.at(distanceArray, cities[i-1], cities[i]); });
        obj = model.sum(model.range(1, nbCities), distSelector) + model.at(distanceArray, cities[nbCities-1], cities[0]);

        model.minimize(obj);

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

        outfile << obj.getValue() << endl;
        LSCollection citiesCollection = cities.getCollectionValue();
        for (int i = 0; i < nbCities; i++) {
            outfile << citiesCollection[i] << " ";
        }
        outfile << endl;
    }
};

int main(int argc, char** argv) {
    if (argc < 2) {
        cerr << "Usage: tsp inputFile [outputFile] [timeLimit]" << endl;
        return 1;
    }

    const char* instanceFile = argv[1];
    const char* solFile = argc > 2 ? argv[2] : NULL;
    const char* strTimeLimit = argc > 3 ? argv[3] : "5";
     try {
        Tsp model;
        model.readInstance(instanceFile);
        model.solve(atoi(strTimeLimit));
        if (solFile != NULL) model.writeSolution(solFile);
        return 0;
    } catch (const exception& e) {
            cerr << "An error occurred: " << e.what() << endl;
        return 1;
    }
}
