########## steel_mill_slab_design.py ##########

import localsolver
import sys

if len(sys.argv) < 2:
    print("Usage: python steel_mill_slab_design.py inputFile [outputFile] [timeLimit]")
    sys.exit(1)


def read_integers(filename):
    with open(filename) as f:
        return [int(elem) for elem in f.read().split()]


#
# Computes the vector waste_for_content
#
def pre_compute_waste_for_content(slab_sizes, sum_size_orders):

    # No waste when a slab is empty.
    waste_for_content = [0]*sum_size_orders

    prev_size = 0
    for size in slab_sizes:
        if size < prev_size:
            print("Usage: python steel_mill_slab_design.py inputFile [outputFile] [timeLimit]")
            sys.exit(1)
        for content in range(prev_size + 1, size):
            waste_for_content[content] = size - content
        prev_size = size
    return waste_for_content


with localsolver.LocalSolver() as ls:

    #
    # Reads instance data
    #
    nb_colors_max_slab = 2

    file_it = iter(read_integers(sys.argv[1]))
    nb_slab_sizes = next(file_it)
    slab_sizes = [next(file_it) for i in range(nb_slab_sizes)]
    max_size = slab_sizes[nb_slab_sizes - 1]

    nb_colors = next(file_it)
    nb_orders = next(file_it)
    nb_slabs = nb_orders

    orders_by_color = [list() for c in range(nb_colors)]
    orders = [None]*nb_orders
    sum_size_orders = 0
    for o in range(nb_orders):
        orders[o] = next(file_it)
        c = next(file_it)
        # Note: colors are in [1..nb_colors]
        orders_by_color[c - 1].append(o)
        sum_size_orders += orders[o]

    waste_for_content = pre_compute_waste_for_content(slab_sizes, sum_size_orders)

    #
    # Declares the optimization model
    #
    model = ls.model

    # x[o, s] = 1 if order o is assigned to slab s, 0 otherwise
    x = [[model.bool() for s in range(nb_slabs)] for o in range(nb_orders)]

    # Each order is assigned to a slab
    for o in range(nb_orders):
        nb_slabs_assigned = model.sum(x[o])
        model.constraint(model.eq(nb_slabs_assigned, 1))

    # The content of each slab must not exceed the maximum size of the slab
    slab_content = [None]*nb_slabs
    for s in range(nb_slabs):
        slab_content[s] = model.sum([orders[o]*x[o][s] for o in range(nb_orders)])
        model.constraint(slab_content[s] <= max_size)

    # Create the LocalSolver array corresponding to the vector waste_for_content
    # (because "at" operators can only access LocalSolver arrays)
    waste_for_content_array = model.array(waste_for_content)

    # Wasted steel is computed according to the content of the slab
    wasted_steel = [waste_for_content_array[slab_content[s]] for s in range(nb_slabs)]

    # color[c][s] = 1 if the color c in the slab s, 0 otherwise
    color = [list() for c in range(nb_colors)]
    for c in range(nb_colors):
        if len(orders_by_color[c]) == 0: continue
        color[c] = [model.or_([x[o][s] for o in orders_by_color[c]]) for s in range(nb_slabs)]

    # The number of colors per slab must not exceed a specified value
    for s in range(nb_slabs):
        nb_colors_slab = model.sum([color[c][s] for c in range(nb_colors) if len(orders_by_color[c]) > 0])
        model.constraint(nb_colors_slab <= nb_colors_max_slab)

    # Minimize the total wasted steel
    total_wasted_steel = model.sum(wasted_steel)
    model.minimize(total_wasted_steel)

    model.close()

    #
    # Parameterizes the solver
    #
    if len(sys.argv) >= 4: ls.param.time_limit = int(sys.argv[3])
    else: ls.param.time_limit = 60
    ls.param.nb_threads = 4

    ls.solve()

    #
    # Writes the solution in a file with the following format:
    #  - total wasted steel
    #  - number of slabs used
    #  - for each slab used, the number of orders in the slab and the list of orders
    #
    if len(sys.argv) >= 3:
        with open(sys.argv[2], 'w') as f:
            f.write("%d\n" % total_wasted_steel.value)

            actual_nb_slabs = 0
            orders_by_slabs = [None]*nb_slabs
            for s in range(nb_slabs):
                orders_by_slabs[s] = [o for o in range(nb_orders) if x[o][s].value == 1]
                if len(orders_by_slabs[s]) > 0: actual_nb_slabs += 1
            f.write("%d\n" % actual_nb_slabs)

            for s in range(nb_slabs):
                nb_orders_in_slab = len(orders_by_slabs[s])
                if nb_orders_in_slab == 0: continue
                f.write("%d " % nb_orders_in_slab)
                for i in range(nb_orders_in_slab):
                    f.write("%d " % orders_by_slabs[s][i])
                f.write("\n")
