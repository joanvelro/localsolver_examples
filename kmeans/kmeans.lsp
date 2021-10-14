/********** kmeans.lsp **********/
use io;

/* Reads instance data */
function input() {
    usage = "\nUsage: localsolver kmeans.lsp "
        + "inFileName=inputFile [solFileName=outputFile] [lsTimeLimit=timeLimit] [k=value]\n";

    if (inFileName == nil) throw usage;
    local f = io.openRead(inFileName);
    nbObservations = f.readInt();
    nbDimensions = f.readInt();

    if (k == nil) {
        k = 2;
    }

    for [o in 0..nbObservations-1] {
        for [d in 0..nbDimensions-1] {
            coordinates[o][d] = f.readDouble();
        }
        initialClusters[o] = f.readString();
    }
}

/* Declares the optimization model. */
function model() {
    // Set decisions: clusters[c] represents the points in cluster c
    clusters[1..k] <- set(nbObservations);

    // Each point must be in one cluster and one cluster only
    constraint partition[c in 1..k](clusters[c]);

    // Compute variances
    for [c in 1..k] {
        local cluster <- clusters[c];
        local size <- count(cluster);

        // Compute the centroid of the cluster
        centroid[d in 0..nbDimensions-1] <- size == 0 ? 0 :
                sum(cluster, o => coordinates[o][d]) / size;

        // Compute the variance of the cluster
        squares[d in 0..nbDimensions-1] <- sum(cluster,
            o => pow(coordinates[o][d] - centroid[d], 2));
        variances[c] <- sum[d in 0..nbDimensions-1](squares[d]);
    }

    // Minimize the total variance
    obj <- sum[c in 1..k](variances[c]);
    minimize obj;
}

/* Parameterizes the solver. */
function param() {
    if (lsTimeLimit == nil) lsTimeLimit = 5;
}

/* Writes the solution in a file in the following format:
 *  - objective value
 *  - k
 *  - for each cluster, a line with the elements in the cluster (separated by spaces)
 */
function output() {
    if (solFileName == nil) return;
    local solFile = io.openWrite(solFileName);
    solFile.println(obj.value);
    solFile.println(k);
    for [c in 1..k] {
        for [o in clusters[c].value]
            solFile.print(o + " ");
        solFile.println();
    }
}
