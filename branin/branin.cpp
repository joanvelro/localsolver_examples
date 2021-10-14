//********* branin.cpp *********

#include <iostream>
#include <fstream>
#include <vector>
#include "localsolver.h"

using namespace localsolver;
using namespace std;

class Branin {
public:
    // Solver
    LocalSolver localsolver;

    // LS Program variables.
    LSExpression x1;
    LSExpression x2;

    void solve(int limit) {
        // Parameters of the function
        lsdouble PI = 3.14159265359;
        lsdouble a = 1;
        lsdouble b = 5.1/(4*pow(PI, 2.0));
        lsdouble c = 5/PI;
        lsdouble r = 6;
        lsdouble s = 10;
        lsdouble t = 1/(8*PI);

        // Declares the optimization model. 
        LSModel model = localsolver.getModel();

        // Numerical decisions
        x1 = model.floatVar(-5.0, 10.0);
        x2 = model.floatVar(0.0, 15.0);

        // f = a(x2 - b*x1^2 + c*x1 - r)^2 + s(1-t)cos(x1) + s
        LSExpression f = a*model.pow(x2 - b*model.pow(x1, 2) + c*x1 - r, 2) + s*(1-t)*model.cos(x1) + s;

        // Minimize f
        model.minimize(f);
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
        outfile << "x1=" << x1.getDoubleValue() << endl;
        outfile << "x2=" << x2.getDoubleValue() << endl;
    }
};

int main(int argc, char** argv) {
    const char* solFile = argc > 1 ? argv[1] : NULL;
    const char* strTimeLimit = argc > 2 ? argv[2] : "6";    

    try {
        Branin model;
        model.solve(atoi(strTimeLimit));
        if (solFile != NULL) model.writeSolution(solFile);
    } catch (const exception& e) {
        cerr << "An error occurred: " << e.what() << endl;
        return 1;
    }
    return 0;
}
