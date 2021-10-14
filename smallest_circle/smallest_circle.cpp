//********* smallest_circle.cpp *********

#include <iostream>
#include <sstream>
#include <fstream>
#include <vector>
#include "localsolver.h"

using namespace localsolver;
using namespace std;

class SmallestCircle {
public:
    // Number of points 
    int nbPoints;

    // Point coordinates 
    vector<lsint> coordX;
    vector<lsint> coordY;

    // Minimum and maximum value of the coordinates of the points 
    lsdouble minX;
    lsdouble minY;
    lsdouble maxX;
    lsdouble maxY;

    // Solver. 
    LocalSolver localsolver;

    // LS Program variables 
    LSExpression x;
    LSExpression y;
    
    // Objective 
    LSExpression r;

    // Reads instance data 
    void readInstance(const string& fileName) {
        ifstream infile;
        infile.exceptions(ifstream::failbit | ifstream::badbit);
        infile.open(fileName.c_str());

        infile >> nbPoints;

        coordX.resize(nbPoints);
        coordY.resize(nbPoints);
        infile >> coordX[0];
        infile >> coordY[0];

        minX = coordX[0];
        maxX = coordX[0];
        minY = coordY[0];
        maxY = coordY[0];

        for (int i = 1; i < nbPoints; i++) {
            infile >> coordX[i];
            infile >> coordY[i];
            if (coordX[i] < minX) minX = coordX[i];
            else if (coordX[i] > maxX) maxX = coordX[i];
            if (coordY[i] < minY) minY = coordY[i];
            else if (coordY[i] > maxY) maxY = coordY[i];
        }
    }

    void solve(int limit) {
        // Declares the optimization model. 
        LSModel model = localsolver.getModel();

        // Numerical decisions
        x = model.floatVar(minX, maxX);
        y = model.floatVar(minY, maxY);

        // Distance between the origin and the point i
        vector<LSExpression> radius(nbPoints);
        for (int i = 0; i < nbPoints; i++) {
            radius[i] = model.pow(x - coordX[i], 2) + model.pow(y - coordY[i], 2);
        }

        // Minimize the radius r
        r = model.sqrt(model.max(radius.begin(), radius.end()));

        model.minimize(r);
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

        outfile << "x=" << x.getDoubleValue() << endl;
        outfile << "y=" << y.getDoubleValue() << endl;
        outfile << "r=" << r.getDoubleValue() << endl;
    }    
};

int main(int argc, char** argv) {
    if (argc < 2) {
        cerr << "Usage: smallest_circle inputFile [outputFile] [timeLimit]" << endl;
        return 1;
    }

    const char* instanceFile = argv[1];
    const char* solFile = argc > 2 ? argv[2] : NULL;
    const char* strTimeLimit = argc > 3 ? argv[3] : "6";

    try {
        SmallestCircle model;
        model.readInstance(instanceFile);
        model.solve(atoi(strTimeLimit));
        if (solFile != NULL) model.writeSolution(solFile);
        return 0;
    } catch (const exception& e) {
        cerr << "An error occurred: " << e.what() << endl;
        return 1;
    }
}
