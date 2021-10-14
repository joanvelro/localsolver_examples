//********* optimal_bucket.cpp *********
#include <iostream>
#include <fstream>
#include <vector>
#include "localsolver.h"

using namespace localsolver;
using namespace std;

class OptimalBucket {
public:
    // Solver. 
    LocalSolver localsolver;

    // LS Program variables. 
    LSExpression R;
    LSExpression r;
    LSExpression h;

    LSExpression surface;
    LSExpression volume;

    void solve(int limit) {
        lsdouble PI = 3.14159265359;

        // Declares the optimization model. 
        LSModel model = localsolver.getModel();

        // Numerical decisions
        R = model.floatVar(0.0, 1.0);
        r = model.floatVar(0.0, 1.0);
        h = model.floatVar(0.0, 1.0);

        // Surface must not exceed the surface of the plain disc
        surface = PI*model.pow(r, 2) + PI*(R + r)*model.sqrt(model.pow(R - r, 2) + model.pow(h, 2));
        model.constraint(model.leq(surface, PI));

        // Maximize the volume
        volume = PI*h/3*(model.pow(R, 2) + R*r + model.pow(r, 2));
        model.maximize(volume);

        model.close();

        // Parameterizes the solver. 
        localsolver.getParam().setTimeLimit(limit);


        localsolver.solve();
    }
    
    // Writes the solution in a file with the following format:
    //  - surface and volume of the bucket
    //  - values of R, r and h
    void writeSolution(const string& fileName) {
        ofstream outfile;
        outfile.exceptions(ofstream::failbit | ofstream::badbit);
        outfile.open(fileName.c_str());

        outfile << surface.getDoubleValue() << " " << volume.getDoubleValue() << endl;
        outfile << R.getDoubleValue() << " " << r.getDoubleValue() << " " << h.getDoubleValue() << endl;
    }
};

int main(int argc, char** argv) {
    const char* solFile = argc > 1 ? argv[1] : NULL;
    const char* strTimeLimit = argc > 2 ? argv[2] : "2";    

    try {
        OptimalBucket model;
        model.solve(atoi(strTimeLimit));
        if (solFile != NULL) model.writeSolution(solFile);
        return 0;
    } catch (const exception& e) {
        cerr << "An error occurred:" << e.what() << endl;
        return 1;
    }
}
