from kidney import *
from gurobipy import *

maxNode = 101
model = Model("Kidney Two-ways Exchange")
model.ModelSense = GRB.MAXIMIZE

start = [i[0] for i in data]
end = [i[1] for i in data]
rows = start# + end
cols = end# + start

edgeMaps = {(s, d): 1 for s, d in zip(rows, cols)}
edges = model.addVars(
    edgeMaps.keys(), 
    obj=edgeMaps,
    vtype=GRB.BINARY, 
    name='E'
)

model.addConstrs(
    (edges.sum(i, '*') + edges.sum('*', i) <= 1 for i in range(maxNode)), 
    "OneMatchConstr"
)

model.update()
model.optimize()


# store the solution and the model, so that you can go and look it up
path = os.path.dirname(os.path.abspath(__file__))
model.write(path + "/IP-kedney2.lp")
model.write(path + "/IP-kedney2.mps")
model.write(path + "/IP-kedney2.sol")
