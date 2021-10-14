/********** knapsack.lsp **********/

use io;

/* Reads instance data. */
function input() {
    local usage = "Usage: localsolver knapsack.lsp "
        + "inFileName=inputFile [solFileName=outputFile] [lsTimeLimit=timeLimit]";

    if (inFileName == nil) throw usage;

    local inFile = io.openRead(inFileName);
    nbItems = inFile.readInt();
    weights[i in 0..nbItems-1] = inFile.readInt();
    prices[i in 0..nbItems-1] = inFile.readInt();
    knapsackBound = inFile.readInt();
}

/* Declares the optimization model. */
function model() {
    // 0-1 decisions
    x[i in 0..nbItems-1] <- bool();

    // weight constraint
    knapsackWeight <- sum[i in 0..nbItems-1](weights[i] * x[i]);
    constraint knapsackWeight <= knapsackBound;

    // maximize value
    knapsackValue <- sum[i in 0..nbItems-1](prices[i] * x[i]);
    maximize knapsackValue;
}

/* Parameterizes the solver. */
function param() {
    if (lsTimeLimit == nil) lsTimeLimit = 20; 
}

/* Writes the solution in a file */
function output() {
    if (solFileName == nil) return;
    local solFile = io.openWrite(solFileName);
    solFile.println(knapsackValue.value);
    for [i in 0..nbItems-1 : x[i].value == 1]
        solFile.print(i + " ");
    solFile.println();
}
