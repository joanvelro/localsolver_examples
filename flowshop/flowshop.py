########## flowshop.py ##########

import localsolver
import sys

if len(sys.argv) < 2:
    print("Usage: python flowshop.py inputFile [outputFile] [timeLimit]")
    sys.exit(1)


def read_integers(filename):
    with open(filename) as f:
        return [int(elem) for elem in f.read().split()]


with localsolver.LocalSolver() as ls:

    #
    # Reads instance data
    #
    file_it = iter(read_integers(sys.argv[1]))

    nb_jobs = int(next(file_it))
    nb_machines = int(next(file_it))
    initial_seed = int(next(file_it))
    upper_bound = int(next(file_it))
    lower_bound = int(next(file_it))

    processing_time = [[int(next(file_it)) for j in range(nb_jobs)] for j in range(nb_machines)]

    #
    # Declares the optimization model
    #
    model = ls.model

    # Permutation of jobs
    jobs = model.list(nb_jobs)

    # All jobs have to be assigned
    model.constraint(model.eq(model.count(jobs), nb_jobs))

    # For each machine create proccessingTime[m] as an array to be able to access it
    # with an 'at' operator
    processing_time_array = [model.array(processing_time[m]) for m in range(nb_machines)]

    # On machine 0, the jth job ends on the time it took to be processed after the end of the previous job
    end = [None]*nb_machines

    first_end_selector = model.lambda_function(lambda i, prev: prev + processing_time_array[0][jobs[i]])

    end[0] = model.array(model.range(0, nb_jobs), first_end_selector)

    # The jth job on machine m starts when it has been processed by machine n-1
    # AND when job j-1 has been processed on machine m. It ends after it has been processed.
    for m in range(1, nb_machines):
        mL = m
        end_selector = model.lambda_function(lambda i, prev: \
                    model.max(prev, end[mL - 1][i]) + \
                    processing_time_array[mL][jobs[i]])
        end[m] = model.array(model.range(0, nb_jobs), end_selector)


    # Minimize the makespan: end of the last job on the last machine
    makespan = end[nb_machines-1][nb_jobs-1]
    model.minimize(makespan)

    model.close()

    #
    # Parameterizes the solver
    #
    if len(sys.argv) >= 4: ls.param.time_limit = int(sys.argv[3])
    else: ls.param.time_limit = 5

    ls.solve()

    #
    # Writes the solution in a file
    #
    if len(sys.argv) >= 3:
        with open(sys.argv[2], 'w') as f:
            f.write("%d\n" % makespan.value)
            for j in jobs.value:
                f.write("%d " % j)
            f.write("\n")
