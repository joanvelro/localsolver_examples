/********** car_sequencing.lsp **********/

use io;

/* Reads instance data. */
function input() {
    local usage = "Usage: localsolver car_sequencing.lsp "
        + "inFileName=inputFile [solFileName=outputFile] [lsTimeLimit=timeLimit]";

    if (inFileName == nil) throw usage;
    local inFile = io.openRead(inFileName);
    nbPositions = inFile.readInt();
    nbOptions = inFile.readInt();
    nbClasses = inFile.readInt();

    maxCarsPerWindow[1..nbOptions] = inFile.readInt();
    windowSize[1..nbOptions] = inFile.readInt();

    for [c in 1..nbClasses] {
        inFile.readInt(); // Note: index of class is read but not used
        nbCars[c] = inFile.readInt();
        options[c][1..nbOptions] = inFile.readInt();
    }
}

/* Declares the optimization model. */
function model() {    
    // classOnPos[c][p] = 1 if class c is at position p, and 0 otherwise
    classOnPos[1..nbClasses][1..nbPositions] <- bool();

    // All cars of class c are assigned to positions
    for [c in 1..nbClasses] 
        constraint sum[p in 1..nbPositions](classOnPos[c][p]) == nbCars[c];

    // One car assigned to each position p
    for [p in 1..nbPositions] 
        constraint sum[c in 1..nbClasses](classOnPos[c][p]) == 1;

    // optionsOnPos[o][p] = 1 if option o appears at position p, and 0 otherwise
    optionsOnPos[o in 1..nbOptions][p in 1..nbPositions] 
        <- or[c in 1..nbClasses : options[c][o]](classOnPos[c][p]);

    // Number of cars with option o in each window
    nbCarsWindows[o in 1..nbOptions][p in 1..nbPositions - windowSize[o] + 1] 
        <- sum[k in 1..windowSize[o]](optionsOnPos[o][p + k - 1]);

    // Number of violations of option o capacity in each window
    nbViolationsWindows[o in 1..nbOptions][p in 1..nbPositions - windowSize[o] + 1] 
        <- max(nbCarsWindows[o][p] - maxCarsPerWindow[o], 0);

    // Minimize the sum of violations for all options and all windows
    totalViolations <- sum[o in 1..nbOptions][p in 1..nbPositions - windowSize[o] + 1](nbViolationsWindows[o][p]);
    minimize totalViolations;
}

/* Parameterizes the solver. */
function param() {
    if (lsTimeLimit == nil) lsTimeLimit = 60;
}

/* Writes the solution in a file following the following format: 
 * - 1st line: value of the objective;
 * - 2nd line: for each position p, index of class at positions p. */
function output() {
    if (solFileName == nil) return;
    local solFile = io.openWrite(solFileName);
    solFile.println(totalViolations.value);
    for [p in 1..nbPositions][c in 1..nbClasses : classOnPos[c][p].value == 1] 
        solFile.print(c - 1, " ");
    solFile.println();
}

