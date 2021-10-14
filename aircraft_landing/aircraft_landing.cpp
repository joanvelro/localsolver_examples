/********** aircraft_landing.cpp **********/

#include <iostream>
#include <fstream>
#include <vector>
#include <string.h>
#include "localsolver.h"

using namespace localsolver;
using namespace std;

class AircraftLanding {
private:

    // Data from the problem
    int nbPlanes;
    int freezeTime;
    vector<lsint> appearanceTime;
    vector<lsint> earliestTime;
    vector<lsint> targetTime;
    vector<lsint> latestTime;
    vector<lsdouble> earlinessCost;
    vector<lsdouble> latenessCost;
    vector<vector<int>> separationTime;

    // LocalSolver
    LocalSolver localsolver;

    // Decision variables
    LSExpression landingOrder;
    vector<LSExpression> preferredTime;

    // Landing time for each plane
    LSExpression landingTime;

    // Objective
    LSExpression totalCost;

public:
    /* Read instance data */
    void readInstance(const string& fileName) {
        ifstream infile;
        infile.exceptions(ifstream::failbit | ifstream::badbit);
        infile.open(fileName.c_str());

        infile >> nbPlanes;
        infile >> freezeTime;
        appearanceTime.resize(nbPlanes);
        earliestTime.resize(nbPlanes);
        targetTime.resize(nbPlanes);
        latestTime.resize(nbPlanes);
        earlinessCost.resize(nbPlanes);
        latenessCost.resize(nbPlanes);
        separationTime.resize(nbPlanes, vector<int>(nbPlanes));
        preferredTime.resize(nbPlanes);

        for (int i = 0; i < nbPlanes; ++i) {
            infile >> appearanceTime[i];
            infile >> earliestTime[i];
            infile >> targetTime[i];
            infile >> latestTime[i];
            infile >> earlinessCost[i];
            infile >> latenessCost[i];
            for (int j = 0; j < nbPlanes; ++j) {
                infile >> separationTime[i][j];
            }
        }
        infile.close();
    }

    LSExpression getMinLandingTime(LSExpression p, LSExpression prev, LSModel model, LSExpression separationTimeArray) {
        return model.iif(p > 0,
                         prev + model.at(separationTimeArray, landingOrder[p - 1], landingOrder[p]),
                         0);
    }

    void solve(int limit) {
        // Declare the optimization model
        LSModel model = localsolver.getModel();

        // A list variable: landingOrder[i] is the index of the ith plane to land
        landingOrder = model.listVar(nbPlanes);

        // All planes must be scheduled
        model.constraint(model.count(landingOrder) == nbPlanes);

        // Create LocalSolver arrays to be able to access them with an "at" operator
        LSExpression targetTimeArray = model.array(targetTime.begin(), targetTime.end());
        LSExpression latestTimeArray = model.array(latestTime.begin(), latestTime.end());
        LSExpression earlinessCostArray = model.array(earlinessCost.begin(), earlinessCost.end());
        LSExpression latenessCostArray = model.array(latenessCost.begin(), latenessCost.end());
        LSExpression separationTimeArray = model.array();
        for (int i = 0; i < nbPlanes; i++) {
            LSExpression row = model.array(separationTime[i].begin(), separationTime[i].end());
            separationTimeArray.addOperand(row);
        }

        // Int variables: preferred time for each plane
        for (int p = 0; p < nbPlanes; ++p) {
            preferredTime[p] = model.intVar(earliestTime[p], targetTime[p]);
        }
        LSExpression preferredTimeArray = model.array(preferredTime.begin(), preferredTime.end());

        // Landing time for each plane
        LSExpression landingTimeSelector = model.createLambdaFunction([&](LSExpression p, LSExpression prev) {
                return model.max(preferredTimeArray[landingOrder[p]], getMinLandingTime(p, prev, model, separationTimeArray));});
        landingTime = model.array(model.range(0, nbPlanes), landingTimeSelector);

        // Landing times must respect the separation time with every previous plane.
        for (int p = 1; p < nbPlanes; ++p) {
            LSExpression lastSeparationEnd = model.max();
            for (int previousPlane = 0; previousPlane < p; ++previousPlane) {
                lastSeparationEnd.addOperand(landingTime[previousPlane]
                                            + model.at(separationTimeArray, landingOrder[previousPlane], landingOrder[p]));
            }
            model.constraint(landingTime[p] >= lastSeparationEnd);
        }
        
        totalCost = model.sum();
        for (int p = 0; p < nbPlanes; ++p) {
            // Constraint on latest landing time
            LSExpression planeIndex = landingOrder[p];
            model.constraint(landingTime[p] <= latestTimeArray[planeIndex]);

            // Cost for each plane
            LSExpression unitCost = model.iif(landingTime[p] < targetTimeArray[planeIndex],
                                              earlinessCostArray[planeIndex],
                                              latenessCostArray[planeIndex]);
            LSExpression differenceToTargetTime = model.abs(landingTime[p] - targetTimeArray[planeIndex]);
            totalCost.addOperand(unitCost * differenceToTargetTime);
        }

        // Minimize the total cost
        model.minimize(totalCost);

        model.close();

        // Parameterize the solver
        localsolver.getParam().setTimeLimit(limit);

        localsolver.solve();
    }

    /* Write the solution in a file */
    void writeSolution(const string& fileName) {
        ofstream outfile;
        outfile.exceptions(ofstream::failbit | ofstream::badbit);
        outfile.open(fileName.c_str());
        outfile << totalCost.getDoubleValue() << endl;
        LSCollection landingOrderCollection = landingOrder.getCollectionValue();
        for (int i = 0; i < nbPlanes; i++) {
            outfile << landingOrderCollection[i] << " ";
        }
        outfile << endl;
    }
};

int main(int argc, char** argv) {
    if (argc < 2) {
        cerr << "Usage: aircraft_landing inputFile [outputFile] [timeLimit]" << endl;
        return 1;
    }
    const char* instanceFile = argv[1];
    const char* solFile = argc > 2 ? argv[2] : NULL;
    const char* strTimeLimit = argc > 3 ? argv[3] : "20";
    try {
        AircraftLanding model;
        model.readInstance(instanceFile);
        model.solve(atoi(strTimeLimit));
        if (solFile != NULL) model.writeSolution(solFile);
        return 0;
    } catch (const exception& e) {
        cerr << "An error occurred: " << e.what() << endl;
        return 1;
    }
}
