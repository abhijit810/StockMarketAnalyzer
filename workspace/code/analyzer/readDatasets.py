import pandas as pd
import os


def def_companies_df():

    NSE = pd.read_csv ('template\\NSE_list_of_companies.csv',index_col='SYMBOL')
    NSE = NSE.rename(columns={"SYMBOL": "SECURITY"})

    BSE = pd.read_csv ('template\\BSE_list_of_companies.csv',index_col='Security Id')
    BSE = BSE.rename(columns={"Security Id": "SECURITY"})
    
    companies_df = pd.concat([NSE, BSE],axis=1)
    return companies_df[['NAME OF COMPANY','Industry','Group']]
