
# Program that takes as input a file data: containing:
# number stocks
# stock name, with value on 06/30/17
# correlation between those stocks in the last 3 years
# and as input from the user the different kind of stocks to buy
# And then builds an index fund tracking them using IP
# Author: Yuri Faenza
import re
import os
import sys
import math
import random
import itertools
from gurobipy import *


if len(sys.argv) < 2:
    print('Usage: Index.py nr-stocks-to-buy')
    exit(1)
nr_stocks_to_buy = int(sys.argv[1])

# We collect data from file

t = open('data.txt', 'r')

nr_stocks = int(t.readline())

name = []
last_price = []

for i in range(nr_stocks):
    line = t.readline()
    string = re.split(' +|\n', line)
    name.append(string[0])
    last_price.append(float(string[1]))


corr = [[0 for i in range(nr_stocks)] for j in range(nr_stocks)]

for i in range(nr_stocks):
    line = t.readline()
    string = re.split(' +|\n', line)
    for j in range(nr_stocks):
        corr[i][j] = float(string[j])

# The model starts here


model = Model("Index fund - NumOfStock %s" % str(nr_stocks_to_buy))


# store correlation coefficient in a dictionary
correlation = {
    (i, j): corr[i][j]
    for i in range(nr_stocks) for j in range(nr_stocks)
}


# create variables x[i,j] and gives the correlation as objective function value
vars = model.addVars(
    correlation.keys(), 
    obj=correlation,
    vtype=GRB.BINARY, 
    name='x'
)

# create variables y
vary = model.addVars(
    range(nr_stocks), 
    vtype=GRB.BINARY, 
    obj=[0 for j in range(nr_stocks)], 
    name='y'
)


# we want a problem in maximization form
model.ModelSense = GRB.MAXIMIZE


# Add constraints saying that we must select exactly nr_stocks_to_buy
model.addConstr(
    (sum(vary[i] for i in range(nr_stocks)) == nr_stocks_to_buy), 
    "NumberOfStocks"
)


# Add constraints saying that each stock must be represented by one stock
model.addConstrs(
    (vars.sum(i, '*') == 1 for i in range(nr_stocks)), 
    "RepresentativeConstr"
)

# Add constraints saying that a stock i can be represented by a stock j only if j is selected
model.addConstrs(
    (vars[i, j] <= vary[j]
     for i, j in itertools.product(range(nr_stocks), range(nr_stocks))),
    "SelectionConstr"
)


## Run and enjoy
model.update()
model.optimize()


# calculate each proportion of investing stocks
weights = [0] * nr_stocks
for j in range(nr_stocks):
    for i in range(nr_stocks):
        weights[j] += last_price[i] * vars[i, j].x

for ind, val in enumerate(weights):
    if val:
        print("%s: %s" % (name[ind], str(val/sum(weights))))


# store the solution and the model, so that you can go and look it up
path = os.path.dirname(os.path.abspath(__file__))
model.write(path + "/LP-num%s.lp" % str(nr_stocks_to_buy))
model.write(path + "/LP-num%s.mps" % str(nr_stocks_to_buy))
model.write(path + "/LP-num%s.sol" % str(nr_stocks_to_buy))
