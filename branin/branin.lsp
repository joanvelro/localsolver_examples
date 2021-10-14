/********** branin.lsp **********/

use io;

/* Declares the optimization model. */
function model() {
    PI = 3.14159265359;
    a = 1;
    b = 5.1/(4*pow(PI, 2));
    c = 5/PI;
    r = 6;
    s = 10;
    t = 1/(8*PI);

    x1 <- float(-5, 10);
    x2 <- float(0, 15);

    // f = a(x2 - b*x1^2 + c*x1 - r)^2 + s(1-t)cos(x1) + s
    f <- a*pow(x2 - b*pow(x1, 2) + c*x1 - r, 2) + s*(1-t)*cos(x1) + s;

    minimize f;
}

/* Parameterizes the solver. */
function param() {
    if (lsTimeLimit == nil) lsTimeLimit = 6;
}

/* Writes the solution in a file */
function output() {
    if (solFileName != nil) // write solution file if needed
    {
        local solFile = io.openWrite(solFileName);
        solFile.println("x1=", x1.value);
        solFile.println("x2=", x2.value);
    }
}
