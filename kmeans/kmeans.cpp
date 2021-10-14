//********* kmeans.cpp *********

#include <iostream>
#include <fstream>
#include <vector>
#include <limits>
#include "localsolver.h"

using namespace localsolver;
using namespace std;

class Kmeans {
public:
    // Data properties 
    int nbObservations;
    int nbDimensions;
    int k;

    vector<vector<lsdouble> > coordinates;
    vector<string> initialClusters;

    // Solver. 
    LocalSolver localsolver;

    // Decisions 
    vector<LSExpression> clusters;

    // Objective 
    LSExpression obj;

    // Constructor 
    Kmeans(int k) : k(k) { }

    // Reads instance data 
    void readInstance(const string& fileName) {
        ifstream infile;
        infile.exceptions(ifstream::failbit | ifstream::badbit);
        infile.open(fileName.c_str());

        infile >> nbObservations;
        infile >> nbDimensions;

        coordinates.resize(nbObservations);
        initialClusters.resize(nbObservations);
        for (int o = 0; o < nbObservations; o++) {
            coordinates[o].resize(nbDimensions);
            for (int d = 0; d < nbDimensions; d++) {
                infile >> coordinates[o][d];
            }
            infile >> initialClusters[o];
        }
    }

    void solve(int limit) {
        // Declares the optimization model. 
        LSModel model = localsolver.getModel();

        // Set decisions: clusters[c] represents the points in cluster c
        clusters.resize(k);
        for (int c = 0; c < k; ++c) {
            clusters[c] = model.setVar(nbObservations);
        }

        // Each point must be in one cluster and one cluster only
        model.constraint(model.partition(clusters.begin(), clusters.end()));

        // Coordinates of points
        LSExpression coordinatesArray = model.array();
        for (int o = 0; o < nbObservations; o++) {
            coordinatesArray.addOperand(model.array(coordinates[o].begin(),
                                                    coordinates[o].end()));
        }

        // Compute variances
        vector<LSExpression> variances;
        variances.resize(k);
        for (int c = 0; c < k; c++) {
            LSExpression cluster = clusters[c];
            LSExpression size = model.count(cluster);

            // Compute the centroid of the cluster
            LSExpression centroid = model.array();
            for (int d = 0; d < nbDimensions; d++) {
                LSExpression coordinateSelector = model.createLambdaFunction(
                    [&](LSExpression o) { return model.at(coordinatesArray, o, d); });
                centroid.addOperand(model.iif(size == 0, 0,
                    model.sum(cluster, coordinateSelector) / size));
            }

            // Compute the variance of the cluster
            LSExpression variance = model.sum();
            for (int d = 0; d < nbDimensions; d++) {
                LSExpression dimensionVarianceSelector = model.createLambdaFunction(
                    [&](LSExpression o) { 
                        return model.pow(model.at(coordinatesArray, o, d) 
                                         - model.at(centroid, d), 2);
                    });
                LSExpression dimensionVariance = model.sum(cluster,
                    dimensionVarianceSelector);
                variance.addOperand(dimensionVariance);
            }
            variances[c] = variance;
        }

        // Minimize the total variance
        obj = model.sum(variances.begin(), variances.end());
        model.minimize(obj);

        model.close();

        // Parameterizes the solver. 
        localsolver.getParam().setTimeLimit(limit);

        localsolver.solve(); 
    }

    // Writes the solution in a file in the following format:
    //  - objective value
    //  - k
    //  - for each cluster, a line with the elements in the cluster (separated by spaces)
    void writeSolution(const string& fileName) {
        ofstream outfile;
        outfile.exceptions(ofstream::failbit | ofstream::badbit);
        outfile.open(fileName.c_str());

        outfile << obj.getDoubleValue() << endl;
        outfile << k << endl;
        for (int c = 0; c < k; c++) {
            LSCollection clusterCollection = clusters[c].getCollectionValue();
            for (int i = 0; i < clusterCollection.count(); i++) {
                    outfile << clusterCollection[i] << " ";
                }
            outfile << endl;
        }
    }
};
    
int main(int argc, char** argv) {
    if (argc < 2) {
        cerr << "Usage: kmeans inputFile [outputFile] [timeLimit] [k value]" << endl;
        return 1;
    }

    const char* instanceFile = argv[1];
    const char* solFile = argc > 2 ? argv[2] : NULL;
    const char* strTimeLimit = argc > 3 ? argv[3] : "5";
    const char* k = argc > 4 ? argv[4] : "2";

    try {
        Kmeans model(atoi(k));
        model.readInstance(instanceFile);
        model.solve(atoi(strTimeLimit));
        if (solFile != NULL) model.writeSolution(solFile);
        return 0;
    } catch (const exception& e) {
        cerr << "An error occurred: " << e.what() << endl;
        return 1;
    }
}
