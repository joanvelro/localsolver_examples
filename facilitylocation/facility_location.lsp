/********** facility_location.lsp **********/

use io;

/* Reads instance data. */
function input() {
    local usage = "Usage: localsolver facility_location.lsp "
        + "inFileName=inputFile [solFileName=outputFile] [lsTimeLimit=timeLimit]";

    if (inFileName == nil) throw usage;

    local inFile = io.openRead(inFileName);
    N = inFile.readInt();
    E = inFile.readInt();
    p = inFile.readInt();
    wmax = 0;

    for [i in 1..N][j in 1..N] {
        w[i][j] = inFile.readInt();
        if (w[i][j] > wmax) wmax = w[i][j];
    }
}

/* Declares the optimization model. */
function model() {
    // One variable for each location : 1 if facility, 0 otherwise
    x[1..N] <- bool();

    // No more than p locations are selected to be facilities
    constraint sum[i in 1..N] (x[i]) <= p;

    // Costs between location i and j is w[i][j] if j is a facility or 2*wmax if not
    costs[i in 1..N][j in 1..N] <- x[j] ? w[i][j] : 2*wmax;

    // Cost between location i and the closest facility
    cost[i in 1..N] <- min[j in 1..N] (costs[i][j]);

    // Minimize the total cost
    totalCost <- sum[i in 1..N] (cost[i]);
    minimize totalCost;
}

/* Parameterizes the solver. */
function param() {
    if (lsTimeLimit == nil) lsTimeLimit = 20;
}

/* Writes the solution in a file following the following format: 
 * - value of the objective
 * - indices of the facilities (between 0 and N-1) */
function output() {
    if (solFileName == nil) return; 
    local solFile = io.openWrite(solFileName);
    solFile.println(totalCost.value);
    for [i in 1..N : x[i].value == 1] {
        solFile.print(i-1, " ");
    }
    solFile.println("");
}
