//********* hosaki.cpp *********

#include <iostream>
#include <fstream>
#include <cmath>
#include "localsolver.h"

using namespace localsolver;
using namespace std;

/* Black-box function */
class HosakiFunction : public LSBlackBoxFunction<lsdouble> {
    lsdouble call(const LSBlackBoxArgumentValues& argumentValues) override {
        lsdouble x1 = argumentValues.getDoubleValue(0);
        lsdouble x2 = argumentValues.getDoubleValue(1);
        return (1 - 8*x1 + 7*x1*x1 - 7*pow(x1, 3)/3 + pow(x1, 4)/4) * x2*x2
            * exp(-x2);
    }
};

class Hosaki {
public:
    // Solver
    LocalSolver localsolver;

    // LS Program variables
    LSExpression x1;
    LSExpression x2;
    LSExpression bbCall;

    void solve(int evaluationLimit) {
        // Declares the optimization model
        LSModel model = localsolver.getModel();

        // Numerical decisions
        x1 = model.floatVar(0, 5);
        x2 = model.floatVar(0, 6);

        // Creates and calls blackbox function
        HosakiFunction bbFuncClass;
        LSExpression bbFunc = model.createBlackBoxFunction(&bbFuncClass);
        bbCall = model.call(bbFunc, x1, x2);

        // Minimizes function call
        model.minimize(bbCall);
        model.close();

        // Parameterizes the solver
        LSBlackBoxContext context = bbFunc.getBlackBoxContext();
        context.setEvaluationLimit(evaluationLimit);

        localsolver.solve();
    }

    // Writes the solution in a file
    void writeSolution(const string& fileName) {
        ofstream outfile;
        outfile.exceptions(ofstream::failbit | ofstream::badbit);
        outfile.open(fileName.c_str());
        outfile << "obj=" << bbCall.getDoubleValue() << endl;
        outfile << "x1=" << x1.getDoubleValue() << endl;
        outfile << "x2=" << x2.getDoubleValue() << endl;
    }
};

int main(int argc, char** argv) {
    const char* solFile = argc > 1 ? argv[1] : NULL;
    const char* strEvaluationLimit = argc > 2 ? argv[2] : "30";

    try {
        Hosaki model;
        model.solve(atoi(strEvaluationLimit));
        if (solFile != NULL) model.writeSolution(solFile);
    } catch (const exception& e) {
        cerr << "An error occurred: " << e.what() << endl;
        return 1;
    }
    return 0;
}
