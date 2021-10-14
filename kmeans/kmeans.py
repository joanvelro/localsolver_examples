########## kmeans.py ##########

import localsolver
import sys

if len(sys.argv) < 2:
    print("Usage: python kmeans.py inputFile [outputFile] [timeLimit] [k value]")
    sys.exit(1)

def read_elem(filename):
    with open(filename) as f:
        return [str(elem) for elem in f.read().split()]

with localsolver.LocalSolver() as ls:

    #
    # Reads instance data
    #
    if len(sys.argv) > 4: k = int(sys.argv[4])
    else: k = 2

    file_it = iter(read_elem(sys.argv[1]))
    
    # Data properties
    nb_observations = int(next(file_it))
    nb_dimensions = int(next(file_it))

    coordinates = [None]*nb_observations
    initial_clusters = [None]*nb_observations
    for o in range(nb_observations):
        coordinates[o] = [None]*(nb_dimensions)
        for d in range(nb_dimensions):
            coordinates[o][d] = float(next(file_it))
        initial_clusters[o] = next(file_it)

    #
    # Declares the optimization model
    #
    model = ls.model

    # clusters[c] represents the points in cluster c
    clusters = [model.set(nb_observations) for c in range(k)]

    # Each point must be in one cluster and one cluster only
    model.constraint(model.partition(clusters))

    # Coordinates of points
    coordinates_array = model.array(coordinates)

    # Compute variances
    variances = []
    for cluster in clusters:
        size = model.count(cluster)

        # Compute centroid of cluster
        centroid = [0 for d in range(nb_dimensions)]
        for d in range(nb_dimensions):
            coordinate_selector = model.lambda_function(
                    lambda i: model.at(coordinates_array, i, d))
            centroid[d] = model.iif(size == 0, 0,
                    model.sum(cluster, coordinate_selector) / size)

        # Compute variance of cluster
        variance = model.sum()
        for d in range(nb_dimensions):
            dimension_variance_selector = model.lambda_function(lambda i: model.sum(
                    model.pow(model.at(coordinates_array, i, d) - centroid[d], 2)))
            dimension_variance = model.sum(cluster, dimension_variance_selector)
            variance.add_operand(dimension_variance)
        variances.append(variance)

    # Minimize the total variance
    obj = model.sum(variances)
    model.minimize(obj)

    model.close()

    #
    # Parameterizes the solver
    #
    if len(sys.argv) > 3: ls.param.time_limit = int(sys.argv[3])
    else: ls.param.time_limit = 5

    ls.solve()

    #
    # Writes the solution in a file in the following format:
    #  - objective value
    #  - k
    #  - for each cluster, a line with the elements in the cluster (separated by spaces)
    #
    if len(sys.argv) > 2:
        with open(sys.argv[2], 'w') as f:
            f.write("%f\n" % obj.value)
            f.write("%d\n" % k)
            for c in range(k):
                for o in clusters[c].value:
                    f.write("%d " % o)
                f.write("\n")
