/********** qap.lsp **********/
use io;

/* Reads instance data */
function input() {
    local usage = "Usage: localsolver qap.lsp "
        + "inFileName=inName [solFileName=solName] [lsTimeLimit=limit]";

    if (inFileName == nil) throw usage;

    local inFile = io.openRead(inFileName);
    n = inFile.readInt();
    
    // Distance between locations
    A[0..n-1][0..n-1] = inFile.readInt();
    // Flow between facilites (indices of the map must start at 0
    // to access it with an "at" operator")
    B[0..n-1][0..n-1] = inFile.readInt();
}


/* Declares the optimization model */
function model() {
    // Permutation such that p[i] is the facility on the location i
    p <- list(n);

    // The list must be complete
    constraint count(p) == n;

    // Minimize the sum of product distance*flow
    obj <- sum[i in 0..n-1][j in 0..n-1](A[i][j] * B[p[i]][p[j]]);
    minimize obj;
}

/* Parameterizes the solver. */
function param() {
    if (lsTimeLimit == nil) lsTimeLimit = 300;
}

/* Writes the solution in a file with the following format:
 *  - n objValue
 *  - permutation p */
function output() {
    if (solFileName == nil) return;

    local solFile = io.openWrite(solFileName);
    solFile.println(n + " " + obj.value);
    for[i in 0..n-1]{
        solFile.print(p.value[i] + " ");
    }
    solFile.println();
}

