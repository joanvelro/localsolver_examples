import json

import localsolver

# Constant for incompatible machines
INFINITE = 1000000


def write_json(filename: str, dictionary: dict):
    with open(filename, 'w') as f:
        json.dump(dictionary, f, indent=4)


def read_instance(filename: str) -> dict:
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

    # Trivial upper bound for the start times of the tasks
    max_start = sum(
        max(task_processing_time[t][m] for m in range(nb_machines) if task_processing_time[t][m] != INFINITE)
        for t in range(nb_tasks))

    input_instance = dict()
    input_instance['nb_jobs'] = nb_jobs
    input_instance['nb_machines'] = nb_machines
    input_instance['nb_tasks'] = nb_tasks
    input_instance['task_processing_time'] = task_processing_time
    input_instance['job_operation_task'] = job_operation_task
    input_instance['nb_operations'] = nb_operations
    input_instance['max_start'] = max_start

    filename = instance_file.split(".")[1]
    write_json(filename='./' + filename + '.json', dictionary=input_instance)

    return input_instance


def main(instance_file: str, output_file: str = None, time_limit: int = None):

    input_instance = read_instance(instance_file)

    nb_jobs = input_instance['nb_jobs']
    nb_machines = input_instance['nb_machines']
    nb_tasks = input_instance['nb_tasks']
    task_processing_time = input_instance['task_processing_time']
    job_operation_task = input_instance['job_operation_task']

    nb_operations = input_instance['nb_operations']
    max_start = input_instance['max_start']

    # task_processing_time --> # for each task, gives the compatibility and duration that it will take in each equipment
    # job_operation_task --> for each job, gives the sequence of machines to be completed
    # nb_operations --> operations/tasks for each job

    with localsolver.LocalSolver() as ls:
        # Declares the optimization model
        model = ls.model

        # Sequence of tasks on each machine
        jobs_order = [model.list(nb_tasks) for m in range(nb_machines)]
        machine_array = model.array(jobs_order)

        # Each task is scheduled on a machine
        model.constraint(model.partition(machine_array))

        # Only compatible machines can be selected for a task
        for t in range(nb_tasks):
            for m in range(nb_machines):
                if task_processing_time[t][m] == INFINITE:
                    model.constraint(model.not_(model.contains(jobs_order[m], t)))

        # For each task, the selected machine
        task_machine = [model.find(machine_array, t) for t in range(nb_tasks)]

        task_processing_time_array = model.array(task_processing_time)

        # Integer decisions: start time of each task
        start = [model.int(0, max_start) for t in range(nb_tasks)]

        # The task duration depends on the selected machine
        duration = [model.at(task_processing_time_array, t, task_machine[t]) for t in range(nb_tasks)]
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
            sequence_selector = model.lambda_function(
                lambda t: model.geq(model.at(start_array, sequence[t + 1]), model.at(end_array, sequence[t])))
            model.constraint(model.and_(model.range(0, model.count(sequence) - 1), sequence_selector))

        # Minimize the makespan: end of the last task
        makespan = model.max([end[t] for t in range(nb_tasks)])
        model.minimize(makespan)

        model.close()

        # Parameterizes the solver
        if time_limit:
            ls.param.time_limit = time_limit
        else:
            ls.param.time_limit = 60

        ls.solve()

        # Writes the solution in a file with the following format:
        # - for each operation of each job, the selected machine, the start and end dates
        if output_file:
            with open(output_file, "w") as f:
                print("Solution written in file", output_file)
                for j in range(nb_jobs):
                    for o in range(0, nb_operations[j]):
                        task = job_operation_task[j][o]
                        f.write(
                            'Job:' + str(j + 1) +
                            "\tOperation:" + str(o + 1) +
                            "\tMachine:" + str(task_machine[task].value + 1) +
                            "\tStart time:" + str(start[task].value) +
                            "\tEnd time:" + str(end[task].value) +
                            "\n")


if __name__ == '__main__':
    instance_file = './instances/Mk10.fjs'
    output_file = './reports/Mk10_report.txt'
    time_limit = 10
    main(instance_file, output_file, time_limit)
