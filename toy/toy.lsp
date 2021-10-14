/********** toy.lsp **********/

/* Declares the optimization model. */
function model() {

    // 0-1 decisions
    x_0 <- bool(); x_1 <- bool(); x_2 <- bool(); x_3 <- bool();
    x_4 <- bool(); x_5 <- bool(); x_6 <- bool(); x_7 <- bool();

    // weight constraint
    knapsackWeight <- 10*x_0 + 60*x_1 + 30*x_2 + 40*x_3 + 30*x_4 + 20*x_5 + 20*x_6 + 2*x_7;
    constraint knapsackWeight <= 102;

    // maximize value
    knapsackValue <- 1*x_0 + 10*x_1 + 15*x_2 + 40*x_3 + 60*x_4 + 90*x_5 + 100*x_6 + 15*x_7;
    maximize knapsackValue;
}

/* Parameterizes the solver. */
function param() {
    lsTimeLimit = 10;
}
