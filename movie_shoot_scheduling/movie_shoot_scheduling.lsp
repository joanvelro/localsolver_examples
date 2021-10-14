/********** movie_shoot_scheduling.lsp **********/
use io;
use ls;

/* Read instance data */
function input() {
    local usage = "Usage: localsolver movie_shoot_scheduling.lsp "
        + "inFileName=inputFile [lsTimeLimit=timeLimit]";

    if (inFileName == nil) throw usage;
    local inFile = io.openRead(inFileName);
    nbActors = inFile.readInt();
    nbScenes = inFile.readInt();
    nbLocations = inFile.readInt();
    nbPrecedences = inFile.readInt();
    actorCost[i in 0..nbActors-1] = inFile.readInt();
    locationCost[i in 0..nbLocations-1] = inFile.readInt();
    sceneDuration[i in 0..nbScenes-1] = inFile.readInt();
    sceneLocation[i in 0..nbScenes-1] = inFile.readInt();
    for [i in 0..nbActors-1]
        isActorInScene[i][j in 0..nbScenes-1] = inFile.readInt();
    for [i in 0..nbPrecedences-1]
        precedence[i][j in 0..1] = inFile.readInt();
    inFile.close();
    computeNbWorkedDays();
}

function computeNbWorkedDays() {
    nbWorkedDays[i in 0..nbActors-1] = 0;
    for [j in 0..nbActors-1] {
        for [i in 0..nbScenes-1] {
            if (isActorInScene[j][i]) {
                nbWorkedDays[j] += sceneDuration[i];
            }
        }
    }
}

function computeLocationCost(shootOrder) {
    // Number of visits per location (group of successive shoots)
    nbLocationVisits[0..nbLocations-1] = 0;
    previousLocation = -1;
    for [i in 0..nbScenes-1] {
        currentLocation = sceneLocation[shootOrder[i]];
        // When we change location, we increment the number of shoots of the new location
        if (previousLocation != currentLocation) {
            nbLocationVisits[currentLocation] = nbLocationVisits[currentLocation] + 1;
            previousLocation = currentLocation;
        }
    }

    locationExtraCost = 0;
    for [k in 0..nbLocations-1]
        locationExtraCost += locationCost[k] * (nbLocationVisits[k] - 1);
    return locationExtraCost;
}

function computeActorCost(shootOrder) {
    for [j in 0..nbActors-1] {
        hasActorStartingWorking = false;
        startDayOfScene = 0;
        for [i in 0..nbScenes-1] {
            currentScene = shootOrder[i];
            endDayOfScene = startDayOfScene + sceneDuration[currentScene] - 1;
            if (isActorInScene[j][currentScene]) {
                actorLastDay[j] = endDayOfScene;
                if (not(hasActorStartingWorking)) {
                    hasActorStartingWorking = true;
                    actorFirstDay[j] = startDayOfScene;
                }
            }
            // The next scene begins the day after the end of the current one
            startDayOfScene = endDayOfScene + 1;
        }
    }

    // Compute actor extra cost due to days paid but not worked
    actorExtraCost = 0;
    for [j in 0..nbActors-1] {
        nbPaidDays = actorLastDay[j] - actorFirstDay[j] + 1;
        actorExtraCost += (nbPaidDays - nbWorkedDays[j]) * actorCost[j];
    }
    return actorExtraCost;
}

/* External function */
function costFunction(context) {
    scenes = context;
    if (count(scenes) < nbScenes) {
        // Infeasible solution if some shoots are missing
        return round(pow(10, 6));
    }
    locationExtraCost = computeLocationCost(scenes);
    actorExtraCost = computeActorCost(scenes);
    return locationExtraCost + actorExtraCost;
}

function model() {
    // Decision variable: a list, shootOrder[i] is the index of the i-th scene to be shot
    shootOrder <- list(nbScenes);

    // All scenes must be scheduled
    constraint count(shootOrder) == nbScenes;

    // Constraint of precedence between scenes
    for [i in 0..nbPrecedences-1] {
        constraint indexOf(shootOrder, precedence[i][0]) < indexOf(shootOrder, precedence[i][1]);
    }

    // Minimize external function
    func <- intExternalFunction(costFunction);
    func.context.lowerBound = 0;
    cost <- call(func, shootOrder);
    minimize cost;
}

/* Parameterize the solver */
function param() {
    if (lsTimeLimit == nil) lsTimeLimit = 20;
}

/* Write the solution in a file in the following format:
 * - 1st line: value of the objective;
 * - 2nd line: for each i, the index of the ith scene to be shot. */
function output() {
    if (solFileName == nil) return;
    local solFile = io.openWrite(solFileName);
    solFile.println(cost.value);
    for [i in shootOrder.value]
        solFile.print(i, " ");
    solFile.println();
}
