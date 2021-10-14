/********** maxcut.lsp **********/

use io;

/* Reads instance data. */
function input() {
    local usage = "Usage: localsolver maxcut.lsp "
        + "inFileName=inputFile [solFileName=outputFile] [lsTimeLimit=timeLimit]";

    if (inFileName == nil) throw usage;

    local inFile = io.openRead(inFileName);
    n = inFile.readInt();
    m = inFile.readInt();

    for [e in 1..m] {
        origin[e] = inFile.readInt();
        dest[e] = inFile.readInt();
        w[e] = inFile.readInt();
    }
}

/* Declares the optimization model. */
function model() {
    // x[i] is 1 if vertex i is in the subset S, 0 if it is in V-S
    x[1..n] <- bool();

    //an edge is in the cut-set if it has an extremity in each class of the bipartition
    incut[e in 1..m] <- x[origin[e]] != x[dest[e]];
    cutWeight <- sum[e in 1..m] (w[e]* incut[e]);
    maximize cutWeight;
}

/* Parameterizes the solver. */
function param() {
    if (lsTimeLimit == nil) lsTimeLimit = 10;
}

/* Writes the solution in a file following the following format: 
 *  - objective value
 *  - each line contains a vertex number and its subset (1 for S, 0 for V-S) */
function output() {
    if (solFileName == nil) return;
    println("Write solution into file '" + solFileName + "'");
    local solFile = io.openWrite(solFileName);
    solFile.println(cutWeight.value);
    for [i in 1..n] {
        solFile.println(i, " ", x[i].value);
	}
}
