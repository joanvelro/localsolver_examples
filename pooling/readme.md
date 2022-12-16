# Pooling 
## Description

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

## data
The instances are in format JSON. They are composed of the following elements:

https://github.com/cog-imperial/pooling-network/blob/main/pooling_network/instances/data

* “components” array of objects characterizing the raw materials with:
    “name” name of the source node
    “lower” minimal outflow (unused as equals to 0)
    “upper” maximal outflow (supply)
    “price” price of one unit of the raw material
    “quality” object containing the concentration of each attribute in the raw material
* “products” array of object characterizing the final products with:
    “name” name of the target node
    “lower” minimal inflow (demand)
    “upper” maximal inflow (capacity)
    “price” sale price of one unit of the final product
    “quality_lower” object containing the minimal tolerate concentration of each attribute in the final product
    “quality_upper” object containing the maximal tolerate concentration of each attribute in the final product
* “pool_size” object containing the capacities of the pools
* “component_to_product_bound” array of objects characterizing the edge between the source nodes and the target nodes with:
    “component” name of the source node c
    “product” name of the target node p
    “bound” maximal flow on edge (c, p)
    “cost” cost of one unit of flow on edge (c, p)
* “component_to_pool_fraction” array of objects characterizing the edge between the source node and the pool nodes with:
    “component” name of the source node c
    “pool” name of the pool node o
    “fraction” maximal proportion of inflow at pool p coming from component c
    “cost” cost of one unit of flow in edge (c, o)
* “pool_to_product_bound” array of objects characterizing the edge between the pool nodes and the target nodes with:
    “pool” name of the pool node o
    “product” name of the target node p
    “bound” maximal flow on edge (o, p)
    “cost” cost of one unit of flow in edge (o, p)

The price of the raw materials and of the final products are either conveyed in the feature “price” or in the “cost” on the edges.
The “cost” representation is used for the randstd instances and the “price” representation for the others.

We use JSON libraries for each API model to read the instance data and write the output solution:
C# (Newtonsoft.Json), Java (gson-2.8.8), python (json), C++ (nlohmann/json.hpp). For the LSP model, the JSON module is used.


## Program

This localsolver model is based on the Q-formulation of the pooling problem which uses both flow proportions and flow quantities.
The parameters of the problem are:
* "C" a set of raw materials
* "P" a set of products
* "O" a set of pools

A tripartite flow graph composed with the three previous sets.

Three arrays of LSExpression decision variables are declared. They represent:

* The flow from the source node "c" to the target node "p" for all ("c", "p") in CxP,
* The flow from the pool "o" to the target node "p" for all ("o", "p") in OxP,
* The proportion of the inflow at pool "o" coming from the source node "c" for all (c, o) in CxO.

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