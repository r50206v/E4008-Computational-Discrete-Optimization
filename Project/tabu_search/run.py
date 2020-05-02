import os
import gc
import pickle
import itertools
import numpy as np
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

# self-defined functions
# from helper import *
# from tabu_helper import *
from tabu import tabu_search


currentPath = os.getcwd()
projectPath = currentPath + '/../'
with open(projectPath + '/clean_data/sectorMap.pkl', 'rb') as f:
    sectorMap = pickle.load(f)
    
with open(projectPath + '/clean_data/inv_sectorMap.pkl', 'rb') as f:
    inv_sectorMap = pickle.load(f)

with open(projectPath + '/clean_data/ratingMap.pkl', 'rb') as f:
    ratingMap = pickle.load(f)
    
train = pd.read_csv(projectPath + '/clean_data/train.csv', index_col=0)
test = pd.read_csv(projectPath + '/clean_data/test.csv', index_col=0)
corr = pd.read_csv(projectPath + '/clean_data/corr.csv', index_col=0)
varDF = pd.read_csv(projectPath + '/clean_data/var.csv', index_col=0)

train.index = pd.DatetimeIndex(train.index)
test.index = pd.DatetimeIndex(test.index)


alpha = 0.05
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



### Grid Search
testResult = {}
GridParams = {
    'tabu_list_size': [10, 30, 50], 
    'iterations_times': [100, 200, 300],
    'early_stop': [20, 50, float("inf")], 
    'neighbor_size': [50, 100, 300], 
    'asp_improve_level': [-1, 1, 5], 
}
params = {
    'return_df': train, 
    'test_return_df': test,
    'params': check_params, 
}

for vs in list(itertools.product(*tuple(GridParams.values()))):
    print(vs)
    g_param = {**params, **{k: v for k, v in zip(GridParams.keys(), vs)}}
    testResult[vs] = tabu_search(**g_param)
    gc.collect()
    
with open(projectPath + '/result/grid_search.pkl', 'wb') as f:
    pickle.dump(testResult, f, pickle.HIGHEST_PROTOCOL)