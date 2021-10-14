/********** cvrp.lsp **********/
use io;

/* Reads instance data. The input files follow the "Augerat" format. */
function input() {
    usage = "\nUsage: localsolver cvrp.lsp " + 
            "inFileName=inputFile [solFileName=outputFile] [lsTimeLimit=timeLimit] [nbTrucks=value]\n";

    if (inFileName == nil) throw usage;
    
    readInputCvrp();
    
    // The number of trucks is usually given in the name of the file
    // nbTrucks can also be given in command line
    if (nbTrucks == nil) nbTrucks = getNbTrucks();

    // Compute distance matrix
    computeDistanceMatrix();
}
 
/* Declares the optimization model. */
function model() {
    // Sequence of customers visited by each truck.
    customersSequences[k in 1..nbTrucks] <- list(nbCustomers);

    // All customers must be visited by the trucks
    constraint partition[k in 1..nbTrucks](customersSequences[k]);

    for [k in 1..nbTrucks] {
        local sequence <- customersSequences[k];
        local c <- count(sequence);

        // A truck is used if it visits at least one customer
        trucksUsed[k] <- c > 0;

        // The quantity needed in each route must not exceed the truck capacity
        routeQuantity <- sum(0..c-1, i => demands[sequence[i]]);
        constraint routeQuantity <= truckCapacity;

        // Distance traveled by truck k
        routeDistances[k] <- sum(1..c-1, i => distanceMatrix[sequence[i - 1]][sequence[i]])
             + (c > 0 ? (distanceWarehouse[sequence[0]] + distanceWarehouse[sequence[c - 1]]) : 0);
    }

    nbTrucksUsed <- sum[k in 1..nbTrucks](trucksUsed[k]);

    // Total distance traveled
    totalDistance <- sum[k in 1..nbTrucks](routeDistances[k]);

    // Objective: minimize the number of trucks used, then minimize the distance traveled
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
        if (trucksUsed[k].value != 1) continue;
        // Values in sequence are in [0..nbCustomers-1].
        // +2 is to put it back in [2..nbCustomers+1]
        // as in the data files (1 being the depot)
        for [customer in customersSequences[k].value]
            outfile.print(customer + 2, " ");
        outfile.println();
    }
}


function readInputCvrp() {
    local inFile = io.openRead(inFileName);
    local nbNodes = 0;
    while (true) {
        local str = inFile.readString();
        if (str.startsWith("DIMENSION")) {
            if (!str.endsWith(":")) str = inFile.readString();
            nbNodes = inFile.readInt();
            nbCustomers = nbNodes - 1;
        } else if ((str.startsWith("CAPACITY"))) {
            if (!str.endsWith(":")) str = inFile.readString();
            truckCapacity = inFile.readInt();
        } else if ((str.startsWith("EDGE_WEIGHT_TYPE"))) {
            if (!str.endsWith(":")) str = inFile.readString();
            local weightType = inFile.readString();
            if (weightType != "EUC_2D") throw ("Edge Weight Type " + weightType + " is not supported (only EUC_2D)");
        } else if (str.startsWith("NODE_COORD_SECTION")) {
            break;
        } else {
            local dump = inFile.readln();
        }
    }

    //nodeX and nodeY are indexed by original data indices (1 for depot)
    for[n in 1..nbNodes] {
        if (n != inFile.readInt()) throw "Unexpected index";
        nodesX[n] = round(inFile.readDouble());
        nodesY[n] = round(inFile.readDouble());
    }

    dump = inFile.readln();
    if (!dump.startsWith("DEMAND_SECTION")) throw "Expected keyword DEMAND_SECTION";
    for[n in 1..nbNodes] {
        if (n != inFile.readInt()) throw "Unexpected index";
        // demands must start at 0 to be accessed by an "at" operator. Thus
        // node ids will start at 0 in the model.
        local demand = inFile.readInt();
        if (n == 1) {
            if (demand != 0) throw "expected demand for depot is 0";
        } else {
            demands[n - 2] = demand; // demands is indexed by customers
        }
    }

    dump = inFile.readln();
    if (!dump.startsWith("DEPOT_SECTION")) throw "Expected keyword DEPOT_SECTION";
    local warehouseId = inFile.readInt();
    if (warehouseId != 1) throw "Warehouse id is supposed to be 1";
    local endOfDepotSection = inFile.readInt();
    if (endOfDepotSection != -1) throw "Expecting only one warehouse, more than one found";
}

/* Compute the distance between each node */
function computeDistanceMatrix() {
    for[i in 0..nbCustomers-1] {
        distanceMatrix[i][i] = 0;
        for[j in i+1..nbCustomers-1] {
            // +2 because computeDist expected original data indices,
            // with customers in 2..nbNodes (1 being the depot)
            local localDistance = computeDist(i + 2, j + 2);
            distanceMatrix[j][i] = localDistance;
            distanceMatrix[i][j] = localDistance;
        }
    }

    for[i in 0..nbCustomers-1] {
        local localDistance = computeDist(1, i+2);
        distanceWarehouse[i] = localDistance;
    }
}

function computeDist(i, j) {
    local exactDist = sqrt(pow((nodesX[i] - nodesX[j]), 2) + pow((nodesY[i] - nodesY[j]), 2));
    return round(exactDist);
}

function getNbTrucks() {
    local splitted = inFileName.split("-k");
    if (count(splitted) >= 2) {
        local numvrp = splitted[count(splitted) - 1];
        splitted = numvrp.split(".");
        if (count(splitted) == 2) return splitted[0].toInt();
    } else {
        println("Error: nbTrucks could not be read from the file name. Enter it from the command line");
        throw usage;
    }
}
