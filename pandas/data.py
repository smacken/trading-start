import sys
import os
import os.path, time
import glob
import datetime
import pandas as pd
import numpy as np
import csv
import featuretools as ft

def get_holdings(file):
    '''
    holdings can come from export or data feed (simple)
    '''
    simple_csv = False;
    with open(file, encoding="utf8") as csvfile:
        hold = csv.reader(csvfile, delimiter=',', quotechar='|')
        line_count = 0
        for row in hold: 
            if line_count == 1:
                break
            if 'Code' in row:
                simple_csv = True
            line_count+=1
    if simple_csv:
        holdings = pd.read_csv(file, header=0)
    else:
        holdings = pd.read_csv(file, skiprows=[0, 1, 3], header=0)
        cols = [9, 10, 11]
        holdings.drop(holdings.columns[cols],axis=1,inplace=True)
        holdings = holdings[:-4]
    return holdings
    
def get_holdings_frame(data_path):
    ''' current holdings data frame'''
    pkl = data_path + 'Holdings.pkl'
    df = None
    holdings_files = [f for f in glob.glob(data_path + 'Holdings*.csv')]
    for f in holdings_files:
        modified = time.ctime(os.path.getmtime(f))
        mod = datetime.datetime.strptime(modified, "%a %b %d %H:%M:%S %Y")
        df = get_holdings(f)
        df['Date'] = mod.date()
        df = df[df['Avail Units'].notnull()]
        try:
            existing = pd.read_pickle(pkl)
            has_holdings = existing[existing['Date'] == mod.date()]
            if has_holdings.Code.count() > 0:
                continue
            df = df.append(existing, ignore_index=True)
        except Exception as ex:
            print('no pkl exists', str(ex))
        df.to_pickle(pkl)
    
    df = df.sort_values(by=['Date', 'Code'], ascending=False)
    return df

def get_transactions(file):
    trans = pd.read_csv(file)
    trans = trans.loc[trans['Type'] == 'Contract']
    del trans['Type']
    trans.drop(trans.columns[-1], axis=1)
    trans["Qty"] = trans["Detail"].str.split(' ').str[1]
    trans["Tick"] = trans["Detail"].str.split(' ').str[2]
    trans["Price"] = trans["Detail"].str.split(' ').str[4]
    trans["Type"] = trans.apply(lambda x: 'Sell' if str.startswith(x["Detail"], 'S') else "Buy", axis=1)
    trans['Date'] = pd.to_datetime(trans['Date'], format='%d/%m/%Y')
    trans.drop(trans.columns[5], axis=1, inplace=True)
    trans.sort_index(ascending=False, inplace=True)
    trans.sort_values('Date', ascending=False)
    return trans

def get_transaction_frame(data_path):
    ''' build a data frame from all transaction files'''
    pkl = f'{data_path}Transactions.pkl'
    df = None
    files = [f for f in glob.glob(data_path + 'Transactions*.csv')]
    for f in files:
        modified = time.ctime(os.path.getmtime(f))
        mod = datetime.datetime.strptime(modified, "%a %b %d %H:%M:%S %Y")
        #print(mod.date())
        df = get_transactions(f)
        try:
            existing = pd.read_pickle(pkl)
            # drop all existing rows by reference
            drop_index = []
            for index, row in df.iterrows():
                has_existing = existing[existing['Reference'] == row['Reference']]
                if has_existing.empty:
                    continue
                drop_index.append(index)
            if len(drop_index) > 0:
                df.drop(drop_index, inplace=True)
            df = df.append(existing, ignore_index=True)
            #print(len(df.index))
        except Exception as e:
            print('no pkl exists', str(e))
        df.to_pickle(pkl)
    
    if df is None:
        return pd.DataFrame()
    df = df.sort_values(by=['Date'], ascending=False)
    df['index'] = df.index
    return df

def get_account_transactions(file):
    columns = ['Date', 'Amount', 'Details', 'Balance']
    account = pd.read_csv(file, header=None, names=columns, dayfirst=True, parse_dates=['Date'])
    return account

def get_account_frame(data_path):
    files = [f for f in glob.glob(f'{data_path}Account*.csv')]
    df = None
    for f in files:
        modified = time.ctime(os.path.getmtime(f))
        mod = datetime.datetime.strptime(modified, "%a %b %d %H:%M:%S %Y")
        #print(mod.date())
        df = get_account_transactions(f)
        pkl = f'{data_path}Account.pkl'
        try:
            existing = pd.read_pickle(pkl)
            drop_index = []
            for index, row in df.iterrows():
                has_existing = existing[(existing['Date'] == row['Date']) & (existing['Amount'] == row['Amount'])]
                if has_existing.empty:
                    continue
                drop_index.append(index)
            if len(drop_index) > 0:
                df.drop(drop_index, inplace=True)
            df = df.append(existing, ignore_index=True)
        except Exception as e:
            print('no pkl exists', str(e))
        df.to_pickle(pkl)
    
    df = df.sort_values(by=['Date'], ascending=False)
    return df

def get_price_frame(data_path):
    ''' get price time-series ticker data ohlc '''
    price_data = pd.read_pickle(f'{data_path}Prices.pkl')
    price_data.drop_duplicates(subset=['Date', 'Tick'], keep='first', inplace=True)
    return price_data

def get_entityset(holding_data, price_data, trans_data):
    ''' entityset '''
    es = ft.EntitySet(id="trading")
    es = es.entity_from_dataframe(entity_id="prices",
                                    dataframe=price_data,
                                    time_index="Date",
                                    index='index',
                                    variable_types={"Tick": ft.variable_types.Categorical})
    es = es.entity_from_dataframe(entity_id="holdings",
                                    dataframe=holding_data,
                                    index='Tick',
                                    time_index="Date",
                                    variable_types={"Tick": ft.variable_types.Categorical})
    es = es.entity_from_dataframe(entity_id="transactions",
                                    dataframe=trans_data,
                                    index='index',
                                    time_index="Date",
                                    variable_types={"Tick": ft.variable_types.Categorical, 
                                                    "Type": ft.variable_types.Categorical})
    holdings_trans = ft.Relationship(es["holdings"]["Tick"], es["transactions"]["Tick"])
    es = es.add_relationship(holdings_trans)
    holdings_prices = ft.Relationship(es["holdings"]["Tick"], es["prices"]["Tick"])
    es = es.add_relationship(holdings_prices)
    return es
