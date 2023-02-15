# Flexible Job Shop Scheduling Problem with Sequence-Dependent Setup Times (FJSP-SDST)
## Description

In the flexible job shop scheduling problem with sequence-dependent setup times (FJSP-SDST), a set of jobs has to be processed on the machines in 
the shop. 

Each job consists of an ordered sequence of tasks (called operations), and each operation must be performed by one of the machines compatible with 
that operation. An operation cannot begin until the previous operation in the job is completed. Each operation has a given processing time that 
depends on the chosen machine. Each machine can only process one operation at a time and must be set up between two consecutive operations. These 
setup times depend both on the operations and the machine considered.

The goal is to find a sequence of jobs that minimizes the makespan: the time when all jobs have been processed. 

## Data
The format of the data files is as follows:

* _First line_: number of jobs, number of machines (+ average number of machines per operations, not needed)

* From the _second line_, for each job:

  * Number of operations in that job

      * For each operation:

          * Number of machines compatible with this operation

          * For each compatible machine: a pair of numbers (machine, processing time)

* For each machine and each operation:

  * Setup time between the first operation and every other operation on the machine considered



# Program

* The model is an extension from the Flexible Job Shop Problem with the use of the setup times on the machines. 
* The decision variables are the following : 
  * we represent the start times of the tasks by integer decision variables 
  * we model the order of the operations performed on each machine by a list decision variable.

* Each operation of each job must be processed on one and only one machine, hence the partition operator on the lists.

* The disjunctive resource contraints between tasks on a machine guarantee that an operation starts on a machine only after the previous operation 
is done and the setup between the two operations is completed.

* The constraints of compatibility of the machines are modeled in the same way as for the flexible job shop problem, and the makespan to be minimized
is the time when all tasks have been processed.