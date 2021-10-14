/********** flowshop.lsp **********/

use io;

/* Reads instance data */
function input() {
    local usage = "Usage: localsolver flowshop.lsp "
        + "inFileName=inputFile [lsTimeLimit=timeLimit]";

    if (inFileName == nil) throw usage;
    local inFile = io.openRead(inFileName);

    nbJobs = inFile.readInt();
    nbMachines = inFile.readInt();
    initialSeed = inFile.readInt();
    upperBound = inFile.readInt();
    lowerBound = inFile.readInt();
    processingTime[m in 0..nbMachines-1][j in 0..nbJobs-1] = inFile.readInt();
}

/* Declares the optimization model. */
function model() {
    // Permutation of jobs
    jobs <- list(nbJobs);

    // All jobs have to be assigned
    constraint count(jobs) == nbJobs;

    // On machine 0, the jth job ends on the time it took to be processed after 
    // the end of the previous job
    end[0] <- array(0..nbJobs-1, (i, prev) => prev + processingTime[0][jobs[i]]);

    // The jth job on machine m starts when it has been processed by machine n-1
    // AND when job j-1 has been processed on machine m. It ends after it has been processed.
    for[m in 1..nbMachines-1] {
        end[m] <- array(0..nbJobs-1, (i, prev) => max(prev, end[m-1][i]) + processingTime[m][jobs[i]]);
    }

    // Minimize the makespan: end of the last job on the last machine
    makespan <- end[nbMachines-1][nbJobs-1];
    minimize makespan;
}

/* Parameterizes the solver. */
function param() {
    if (lsTimeLimit == nil) lsTimeLimit = 5;
}

/* Writes the solution in a file */
function output() {
    if (solFileName == nil) return;

    local solFile = io.openWrite(solFileName);
    solFile.println(makespan.value);
    for[j in jobs.value]
        solFile.print(j + " ");
    solFile.println();
}
