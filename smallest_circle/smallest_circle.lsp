/********** smallest_circle.lsp **********/

use io;

/* Reads instance data */
function input() {
     usage = "\nUsage: localsolver smallest_circle.lsp "
         + "inFileName=inputFile [solFileName=outputFile] [lsTimeLimit=timeLimit]\n";

    if (inFileName == nil) throw usage;
    local instance = io.openRead(inFileName);

    nbPoints = instance.readInt();
    for [i in 1..nbPoints]{
        coordX[i] = instance.readInt();
        coordY[i] = instance.readInt();
    }

    minX = min[i in 1..nbPoints](coordX[i]);
    minY = min[i in 1..nbPoints](coordY[i]);
    maxX = max[i in 1..nbPoints](coordX[i]);
    maxY = max[i in 1..nbPoints](coordY[i]);
}

/* Declares the optimization model. */
function model() {

    // x, y are respectively the abscissa and the ordinate of the origin of the circle
    x <- float(minX, maxX);    
    y <- float(minY, maxY);

    // Minimize the radius
    r <- sqrt(max[i in 1..nbPoints](pow(x - coordX[i], 2) + pow(y - coordY[i], 2)));
    minimize r;
}

/* Parameterizes the solver. */
function param() {
    if (lsTimeLimit == nil) lsTimeLimit = 6;
}

/* Writes the solution in a file */
function output() {
    if (solFileName != nil) // write solution file if needed
    {
        println("Write solution into file '" + solFileName + "'");
        local solFile = io.openWrite(solFileName);
        solFile.println("x=", x.value);
        solFile.println("y=", y.value);
        solFile.println("r=", r.value);
    }
}
