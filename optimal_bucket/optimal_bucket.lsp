/********** optimal_bucket.lsp **********/
use io;

/* Declares the optimization model. */
function model() {
    PI = 3.14159265359;

    // Numerical decisions
    R <- float(0, 1);
    r <- float(0, 1);
    h <- float(0, 1);

    // Surface must not exceed the surface of the plain disc
    surface <- PI*pow(r, 2) + PI*(R + r)*sqrt(pow(R - r, 2) + pow(h, 2));
    constraint surface <= PI;

    // Maximize the volume
    volume <- PI*h/3*(pow(R, 2) + R*r + pow(r, 2));
    maximize volume;
}

/* Parameterizes the solver. */
function param() {
    if (lsTimeLimit == nil) lsTimeLimit = 2;
}

/* Writes the solution in a file with the following format:
 *  - surface and volume of the bucket
 *  - values of R, r and h */
function output() {
    if (solFileName == nil) return;
    local solFile = io.openWrite(solFileName);
    solFile.println(surface.value, "  ", volume.value);
    solFile.println(R.value, "  ", r.value, "  ", h.value);
}
