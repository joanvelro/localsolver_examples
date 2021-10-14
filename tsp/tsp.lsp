/********** tsp.lsp **********/

use io;

/* Reads instance data. */
function input() {
    local usage = "Usage: localsolver tsp.lsp "
        + "inFileName=inputFile [lsTimeLimit=timeLimit]";

    if (inFileName == nil) throw usage;
    local inFile = io.openRead(inFileName);

    // The input files follow the TSPLib "explicit" format.
    while (true) {
        local str = inFile.readln();
        if (str.startsWith("DIMENSION:")) {
            local dim = str.trim().split(":")[1];
            nbCities = dim.toInt();
        } else if (str.startsWith("EDGE_WEIGHT_SECTION")) {
            break;
        }
    }

    // Distance from i to j
    distanceWeight[0..nbCities - 1][0..nbCities - 1] = inFile.readInt();
}

/* Declares the optimization model. */
function model() {
    // A list variable: cities[i] is the index of the ith city in the tour
    cities <- list(nbCities); 

    // All cities must be visited
    constraint count(cities) == nbCities;

    // Minimize the total distance
    obj <- sum(1..nbCities-1, i => distanceWeight[cities[i-1]][cities[i]])
            + distanceWeight[cities[nbCities-1]][cities[0]];

    minimize obj;
}

/* Parameterizes the solver. */
function param() {
    if (lsTimeLimit == nil) lsTimeLimit = 5;  
}


/* Writes the solution in a file */
function output() {
    if (solFileName == nil) return;
    local solFile = io.openWrite(solFileName);
    solFile.println(obj.value);
    for [c in cities.value] 
        solFile.print(c, " ");
    solFile.println();
}
