# Flexible Job Shop
## Description

* A set of jobs has to be processed on the machines in the shop. 
* Each job consists of an ordered sequence of tasks (called operations),
and each operation must be performed by one of the machines compatible with 
that operation. 

* An operation cannot begin until the previous operation in the job is completed. 
* Each operation has a given processing time that depends on the chosen machine,
and each machine can only process one operation at a time.

* The goal is to find a sequence of jobs that minimizes the makespan: the time when
* all jobs have been processed.

## Data
The format of the data files is as follows:

* First line: number of jobs, number of machines (+ average number of machines per operations, not needed)

* From the second line, for each job:

  * Number of operations in that job

  * For each operation:
    * Number of machines compatible with this operation 
    * For each compatible machine: a pair of numbers (machine, processing time)

# Program

* The model is very similar to the original __Job Shop Problem__, and the decision variables remain unchanged: 
integer decision variables to model  the start times of the operations, and a list decision variable for each machine, representing the order of the 
tasks scheduled on this machine.

* Each operation of each job must be processed, hence the _partition_ operator on the lists,  
which ensures that each task will belong to one and only one machine. Machines that are not 
compatible for an operation are filtered out using a _contains_ operator.

* The _find_ operator takes as argument an array of lists and an integer value, and returns the position of the list containing the value in the 
array, if it exists. Here, we use this operator to retrieve the id of the machine used for each task. It then allows to deduce the duration of the
operation, since it depends on the selected machine.

* The disjunctive resource constraints are modeled in the same way as for the original job shop problem, and the makespan to be minimized is the 
time when all tasks have been processed.