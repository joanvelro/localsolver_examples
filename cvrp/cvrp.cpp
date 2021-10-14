/********** cvrp.cpp **********/

#include <iostream>
#include <fstream>
#include <vector>
#include <cstring>
#include <cmath>
#include "localsolver.h"

using namespace localsolver;
using namespace std;

class Cvrp {
public:
    // LocalSolver
    LocalSolver localsolver;

    // Number of customers
    int nbCustomers;

    // Capacity of the trucks
    int truckCapacity;

    // Demand on each node
    vector<lsint> demands;

    // Distance matrix
    vector<vector<lsint> > distanceMatrix;

    // Distance to depot
    vector<lsint> distanceWarehouses;

    // Number of trucks
    int nbTrucks;

    // Decision variables
    vector<LSExpression> customersSequences;
    
    // Are the trucks actually used
    vector<LSExpression> trucksUsed;

    // Number of trucks used in the solution
    LSExpression nbTrucksUsed;

    // Distance traveled by all the trucks
    LSExpression totalDistance;
    
    // Constructor
    Cvrp(const char* strNbTrucks) {
        nbTrucks = atoi(strNbTrucks);
    }

    // Reads instance data.
    void readInstance(const string& fileName) {
        readInputCvrp(fileName);
        // The number of trucks is usually given in the name of the file
        // nbTrucks can also be given in command line
        if (nbTrucks == 0) nbTrucks = getNbTrucks(fileName);
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

        // Create demands as an array to be able to access it with an "at" operator
        LSExpression demandsArray = model.array(demands.begin(), demands.end());

        // Create distance as an array to be able to acces it with an "at" operator
        LSExpression distanceArray = model.array();
        for (int n = 0; n < nbCustomers; n++) {
            distanceArray.addOperand(model.array(distanceMatrix[n].begin(), distanceMatrix[n].end()));
        }
        LSExpression distanceWarehousesArray = model.array(distanceWarehouses.begin(), distanceWarehouses.end());
        
        trucksUsed.resize(nbTrucks);
        vector<LSExpression> routeDistances(nbTrucks);
                   
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
        }
        
        // Total nb trucks used
        nbTrucksUsed = model.sum(trucksUsed.begin(), trucksUsed.end());

        // Total distance traveled
        totalDistance = model.sum(routeDistances.begin(), routeDistances.end());

        // Objective: minimize the number of trucks used, then minimize the distance traveled
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
        
        outfile << nbTrucksUsed.getValue() << " " << totalDistance.getValue() << endl;
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
    // The input files follow the "Augerat" format.
    void readInputCvrp(const string& fileName) {
        ifstream infile(fileName.c_str());
        if (!infile.is_open()) {
            throw std::runtime_error("File cannot be opened.");
        }
        
        string str;
        char *pch;
        char* line;
        int nbNodes;
        while (true) {
            getline(infile, str);
            line = strdup(str.c_str());
            pch = strtok(line, " :");
            if (strcmp(pch, "DIMENSION") == 0) {
                pch = strtok(NULL, " :");
                nbNodes = atoi(pch);
                nbCustomers = nbNodes - 1;
            } else if (strcmp(pch, "CAPACITY") == 0) {
                pch = strtok(NULL, " :");
                truckCapacity = atoi(pch);
            } else if (strcmp(pch, "EDGE_WEIGHT_TYPE") == 0) {
                pch = strtok(NULL, " :");
                if (strcmp(pch, "EUC_2D") != 0) {
                    throw std::runtime_error("Only Edge Weight Type EUC_2D is supported");
                }
            } else if (strcmp(pch, "NODE_COORD_SECTION") == 0) {
                break;
            }
        }

        vector<int> customersX(nbCustomers);
        vector<int> customersY(nbCustomers);
        int depotX, depotY;
        for (int n = 1; n <= nbNodes; n++) {
            int id;
            infile >> id;
            if (id != n) {
                throw std::runtime_error("Unexpected index");
            }
            if (n == 1) {
                infile >> depotX;
                infile >> depotY;
            } else {
                // -2 because orginal customer indices are in 2..nbNodes 
                infile >> customersX[n-2];
                infile >> customersY[n-2];
            }
        }

        // Compute distance matrix
        computeDistanceMatrix(depotX, depotY, customersX, customersY);

        getline(infile, str); // End the last line
        getline(infile, str);
        line = strdup(str.c_str());
        pch = strtok(line, " :");
        if (strcmp(pch, "DEMAND_SECTION") != 0) {
            throw std::runtime_error("Expected keyword DEMAND_SECTION");
        }

        demands.resize(nbCustomers);
        for (int n = 1; n <= nbNodes; n++) {
            int id;
            infile >> id;
            if (id != n) {
                throw std::runtime_error("Unexpected index");
            }
            int demand;
            infile >> demand;
            if (n == 1) {
                if (demand != 0) {
                    throw std::runtime_error("Demand for depot should be O");
                } 
            } else {
                // -2 because orginal customer indices are in 2..nbNodes 
                demands[n-2] = demand;
            }                
        }

        getline(infile, str); // End the last line
        getline(infile, str);
        line = strdup(str.c_str());
        pch = strtok(line, " :");
        if (strcmp(pch, "DEPOT_SECTION") != 0) {
            throw std::runtime_error("Expected keyword DEPOT_SECTION");
        }

        int warehouseId;
        infile >> warehouseId;
        if (warehouseId != 1) {
            throw std::runtime_error("Warehouse id is supposed to be 1");
        }

        int endOfDepotSection;
        infile >> endOfDepotSection;
        if (endOfDepotSection != -1) {
            throw std::runtime_error("Expecting only one warehouse, more than one found");
        }

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
                lsint distance = computeDist(customersX[i], customersX[j], customersY[i], customersY[j]);
                distanceMatrix[i][j] = distance;
                distanceMatrix[j][i] = distance;
            }
        }
        
        distanceWarehouses.resize(nbCustomers);
        for (int i = 0; i < nbCustomers; ++i) {
            distanceWarehouses[i] = computeDist(depotX, customersX[i], depotY, customersY[i]);
        }
    }

    lsint computeDist(int xi, int xj, int yi, int yj) {
        double exactDist = sqrt(pow((double) xi - xj, 2) + pow((double) yi - yj, 2));
        return floor(exactDist + 0.5);
    }

    int getNbTrucks(const string& fileName) {
        size_t pos = fileName.rfind("-k");
        if (pos != string::npos) {
            string nbTrucksStr = fileName.substr(pos + 2);
            pos = nbTrucksStr.find(".");
            if (pos != string::npos) {
                return atoi(nbTrucksStr.substr(0, pos).c_str());
            }
        }
        throw std::runtime_error("Error: nbTrucks could not be read from the file name. Enter it from the command line");
        return -1;
    }
};

int main(int argc, char** argv) {
    if (argc < 2) {
        cerr << "Usage: cvrp inputFile [outputFile] [timeLimit] [nbTrucks]" << endl;
        return 1;
    }

    const char* instanceFile = argv[1];
    const char* solFile = argc > 2 ? argv[2] : NULL;
    const char* strTimeLimit = argc > 3 ? argv[3] : "20";
    const char* strNbTrucks = argc > 4 ? argv[4] : "0";

    try {
        Cvrp model(strNbTrucks);
        model.readInstance(instanceFile);
        model.solve(atoi(strTimeLimit));
        if (solFile != NULL) model.writeSolution(solFile);
        return 0;
    } catch (const exception& e) {
        cerr << "An error occurred: " << e.what() << endl;
        return 1;
    }
}

