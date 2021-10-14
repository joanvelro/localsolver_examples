/********** cvrptw.lsp **********/

use io;

/* The input files follow the "Solomon" format.*/
function input() {
    usage = "\nUsage: localsolver cvrptw.lsp "
    + "inFileName=inputFile [solFileName=outputFile] [lsTimeLimit=timeLimit]\n";

    if (inFileName == nil) throw usage;

    readInputCvrptw();

    // Compute distance matrix
    computeDistanceMatrix();

}

/* Declares the optimization model. */
function model() {
    customersSequences[k in 1..nbTrucks] <- list(nbCustomers);

    // All customers must be visited by the trucks
    constraint partition[k in 1..nbTrucks](customersSequences[k]);

    for[k in 1..nbTrucks] {
      local sequence <- customersSequences[k];
      local c <- count(sequence);

      // A truck is used if it visits at least one customer
      truckUsed[k] <- c > 0;

      // The quantity needed in each route must not exceed the truck capacity
      routeQuantity[k] <- sum(0..c-1, i => demands[sequence[i]]);
      constraint routeQuantity[k] <= truckCapacity;

      endTime[k] <- array(0..c-1, (i, prev) => max(earliestStart[sequence[i]],
                            i == 0 ?
                            distanceWarehouse[sequence[0]] :
                            prev + distanceMatrix[sequence[i-1]][sequence[i]])
                        + serviceTime[sequence[i]]);

      homeLateness[k] <- truckUsed[k] ?
           max(0, endTime[k][c - 1] + distanceWarehouse[sequence[c - 1]] - maxHorizon) :
           0;

      // Distance traveled by truck k
      routeDistances[k] <- sum(1..c-1,
         i => distanceMatrix[sequence[i-1]][sequence[i]])
         + (truckUsed[k] ?
           (distanceWarehouse[sequence[0]] + distanceWarehouse[sequence[c-1]]) :
           0);

      lateness[k] <- homeLateness[k] + sum(0..c-1,
                        i => max(0, endTime[k][i] - latestEnd[sequence[i]]));
    }

    // Total lateness, must be 0 for a solution to be valid
    totalLateness <- sum[k in 1..nbTrucks](lateness[k]);

    nbTrucksUsed <- sum[k in 1..nbTrucks](truckUsed[k]);

    // Total distance traveled (convention in Solomon's instances is to round to 2 decimals)
    totalDistance <- round(100*sum[k in 1..nbTrucks](routeDistances[k]))/100;

    minimize totalLateness;
    minimize nbTrucksUsed;
    minimize totalDistance;
}


/* Parameterizes the solver. */
function param() {
    if (lsTimeLimit == nil) lsTimeLimit = 20;
}

/* Writes the solution in a file with the following format:
   - number of trucks used and total distance
   - for each truck the nodes visited (omitting the start/end at the depot) */
function output() {
    if (solFileName == nil) return;
    local outfile = io.openWrite(solFileName);

    outfile.println(nbTrucksUsed.value, " ", totalDistance.value);
    for [k in 1..nbTrucks] {
        if (truckUsed[k].value != 1) continue;
        for [customer in customersSequences[k].value] {
            outfile.print(customer + 1, " ");
        }
        outfile.println();
    }
}

function readInputCvrptw() {
    local inFile = io.openRead(inFileName);
    skipLines(inFile, 4);

    //Truck related data
    nbTrucks = inFile.readInt();
    truckCapacity = inFile.readInt();

    skipLines(inFile, 3);

    //Warehouse data
    local line = inFile.readln().split();
    warehouseIndex = line[0].toInt();
    warehouseX = line[1].toInt();
    warehouseY = line[2].toInt();
    maxHorizon = line[5].toInt();

    //Customers data
    i = 0;
    while (!inFile.eof()) {
        inLine = inFile.readln();
        line = inLine.split();
        if (count(line) == 0) break;
        if (count(line) != 7) throw "Wrong file format";
        customerIndex[i] = line[0].toInt();
        customerX[i] = line[1].toInt();
        customerY[i] = line[2].toInt();
        demands[i] = line[3].toInt();
        serviceTime[i] = line[6].toInt();
        earliestStart[i] = line[4].toInt();
        latestEnd[i] = line[5].toInt() + serviceTime[i]; //in input files due date is meant as latest start time
        i = i + 1;
    }
    nbCustomers = i;

    inFile.close();
}

function skipLines(inFile, nbLines) {
    if (nbLines < 1) return;
    local dump = inFile.readln();
    for[i in 2..nbLines] dump = inFile.readln();
}



function computeDistanceMatrix() {
    for[i in 0..nbCustomers-1]
    {
        distanceMatrix[i][i] = 0;
        for[j in i+1..nbCustomers-1] {
            local localDistance = computeDist(i, j);
            distanceMatrix[j][i] = localDistance;
            distanceMatrix[i][j] = localDistance;
        }
    }

    for[i in 0..nbCustomers-1] {
        local localDistance = computeDepotDist(i);
        distanceWarehouse[i] = localDistance;
    }
}


function computeDist(i, j) {
    local x1 = customerX[i];
    local x2 = customerX[j];
    local y1 = customerY[i];
    local y2 = customerY[j];
    return computeDistance(x1, x2, y1, y2);
}

function computeDepotDist(i) {
    local x1 = customerX[i];
    local xd = warehouseX;
    local y1 = customerY[i];
    local yd = warehouseY;
    return computeDistance(x1, xd, y1, yd);
}


function computeDistance(x1, x2, y1, y2) {
    return sqrt(pow((x1 - x2), 2) + pow((y1 - y2), 2));
}




