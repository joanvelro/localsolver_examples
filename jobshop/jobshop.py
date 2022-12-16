import json

import localsolver
from pandas import DataFrame


def write_json(filename: str, dictionary: dict):
    with open(filename, 'w') as f:
        json.dump(dictionary, f, indent=4)


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

    # Processing times for each job on each machine (given in the processing order)
    # processing_times_in_processing_order[i][j] list of lists
    processing_times_in_processing_order = [[int(lines[i].split()[j]) for j in range(nb_machines)] for i in
                                            range(3, 3 + nb_jobs)]

    # print(processing_times_in_processing_order)

    # Processing order of machines for each job machine_order[i][j]
    machine_order = \
        [[int(lines[i].split()[j]) - 1 for j in range(nb_machines)] for i in range(4 + nb_jobs, 4 + 2 * nb_jobs)]

    # print(machine_order)

    # Reorder processing times: processing_time[j][m] is the processing time of the
    # activity of job j that is processed on machine m
    processing_time = \
        [[processing_times_in_processing_order[i][machine_order[i].index(j)]
          for j in range(nb_machines)]
         for i in range(nb_jobs)]

    # Trivial upper bound for the start times of the activities
    max_start = sum(sum(processing_time[j]) for j in range(nb_jobs))

    input_instance = dict()
    input_instance['nb_jobs'] = nb_jobs
    input_instance['nb_machines'] = nb_machines
    input_instance['processing_time'] = processing_time
    input_instance['machine_order'] = machine_order
    input_instance['max_start'] = max_start

    filename = filename.split(".")[1]
    write_json(filename='./' + filename + '.json', dictionary=input_instance)

    return input_instance


def main(input_instance: dict, output_file: str, time_limit: int):
    nb_jobs = input_instance['nb_jobs']
    nb_machines = input_instance['nb_machines']
    processing_time = input_instance['processing_time']
    machine_order = input_instance['machine_order']
    max_start = input_instance['max_start']

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
        start_array = model.array(start)

        # ------------
        # EXPRESSIONS
        # ------------
        # The ending time is an expression of the start (varible) and the duration (input data)
        end = [[start[i][j] + processing_time[i][j] for j in range(nb_machines)] for i in range(nb_jobs)]
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
                lambda i: model.geq(model.at(start_array, sequence[i], m),
                                    model.at(end_array, sequence[i - 1], m)
                                    )
            )
            # Operands to add. An iterable or any number of arguments
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
        if time_limit:
            ls.param.time_limit = time_limit
        else:
            ls.param.time_limit = 100
        ls.solve()

        # ----------
        # SOLUTION
        # -----------
        optimal_makespan = makespan.get_value()
        print('Optimal makespan:{}'.format(optimal_makespan))

        # Writes the solution in a file with the following format:
        # - for each machine, the job sequence
        def write_results(output_file, jobs_order, nb_machines, nb_jobs):
            if output_file is not None:
                final_jobs_order = [list(jobs_order[m].value) for m in range(nb_machines)]
                with open(output_file, "w+") as f:
                    print("Solution written in file:", output_file)
                    sol = []
                    for m in range(nb_machines):
                        for j in range(nb_jobs):
                            f.write(
                                'machine {}  job:{}  '.format(m, j) +
                                'job order:' + str(final_jobs_order[m][j]) + " ")
                            print('Machine:{} - Job:{} - order:{}'.format(m, j, final_jobs_order[m][j]))
                            sol.append({'machine': m, 'job': j, 'order': final_jobs_order[m][j]})
                        f.write("\n")

            return sol

        sol = write_results(output_file, jobs_order, nb_machines, nb_jobs)

    return sol


if __name__ == '__main__':
    instance_file = './instances/la35.txt'
    output_file = './results/la35_results.txt'
    time_limit = 200
    input_instance = read_instance(instance_file)
    sol = main(input_instance=input_instance, output_file=output_file, time_limit=time_limit)
    df_sol = DataFrame.from_records(sol)
    df_sol.sort_values(by=['machine', 'order'], inplace=True)
    df_sol.to_csv('./results/ft06_results.csv', index=False)
    print('hi')
