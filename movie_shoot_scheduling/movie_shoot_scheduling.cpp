/********** movie_Shoot_scheduling.cpp **********/

#include <iostream>
#include <fstream>
#include <vector>
#include <string.h>
#include "localsolver.h"
#include <limits>
using namespace localsolver;
using namespace std;

class MssInstance {
public:
    int nbActors;
    int nbScenes;
    int nbLocations;
    int nbPrecedences;
    vector<int> actorCost;
    vector<int> locationCost;
    vector<int> sceneDuration;
    vector<int> sceneLocation;
    vector<int> nbWorkedDays;

    vector<vector<bool>> isActorInScene;
    vector<vector<int>> precedence;

    /* Read instance data */
    void readInstance(const string& fileName) {
        ifstream infile;
        infile.exceptions(ifstream::failbit | ifstream::badbit);
        infile.open(fileName.c_str());

        infile >> nbActors;
        infile >> nbScenes;
        infile >> nbLocations;
        infile >> nbPrecedences;
        actorCost.resize(nbActors);
        locationCost.resize(nbLocations);
        sceneDuration.resize(nbScenes);
        sceneLocation.resize(nbScenes);
        isActorInScene.resize(nbActors, vector<bool>(nbScenes));
        precedence.resize(nbPrecedences, vector<int>(2));

        for (int j = 0; j < nbActors; ++j)
            infile >> actorCost[j];
        for (int k = 0; k < nbLocations; ++k)
            infile >> locationCost[k];
        for (int i = 0; i < nbScenes; ++i)
            infile >> sceneDuration[i];
        for (int i = 0; i < nbScenes; ++i)
            infile >> sceneLocation[i];
        int tmp;
        for (int j = 0; j < nbActors; ++j) {
            for (int i = 0; i < nbScenes; ++i) {
                infile >> tmp;
                isActorInScene[j][i] = tmp;
            }
        }
        for (int p = 0; p < nbPrecedences; ++p) {
            for (int i = 0; i < 2; ++i)
                infile >> precedence[p][i];
        }
        infile.close();
    }

    void computeNbWorkedDays() {
        nbWorkedDays.resize(nbActors);
        for (int j = 0; j < nbActors; ++j) {
            nbWorkedDays[j] = 0;
            for (int i = 0; i < nbScenes; ++i) {
                if (isActorInScene[j][i]) {
                    nbWorkedDays[j] += sceneDuration[i];
                }
            }
        }
    }

public:
    // Constructor
    MssInstance(const string& fileName) {
        readInstance(fileName);
        computeNbWorkedDays();
    }
};

/* External function */
class CostFunction : public LSExternalFunction<lsint> {
private:
    const MssInstance* instance;
    // To maintain thread-safety property, thread_local (since C++11) is used
    // here. Each thread must have have independant following variables.

    // Number of visits per location (group of successive shoots)
    static thread_local vector<int> nbLocationVisits;

    // Last day of work for each actor
    static thread_local vector<int> actorFirstDay;

    // Last day of work for each actor
    static thread_local vector<int> actorLastDay;

    int computeLocationCost(LSCollection shootOrder) {
        int previousLocation = -1;
        for (int i = 0; i < instance->nbScenes; ++i) {
            int currentLocation = instance->sceneLocation[shootOrder[i]];
            // When we change location, we increment the number of shoots of the new location
            if (previousLocation != currentLocation) {
                nbLocationVisits[currentLocation] += 1;
                previousLocation = currentLocation;
            }
        }
        int locationExtraCost = 0;
        for (int k = 0; k < instance->nbLocations; ++k) {
            locationExtraCost += (nbLocationVisits[k] - 1) * instance->locationCost[k];
        }
        return locationExtraCost;
    }

    int computeActorCost(LSCollection shootOrder) {
        // Compute first and last days of work for each actor
        for (int j = 0; j < instance->nbActors; ++j)
        {
            bool hasActorStartedWorking = false;
            int startDayOfScene = 0;
            for (int i = 0; i < instance->nbScenes; ++i)
            {
                int currentScene = shootOrder[i];
                int endDayOfScene = startDayOfScene + instance->sceneDuration[currentScene] - 1;
                if (instance->isActorInScene[j][currentScene])
                {
                    actorLastDay[j] = endDayOfScene;
                    if (!(hasActorStartedWorking))
                    {
                        hasActorStartedWorking = true;
                        actorFirstDay[j] = startDayOfScene;
                    }
                }
                // The next scene begins the day after the end of the current one
                startDayOfScene = endDayOfScene + 1;
            }
        }

        // Compute actor extra cost due to days paid but not worked
        int actorExtraCost = 0;
        for (int j = 0; j < instance->nbActors; ++j)
        {
            int nbPaidDays = actorLastDay[j] - actorFirstDay[j] + 1;
            actorExtraCost += (nbPaidDays - instance->nbWorkedDays[j]) * instance->actorCost[j];
        }
        return actorExtraCost;
    }

    void initStaticVectors() {
        nbLocationVisits.clear();
        nbLocationVisits.resize(instance->nbLocations, 0);
        actorFirstDay.clear();
        actorFirstDay.resize(instance->nbActors, 0);
        actorLastDay.clear();
        actorLastDay.resize(instance->nbActors, 0);
    }

public:
    // Constructor
    CostFunction(const MssInstance* instance) : instance(instance) {
    }

    lsint call(const LSExternalArgumentValues& argumentValues) {
        LSCollection shootOrder = argumentValues.getCollectionValue(0);
        if (shootOrder.count() < instance->nbScenes) {
            // Infeasible solution if some shoots are missing
            return numeric_limits<int>::max();
        }

        initStaticVectors();
        int locationExtraCost = computeLocationCost(shootOrder);
        int actorExtraCost = computeActorCost(shootOrder);
        return locationExtraCost + actorExtraCost;
    }
};

class MovieShootScheduling {
private:
    // LocalSolver
    LocalSolver localsolver;

    // Instance data
    const MssInstance* instance;

    // Decision variable
    LSExpression shootOrder;

    // Objective
    LSExpression callCostFunc;

public:
    // Constructor
    MovieShootScheduling(const MssInstance* mssi) {
        instance = mssi;
    }
    void solve(int limit) {
        // Declare the optimization model
        LSModel model = localsolver.getModel();

        // A list variable: shootOrder[i] is the index of the ith scene to be shot
        shootOrder = model.listVar(instance->nbScenes);

        // All shoots must be scheduled
        model.constraint(model.count(shootOrder) == instance->nbScenes);

        // Constraint of precedence between scenes
        for (int p = 0; p < instance->nbPrecedences; ++p)
            model.constraint(model.indexOf(shootOrder, instance->precedence[p][0]) < model.indexOf(shootOrder, instance->precedence[p][1]));

        // Minimize external function
        CostFunction costObject(instance);
        LSExpression costFunc = model.createExternalFunction(&costObject);
        costFunc.getExternalContext().setIntLowerBound(0);
        callCostFunc = costFunc(shootOrder);
        model.minimize(callCostFunc);

        model.close();

        // Parameterize the solver
        localsolver.getParam().setTimeLimit(limit);

        localsolver.solve();
    }

    /* Write the solution in a file in the following format:
    * - 1st line: value of the objective;
    * - 2nd line: for each i, the index of the ith scene to be shot. */
    void writeSolution(const string& fileName) {
        ofstream outfile;
        outfile.exceptions(ofstream::failbit | ofstream::badbit);
        outfile.open(fileName.c_str());
        outfile << callCostFunc.getIntValue() << endl;
        LSCollection shootOrderCollection = shootOrder.getCollectionValue();
        for (int i = 0; i < instance->nbScenes; i++) {
            outfile << shootOrderCollection[i] << " ";
        }
        outfile << endl;
    }
};

thread_local std::vector<int> CostFunction::nbLocationVisits;
thread_local std::vector<int> CostFunction::actorFirstDay;
thread_local std::vector<int> CostFunction::actorLastDay;

int main(int argc, char** argv) {
    if (argc < 2) {
        cerr << "Usage: movie_shoot_scheduling inputFile [outputFile] [timeLimit]" << endl;
        return 1;
    }
    const char* instanceFile = argv[1];
    const char* solFile = argc > 2 ? argv[2] : NULL;
    const char* strTimeLimit = argc > 3 ? argv[3] : "20";
    MssInstance instance(instanceFile);
    MovieShootScheduling model(&instance);
    try {
        model.solve(atoi(strTimeLimit));
        if (solFile != NULL) model.writeSolution(solFile);
        return 0;
    } catch (const exception& e) {
            cerr << "An error occurred: " << e.what() << endl;
        return 1;
    }
}
