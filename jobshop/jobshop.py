#!/usr/bin/python
# -*- coding: utf-8 -*-

"""

A set of jobs has to be processed on every machine of the shop.
Each job consists in an ordered sequence of tasks (called activities)
each representing the processing of the job on one of the machines.
Each job has one activity per machine, and cannot start an activity while
the previous activity of the job is not completed. Each activity has a
given processing time and each machine can only perform one activity at a time.

The goal is to find a sequence of jobs that minimize the makespan: the time when all jobs have been processed.


Data

The instances provided follow the Taillard format. The format of the data files is as follows:

    First line : number of jobs, number of machines, seed used to generate the instance, upper and lower bound previously found.
    For each job: the processing time on each machine (given in the processing order).
    For each job: the processing order (ordered list of visited machines).


Program

As in the jobshop example, the ordering of activities within a machine can be modeled with a list variable.
The difference here is that this ordering will represent a priority between activities and we will use a native
function to derive a schedule from these priority lists. Indeed, natives functions can be used to return some arithmetic
operations but also to embed a simple algorithm. We will illustrate this usage here.

For each machine we introduce a list decision variable whose size will be constrained to be equal to the number of jobs.
 Now the rest of the model consists of a single native function implementing the classical Giffler and Thompson rule (1960)
 and returning the resulting makespan.

This basic rule amounts to repeatedly planning the earliest available activity, unless it would delay jobs of higher priority
 on this machine, in which case we schedule the job with highest priority among these. This rule is applied until all jobs are complete.
 Note that resource and precedence constraints are implicitly modeled through this iterative heuristic.

This chronological algorithm is implemented with several cursors monitoring the progress on machines and
 jobs (jobProgress, jobProgressTime, machineProgressTime). As the search strategy of LocalSolver is multi-threaded,
 these variables have to be independent between each thread. To maintain the thread-safety property, a thread-local storage (TLS) is used here.

The only decision variables here are the priority lists which define foreach machine a priority order between jobs.
 They are constrained to be full (each job has a priority). To execute the algorithm described above as a native function,
 a call expression is created. The content of the lists variables is given as input of the native function by using the addOperand method.

The speed of the search may be lower in Python than in C++, Java or C# (see performance issues in Python for native functions).

Consult the dedicated section of the documentation for more information about native functions.

The input files follow the "Taillard" format
row: jobs
columns: machine
l1: machines of job 1
ln: machines of job n
[[l1], [l1], ..., [ln]]

processing_times_in_processing_order = [[1, 3, 6, 7, 3, 6], [8, 5, 10, 10, 10, 4], [5, 4, 8, 9, 1, 7]]

[1, 3, 6, 7, 3, 6] are the processing times of job 1, each element is the processsing time of each machine.


machine_order = [[2, 0, 1, 3, 5, 4], [1, 2, 4, 5, 0, 3], [2, 3, 5, 0, 1, 4]]

[2, 0, 1, 3, 5, 4] are the order of the machines for the job 1, each element is the order that have each machine.
Machine 1 (0) have order 2 in the process

"""

import localsolver
import sys


def exception_handler(func):
    def inner_function(*args, **kwargs):
        try:
            func(*args, **kwargs)
        # except TypeError:
        #    print(f"{func.__name__} only takes numbers as the argument")
        except Exception as exception_msg:
            print('(!) Error in {}: {} '.format(func.__name__, str(exception_msg)))

    return inner_function


def read_instance(filename):
    with open(filename) as f:
        lines = f.readlines()

    first_line = lines[1].split()
    # Number of jobs
    nb_jobs = int(first_line[0])
    print('nb_jobs:{}'.format(nb_jobs))
    # Number of machines
    nb_machines = int(first_line[1])
    print('nb_machines:{}'.format(nb_machines))

    # Processing times for each job on each machine (given in the processing order) processing_times_in_processing_order[i][j]
    # list of lists
    processing_times_in_processing_order = [[int(lines[i].split()[j]) for j in range(nb_machines)] for i in range(3, 3 + nb_jobs)]

    # print(processing_times_in_processing_order)

    # Processing order of machines for each job machine_order[i][j]
    machine_order = [[int(lines[i].split()[j]) - 1 for j in range(nb_machines)] for i in range(4 + nb_jobs, 4 + 2 * nb_jobs)]

    # print(machine_order)

    # Reorder processing times: processing_time[j][m] is the processing time of the
    # activity of job j that is processed on machine m
    processing_time = [[processing_times_in_processing_order[i][machine_order[i].index(j)] for j in range(nb_machines)] for i in range(nb_jobs)]

    # Trivial upper bound for the start times of the activities
    max_start = sum(sum(processing_time[j]) for j in range(nb_jobs))

    return (nb_jobs, nb_machines, processing_time, machine_order, max_start)


def main(instance_file, output_file, time_limit):
    nb_jobs, nb_machines, processing_time, machine_order, max_start = read_instance(instance_file)

    with localsolver.LocalSolver() as ls:
        # ---------------------
        # MODEL INITIALIZATION
        # ------------------------
        # Declares the optimization model
        model = ls.model

        # ------------
        # VARIABLES
        # ------------
        # Integer decisions: start time of each activity
        # start[i][j] is the start time of the activity of job "i" which is processed on machine "j"
        start = [[model.int(0, max_start) for j in range(nb_machines)] for i in range(nb_jobs)]
        end = [[start[i][j] + processing_time[i][j] for j in range(nb_machines)] for i in range(nb_jobs)]
        start_array = model.array(start)
        end_array = model.array(end)

        # --------------
        # CONSTRAINTS
        # ---------------
        #
        # Constraint (1)
        #
        # Precedence constraints between the activities of a job
        for i in range(nb_jobs):
            for j in range(1, nb_machines):
                model.constraint(start[i][machine_order[i][j]] >= end[i][machine_order[i][j - 1]])
        #
        # Constraint (2)
        #
        # Sequence of activities on each machine
        jobs_order = [model.list(nb_jobs) for m in range(nb_machines)]
        for m in range(nb_machines):
            # Each job has an activity scheduled on each machine
            sequence = jobs_order[m]
            model.constraint(model.eq(model.count(sequence), nb_jobs))

            # Disjunctive resource constraints between the activities on a machine
            # the start of job i has to be after the end of job i-1
            sequence_selector = model.lambda_function(
                lambda i: model.geq(model.at(start_array, sequence[i], m), model.at(end_array, sequence[i - 1], m)))
            model.constraint(model.and_(model.range(1, nb_jobs), sequence_selector))

        # -----------
        # OBJECTIVE
        # -----------
        # Minimize the makespan: end of the last activity of the last job
        makespan = model.max([end[j][machine_order[j][nb_machines - 1]] for j in range(nb_jobs)])
        model.minimize(makespan)

        # --------------
        # SOLVE MODEL
        # -------------
        model.close()
        # Parameterizes the solver
        ls.param.time_limit = time_limit
        ls.solve()

        # ----------
        # SOLUTION
        # -----------
        optimal_makespan = makespan.get_value()
        print('Optimal makespan:{}'.format(optimal_makespan))

        # Writes the solution in a file with the following format:
        # - for each machine, the job sequence
        @exception_handler
        def write_results(output_file, jobs_order, nb_machines, nb_jobs):
            if output_file is not None:
                final_jobs_order = [list(jobs_order[m].value) for m in range(nb_machines)]
                with open(output_file, "w+") as f:
                    print("Solution written in file:", output_file)
                    sol = []
                    for m in range(nb_machines):
                        for j in range(nb_jobs):
                            f.write('machine {} - job:{}'.format(m, j) + 'job order:' + str(final_jobs_order[m][j]) + " ")
                            print('Machine:{} - Job:{} - :{}'.format(m, j, final_jobs_order[m][j]))
                            sol.append(final_jobs_order[m][j])
                        f.write("\n")

            return sol

        sol = write_results(output_file, jobs_order, nb_machines, nb_jobs)

    return sol


if __name__ == '__main__':
    # if len(sys.argv) < 2:
    #    print("Usage: python jobshop.py instance_file [output_file] [time_limit]")
    #    sys.exit(1)

    instance_file = 'instances\\ft06.txt'  # sys.argv[1]
    output_file = 'results\\ft06_results.txt'  # sys.argv[2] if len(sys.argv) >= 3 else None
    time_limit = 200  # int(sys.argv[3]) if len(sys.argv) >= 4 else 60
    nb_jobs, nb_machines, processing_time, machine_order, max_start = read_instance(instance_file)
    sol = main(instance_file, output_file, time_limit)
