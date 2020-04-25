import itertools
import numpy as np
import pandas as pd
import warnings
warnings.filterwarnings('ignore')


# self-defined functions
from helper import *


def generate_start_point(stockList, inv_sectorMap, n, params, seed=100):
    sectorList = list(inv_sectorMap.keys())
    check = False
    if seed is not None:
        np.random.seed(seed=seed)
    
    while not check:
        series = pd.Series(0, index=stockList)
        
        
        sectorAssignMap = {s: int(n/len(sectorList)) for s in sectorList}
        for i in range(n%len(sectorList)):
            sectorAssignMap[ sectorList[i] ] += 1
        
        
        for sector, n_sample in sectorAssignMap.items():
            sample_stocks = list(np.random.choice(inv_sectorMap[sector], int(n_sample), replace=False))
            series.loc[sample_stocks] = 1

        check = checkFeasible(series, **params)
    return series



'''
(i, j): change stock i to stock j => convert stock i from 1 to 0 and stock j from 0 to 1
(i, ""): remove stock i from portfolio => convert stock i from 1 to 0
("", j): add stock j into portfolio => convert stock j from 0 to 1

tabuList = [
    ('A', 'C'), ('B', 'D'), ('E', ), (, 'D')
]
'''

def find_neighbors(series, return_df, params, neighbor_size=10, seed=100):
    if seed is not None:
        np.random.seed(seed=seed)
    
    selectStocks = series.iloc[series.nonzero()].index
    unselectStocks = series.loc[series == 0].index
    neighborList = []
    
    # exchange two stocks
    neighborList.extend(list(zip(
        np.random.choice(selectStocks, size=int(neighbor_size/3), replace=True), 
        np.random.choice(unselectStocks, size=int(neighbor_size/3), replace=True)
    )))
    
    # removing stocks from the portfolio
    if len(selectStocks) > params['snum_lb']:
        neighborList.extend([
            (i,"") for i in np.random.choice(selectStocks, size=int(neighbor_size/3), replace=False)
        ])

    # adding stocks to the portfolio
    if len(selectStocks) < params['snum_ub']:
        neighborList.extend([
            ("",j) for j in np.random.choice(unselectStocks, size=int(neighbor_size/3), replace=False)
        ])
        
        
    # evaluate all neighbors
    neighborSearch = pd.Series([])

    for exc in neighborList:
        tmp = series.copy(deep=True)
        return_change = 0
        # if the first position (removing from the portfolio) has a stock
        if exc[0]: 
            tmp.loc[exc[0]] = 0
            return_change += -1 * getReturn(exc[0], return_df)
        # if the second position (adding to the portfolio) has a stock
        if exc[1]:
            tmp.loc[exc[1]] = 1
            return_change += 1 * getReturn(exc[1], return_df)
            
        # check the feasibility of the neighbor
        if checkFeasible(tmp, **params):
            neighborSearch = neighborSearch.append(
                pd.Series([return_change], index=[exc])
            )

    neighborSearch.sort_values(inplace=True, ascending=False)
    try:
        neighbor_series = series.copy(deep=True)
        if neighborSearch.index[0][0]: 
            neighbor_series.loc[neighborSearch.index[0][0]] = 0
        if neighborSearch.index[0][1]:
            neighbor_series.loc[neighborSearch.index[0][1]] = 1
        
        return {
            'best_neighbor': neighborSearch.index[0],
            'best_neighbor_series': neighbor_series, 
            'best_neighbor_perf': getPortfolioReturn(neighbor_series, return_df),
            'neighbor_set': neighborSearch
        }
    except: 
        return {
            'best_neighbor': "",
            'best_neighbor_series': pd.Series(0, index=series.index),
            'best_neighbor_perf': float("-inf"),
            'neighbor_set': neighborSearch
        }
    
    
def asp(org_cand, new_cand, return_df, improve_level=0.05):
    if getPortfolioReturn(new_cand, return_df) - getPortfolioReturn(org_cand, return_df) > improve_level:
        return True
    return False