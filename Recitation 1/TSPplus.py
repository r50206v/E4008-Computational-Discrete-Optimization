#!/usr/bin/python

# Copyright 2016, Gurobi Optimization, Inc.

# Solve a traveling salesman problem on a randomly generated set of
# points using lazy constraints.   The base MIP model only includes
# 'degree-2' constraints, requiring each node to have exactly
# two incident edges.  Solutions to this model may contain subtours -
# tours that don't visit every city.  The lazy constraint callback
# adds new constraints to cut them off.

#### Addition: implements and solves the MTZ formulation on the same graph. To execute it, just type "gurobi TSPplus.py #", where # is the number of nodes of the graph you want to create. Yuri Faenza

import sys
import math
import random
import itertools
from gurobipy import *
from itertools import chain

# Callback - use lazy constraints to eliminate sub-tours

def subtourelim(model, where):
    if where == GRB.Callback.MIPSOL:
        # make a list of edges selected in the solution
        vals = model.cbGetSolution(model._vars)
        selected = tuplelist((i,j) for i,j in model._vars.keys() if vals[i,j] > 0.5)
        # find the shortest cycle in the selected edge list
        tour = subtour(selected)
        if len(tour) < n:
            # add subtour elimination constraint for every pair of cities in tour
            model.cbLazy(quicksum(model._vars[i,j]
                                  for i,j in itertools.combinations(tour, 2))
                         <= len(tour)-1)


# Given a tuplelist of edges, find the shortest subtour

def subtour(edges):
    unvisited = list(range(n))
    cycle = range(n+1) # initial length has 1 more city
    while unvisited: # true if list is non-empty
        thiscycle = []
        neighbors = unvisited
        while neighbors:
            current = neighbors[0]
            thiscycle.append(current)
            unvisited.remove(current)
            neighbors = [j for i,j in edges.select(current,'*') if j in unvisited]
        if len(cycle) > len(thiscycle):
            cycle = thiscycle
    return cycle


# Parse argument

if len(sys.argv) < 2:
    print('Usage: tsp.py npoints')
    exit(1)
n = int(sys.argv[1])

# Create n random points

random.seed()
points = [(random.randint(0,100),random.randint(0,100)) for i in range(n)]

# Dictionary of Euclidean distance between each pair of points

dist = {(i,j) : math.sqrt(sum((points[i][k]-points[j][k])**2 for k in range(2))) for i in range(n) for j in range(i)}

m = Model()

# Create variables

vars = m.addVars(dist.keys(), obj=dist, vtype=GRB.BINARY, name='e')
for i,j in vars.keys():
    vars[j,i] = vars[i,j] # edge in opposite direction

# You could use Python looping constructs and m.addVar() to create
# these decision variables instead.  The following would be equivalent
# to the preceding m.addVars() call...
#
# vars = tupledict()
# for i,j in dist.keys():
#   vars[i,j] = m.addVar(obj=dist[i,j], vtype=GRB.BINARY,
#                        name='e[%d,%d]'%(i,j))


# Add degree-2 constraint

m.addConstrs(vars.sum(i,'*') == 2 for i in range(n))

# Using Python looping constructs, the preceding would be...
#
# for i in range(n):
#   m.addConstr(sum(vars[i,j] for j in range(n)) == 2)


# Optimize model

m._vars = vars
m.Params.lazyConstraints = 1
m.optimize(subtourelim)

vals = m.getAttr('x', vars)
selected = tuplelist((i,j) for i,j in vals.keys() if vals[i,j] > 0.5)

tour = subtour(selected)
assert len(tour) == n

print('')
print('Optimal tour: %s' % str(tour))
print('Optimal cost: %g' % m.objVal)
print('')


#### Addition - MTZ Formulation for TSP
# We now clean up m and rewrite on it the MTZ formulation for the same graph we sampled
# Note that instead of using dictionaries, we use matrices to store distances and variables
# This makes sense because the graph is complete, so we wouldn't save much via dictionary

del m
m1 = Model()

# Compute the distance as a matrix

distance=[[0 for j in range(n)] for i in range(n)]

for i in range(n):
	for j in range(n):
		distance[i][j]= math.sqrt(sum((points[i][k]-points[j][k])**2 for k in range(2)))

# We store the edges for the reverse edges


# Add edge variables

newvars=[]
for i in range(n):
 newvars.append([])
 for j in range(n):
  newvars[i].append(m1.addVar(obj=distance[i][j], vtype=GRB.BINARY))

for i in range(n):
 newvars[i][i]=0



order = m1.addVars(range(n),vtype=GRB.CONTINUOUS,
                 obj=[0 for j in range(n)],
                 name="order")

# Add ordering constraints

m1.addConstr(order[0]==1)


for i in range(1,n):
	m1.addConstr(order[i]<=n)
	m1.addConstr(order[i]>=2)

for i in range(1,n):
 for j in range(1,n):
	m1.addConstr(order[i]-order[j]+1 + (n-1)*newvars[i][j] <= n-1)

# Add degree constraints

for i in range(n):
	m1.addConstr(sum(newvars[i][j] for j in range(n)) == 1)
	m1.addConstr(sum(newvars[j][i] for j in range(n)) == 1)


m1.update()
m1.optimize()






