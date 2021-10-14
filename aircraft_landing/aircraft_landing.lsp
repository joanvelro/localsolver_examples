/********** aircraft_landing.lsp **********/

use io;
use ls;

/* Read instance data */
function input() {
    local usage = "Usage: localsolver aircraft_landing.lsp "
        + "inFileName=inputFile [lsTimeLimit=timeLimit]";

    if (inFileName == nil) throw usage;
    local inFile = io.openRead(inFileName);

    nbPlanes = inFile.readInt();
    inFile.readInt(); // Skip freezeTime value

    for [p in 0..nbPlanes-1] {
        inFile.readInt(); // Skip appearanceTime values
        earliestTime[p] = inFile.readInt();
        targetTime[p] = inFile.readInt();
        latestTime[p] = inFile.readInt();
        earlinessCost[p] = inFile.readDouble();
        tardinessCost[p] = inFile.readDouble();
        separationTime[p][0..nbPlanes-1] = inFile.readInt();
    }
    inFile.close();
}

/* Declare the optimization model */
function model() {
    // A list variable: landingOrder[i] is the index of the ith plane to land
    landingOrder <- list(nbPlanes);

    // All planes must be scheduled
    constraint count(landingOrder) == nbPlanes;

    // Int variable: preferred landing time for each plane
    preferredTime[p in 0..nbPlanes-1] <- int(earliestTime[p], targetTime[p]);

    // Landing time for each plane
    landingTime <- array(0..nbPlanes-1, (p, prev) => max(preferredTime[landingOrder[p]],
                p > 0 ? prev + separationTime[landingOrder[p-1]][landingOrder[p]] : 0));
                
    // Landing times must respect the separation time with every previous plane.
    for [p in 1..nbPlanes-1] {
        constraint landingTime[p] >= max[previousPlane in 0..p-1](landingTime[previousPlane] + separationTime[landingOrder[previousPlane]][landingOrder[p]]);
    }

    // Cost for each plane
    for [p in 0..nbPlanes-1] {
        local planeIndex <- landingOrder[p];
        constraint landingTime[p] <= latestTime[planeIndex];
        cost[p] <- (landingTime[p] < targetTime[planeIndex] ? earlinessCost[planeIndex] :
                tardinessCost[planeIndex]) * abs(landingTime[p] - targetTime[planeIndex]);
    }

    // Minimize the total cost
    totalCost <- sum[p in 0..nbPlanes-1] (cost[p]);
    minimize totalCost;
}

/* Parameterize the solver */
function param() {
    if (lsTimeLimit == nil) lsTimeLimit = 20;
}

/* Write the solution in a file following the following format:
 * - 1st line: value of the objective;
 * - 2nd line: for each position p, index of plane at position p. */
function output() {
    if (solFileName == nil) return;
    local solFile = io.openWrite(solFileName);
    solFile.println(totalCost.isUndefined() ? "(invalid)" : totalCost.value);
    for [p in landingOrder.value]
        solFile.print(p, " ");
    solFile.println();
}
