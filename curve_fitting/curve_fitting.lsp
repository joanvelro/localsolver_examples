/********** curve_fitting.lsp **********/

use io;

/* Reads instance data. */
function input() {

    local usage = "Usage: localsolver curve_fitting.lsp "
        + "inFileName=inputFile [solFileName=outputFile] [lsTimeLimit=timeLimit]";

    if (inFileName == nil) throw usage;

    local inFile = io.openRead(inFileName);
    nbObervations = inFile.readInt();
    for [i in 1..nbObervations]{
        inputs[i] = inFile.readDouble();
        outputs[i] = inFile.readDouble();
    }
}

/* Declares the optimization model. */
function model() {

    // parameters of the mapping function
    a <- float(-100, 100);
    b <- float(-100, 100);
    c <- float(-100, 100);
    d <- float(-100, 100);

    // minimize square error bewteen prediction and output
    predictions[i in 1..nbObervations] <- a * sin(b - inputs[i]) + c * pow(inputs[i], 2) + d;
    errors[i in 1..nbObervations] <- predictions[i] - outputs[i];
    squareError <- sum[i in 1..nbObervations] (pow(errors[i], 2));
    minimize squareError;
}

/* Parameterizes the solver. */
function param() {
    if (lsTimeLimit == nil) lsTimeLimit = 3; 
}

/* Writes the solution in a file */
function output() {
    if (solFileName == nil) return;
    local solFile = io.openWrite(solFileName);
    solFile.println("Optimal mapping function");
    solFile.println("a = " + a.value);
    solFile.println("b = " + b.value);
    solFile.println("c = " + c.value);
    solFile.println("d = " + d.value);
}