/********** cvrptw.cpp **********/

#include <iostream>
#include <fstream>
#include <vector>
#include <cstring>
#include <cmath>
#include "localsolver.h"

using namespace localsolver;
using namespace std;

class Cvrptw {
public:
    // LocalSolver
    LocalSolver localsolver;

    // Number of customers
    int nbCustomers;

    // Capacity of the trucks
    int truckCapacity;

    // Latest allowed arrival to depot
    int maxHorizon;

    // Demand on each node
    vector<lsint> demands;

    // Earliest arrival on each node
    vector<lsint> earliestStart;

    // Latest departure from each node
    vector<lsint> latestEnd;

    // Service time on each node
    vector<lsint> serviceTime;

    // Distance matrix
    vector<vector<lsdouble> > distanceMatrix;

    // Distance to depot
    vector<lsdouble> distanceWarehouses;

    // Number of trucks
    int nbTrucks;

    // Decision variables
    vector<LSExpression> customersSequences;

    // Are the trucks actually used
    vector<LSExpression> trucksUsed;

    // Cumulated lateness in the solution (must be 0 for the solution to be valid)
    LSExpression totalLateness;

    // Number of trucks used in the solution
    LSExpression nbTrucksUsed;

    // Distance traveled by all the trucks
    LSExpression totalDistance;

    // Constructor
    Cvrptw() {
    }

    // Reads instance data.
    void readInstance(const string& fileName) {
        readInputCvrptw(fileName);
    }

    void solve(int limit) {
        // Declares the optimization model.
        LSModel model = localsolver.getModel();

        // Sequence of customers visited by each truck.
        customersSequences.resize(nbTrucks);
        for (int k = 0; k < nbTrucks; k++) {
            customersSequences[k] = model.listVar(nbCustomers);
        }

        // All customers must be visited by the trucks
        model.constraint(model.partition(customersSequences.begin(), customersSequences.end()));

        // Create demands, earliest, latest and service as arrays to be able to access it with an "at" operator
        LSExpression demandsArray = model.array(demands.begin(), demands.end());
        LSExpression earliestArray = model.array(earliestStart.begin(), earliestStart.end());
        LSExpression latestArray = model.array(latestEnd.begin(), latestEnd.end());
        LSExpression serviceArray = model.array(serviceTime.begin(), serviceTime.end());


        // Create distance as an array to be able to acces it with an "at" operator
        LSExpression distanceArray = model.array();
        for (int n = 0; n < nbCustomers; n++) {
            distanceArray.addOperand(model.array(distanceMatrix[n].begin(), distanceMatrix[n].end()));
        }
        LSExpression distanceWarehousesArray = model.array(distanceWarehouses.begin(), distanceWarehouses.end());

        trucksUsed.resize(nbTrucks);
        vector<LSExpression> routeDistances(nbTrucks), endTime(nbTrucks), homeLateness(nbTrucks), lateness(nbTrucks);

        for (int k = 0; k < nbTrucks; k++) {
            LSExpression sequence = customersSequences[k];
            LSExpression c = model.count(sequence);

            // A truck is used if it visits at least one customer
            trucksUsed[k] = c > 0;

            // The quantity needed in each route must not exceed the truck capacity
            LSExpression demandSelector = model.createLambdaFunction([&](LSExpression i) { return demandsArray[sequence[i]]; });
            LSExpression routeQuantity = model.sum(model.range(0, c), demandSelector);
            model.constraint(routeQuantity <= truckCapacity);

            // Distance traveled by truck k
            LSExpression distSelector = model.createLambdaFunction([&](LSExpression i) { return model.at(distanceArray, sequence[i - 1], sequence[i]); });
            routeDistances[k] = model.sum(model.range(1, c), distSelector) +
                model.iif(c > 0, distanceWarehousesArray[sequence[0]] + distanceWarehousesArray[sequence[c - 1]], 0);

            //End of each visit
            LSExpression endSelector = model.createLambdaFunction([&](LSExpression i, LSExpression prev) {
             return model.max(earliestArray[sequence[i]],
                      model.iif(i == 0,
                              distanceWarehousesArray[sequence[0]],
                              prev + model.at(distanceArray, sequence[i - 1], sequence[i]))
                             )
                              + serviceArray[sequence[i]]; });
            
            endTime[k] = model.array(model.range(0, c), endSelector);
            
            // Arriving home after max_horizon
            homeLateness[k] = model.iif(trucksUsed[k],
                            model.max(0, endTime[k][c - 1] + distanceWarehousesArray[sequence[c - 1]] - maxHorizon),
                            0);

            //completing visit after latest_end
            LSExpression lateSelector = model.createLambdaFunction([&](LSExpression i) { return model.max(0, endTime[k][i] - latestArray[sequence[i]]);});
            lateness[k] = homeLateness[k] + model.sum(model.range(0, c), lateSelector);
        }

        // Total lateness
        totalLateness = model.sum(lateness.begin(), lateness.end());

        // Total nb trucks used
        nbTrucksUsed = model.sum(trucksUsed.begin(), trucksUsed.end());

        // Total distance traveled
        totalDistance = model.round(100*model.sum(routeDistances.begin(), routeDistances.end()))/100;

        // Objective: minimize the number of trucks used, then minimize the distance traveled
        model.minimize(totalLateness);
        model.minimize(nbTrucksUsed);
        model.minimize(totalDistance);

        model.close();

        // Parameterizes the solver.
        localsolver.getParam().setTimeLimit(limit);

        localsolver.solve();
    }

    // Writes the solution in a file with the following format:
    //  - number of trucks used and total distance
    //  - for each truck the nodes visited (omitting the start/end at the depot)
    void writeSolution(const string& fileName) {
        ofstream outfile;
        outfile.exceptions(ofstream::failbit | ofstream::badbit);
        outfile.open(fileName.c_str());

        outfile << nbTrucksUsed.getValue() << " " << totalDistance.getDoubleValue() << endl;
        for (int k = 0; k < nbTrucks; k++) {
            if (trucksUsed[k].getValue() != 1) continue;
            // Values in sequence are in [0..nbCustomers-1]. +2 is to put it back in [2..nbCustomers+1]
            // as in the data files (1 being the depot)
            LSCollection customersCollection = customersSequences[k].getCollectionValue();
            for (lsint i = 0; i < customersCollection.count(); i++) {
                outfile << customersCollection[i] + 2 << " ";
            }
            outfile << endl;
        }
    }

private:

    // The input files follow the "Solomon" format.
    void readInputCvrptw(const string& fileName) {
        ifstream infile(fileName.c_str());
        if (!infile.is_open()) {
            throw std::runtime_error("File cannot be opened.");
        }

        string str;
        char *pch;
        char* line;
        int nbNodes;
        long dump;

        int depotX, depotY;
        vector<int> customersX;
        vector<int> customersY;

        getline(infile, str);
        getline(infile, str);
        getline(infile, str);
        getline(infile, str);

        infile >> nbTrucks;
        infile >> truckCapacity;

        cout << nbTrucks << " " << truckCapacity <<endl;

        getline(infile, str);
        getline(infile, str);
        getline(infile, str);
        getline(infile, str);

        infile >> dump;
        infile >> depotX;
        infile >> depotY;
        infile >> dump;
        infile >> dump;
        infile >> maxHorizon;
        infile >> dump;

        int tt = 1;
        while (!infile.eof()) {
            int cx, cy, demand, ready, due, service;
            infile >> dump;
            infile >> cx;
            infile >> cy;
            infile >> demand;
            infile >> ready;
            infile >> due;
            infile >> service;

            customersX.push_back(cx);
            customersY.push_back(cy);
            demands.push_back(demand);
            earliestStart.push_back(ready);
            latestEnd.push_back(due+service);//in input files due date is meant as latest start time
            serviceTime.push_back(service);
        }

        nbCustomers = customersX.size();

        // Compute distance matrix
        computeDistanceMatrix(depotX, depotY, customersX, customersY);

        infile.close();
    }

    // Computes the distance matrix
    void computeDistanceMatrix(int depotX, int depotY, const vector<int>& customersX, const vector<int>& customersY) {
        distanceMatrix.resize(nbCustomers);
        for (int i = 0; i < nbCustomers; i++) {
            distanceMatrix[i].resize(nbCustomers);
        }
        for (int i = 0; i < nbCustomers; i++) {
            distanceMatrix[i][i] = 0;
            for (int j = i + 1; j < nbCustomers; j++) {
                lsdouble distance = computeDist(customersX[i], customersX[j], customersY[i], customersY[j]);
                distanceMatrix[i][j] = distance;
                distanceMatrix[j][i] = distance;
            }
        }

        distanceWarehouses.resize(nbCustomers);
        for (int i = 0; i < nbCustomers; ++i) {
            distanceWarehouses[i] = computeDist(depotX, customersX[i], depotY, customersY[i]);
        }
    }

    lsdouble computeDist(int xi, int xj, int yi, int yj) {
        return sqrt(pow((double) xi - xj, 2) + pow((double) yi - yj, 2));
    }

};

int main(int argc, char** argv) {
    if (argc < 2) {
        cerr << "Usage: cvrptw inputFile [outputFile] [timeLimit] [nbTrucks]" << endl;
        return 1;
    }

    const char* instanceFile = argv[1];
    const char* solFile = argc > 2 ? argv[2] : NULL;
    const char* strTimeLimit = argc > 3 ? argv[3] : "20";

    try {
        Cvrptw model;
        model.readInstance(instanceFile);
        model.solve(atoi(strTimeLimit));
        if (solFile != NULL) model.writeSolution(solFile);
        return 0;
    } catch (const exception& e) {
        cerr << "An error occurred: " << e.what() << endl;
        return 1;
    }
}

