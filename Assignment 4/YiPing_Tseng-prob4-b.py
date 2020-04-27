from kidney import *
from gurobipy import *
import numpy as np
import scipy.sparse as ss


model = Model("Kidney Three-ways Exchange")
model.ModelSense = GRB.MAXIMIZE

E = [1 for _ in range(len(data))]
start = [i[0] for i in data]
end = [i[1] for i in data]
rows = start
cols = end


mat = ss.csr_matrix((E, (rows, cols)), shape=(100, 100)).toarray()
edgeMaps = {(s, d): 1 for s, d in zip(rows, cols)}
edges = model.addVars(
    edgeMaps.keys(), 
    obj=edgeMaps,
    vtype=GRB.BINARY, 
    name='E'
)

model.addConstrs(
    (edges.sum(i, '*') - edges.sum('*', i) == 0 for i in range(100)), 
    "FlowConstr"
)

model.addConstrs(
    (edges.sum(i, '*') <= 1 for i in range(100)),
    "CycleConstr"
)

for s in range(100):
    for n1 in np.nonzero(mat[s, :])[0]:
        for n2 in np.nonzero(mat[n1, :])[0]:
            for n3 in np.nonzero(mat[n2, :])[0]:
                if len(set([s, n1, n2, n3])) == 4:
                    model.addConstr(
                        edges[s,n1] + edges[n1, n2] + edges[n2, n3] <= 2,
                        "ThreePathConstr-Node%s-Node%s-Node%s-Node%s" % (str(s), str(n1), str(n2), str(n3))
                    )

                
model.update()
model.optimize()


# store the solution and the model, so that you can go and look it up
path = os.path.dirname(os.path.abspath(__file__))
model.write(path + "/IP-kedney3.lp")
model.write(path + "/IP-kedney3.mps")
model.write(path + "/IP-kedney3.sol")
