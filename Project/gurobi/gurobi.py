import os
import pickle
import pandas as pd
from gurobipy import *
currentPath = os.path.dirname(os.path.abspath(__file__))


# import data
train = pd.read_csv(currentPath + '/clean_data/train.csv', index_col=0)
test = pd.read_csv(currentPath + '/clean_data/test.csv', index_col=0)
corr = pd.read_csv(currentPath + '/clean_data/corr.csv', index_col=0)
varDF = pd.read_csv(currentPath + '/clean_data/var.csv', index_col=0)
with open(currentPath + '/clean_data/sectorMap.pkl', 'rb') as f:
    sectorMap = pickle.load(f)
    
with open(currentPath + '/clean_data/inv_sectorMap.pkl', 'rb') as f:
    inv_sectorMap = pickle.load(f)

with open(currentPath + '/clean_data/ratingMap.pkl', 'rb') as f:
    ratingMap = pickle.load(f)


alpha = 0.05
# portfolio constraint parameters
check_params = {
    "sectorMap": sectorMap,
    "inv_sectorMap": inv_sectorMap,
    "corr_df": corr,
    "risk_series": varDF[str(alpha)],
    "snum_ub": 30,
    "snum_lb": 10,
    "sector_snum_ub": 6,
    "corr_ub": 0.5,
    "risk_all_ub": 0,
    "risk_ind_ub": 0,
    "risk_all_lb": -0.03,
    "risk_ind_lb": -0.05,
    "details": False
}


# dictionary: 
# key - (Stock1, Stock2)
# value - correlation float
corr_pair = check_params["corr_df"].stack()
corr_pair = corr_pair[corr_pair.index.get_level_values(0) != corr_pair.index.get_level_values(1)]
corrMap = corr_pair.to_dict()



# init Gurobi Model
model = Model("Portfolio")
model.ModelSense = GRB.MAXIMIZE


# adding variables
stockList = train.columns.values.tolist()
stocks = model.addVars(
    stockList, 
    obj=(train.iloc[-1] - train.iloc[0]).to_dict(),
    vtype=GRB.BINARY,
    name='Stock-'
)


# Adding constraints
# number of stocks in portfolio
model.addConstr(
    stocks.sum() <= check_params["snum_ub"],
    "NumberOfStocksUB"
)
model.addConstr(
    stocks.sum() >= check_params["snum_lb"],
    "NumberOfStocksLB"
)

# number of stocks in each sector
for sector, sector_stocks in inv_sectorMap.items():
    model.addConstr(
        (sum(stocks[i] for i in sector_stocks) <= check_params["sector_snum_ub"]), 
        "NumberOfSectorStocksUB-%s" % str(sector)
    )

# average correlation should not exceed correlation upper bound
model.addConstr(
   (sum(stocks[s_tuple[0]]*stocks[s_tuple[1]]*j for s_tuple,j in corrMap.items()) <= check_params["corr_ub"] * stocks.sum('*')),
    "AverageOfCorrelationUB"
)

# individual stock risk should not below VaR lower bound
# use VaR at here
model.addConstrs(
    (stocks[s]*var >= check_params["risk_ind_lb"] for s, var in check_params["risk_series"].to_dict().items()),
    "IndividualRiskConstr"
)

# average stock risk should not below VaR lower bound
# use VaR at here
model.addConstr(
    sum(stocks[s]*var for s, var in check_params["risk_series"].to_dict().items()) >= check_params["risk_all_lb"] * stocks.sum('*'),
    "AverageRiskConstr"
)


# run the model
model.write(currentPath + "/portfolio.lp")
model.update()
model.optimize()


# calculate the optimal solution on test set
selectedStocks = []
for i in stockList:
    if abs(stocks[i].X):
        selectedStocks.append(i)
print(selectedStocks)

model.write(currentPath + "/portfolio.mps")
model.write(currentPath + "/portfolio.sol")