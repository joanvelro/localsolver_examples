//********* social_golfer.cpp *********

#include <iostream>
#include <sstream>
#include <fstream>
#include <vector>
#include "localsolver.h"

using namespace localsolver;
using namespace std;

class SocialGolfer{
public:

    // Number of groups 
    lsint nbGroups;
    // Size of each group 
    lsint groupSize;
    // Number of week 
    lsint nbWeeks;
    // Number of golfers 
    lsint nbGolfers;

    // Objective 
    LSExpression obj;

    // LocalSolver. 
    LocalSolver localsolver;

    // Decisions variables 
    vector< vector< vector< LSExpression > > > x;

    // Reads instance data 
    void readInstance(const string & fileName) {
        ifstream infile;
        infile.exceptions(ifstream::failbit | ifstream::badbit);
        infile.open(fileName.c_str());

        infile >> nbGroups;
        infile >> groupSize;
        infile >> nbWeeks;
        infile.close();

        nbGolfers = nbGroups*groupSize;
    }

    // Declares the optimization model. 
    void solve(int limit) {
        LSModel model = localsolver.getModel(); 

        // Decision variables
        // 0-1 decisions variables: x[w][gr][gf]=1 if golfer gf is in group gr on week w
        x.resize(nbWeeks);
        for (int w = 0; w < nbWeeks; w++) {
            x[w].resize(nbGroups);
            for (int gr = 0; gr < nbGroups; gr++) {
                x[w][gr].resize(nbGolfers);
                for (int gf = 0; gf < nbGolfers; gf++) {
                    x[w][gr][gf]=model.boolVar();
                }
            }
        }

        // each week, each golfer is assigned to exactly one group
        for (int w = 0; w < nbWeeks; w++) {
            for (int gf = 0; gf < nbGolfers; gf++) {
                LSExpression nbGroupsAssigned = model.sum();
                for (int gr = 0; gr < nbGroups; gr++) {
                    nbGroupsAssigned += x[w][gr][gf];
                }
                model.constraint(nbGroupsAssigned == 1);
            }
        }

        // each week, each group contains exactly groupSize golfers
        for (int w = 0; w < nbWeeks; w++) {
            for (int gr = 0; gr < nbGroups; gr++) {
                LSExpression nbGolfersInGroup = model.sum();
                for (int gf = 0; gf < nbGolfers; gf++) {
                    nbGolfersInGroup += x[w][gr][gf];
                }
                model.constraint(nbGolfersInGroup == groupSize);
            }
        }

        // golfers gf0 and gf1 meet in group gr on week w if both are assigned to this group for week w.
        vector< vector< vector< vector< LSExpression > > > > meetings;
        meetings.resize(nbWeeks);
        for (int w = 0; w < nbWeeks; w++) {
            meetings[w].resize(nbGroups);
            for (int gr = 0; gr < nbGroups; gr++) {
                meetings[w][gr].resize(nbGolfers);
                for (int gf0 = 0; gf0 < nbGolfers; gf0++) {
                    meetings[w][gr][gf0].resize(nbGolfers);
                    for (int gf1 = gf0+1; gf1 < nbGolfers; gf1++) {
                        meetings[w][gr][gf0][gf1] = model.and_(x[w][gr][gf0], x[w][gr][gf1]);
                    }
                }
            }
        }

        // the number of meetings of golfers gf0 and gf1 is the sum of their meeting variables over all weeks and groups
        vector< vector< LSExpression> > redundantMeetings;
        redundantMeetings.resize(nbGolfers);
        for (int gf0 = 0; gf0 < nbGolfers; gf0++) {
            redundantMeetings[gf0].resize(nbGolfers);
            for (int gf1 = gf0+1; gf1 < nbGolfers; gf1++) {
                LSExpression nbMeetings = model.sum();
                for (int w = 0; w < nbWeeks; w++) {
                    for (int gr = 0; gr < nbGroups; gr++) {
                        nbMeetings += meetings[w][gr][gf0][gf1];
                    }
                }
                redundantMeetings[gf0][gf1] = model.max(nbMeetings -1, 0);
            }
        }

        // the goal is to minimize the number of redundant meetings
        obj = model.sum();
        for (int gf0 = 0; gf0 < nbGolfers; gf0++) {
            for (int gf1 = gf0+1; gf1 < nbGolfers; gf1++) {
                obj += redundantMeetings[gf0][gf1];
            }
        }
        model.minimize(obj);

        model.close();
        // Parameterizes the solver. 
        localsolver.getParam().setTimeLimit(limit);

        localsolver.solve(); 
    }

    // Writes the solution in a file following the following format: 
    //  - the objective value
    //  - for each week and each group, write the golfers of the group 
    // (nbWeeks x nbGroupes lines of groupSize numbers).
    void writeSolution(const string& fileName) {
        ofstream outfile;
        outfile.exceptions(ofstream::failbit | ofstream::badbit);
        outfile.open(fileName.c_str());

        outfile << obj.getValue() << endl;
        for (int w = 0; w < nbWeeks; w++) {
            for (int gr = 0; gr < nbGroups; gr++) {
                for (int gf = 0; gf < nbGolfers; gf++) {
                    if (x[w][gr][gf].getValue()) {
                        outfile << gf << " ";
                    }
                }
                outfile << endl;
            }
            outfile << endl;
        }
    }
};
    
int main(int argc, char** argv) {
    if (argc < 2) {
        cerr << "Usage: solcial_golfer inputFile [outputFile] [timeLimit]" << endl;
        return 1;
    }

    const char* instanceFile = argv[1];
    const char* solFile = argc > 2 ? argv[2] : NULL;
    const char* strTimeLimit = argc > 3 ? argv[3] : "10";

    try {
        SocialGolfer model;
        model.readInstance(instanceFile);
        model.solve(atoi(strTimeLimit));
        if (solFile != NULL) model.writeSolution(solFile);
        return 0;
    } catch (const exception& e) {
        cerr << "An error occurred: " << e.what() << endl;
        return 1;
    }
}

