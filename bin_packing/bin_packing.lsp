/********** bin_packing.lsp **********/

use io;

/* Reads instance data. */
function input() {
    local usage = "Usage: localsolver bin_packing.lsp "
        + "inFileName=inputFile [lsTimeLimit=timeLimit]";

    if (inFileName == nil) throw usage;
    local inFile = io.openRead(inFileName);

    nbItems = inFile.readInt();
    binCapacity = inFile.readInt();
    itemWeights[i in 0..nbItems-1] = inFile.readInt();

    nbMinBins = ceil(sum[i in 0..nbItems-1](itemWeights[i])/binCapacity);
    nbMaxBins = min(nbItems, 2 * nbMinBins);
}


/* Declares the optimization model. */
function model() {
    // Set decisions: bins[k] represents the items in bin k
    bins[k in 0..nbMaxBins-1] <- set(nbItems);

    // Each item must be in one bin and one bin only
    constraint partition[k in 0..nbMaxBins-1](bins[k]);
    
    for [k in 0..nbMaxBins-1] {
        // Weight constraint for each bin
        binWeights[k] <- sum(bins[k], i => itemWeights[i]);
        constraint binWeights[k] <= binCapacity;
    
        // Bin k is used if at least one item is in it
        binsUsed[k] <- (count(bins[k]) > 0);
    }
    
    // Count the used bins
    totalBinsUsed <- sum[k in 0..nbMaxBins-1](binsUsed[k]);

    // Minimize the number of used bins
    minimize totalBinsUsed;
}

/* Parameterizes the solver. */
function param() {
    if (lsTimeLimit == nil) lsTimeLimit = 20;  
    if (lsNbThreads == nil) lsNbThreads = 1;
    if (lsTimeBetweenDisplays == nil) lsTimeBetweenDisplays = 1;

    // Stop the search if the lower threshold is reached
    lsObjectiveThreshold = nbMinBins;
}

function output() {
    for[k in 0..nbMaxBins-1] {
        if (count(bins[k].value) > 0) {
            print("Bin weight: ", binWeights[k].value, " | Items: ");
            for[e in bins[k].value]
                print(e + " ");
            println();
        }
    }
}

