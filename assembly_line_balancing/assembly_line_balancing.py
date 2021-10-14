########## assembly_line_balancing.py ##########

import localsolver
import sys

#
# Functions to read the instances
#
def read_elem(filename):
    with open(filename) as f:
        return [str(elem) for elem in f.read().split()]

def read_instance(instance_file):
    file_it = iter(read_elem(instance_file))
    for i in range(3):
        to_throw = next(file_it)

    # Read number of tasks
    nbTasks = int(next(file_it))
    maxNbStations = nbTasks
    for i in range(2):
        to_throw = next(file_it)

    # Read the cycle time limit
    cycleTime = int(next(file_it))
    for i in range(5):
        to_throw = next(file_it)

    # Read the processing times
    processingTimeDict = {}
    for i in range(nbTasks):
        task = int(next(file_it)) - 1
        processingTimeDict[task] = int(next(file_it))
    for i in range(2):
        to_throw = next(file_it)
    processingTime = [elem[1] for elem in sorted(processingTimeDict.items(), key=lambda x: x[0])]

    # Read the successors' relations
    successors = {}
    while True:
        try:
            pred, succ = next(file_it).split(',')
            pred = int(pred) -1
            succ = int(succ) -1
            if pred in successors:
                successors[pred].append(succ)
            else:
                successors[pred] = [succ]
        except:
            break
    return nbTasks, maxNbStations, cycleTime, processingTime, successors

#
# Modeling and solve
#
def main(instance_file, output_file, time_limit):
    nbTasks, maxNbStations, cycleTime, processingTime, successors = read_instance(instance_file)

    with localsolver.LocalSolver() as ls:

        # Declare the optimization model
        model = ls.model

        # Decision variables: station[s] is the set of tasks assigned to station s
        station = [model.set(nbTasks) for s in range(maxNbStations)]
        model.constraint(model.partition(station))

        # Objective: nbUsedStations is the total number of used stations
        nbUsedStations = model.sum((model.count(station[s]) > 0) for s in range(maxNbStations))

        # All stations must respect the cycleTime constraint
        processingTime_array = model.array(processingTime)
        time_selector = model.lambda_function(lambda i : processingTime_array[i])
        timeInStation = [model.sum(station[s], time_selector) for s in range(maxNbStations)]
        for s in range(maxNbStations):
            model.constraint(timeInStation[s] <= cycleTime)

        # The stations must respect the succession's order of the tasks
        taskStation = [model.sum(model.contains(station[s], i) * s for s in range(maxNbStations)) for i in range(nbTasks)]
        for i in range(nbTasks):
            if i in successors.keys():
                for j in successors[i]:
                    model.constraint(taskStation[i] <= taskStation[j])

        # Minimization of the number of active stations
        model.minimize(nbUsedStations)

        model.close()

        #
        # Parameterize the solver
        #
        ls.param.time_limit = time_limit
        # Initialize with a naive solution: each task belongs to one separate station
        # Note: nbTasks equals nbMaxStations
        for i in range(nbTasks):
            station[i].value.add(i)

        ls.solve()

        # Write the solution in a file following the format:
        # - 1st line: value of the objective
        # - 2nd line: number of tasks
        # - following lines: task's number, station's number
        if output_file is not None:
            with open(output_file, 'w') as f:
                f.write("%d\n" % nbUsedStations.value)
                f.write("%d\n" % nbTasks)
                for i in range(nbTasks):
                    f.write("{},{}\n".format(i+1, taskStation[i].value+1))

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python assembly_line_balancing.py instance_file [output_file] [time_limit]")
        sys.exit(1)

    instance_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) >= 3 else None
    time_limit = int(sys.argv[3]) if len(sys.argv) >= 4 else 20
    main(instance_file, output_file, time_limit)
