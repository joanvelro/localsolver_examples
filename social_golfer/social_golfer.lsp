/********** social_golfer.lsp **********/

use io;

/* Reads instance data. */
function input() {
    local usage = "\nUsage: localsolver social_golfer.lsp "
    + "inFileName=inputFile [solFileName=outputFile] [lsTimeLimit=timeLimit]\n";

    if (inFileName == nil) throw usage;

    local inFile = io.openRead(inFileName);
    nbGroups = inFile.readInt();
    groupSize = inFile.readInt();
    nbWeeks = inFile.readInt();
}

/* Declares the optimization model. */
function model() {

    // the number of golfers 
    nbGolfers = nbGroups*groupSize;

    // 0-1 decisions variables: x[w][gr][gf]=1 if golfer gf is in group gr on week w.
    x[1..nbWeeks][1..nbGroups][1..nbGolfers] <- bool();

    // each week, each golfer is assigned to exactly one group
    for[w in 1..nbWeeks][gf in 1..nbGolfers]
        constraint sum[gr in 1..nbGroups](x[w][gr][gf]) == 1;

    // each week, each group contains exactly groupSize golfers
    for[w in 1..nbWeeks][gr in 1..nbGroups]
        constraint sum[gf in 1..nbGolfers](x[w][gr][gf]) == groupSize;

    // golfers gf0 and gf1 meet in group gr on week w if both are assigned to this group for week w.
    meetings[w in 1..nbWeeks][gr in 1..nbGroups][gf0 in 1..nbGolfers][gf1 in gf0+1..nbGolfers]
            <- and(x[w][gr][gf0], x[w][gr][gf1]);

    // the number of meetings of golfers gf0 and gf1 is the sum of their meeting variables over all weeks and groups
    for[gf0 in 1..nbGolfers][gf1 in gf0+1..nbGolfers] {
        nb_meetings[gf0][gf1] <- sum[w in 1..nbWeeks][gr in 1..nbGroups](meetings[w][gr][gf0][gf1]);
        redundant_meetings[gf0][gf1] <- max(nb_meetings[gf0][gf1] -1, 0);
    }

    // the goal is to minimize the number of redundant meetings
    obj <- sum[gf0 in 1..nbGolfers][gf1 in gf0+1..nbGolfers](redundant_meetings[gf0][gf1]);
    minimize obj;
}

/* Parameterizes the solver. */
function param() {
    if (lsTimeLimit == nil) lsTimeLimit = 10; 
    if (lsNbThreads == nil) lsNbThreads = 1;
}

/* Writes the solution in a file following the following format: 
 * - the objective value
 * - for each week and each group, write the golfers of the group 
 * (nbWeeks x nbGroupes lines of groupSize numbers).
 */
function output() {
    if (solFileName == nil) return;
    local solution = io.openWrite(solFileName);
    solution.println(obj.value);
    for [w in 1..nbWeeks]{
        for [gr in 1..nbGroups]{
            for [gf in 1..nbGolfers] {
                if (x[w][gr][gf].value==true) {
                    solution.print(gf-1, " ");
                }
            }
            solution.println();
        }
        solution.println();
    }
}
