import localsolver
import sys

# Constant for incompatible machines
INFINITE = 1000000


def read_instance(filename):
    with open(filename) as f:
        lines = f.readlines()

    first_line = lines[0].split()
    # Number of jobs
    nb_jobs = int(first_line[0])
    # Number of machines
    nb_machines = int(first_line[1])

    # Number of operations for each job
    nb_operations = [int(lines[j + 1].split()[0]) for j in range(nb_jobs)]

    # Number of tasks
    nb_tasks = sum(nb_operations[j] for j in range(nb_jobs))

    # Processing time for each task, for each machine
    task_processing_time = [[INFINITE for m in range(nb_machines)] for t in range(nb_tasks)]

    # For each job, for each operation, the corresponding task id
    job_operation_task = [[0 for o in range(nb_operations[j])] for j in range(nb_jobs)]

    # Setup time between every two consecutive tasks, for each machine
    task_setup_time = [[[-1 for r in range(nb_tasks)] for t in range(nb_tasks)] for m in range(nb_machines)]

    id = 0
    for j in range(nb_jobs):
        line = lines[j + 1].split()
        tmp = 0
        for o in range(nb_operations[j]):
            nb_machines_operation = int(line[tmp + o + 1])
            for i in range(nb_machines_operation):
                machine = int(line[tmp + o + 2 * i + 2]) - 1
                time = int(line[tmp + o + 2 * i + 3])
                task_processing_time[id][machine] = time
            job_operation_task[j][o] = id
            id = id + 1
            tmp = tmp + 2 * nb_machines_operation

    id_line = nb_jobs + 2
    for m in range(nb_machines):
        for t1 in range(nb_tasks):
            task_setup_time[m][t1] = list(map(int, lines[id_line].split()))
            id_line += 1

    # Trivial upper bound for the start times of the tasks
    max_start = sum(
        max(task_processing_time[t][m] for m in range(nb_machines) if task_processing_time[t][m] != INFINITE)
        for t in range(nb_tasks))

    return nb_jobs, nb_machines, nb_tasks, task_processing_time, job_operation_task, \
        nb_operations, task_setup_time, max_start


def main(instance_file, output_file, time_limit):
    nb_jobs, nb_machines, nb_tasks, task_processing_time_data, job_operation_task, \
        nb_operations, task_setup_time_data, max_start = read_instance(instance_file)

    with localsolver.LocalSolver() as ls:
        #
        # Declare the optimization model
        #
        model = ls.model

        # Sequence of tasks on each machine
        jobs_order = [model.list(nb_tasks) for _ in range(nb_machines)]
        machines = model.array(jobs_order)

        # Each task is scheduled on a machine
        model.constraint(model.partition(machines))

        # Only compatible machines can be selected for a task
        for t in range(nb_tasks):
            for m in range(nb_machines):
                if task_processing_time_data[t][m] == INFINITE:
                    model.constraint(model.not_(model.contains(jobs_order[m], t)))

        # For each task, the selected machine
        task_machine = [model.find(machines, t) for t in range(nb_tasks)]

        task_processing_time = model.array(task_processing_time_data)
        task_setup_time = model.array(task_setup_time_data)

        # Integer decisions: start time of each task
        start = [model.int(0, max_start) for _ in range(nb_tasks)]

        # The task duration depends on the selected machine
        duration = [model.at(task_processing_time, t, task_machine[t]) for t in range(nb_tasks)]
        end = [start[t] + duration[t] for t in range(nb_tasks)]

        start_array = model.array(start)
        end_array = model.array(end)

        # Precedence constraints between the operations of a job
        for j in range(nb_jobs):
            for o in range(nb_operations[j] - 1):
                t1 = job_operation_task[j][o]
                t2 = job_operation_task[j][o + 1]
                model.constraint(start[t2] >= end[t1])

        # Disjunctive resource constraints between the tasks on a machine
        for m in range(nb_machines):
            sequence = jobs_order[m]
            sequence_lambda = model.lambda_function(
                lambda t: start_array[sequence[t + 1]] >= end_array[sequence[t]]
                        + model.at(task_setup_time, m, sequence[t], sequence[t + 1]))
            model.constraint(model.and_(model.range(0, model.count(sequence) - 1), sequence_lambda))

        # Minimize the makespan: end of the last task
        makespan = model.max(end)
        model.minimize(makespan)

        model.close()

        # Parameterize the solver
        ls.param.time_limit = time_limit

        ls.solve()

        # Write the solution in a file with the following format:
        # - for each operation of each job, the selected machine, the start and end dates
        if output_file is not None:
            with open(output_file, "w") as f:
                print("Solution written in file", output_file)
                for j in range(nb_jobs):
                    for o in range(0, nb_operations[j]):
                        task = job_operation_task[j][o]
                        f.write(str(j + 1) + "\t" + str(o + 1) + "\t" + str(task_machine[task].value + 1)
                            + "\t" + str(start[task].value) + "\t" + str(end[task].value) + "\n")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python flexible_jobshop_setup.py instance_file [output_file] [time_limit]")
        sys.exit(1)

    instance_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) >= 3 else None
    time_limit = int(sys.argv[3]) if len(sys.argv) >= 4 else 60
    main(instance_file, output_file, time_limit)
