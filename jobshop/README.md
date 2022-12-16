# Jobshop
## Problem 
* A set of jobs has to be processed on every machine of the shop. 
* Each job consists in an ordered sequence of tasks (called activities), 
each representing the processing of the job on one of the machines.
* Each job has one activity per machine, and cannot start an activity while the 
previous activity of the job is not completed. 
* Each activity has a given processing time and each machine can only process one activity at a time.
* The goal is to find a sequence of jobs that minimizes the makespan: 
the time when all jobs have been processed.

## Data

The instances provided follow the _Taillard_ format. The format of the data files is as follows:

  * First line: number of jobs, number of machines, seed used to generate the instance, upper and lower bound previously found.

  * For each job: the processing time on each machine (given in the processing order).

  * For each job: the processing order (ordered list of visited machines).

## Program

* We use integer decision variables to model the start times of the activities. 
* The end time expressions are deduced by summing the start time and the processing time of
each activity.

* The precedence constraints are easily written: for each job, any activity of this job must
start after the activity processed by the previous machine has ended.

* In addition to the integer decisions representing the start times of the activities, 
we also use list decision variables. As in the _Flowshop example_, a list models the 
ordering of activities within a machine.

* We constrain all the jobs to be processed on each machine thanks to the “count” operator.

* The disjunctive resource constraints — each machine can only process one activity at a time —
can be reformulated as follows: given a sequence of jobs, the activity corresponding to any job 
must start after the activity corresponding to the previous job has ended.

* To model these constraints, we pair up the integer decisions (the start times) 
with the list decisions (the job orderings). 

* We write a lambda function, expressing the relationship between the start times of two 
consecutive activities. This function is used within an “and” operator over all activities 
processed by a machine.

* The makespan to minimize is the time when all the activities have been processed.