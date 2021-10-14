/********** steel_mill_slab_design.lsp **********/
use io;

/* Reads instance data. */
function input() {
    local usage = "Usage: localsolver steel_mill_slab_design.lsp "
        + "inFileName=inputFile [solFileName=outputFile] [lsTimeLimit=timeLimit]";

    if (inFileName == nil) throw usage;
    
    local inFile = openRead(inFileName);
    nbColorsMaxSlab = 2;

    nbSlabSizes = inFile.readInt();
    slabSizes[1..nbSlabSizes] = inFile.readInt();
    maxSize = slabSizes[nbSlabSizes];

    nbColors = inFile.readInt();
    nbOrders = inFile.readInt();
    nbSlabs = nbOrders;    

    ordersByColor[1..nbColors] = {};
    sumSizeOrders = 0;

    for [i in 1..nbOrders] {
        orders[i] = inFile.readInt();
        c = inFile.readInt();
		ordersByColor[c].add(i);
        sumSizeOrders += orders[i];
    }

    preComputeWasteForContent();
}

function preComputeWasteForContent() {
    // No waste when a slab is empty
    wasteForContent[0] = 0;

    // The waste for each content is the difference between the minimum slab size
    // able to contain this content and the content
    prevSize = 0;
    for[size in slabSizes] {
        if (size < prevSize) throw "Slab sizes should be sorted in ascending order";
        wasteForContent[content in prevSize + 1..size] = size - content;
        prevSize = size;
    }
   
    wasteForContent[prevSize+1..sumSizeOrders] = 0;
}

/* Declares the optimization model. */
function model() {
    
    // x[o][s] = 1 if order o is assigned to slab s, 0 otherwise
    x[1..nbOrders][1..nbSlabs] <- bool();
    
    // Each order is assigned to a slab
    for [o in 1..nbOrders] 
        constraint sum[s in 1..nbSlabs](x[o][s]) == 1;
    
    
    // The content of each slab must not exceed the maximum size of the slab
    for [s in 1..nbSlabs] {
        slabContent[s] <- sum[o in 1..nbOrders](orders[o]*x[o][s]);
        constraint slabContent[s] <= maxSize;
    }

    // Wasted steel is computed according to the content of the slab
    for [s in 1..nbSlabs] {
        wastedSteel[s] <- wasteForContent[slabContent[s]];
    }

    // color[c][s] = 1 if the color c in the slab s, 0 otherwise
    color[c in 1..nbColors : count(ordersByColor[c]) > 0][s in 1..nbSlabs] <- or[o in ordersByColor[c]](x[o][s]);

    // The number of colors per slab must not exceed a specified value
    for [s in 1..nbSlabs]
        constraint sum[c in 1..nbColors : count(ordersByColor[c]) > 0](color[c][s]) <= nbColorsMaxSlab;

    // Minimize the total wasted steel
    totalWastedSteel <- sum[s in 1..nbSlabs](wastedSteel[s]);            

    minimize totalWastedSteel;
}

/* Parameterizes the solver. */
function param() {
    if (lsTimeLimit == nil) lsTimeLimit = 60;
    if (lsNbThreads == nil) lsNbThreads = 4;
}

/* Writes the solution in a file with the following format: 
 *  - total wasted steel
 *  - number of slabs used
 *  - for each slab used, the number of orders in the slab and the list of orders
 */
function output() {
    if (solFileName == nil) return;

    local ordersBySlabs;
    local solFile = io.openWrite(solFileName);
    solFile.println(totalWastedSteel.value);
    
    local actualNbSlabs = 0;
    for [s in 1..nbSlabs] {
        ordersBySlabs[s] = map[o in 1..nbOrders : x[o][s].value](o);
        if (ordersBySlabs[s].count() > 0) actualNbSlabs = actualNbSlabs + 1;
    }
    solFile.println(actualNbSlabs);
    
    for [s in 1..nbOrders] {
        if (ordersBySlabs[s].count() > 0) {
            solFile.print(ordersBySlabs[s].count() + " ");
            for [o in ordersBySlabs[s].values()] solFile.print(o, " ");
            solFile.println();
        }
    }
}

