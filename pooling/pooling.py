"""
    --- Description

    The pooling problem is a nonlinear network flow problem that models the operation of the supply chain of petrochemicals where crude oils are
     mixed to produce intermediate quality streams that are blended at retail locations to produce the final products.
    The main challenge in finding optimal solutions to pooling problems is that the non-linearities result in many local optima.

    Companies across numerous industries – including petrochemical refining, wastewater treatment, and mining – use mathematical optimization to
    solve the pooling problem wich results in a mixed-integer quadratically-constrained programming (MIQCP) model

    In the pooling problem, flows of raw materials with specific attribute concentrations are blended to create final products whose attribute
    concentrations must be within tolerance intervals (attributes are interesting primary constituents of the materials).
    The flows can either be sent directly from the source nodes to the target nodes or can be blended at intermediate pools and then sent to the
    target nodes. The capacities of the flow graph and of the different nodes must be respected and the raw materials supply cannot be exceeded.
    The objective is to maximize the profit of the operation. The gains are the sale prices of the final products and the costs are the buying prices
    of the raw materials.
    In that sense, the pooling problem can be seen as a mix between the minimal cost flow problem and the blending problem.

    --- data
    The instances are in format JSON. They are composed of the following elements:

    https://github.com/cog-imperial/pooling-network/blob/main/pooling_network/instances/data

    “components” array of objects characterizing the raw materials with:
        “name” name of the source node
        “lower” minimal outflow (unused as equals to 0)
        “upper” maximal outflow (supply)
        “price” price of one unit of the raw material
        “quality” object containing the concentration of each attribute in the raw material
    “products” array of object characterizing the final products with:
        “name” name of the target node
        “lower” minimal inflow (demand)
        “upper” maximal inflow (capacity)
        “price” sale price of one unit of the final product
        “quality_lower” object containing the minimal tolerate concentration of each attribute in the final product
        “quality_upper” object containing the maximal tolerate concentration of each attribute in the final product
    “pool_size” object containing the capacities of the pools
    “component_to_product_bound” array of objects characterizing the edge between the source nodes and the target nodes with:
        “component” name of the source node c
        “product” name of the target node p
        “bound” maximal flow on edge (c, p)
        “cost” cost of one unit of flow on edge (c, p)
    “component_to_pool_fraction” array of objects characterizing the edge between the source node and the pool nodes with:
        “component” name of the source node c
        “pool” name of the pool node o
        “fraction” maximal proportion of inflow at pool p coming from component c
        “cost” cost of one unit of flow in edge (c, o)
    “pool_to_product_bound” array of objects characterizing the edge between the pool nodes and the target nodes with:
        “pool” name of the pool node o
        “product” name of the target node p
        “bound” maximal flow on edge (o, p)
        “cost” cost of one unit of flow in edge (o, p)

    The price of the raw materials and of the final products are either conveyed in the feature “price” or in the “cost” on the edges.
    The “cost” representation is used for the randstd instances and the “price” representation for the others.

    We use JSON libraries for each API model to read the instance data and write the output solution:
    C# (Newtonsoft.Json), Java (gson-2.8.8), python (json), C++ (nlohmann/json.hpp). For the LSP model, the JSON module is used.


     ----- Program

    This localsolver model is based on the Q-formulation of the pooling problem which uses both flow proportions and flow quantities.
    The parameters of the problem are:
        "C" a set of raw materials
        "P" a set of products
        "O" a set of pools

    A tripartite flow graph composed with the three previous sets.

    Three arrays of LSExpression decision variables are declared. They represent:

        The flow from the source node "c" to the target node "p" for all ("c", "p") in CxP,
        The flow from the pool "o" to the target node "p" for all ("o", "p") in OxP,
        The proportion of the inflow at pool "o" coming from the source node "c" for all (c, o) in CxO.

    An intermediate three-dimensional array of LSExpression is declared to represent the flow coming from the source node "c" and going to the target
    node "p" through the pool "o" which equals the proportion of inflow at pool "o" coming from the source node "c" times the flow from the pool "o"
    to the product "p".

    Note that the flow from source "c" to pool "o" can be easily computed by summing the previous array over "P" for fixed "c"
    and "o". This quantity is constrained by the proportion of inflow at pool "o" coming from the source "c" times the capacity of the pool.

    For each pool, the total proportion of inflow coming from the source nodes are computed with the sum operator over all the components.
    This quantity is constrained to be equal to one. The total inflow at the target nodes must satisfy the demand while respecting the capacity of
    the product. The total outflow at the source nodes cannot exceed the supply of the raw materials.

    Finally, for each final product and each attribute, the concentration must be within a tolerance interval. This means the quantity of attribute
    in a final product must be within the interval times the total inflow at the target node. The quantity of attribute incoming at the target node
    is computed by summing the quantity coming directly from the source nodes and the quantity coming from the pools. The quantity coming from the
    source nodes is computed by summing over C the flow from a source node to the target node times the attribute concentration in the raw material.
    The quantity coming from the pools is computed by summing over CxO the flow coming from a source node to the target node through a pool times the
     concentration of attribute in the raw material.

    The objective is to maximize the total profit of the operation. If the prices of the products and of the raw materials are explicit, the profit
    equals the sum over the products of the price times the total inflow minus the sum over the raw materials of the price times the total outflow.
    If the prices are expressed through costs on the edges, the profit is the opposite of the total cost. The total cost is computed by summing the
    unit cost times the flow over all the edges of the graph.
"""

########## pooling.py ##########

import localsolver
import json
import sys


class PoolingInstance:

    #
    # Read instance data
    #
    def __init__(self, instance_file):
        with open(instance_file) as problem:
            problem = json.load(problem)

            self.nbComponents = len(problem["components"])
            self.nbProducts = len(problem["products"])
            self.nbAttributes = len(problem["components"][0]["quality"])
            self.nbPools = len(problem["pool_size"])

            # Components
            self.componentPrices = [problem["components"][c]["price"]
                                    for c in range(self.nbComponents)]
            self.componentSupplies = [problem["components"][c]["upper"]
                                      for c in range(self.nbComponents)]
            self.componentQuality = [list(problem["components"][c]["quality"].values())
                                     for c in range(self.nbComponents)]
            self.componentNames = [problem["components"][c]["name"]
                                   for c in range(self.nbComponents)]

            componentsIdx = {}
            for c in range(self.nbComponents):
                componentsIdx[problem["components"][c]["name"]] = c

            # Final products (blendings)
            self.productPrices = [problem["products"][p]["price"]
                                  for p in range(self.nbProducts)]
            self.productCapacities = [problem["products"][p]["upper"]
                                      for p in range(self.nbProducts)]
            self.demand = [problem["products"][p]["lower"]
                           for p in range(self.nbProducts)]
            self.productNames = [problem["products"][p]["name"]
                                 for p in range(self.nbProducts)]

            productIdx = {}
            for p in range(self.nbProducts):
                productIdx[problem["products"][p]["name"]] = p

            self.minTolerance = [[0 for k in range(self.nbAttributes)]
                                 if (problem["products"][p]["quality_lower"] is None)
                                 else list(problem["products"][p]["quality_lower"].values())
                                 for p in range(self.nbProducts)]
            self.maxTolerance = [list(problem["products"][p]["quality_upper"].values())
                                 for p in range(self.nbProducts)]

            # Intermediate pools
            self.poolNames = list(problem["pool_size"].keys())
            self.poolCapacities = [problem["pool_size"][o] for o in self.poolNames]
            poolIdx = {}
            for o in range(self.nbPools):
                poolIdx[self.poolNames[o]] = o

            # Flow graph

            # Edges from the components to the products
            self.upperBoundComponentToProduct = [[0 for _ in range(self.nbProducts)]
                                                 for _ in range(self.nbComponents)]
            self.costComponentToProduct = [[0 for _ in range(self.nbProducts)]
                                           for _ in range(self.nbComponents)]
            # Edges from the components to the pools
            self.upperBoundFractionComponentToPool = [[0 for _ in range(self.nbPools)]
                                                      for _ in range(self.nbComponents)]
            self.costComponentToPool = [[0 for _ in range(self.nbPools)]
                                        for _ in range(self.nbComponents)]
            # Edges from the pools to the products
            self.upperBoundPoolToProduct = [[0 for _ in range(self.nbProducts)]
                                            for _ in range(self.nbPools)]
            self.costPoolToProduct = [[0 for _ in range(self.nbProducts)]
                                      for _ in range(self.nbPools)]

            # Bound and cost on the edges
            for edge in problem["component_to_product_bound"]:
                self.upperBoundComponentToProduct[componentsIdx[edge["component"]]][productIdx[edge["product"]]] = edge["bound"]
                if len(edge) > 3:
                    self.costComponentToProduct[componentsIdx[edge["component"]]][productIdx[edge["product"]]] = edge["cost"]

            for edge in problem["component_to_pool_fraction"]:
                self.upperBoundFractionComponentToPool[componentsIdx[edge["component"]]][poolIdx[edge["pool"]]] = edge["fraction"]
                if len(edge) > 3:
                    self.costComponentToPool[componentsIdx[edge["component"]]][poolIdx[edge["pool"]]] = edge["cost"]

            for edge in problem["pool_to_product_bound"]:
                self.upperBoundPoolToProduct[poolIdx[edge["pool"]]][productIdx[edge["product"]]] = edge["bound"]
                if len(edge) > 3:
                    self.costPoolToProduct[poolIdx[edge["pool"]]][productIdx[edge["product"]]] = edge["cost"]


def main(instance_file, output_file, time_limit):

    data = PoolingInstance(instance_file)

    with localsolver.LocalSolver() as ls:
        # Declare the optimization model
        model = ls.model

        # =============================================
        #  ----------- Decision variables -------------
        # =============================================
        # Flow from the components to the products
        flowComponentToProduct = [[model.float(0, data.upperBoundComponentToProduct[c][p])
                                   for p in range(data.nbProducts)] for c in range(data.nbComponents)]

        # Fraction of the total flow in pool o coming from the component c
        fractionComponentToPool = [[model.float(0, data.upperBoundFractionComponentToPool[c][o])
                                    for o in range(data.nbPools)] for c in range(data.nbComponents)]

        # Flow from the pools to the products
        flowPoolToProduct = [[model.float(0, data.upperBoundPoolToProduct[o][p])
                              for p in range(data.nbProducts)] for o in range(data.nbPools)]

        # Flow from the components to the products and passing by the pools
        flowComponentToProductByPool = [[[fractionComponentToPool[c][o] *
                                          flowPoolToProduct[o][p] for p in range(data.nbProducts)]
                                         for o in range(data.nbPools)] for c in range(data.nbComponents)]

        # =============================================
        #  ----------- CONSTRAINTS-------------
        # =============================================

        # Proportion
        for o in range(data.nbPools):
            proportion = model.sum(fractionComponentToPool[c][o]
                                   for c in range(data.nbComponents))
            model.constraint(proportion == 1)

        # Component supply
        for c in range(data.nbComponents):
            flowToProducts = model.sum(flowComponentToProduct[c][p]
                                       for p in range(data.nbProducts))
            flowToPools = model.sum(flowComponentToProductByPool[c][o][p]
                                    for p in range(data.nbProducts) for o in range(data.nbPools))
            totalOutFlow = model.sum(flowToPools, flowToProducts)
            model.constraint(totalOutFlow <= data.componentSupplies[c])

        # Pool capacity (bounds on edges)
        for c in range(data.nbComponents):
            for o in range(data.nbPools):
                flowComponentToPool = model.sum(flowComponentToProductByPool[c][o][p]
                                                for p in range(data.nbProducts))
                edgeCapacity = model.prod(data.poolCapacities[o], fractionComponentToPool[c][o])
                model.constraint(flowComponentToPool <= edgeCapacity)

        # Product capacity
        for p in range(data.nbProducts):
            flowFromPools = model.sum(flowPoolToProduct[o][p]
                                      for o in range(data.nbPools))
            flowFromComponents = model.sum(flowComponentToProduct[c][p]
                                           for c in range(data.nbComponents))
            totalInFlow = model.sum(flowFromComponents, flowFromPools)
            model.constraint(totalInFlow <= data.productCapacities[p])
            model.constraint(totalInFlow >= data.demand[p])

        # Product tolerance
        for p in range(data.nbProducts):
            for k in range(data.nbAttributes):
                # Attribute from the components
                attributeFromComponents = model.sum(data.componentQuality[c][k] *
                                                    flowComponentToProduct[c][p] for c in range(data.nbComponents))

                # Attribute from the pools
                attributeFromPools = model.sum(data.componentQuality[c][k] *
                                               flowComponentToProductByPool[c][o][p] for o in range(data.nbPools)
                                               for c in range(data.nbComponents))

                # Total flow in the blending
                totalFlowIn = model.sum(flowComponentToProduct[c][p]
                                        for c in range(data.nbComponents)) + \
                              model.sum(flowPoolToProduct[o][p] for o in range(data.nbPools))

                totalAttributeIn = model.sum(attributeFromComponents, attributeFromPools)
                model.constraint(totalAttributeIn >= data.minTolerance[p][k] * totalFlowIn)
                model.constraint(totalAttributeIn <= data.maxTolerance[p][k] * totalFlowIn)

        # =============================================
        #  ----------- OBJECTIVE           -------------
        # =============================================

        # Cost of the flows from the components directly to the products
        directFlowCost = model.sum(data.costComponentToProduct[c][p] *
                                   flowComponentToProduct[c][p] for c in range(data.nbComponents)
                                   for p in range(data.nbProducts))

        # Cost of the flows from the components to the products passing by the pools
        undirectFlowCost = model.sum((data.costComponentToPool[c][o] +
                                      data.costPoolToProduct[o][p]) * flowComponentToProductByPool[c][o][p]
                                     for c in range(data.nbComponents) for o in range(data.nbPools)
                                     for p in range(data.nbProducts))

        # Gain of selling the final products
        productsGain = model.sum((model.sum(flowComponentToProduct[c][p]
                                            for c in range(data.nbComponents)) +
                                  model.sum(flowPoolToProduct[o][p] for o in range(data.nbPools)))
                                 * data.productPrices[p] for p in range(data.nbProducts))

        # Cost of buying the components
        componentsCost = model.sum((model.sum(flowComponentToProduct[c][p]
                                              for p in range(data.nbProducts)) +
                                    model.sum(fractionComponentToPool[c][o] * flowPoolToProduct[o][p]
                                              for p in range(data.nbProducts) for o in range(data.nbPools))) *
                                   data.componentPrices[c] for c in range(data.nbComponents))

        profit = productsGain - componentsCost - (directFlowCost + undirectFlowCost)

        # Maximize the total profit
        model.maximize(profit)

        model.close()

        #
        # Parameterize the solver
        #

        ls.param.time_limit = time_limit

        # =============================================
        #                SOLVE MODEL
        # =============================================
        ls.solve()

        # Write the solution
        # =============================================
        #                RESULTS
        # =============================================
        with open(output_file, 'w') as f:
            component_to_poduct = []
            component_to_pool_fraction = []
            pool_to_product = []

            # Solution flows from the components to the products
            for c in range(data.nbComponents):
                for p in range(data.nbProducts):
                    component_to_poduct.append({"component": data.componentNames[c],
                                                "product": data.productNames[p],
                                                "flow": flowComponentToProduct[c][p].value})

            # Solution fraction of the inflow at pool o coming from the component c
            for c in range(data.nbComponents):
                for o in range(data.nbPools):
                    component_to_pool_fraction.append({"component": data.componentNames[c],
                                                       "pool": data.poolNames[o],
                                                       "flow": fractionComponentToPool[c][o].value})

            # Solution flows from the pools to the products
            for o in range(data.nbPools):
                for p in range(data.nbProducts):
                    pool_to_product.append({"pool": data.poolNames[o],
                                            "product": data.productNames[p],
                                            "flow": flowPoolToProduct[o][p].value})

            json.dump({"objective": profit.value, "solution":
                {"component_to_pool_fraction": component_to_pool_fraction,
                 "component_to_product": component_to_poduct,
                 "pool_to_product": pool_to_product}}, f)


if __name__ == '__main__':
    # if len(sys.argv) < 2:
    #    print("Usage: python pooling.py instance_file [output_file] [time_limit]")
    #    sys.exit(1)

    instance_file = 'adhya1.json'
    file_name = instance_file.strip('.json')

    path_instance = 'instances\\' + instance_file
    output_file = 'results\\' + file_name + '_results.txt'
    time_limit = 20  # seconds
    main(path_instance, output_file, time_limit)
