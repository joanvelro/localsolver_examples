//********* revenue_management.cpp *********

#include <iostream>
#include <fstream>
#include <stdlib.h>
#include <cmath>
#include <vector>
#include "localsolver.h"

using namespace localsolver;
using namespace std;

struct EvaluatedPoint {
public:
    EvaluatedPoint(vector<int> point, double value) : point(point), value(value) {}
    const int getPoint(int index) { return point[index]; }
    const double getValue() { return value; }
private:
    vector<int> point;
    double value;
};

/* Black-box function */
class RevenueManagementFunction : public LSBlackBoxFunction<lsdouble> {
private:
    int seed;
    const int nbPeriods = 3;
    const int purchasePrice = 80;
    const int nbSimulations = (int) 1e6;
    vector<EvaluatedPoint> evaluatedPoints;

    const int prices(int index) {
        const int p[] = {100, 300, 400};
        return p[index];
    }

    const int meanDemands(int index) {
        const int d[] = {50, 20, 30};
        return d[index];
    }

    double exponentialSample(double rateParam = 1.0) {
        double u = (double) rand() / RAND_MAX;
        return log(1 - u) / (-rateParam);
    }

    double gammaSample(double scaleParam = 1.0) {
        return exponentialSample(scaleParam);
    }

public:
    // Constructor
    RevenueManagementFunction(int seed) : seed(seed) {
        evaluatedPoints.push_back(EvaluatedPoint({100, 50, 30}, 4740.99));
    }

    const unsigned int getNbPeriods() { return nbPeriods; }
    const vector<EvaluatedPoint> getEvaluatedPoints() { return evaluatedPoints; }

    lsdouble call(const LSBlackBoxArgumentValues& argumentValues) override {
        // Initial quantity purchased
        int nbUnitsPurchased = argumentValues.getIntValue(0);
        // Number of units that should be left for future periods
        vector<int> nbUnitsReserved(nbPeriods, 0);
        for (unsigned int j = 0; j < nbPeriods - 1; j++) {
            nbUnitsReserved[j] = argumentValues.getIntValue(j+1);
        }
        // Sets seed for reproducibility
        srand(seed);
        // Creates distribution
        vector<double> X;
        for (unsigned int i = 0; i < nbSimulations; i++) {
            X.push_back(gammaSample());
        }
        vector<vector<double>> Y;
        for (unsigned int i = 0; i < nbSimulations; i++) {
            vector<double> yt;
            for (unsigned int j = 0; j < nbPeriods; j++) {
                yt.push_back(exponentialSample());
            }
            Y.push_back(yt);
        }

        // Runs simulations
        double sumProfit = 0;
        for (unsigned int i = 0; i < nbSimulations; i++) {
            int remainingCapacity = nbUnitsPurchased;
            for (unsigned int j = 0; j < nbPeriods; j++) {
                // Generates demand for period j
                int demand = (int) (meanDemands(j) * X[i] * Y[i][j]);
                int nbUnitsSold = min(max(remainingCapacity - nbUnitsReserved[j], 0),
                        demand);
                remainingCapacity = remainingCapacity - nbUnitsSold;
                sumProfit += prices(j) * nbUnitsSold;
            }
        }
        // Calculates mean revenue
        double meanProfit = sumProfit / nbSimulations;
        double meanRevenue = meanProfit - purchasePrice * nbUnitsPurchased;

        return meanRevenue;
    }
};

class RevenueManagement {
public:
    // Solver
    LocalSolver localsolver;

    // LS Program variables
    vector<LSExpression> variables;
    LSExpression bbCall;

    void solve(int timeLimit, int evaluationLimit) {
        // Declares the optimization model
        LSModel model = localsolver.getModel();

        // Generates data
        RevenueManagementFunction revenueManagement(1);
        unsigned int nbPeriods = revenueManagement.getNbPeriods();
        // Declares decision variables
        for (unsigned int i = 0; i < nbPeriods; i++) {
            variables.push_back(model.intVar(0, 100));
        }

        // Creates blackbox function
        LSExpression bbFunc = model.createBlackBoxFunction(&revenueManagement);
        // Calls function
        bbCall = model.call(bbFunc);
        for (unsigned int i = 0; i < nbPeriods; i++) {
            bbCall.addOperand(variables[i]);
        }

        // Declares constraints
        for (unsigned int i = 1; i < nbPeriods; i++) {
            model.constraint(variables[i] <= variables[i-1]);
        }

        // Maximizes function call
        model.maximize(bbCall);

        // Sets lower bound
        LSBlackBoxContext context = bbFunc.getBlackBoxContext();
        context.setLowerBound(0.0);

        model.close();

        // Parametrizes the solver
        if (timeLimit != 0) {
            localsolver.getParam().setTimeLimit(timeLimit);
        }

        // Sets the maximum number of evaluations
        context.setEvaluationLimit(evaluationLimit);

        // Adds evaluation points
        for (EvaluatedPoint evaluatedPoint : revenueManagement.getEvaluatedPoints()) {
            LSBlackBoxEvaluationPoint evaluationPoint = context.createEvaluationPoint();
            for (int i = 0; i < nbPeriods; i++) {
                evaluationPoint.addArgument((lsint) evaluatedPoint.getPoint(i));
            }
            evaluationPoint.setReturnValue(evaluatedPoint.getValue());
        }

        localsolver.solve();
    }

    // Writes the solution in a file
    void writeSolution(const string& fileName) {
        ofstream outfile;
        outfile.exceptions(ofstream::failbit | ofstream::badbit);
        outfile.open(fileName.c_str());
        outfile << "obj=" << bbCall.getDoubleValue() << endl;
        outfile << "b=" << variables[0].getIntValue() << endl;
        for (unsigned int i = 1; i < variables.size(); i++) {
            outfile << "r" << (i+1) << "=" << variables[i].getIntValue() << endl;
        }
    }
};

int main(int argc, char** argv) {
    const char* solFile = argc > 1 ? argv[1] : NULL;
    const char* strTimeLimit = argc > 2 ? argv[2] : "0";
    const char* strEvaluationLimit = argc > 3 ? argv[3] : "30";

    try {
        RevenueManagement model;
        model.solve(atoi(strTimeLimit), atoi(strEvaluationLimit));
        if (solFile != NULL) model.writeSolution(solFile);
    } catch (const exception& e) {
        cerr << "An error occurred: " << e.what() << endl;
        return 1;
    }
    return 0;
}
