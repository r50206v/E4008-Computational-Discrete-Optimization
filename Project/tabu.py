import sys
import numpy as np
import pandas as pd
from tqdm import tqdm
from copy import deepcopy
import warnings
warnings.filterwarnings('ignore')


# self-defined functions
from helper import *
from tabu_helper import *


def tabu_search(
    return_df, params, tabu_list_size=20, iterations_times=1000, early_stop=30, 
    neighbor_size=50, asp_improve_level=-3, seed=1,
    test_return_df=None
):
    # initialize
    best_perfList = []
    best_test_perfList = []
    cand_perfList = []
    cand_test_perfList = []

    best_perf = float("-inf")
    best_series = None
    
    iterations_times_copy = deepcopy(iterations_times)
    
    
    # find a feasible starting point 
    cand = generate_start_point(
        return_df.columns.values.tolist(), 
        params["inv_sectorMap"], 
        int((params['snum_ub'] + params['snum_lb'])/2), 
        params,
        seed=seed
    )
    cand_perf = getPortfolioReturn(cand, return_df)
    best_perfList.append(cand_perf)
    cand_perfList.append(cand_perf)
    
    if isinstance(test_return_df, pd.DataFrame):
        cand_test_perfList.append(getPortfolioReturn(cand, test_return_df))
        best_test_perfList.append(getPortfolioReturn(cand, test_return_df))
    tabuSeries = pd.Series(0, index=list(range(tabu_list_size)), name='ExchangeRule')
    current_early_stop = deepcopy(early_stop)
    
    
    # tqdm records the progress
    with tqdm(total=iterations_times) as pbar:



        while iterations_times > 0 and current_early_stop > 0:

            # search possible neighbors
            neighborDict = find_neighbors(cand, return_df, params, neighbor_size=neighbor_size, seed=seed)
            # check if there are feasible neighbors in the neighbor set
            if not neighborDict['best_neighbor']:
                sys.stdout.write('TabuStop: no feasible neighbors')
                break

            # check whether the best neighbor is in tabu list
            if neighborDict['best_neighbor'] in tabuSeries.values.tolist():
                # if the best neighbor is in tabu, 
                # we can still change to the neighbor if it meets the aspiration criteria
                if asp(cand, neighborDict['best_neighbor_series'], return_df, improve_level=asp_improve_level):
                    cand = neighborDict['best_neighbor_series']
                    cand_perf = neighborDict['best_neighbor_perf']

            else:
                cand = neighborDict['best_neighbor_series']
                cand_perf = neighborDict['best_neighbor_perf']

                last_element_index = len(tabuSeries.nonzero()[0]) - 1
                tabuSeries.loc[ last_element_index + 1 ] = neighborDict['best_neighbor']
                if len(tabuSeries.nonzero()[0]) > tabu_list_size:
                    tabuSeries = tabuSeries.drop(0).reset_index(drop=True, name='ExchangeRule')

            if cand_perf > best_perf:
                # reset early_stop parameter as the current solution improves
                current_early_stop = deepcopy(early_stop)
                best_perf = cand_perf
                best_series = cand

            else:
                current_early_stop -= 1


            iterations_times -= 1
            best_perfList.append(best_perf)
            cand_perfList.append(cand_perf)
            if isinstance(test_return_df, pd.DataFrame):
                cand_test_perfList.append(getPortfolioReturn(cand, test_return_df))
                best_test_perfList.append(getPortfolioReturn(best_series, test_return_df))


            pbar.update(1)

    return {
        "best_perfList": best_perfList, 
        "cand_perfList": cand_perfList,
        "cand_test_perfList": cand_test_perfList,
        "best_test_perfList": best_test_perfList,
        "best_series": best_series,
        "best_perf": best_perf,
        "iterations": iterations_times_copy - iterations_times + 1,
        "early_stop": current_early_stop
    }