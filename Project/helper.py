import os
import itertools
import importlib
import numpy as np
import pandas as pd
import warnings
warnings.filterwarnings('ignore')


def checkStocksNum(series, ub, lb=None):
    if not lb:
        lb = 0
    if series.sum() < lb or series.sum() > ub:
        return False
    return True


def checkSectorStocksNum(series, sectorMap, ub, lb=None, details=False):
    if not lb:
        lb = 0
        
    countSec = {k: 0 for k in set(list(sectorMap.values()))}
    for ind, val in series.iloc[series.nonzero()].iteritems():
        if val:
            countSec[ sectorMap[ind] ] += 1
            
    if details:
            print(countSec)
    
    if any(i<lb or i>ub for i in list(countSec.values())):
        return False
    
    return True


def checkCorr(series, corr_df, ub, lb=None, details=False):
    if not lb:
        lb = -1
        
    corrMap = {}
    selectStocks = list(series.iloc[series.nonzero()].index)
    for i, j in itertools.product(selectStocks, selectStocks):
        if i != j and corrMap.get((i, j)) is None and corrMap.get((j, i)) is None:
            corrMap[(i, j)] = abs(corr_df.loc[i, j])
            
    sumCorr = sum(list(corrMap.values()))
    avgCorr = sumCorr / len(corrMap.keys())
    
    if details:
        print({'avgCorr': avgCorr, 'sumCorr': sumCorr})
        print(corrMap)
    
    if avgCorr < lb or avgCorr > ub:
        return False
    return True


def checkSD(series, std_series, all_ub=0.03, ind_ub=0.05, all_lb=0, ind_lb=0, details=False):
    selectStocks = list(series.iloc[series.nonzero()].index)
    stdStocks_series = std_series.loc[selectStocks]

    if details:
        print('avg std: ', stdStocks_series.mean())
        print(stdStocks_series)
    
    if (stdStocks_series < ind_lb).sum() or (stdStocks_series > ind_ub).sum():
        return False
    
    if stdStocks_series.mean() < all_lb or stdStocks_series.mean() > all_ub:
        return False
    return True


def checkVaR(series, var_series, all_lb=-0.03, ind_lb=-0.05, all_ub=0, ind_ub=0, details=False):
    selectStocks = list(series.iloc[series.nonzero()].index)
    VaRStocks_series = var_series.loc[selectStocks]

    if details:
        print('avg std: ', VaRStocks_series.mean())
        print(VaRStocks_series)
    
    if (VaRStocks_series < ind_lb).sum():
        return False
    
    if VaRStocks_series.mean() < all_lb:
        return False
    return True


def checkFeasible(
    series, sectorMap, inv_sectorMap, corr_df, risk_series, 
    snum_ub, sector_snum_ub, 
    corr_ub, risk_all_ub, risk_ind_ub, risk_all_lb, risk_ind_lb,
    risk='var', snum_lb=None, sector_snum_lb=None, corr_lb=None,
    details=False
):
    if risk in ['sd', 'var']:
        risk_func_name = 'checkVaR'
        if risk == 'sd':
            risk_func_name = 'checkSD'
    else:
        raise Error('risk function should be either var or sd\n')
        
        
    pkg = importlib.import_module('helper')
    risk_func = getattr(pkg, risk_func_name)
    cond1 = checkStocksNum(series, snum_ub, snum_lb)
    cond2 = checkSectorStocksNum(series, sectorMap, sector_snum_ub, sector_snum_lb, details)
    cond3 = checkCorr(series, corr_df, corr_ub, corr_lb, details)
    cond4 = risk_func(series, risk_series, all_ub=risk_all_ub, ind_ub=risk_ind_ub, all_lb=risk_all_lb, ind_lb=risk_ind_lb, details=details)
    
    if details:
        print(cond1, cond2, cond3, cond4)

    return cond1 and cond2 and cond3 and cond4


def getReturn(stock, return_series):
    return return_series[stock]


def getPortfolioReturn(series, return_df, details=False):
    if details:
        print(return_df.loc[series.iloc[series.nonzero()].index])
    return return_df.loc[series.iloc[series.nonzero()].index].sum()