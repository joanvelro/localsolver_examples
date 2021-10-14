//********* toy.cpp *********

#include <iostream>
#include "localsolver.h"

using namespace localsolver;
using namespace std;

int main()
{
    try {
        lsint weights[] = {10, 60, 30, 40, 30, 20, 20, 2};
        lsint values[] = {1, 10, 15, 40, 60, 90, 100, 15};
        lsint knapsackBound = 102;
    
        // Declares the optimization model. 
        LocalSolver localsolver;
        LSModel model = localsolver.getModel();
    
        // 0-1 decisions
        LSExpression x[8];
        for (int i = 0; i < 8; i++) 
            x[i] = model.boolVar();
    
        // knapsackWeight <- 10*x0 + 60*x1 + 30*x2 + 40*x3 + 30*x4 + 20*x5 + 20*x6 + 2*x7;
        LSExpression knapsackWeight = model.sum();
        for (int i = 0; i < 8; i++) 
            knapsackWeight += weights[i]*x[i];
    
        // knapsackWeight <= knapsackBound;
        model.constraint(knapsackWeight <= knapsackBound);
    
        // knapsackValue <- 1*x0 + 10*x1 + 15*x2 + 40*x3 + 60*x4 + 90*x5 + 100*x6 + 15*x7;
        LSExpression knapsackValue = model.sum();
        for (int i = 0; i < 8; i++) 
            knapsackValue += values[i]*x[i];
    
        // maximize knapsackValue;
        model.maximize(knapsackValue);
    
        // close model, then solve
        model.close();

        // Parameterizes the solver. 
        localsolver.getParam().setTimeLimit(10);
        localsolver.solve();

    } catch (const exception& e) {
        cerr << "An error occurred:" << e.what() << endl;
        return 1;
    }
    
    return 0;
}

