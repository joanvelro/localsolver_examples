########## social_golfer.py ##########

import localsolver
import sys

if len(sys.argv) < 2:
    print("Usage: python social_golfer.py inputFile [outputFile] [timeLimit]")
    sys.exit(1)


def read_integers(filename):
    with open(filename) as f:
        return [int(elem) for elem in f.read().split()]


with localsolver.LocalSolver() as ls:

    #
    # Reads instance data
    #
    file_it = iter(read_integers(sys.argv[1]))
    nb_groups = next(file_it)
    group_size = next(file_it)
    nb_weeks = next(file_it)
    nb_golfers = nb_groups*group_size

    #
    # Declares the optimization model
    #
    model = ls.model

    # 0-1 decisions variables: x[w][gr][gf]=1 if golfer gf is in group gr on week w.
    x = [[[model.bool() for gf in range(nb_golfers)] for gr in range(nb_groups)] for w in range(nb_weeks)]

    # each week, each golfer is assigned to exactly one group
    for w in range(nb_weeks):
        for gf in range(nb_golfers):
            model.constraint(model.eq(model.sum(x[w][gr][gf] for gr in range(nb_groups)), 1))

    # each week, each group contains exactly group_size golfers
    for w in range(nb_weeks):
        for gr in range(nb_groups):
            model.constraint(model.eq(model.sum(x[w][gr][gf] for gf in range(nb_golfers)), group_size))

    # golfers gf0 and gf1 meet in group gr on week w if both are assigned to this group for week w.
    meetings = [None]*nb_weeks
    for w in range(nb_weeks):
        meetings[w] = [None]*nb_groups
        for gr in range(nb_groups):
            meetings[w][gr] = [None]*nb_golfers
            for gf0 in range(nb_golfers):
                meetings[w][gr][gf0] = [None]*nb_golfers
                for gf1 in range(gf0+1, nb_golfers):
                    meetings[w][gr][gf0][gf1] = model.and_(x[w][gr][gf0], x[w][gr][gf1])

    # the number of meetings of golfers gf0 and gf1 is the sum of their meeting variables over all weeks and groups
    redundant_meetings = [None]*nb_golfers
    for gf0 in range(nb_golfers):
        redundant_meetings[gf0] = [None]*nb_golfers
        for gf1 in range(gf0+1, nb_golfers):
            nb_meetings = model.sum(meetings[w][gr][gf0][gf1] for w in range(nb_weeks) for gr in range(nb_groups))
            redundant_meetings[gf0][gf1] = model.max(nb_meetings - 1, 0)

    # the goal is to minimize the number of redundant meetings
    obj = model.sum(redundant_meetings[gf0][gf1] for gf0 in range(nb_golfers) for gf1 in range(gf0+1, nb_golfers))
    model.minimize(obj)

    model.close()

    #
    # Parameterizes the solver
    #
    ls.param.nb_threads = 1
    if len(sys.argv) >= 4: ls.param.time_limit = int(sys.argv[3])
    else: ls.param.time_limit = 10

    ls.solve()

    # Writes the solution in a file following the following format:
    # - the objective value
    # - for each week and each group, write the golfers of the group
    # (nb_weeks x nbGroupes lines of group_size numbers).
    #
    if len(sys.argv) >= 3:
        with open(sys.argv[2], 'w') as f:
            f.write("%d\n" % obj.value)
            for w in range(nb_weeks):
                for gr in range(nb_groups):
                    for gf in range(nb_golfers):
                        if x[w][gr][gf].value:
                            f.write("%d " % (gf))
                    f.write("\n")
                f.write("\n")
