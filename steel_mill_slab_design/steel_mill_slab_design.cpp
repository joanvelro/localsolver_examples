//********* steel_mill_slab_design.cpp *********

#include <iostream>
#include <fstream>
#include <vector>
#include "localsolver.h"

using namespace localsolver;
using namespace std;

class SteelMillSlabDesign {
public:
    // Number of available slabs    
    int nbSlabs;
    // Number of orders 
    int nbOrders;

    // Number of colors 
    int nbColors;

    // Maximum number of colors per slab
    int nbColorsMaxSlab;

    // Maximum size of a slab 
    int maxSize;

    // List of orders for each color 
    vector<vector<int> > ordersByColor;

    // Orders size 
    vector<lsint> orders;

    // Steel waste computed for each content value 
    vector<lsint> wasteForContent;

    // Solver. 
    LocalSolver localsolver;

    // LS Program variables. 
    vector<vector<LSExpression> > x;

    // Objective 
    LSExpression totalWastedSteel;

    // Reads instance data. 
    void readInstance(const string& fileName) {
        ifstream infile;
        infile.exceptions(ifstream::failbit | ifstream::badbit);
        infile.open(fileName.c_str());

        nbColorsMaxSlab = 2;

        int nbSlabSizes;
        infile >> nbSlabSizes;

        vector<int> slabSizes(nbSlabSizes);
        for (int i = 0; i < nbSlabSizes; i++) {
            infile >> slabSizes[i];
        }
        maxSize = slabSizes[nbSlabSizes - 1];

        infile >> nbColors;
        infile >> nbOrders;
        nbSlabs = nbOrders;

        ordersByColor.resize(nbColors);
        orders.resize(nbOrders);
        int sumSizeOrders = 0;
        for (int o = 0; o < nbOrders; o++) {
            infile >> orders[o];
            int c;
            infile >> c;
            // Note: colors are in [1..nbColors]
            ordersByColor[c - 1].push_back(o);
            sumSizeOrders += orders[o];
        } 

        preComputeWasteForContent(slabSizes, sumSizeOrders);
    }

private:
    // Computes the vector wasteForContent 
    void preComputeWasteForContent(const vector<int>& slabSizes, int sumSizeOrders) {       
        
        // No waste when a slab is empty.
        wasteForContent.resize(sumSizeOrders, (lsint) 0);

        int prevSize = 0;
        for (size_t i = 0; i < slabSizes.size(); i++) {
            int size = slabSizes[i];
            if (size < prevSize) {
                cerr << "Slab sizes should be sorted in ascending order" << endl;
                exit(1);
            }
            for (int content = prevSize + 1; content < size; content++) {
                wasteForContent[content] = (lsint) (size - content);
            }
            prevSize = size;
        }
    }

public:
    void solve(int limit) {
        // Declares the optimization model. 
        LSModel model = localsolver.getModel();

        // x[o][s] = 1 if order o is assigned to slab s, 0 otherwise
        x.resize(nbOrders);
        for (int o = 0; o < nbOrders; o++) {
            x[o].resize(nbSlabs);
            for (int s = 0; s < nbSlabs; s++) {
                x[o][s] = model.boolVar();
            }
        }

        // Each order is assigned to a slab
        for (int o = 0; o < nbOrders; o++) {
            LSExpression nbSlabsAssigned = model.sum(x[o].begin(), x[o].end());
            model.constraint(nbSlabsAssigned == 1);
        }

        // The content of each slab must not exceed the maximum size of the slab
        vector<LSExpression> slabContent(nbSlabs);
        for (int s = 0; s < nbSlabs; s++) {
            slabContent[s] = model.sum();
            for (int o = 0; o < nbOrders; o++) {
                slabContent[s] += orders[o]*x[o][s];
            }
            model.constraint(slabContent[s] <= maxSize);
        }

        // Create the LocalSolver array corresponding to the vector wasteForContent
        // (because "at" operators can only access LocalSolver arrays)
        LSExpression wasteForContentArray = model.array(wasteForContent.begin(), wasteForContent.end());

        // Wasted steel is computed according to the content of the slab
        vector<LSExpression> wastedSteel(nbSlabs);
        for (int s = 0; s < nbSlabs; s++) {
            wastedSteel[s] = wasteForContentArray[slabContent[s]];
        }

        // color[c][s] = 1 if the color c in the slab s, 0 otherwise
        vector<vector<LSExpression> > color(nbColors);
        for (int c = 0; c < nbColors; c++) {
            color[c].resize(nbSlabs);
            if (ordersByColor[c].size() == 0) continue;
            for (int s = 0; s < nbSlabs; s++) {
                color[c][s] = model.or_();
                for (size_t i = 0; i < ordersByColor[c].size(); i++) {
                    int o = ordersByColor[c][i];
                    color[c][s].addOperand(x[o][s]);
                }
            }
        }

        // The number of colors per slab must not exceed a specified value
        for (int s = 0; s < nbSlabs; s++) {
            LSExpression nbColorsSlab = model.sum();
            for (int c = 0; c < nbColors; c++) {
                if (ordersByColor[c].size() == 0) continue;
                nbColorsSlab += color[c][s];
            }
            model.constraint(nbColorsSlab <= nbColorsMaxSlab);
        }

        // Minimize the total wasted steel
        totalWastedSteel = model.sum(wastedSteel.begin(), wastedSteel.end());
        model.minimize(totalWastedSteel);

        model.close();

        // Parameterizes the solver. 
        localsolver.getParam().setTimeLimit(limit);

        localsolver.getParam().setNbThreads(4);

        localsolver.solve();
    }

    // Writes the solution in a file with the following format: 
    //  - total wasted steel
    //  - number of slabs used
    //  - for each slab used, the number of orders in the slab and the list of orders
    void writeSolution(const string& fileName) {
        ofstream outfile;
        outfile.exceptions(ofstream::failbit | ofstream::badbit);
        outfile.open(fileName.c_str());

        outfile << totalWastedSteel.getValue() << endl;

        int actualNbSlabs = 0;
        vector<vector<int> > ordersBySlabs(nbSlabs);
        for (int s = 0; s < nbSlabs; s++) {
            for (int o = 0; o < nbOrders; o++) {
                if (x[o][s].getValue() == 1) ordersBySlabs[s].push_back(o);
            }
            if (ordersBySlabs[s].size() > 0) actualNbSlabs++;
        }
        outfile << actualNbSlabs << endl;

        for (int s = 0; s < nbSlabs; s++) {
            size_t nbOrdersInSlab = ordersBySlabs[s].size();
            if (nbOrdersInSlab == 0) continue;
            outfile << nbOrdersInSlab << " ";
            for (size_t i = 0; i < nbOrdersInSlab; i++) {
                outfile << ordersBySlabs[s][i] << " ";
            }
            outfile << endl;
        }
    }
};

int main(int argc, char** argv) {
    if (argc < 2) {
        cerr << "Usage: steel_mill_slab_design inputFile [outputFile] [timeLimit]" << endl;
        return 1;
    }

    const char* instanceFile = argv[1];
    const char* outputFile = argc >= 3 ? argv[2] : NULL;
    const char* strTimeLimit = argc >= 4 ? argv[3] : "60";

    try {
        SteelMillSlabDesign model;
        model.readInstance(instanceFile);
        model.solve(atoi(strTimeLimit));
        if (outputFile != NULL) model.writeSolution(outputFile);
        return 0;
    } catch (const exception& e) {
        cerr << "An error occurred: " << e.what() << endl;
        return 1;
    }
}

