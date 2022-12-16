"""

"""

import localsolver
import json
import sys


def load_json_file(json_file_path: str) -> dict:
    """
    Load json file.
    Args:
        json_file_path: path of the json file.
    Returns:
        dictionary with the content of the json file.
    """
    with open(json_file_path, "r") as json_stream:
        try:
            json_dict = json.load(json_stream)
            return json_dict
        except Exception as exc:
            print('Error in load_json_file: {}'.format(exc))


def write_json(filename: str, dictionary: dict):
    """
    Write json
    Args:
        json_file_path: path of the json file.
    Returns:
        dictionary with the content of the json file.
    """

    with open(filename, 'w') as f:
        json.dump(dictionary, f, indent=4)


class PoolingInstance:

    #
    # Read instance data
    #
    def __init__(self, instance_file):

        problem = load_json_file(instance_file)

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
            self.upperBoundComponentToProduct[componentsIdx[edge["component"]]][productIdx[edge["product"]]] = edge[
                "bound"]
            if len(edge) > 3:
                self.costComponentToProduct[componentsIdx[edge["component"]]][productIdx[edge["product"]]] = edge[
                    "cost"]

        for edge in problem["component_to_pool_fraction"]:
            self.upperBoundFractionComponentToPool[componentsIdx[edge["component"]]][poolIdx[edge["pool"]]] = edge[
                "fraction"]
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
        results = {"objective": profit.value,
                   "solution": {"component_to_pool_fraction": component_to_pool_fraction,
                                "component_to_product": component_to_poduct,
                                "pool_to_product": pool_to_product}
                   }
        write_json(filename=output_file, dictionary=results)


if __name__ == '__main__':
    # if len(sys.argv) < 2:
    #    print("Usage: python pooling.py instance_file [output_file] [time_limit]")
    #    sys.exit(1)

    instance_file = 'adhya1.json'
    file_name = instance_file.strip('.json')

    path_instance = 'instances/' + instance_file
    output_file = 'results/' + file_name + '_results.json'
    time_limit = 20  # seconds
    main(path_instance, output_file, time_limit)
