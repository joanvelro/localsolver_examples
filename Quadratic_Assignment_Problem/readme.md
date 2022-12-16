# Quadratic Assignment Problem (QAP) 

Is a fundamental combinatorial problem in the branch
of optimization and operations research. It has emerged from facility location applications
and models the following real-life problem. You are given a set of n facilities and a set of
n locations. A distance is specified for each pair of locations, and a flow (or weight) is
specified for each pair of facilities (e.g. the amount of supplies transported between the pair).
The problem is to assign each facility to one location with the goal of minimizing the sum of
the distances multiplied by the corresponding flows. Intuitively, the cost function encourages
factories with high flows between each other to be placed close together. 

The problem statement
resembles that of the assignment problem, except that the cost function is expressed in terms
of quadratic inequalities, hence the name. For more details, we invite the reader to have a
look at the QAPLIB webpage.

## Data
Instance files are from the QAPLIB.

The format of the data is as follows:

Number of points
Matrix A: distance between each location
Matrix B: flow between each facility

## Program
Using LocalSolver’s non-linear operators, modeling the problem is really straightforward
(no linearization required). It is not even necessary to introduce a quadratic number of
decision variables x[f][l]. Indeed, we are considering a permutation of all facilities,
which can be modeled directly in LocalSolver with a single list variable. The only constraint
is for the list to contain all the facilities. As for the objective, it is the sum,
for each pair of locations (l1,l2), of the product between the distance between l1 and l2
and the flow between the factory on l1 and the factory on l2. This is written with “at”
operators that can retrieve a member of an array indexed by an expression (see this page
for more information about the “at” operator).

obj <- sum[i in 0..n-1][j in 0..n-1]( A[i][j] * B[p[i]][p[j]]);
With such a compact model, instances with thousands of points can be tackled with no
resource issues.
