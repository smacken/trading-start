import sys
import os
import os.path, time
import glob
import datetime
import pandas as pd
import numpy as np
import csv
import featuretools as ft
import pyasx
import pyasx.data.companies

def get_holdings(file):
    '''
    holdings can come from export or data feed (simple)
    '''
    simple_csv = False
    with open(file, encoding="utf8") as csvfile:
        hold = csv.reader(csvfile, delimiter=',', quotechar='|')
        line_count = 0
        for row in hold:
            if line_count == 1:
                break
            if 'Code' in row:
                simple_csv = True
            line_count += 1
    if simple_csv:
        holdings = pd.read_csv(file, header=0)
    else:
        holdings = pd.read_csv(file, skiprows=[0, 1, 3], header=0)
        cols = [9, 10]
        holdings.drop(holdings.columns[cols], axis=1, inplace=True)
        holdings = holdings[:-4]
        holdings = holdings.rename(columns={
            'Purchase($)': 'Purchase $', 
            'Last($)': 'Last $', 
            'Mkt Value($)': 'Mkt Value $',
            'Profit / Loss($)': 'Profit/Loss $',
            'Profit / Loss(%)': 'P/L %',
            'Change($)': 'Change $',
            'Chg Value($)':'Value Chg $'
        })
    return holdings
    
def get_holdings_frame(data_path):
    ''' get holdings along a time series '''
    pkl = data_path + 'Holdings.pkl'
    df = None
    holdings_files = [f for f in glob.glob(data_path + 'Holdings*.csv')]
    for f in holdings_files:
        modified = time.ctime(os.path.getmtime(f))
        mod = datetime.datetime.strptime(modified, "%a %b %d %H:%M:%S %Y")
        #print(f)
        df = get_holdings(f)
        df['Date'] = mod.date()
        if 'Code' in df.columns:
            df = df.rename(columns={'Code': 'Tick'})
        df = df[df['Avail Units'].notnull()]
        
        existing = pd.read_pickle(pkl) if os.path.isfile(pkl) else pd.DataFrame() 
        try:
            has_holdings = existing[existing['Date'] == mod.date()] if not existing.empty else None
            if not existing.empty and has_holdings.Tick.count() > 0:
                continue
            df = df.append(existing, ignore_index=True)
            df.to_pickle(pkl)
        except Exception as ex:
            print('no pkl exists', str(ex))
        
    df = df.sort_values(by=['Date', 'Tick'], ascending=False)
    return df

def holdings(data_path, latest=True):
    ''' get the pickled holding data set '''
    holding = pd.read_pickle(f'{data_path}Holdings.pkl')
    holding['index'] = holding.index
    return holding if not latest else holding[holding.Date == holding.Date.max()]

def get_transactions(file):
    trans = pd.read_csv(file)
    trans = trans.rename(columns={
        'Detail': 'Details',
        'Credit ($)':'Credit($)',
        'Debit ($)':'Debit($)',
        'Balance ($)':'Balance($)'
        })
    trans = trans.loc[trans.Details.str.startswith('B', na=False) | trans.Details.str.startswith('S', na=False)]
    #del trans['Type']
    trans.drop(trans.columns[-1], axis=1)
    trans["Qty"] = trans["Details"].str.split(' ').str[1]
    trans["Tick"] = trans["Details"].str.split(' ').str[2]
    trans["Price"] = trans["Details"].str.split(' ').str[4]
    trans["Type"] = trans.apply(lambda x: 'Sell' if str.startswith(x["Details"], 'S') else "Buy", axis=1)
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
        df = df.loc[:,~df.columns.duplicated()]
        try:
            existing = pd.read_pickle(pkl)
            existing = existing.rename(columns={
                'Detail': 'Details',
                'Credit ($)':'Credit($)',
                'Debit ($)':'Debit($)',
                'Balance ($)':'Balance($)'
                })
            drop_index = []
            for index, row in df.iterrows():
                has_existing = existing[existing['Reference'] == row['Reference']]
                if has_existing.empty:
                    continue
                drop_index.append(index)
            if len(drop_index) > 0:
                #print(drop_index)
                df.drop(drop_index, inplace=True)
            df = df.append(existing, ignore_index=True)
            #print(len(df.index))
        except Exception as e:
            print('no pkl exists', str(e))
        df.to_pickle(pkl)
    
    df = df.sort_values(by=['Date'], ascending=False)
    df['index'] = df.index
    return df

def get_dividends(df):
    ''' get dividends from transaction frame '''
    div = df[df['Details'].str.contains('Direct Credit') | df['Details'].str.contains('Credit Interest')]
    div = div[div['Details'].str.contains('COMMONWEALTH')==False]
    div["Symbol"] = div["Details"].str.split(' ').str[3]
    df['Date'] = df['Date'].astype('datetime64[ns]')
    df = df.reindex(index=df.index[::-1])
    df['Sum'] = df['Amount'].cumsum()
    return div

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
    price_data['index'] = price_data.index
    return price_data

def get_companies_frame(data_path):
    ''' company details data frame '''

    etf_data = f'{data_path}etf.json'
    etf = pd.read_json(etf_data)
    etf = etf.loc[1:]
    etf_codes = etf['ASX Code'].tolist()

    company_pkl = f'{data_path}Companies.pkl'
    trans_pkl = f'{data_path}Transactions.pkl'
    trans = pd.read_pickle(trans_pkl)
    company_frame = None
    
    for tick in trans.Tick.unique().tolist():
        
        if tick in etf_codes:
            continue
        
        try:
            company = pd.read_pickle(company_pkl)
        except Exception as ex:
            print(ex)
            company_info = pyasx.data.companies.get_company_info(tick)
            company = pd.DataFrame([company_info])
            share = pd.DataFrame([company_info['primary_share']])
            company = company.merge(share, on='Tick')
            company['Date'] = pd.to_datetime('today')
            company.to_pickle(company_pkl)

        #display(company[company.Tick == tick])
        if company[company.Tick == tick].empty:
            company_info = pyasx.data.companies.get_company_info(tick)
            company_df = pd.DataFrame([company_info])
            share = pd.DataFrame([company_info['primary_share']])
            company_df = company_df.merge(share, on='Tick')
            company_df['Date'] = pd.to_datetime('today')
            company = company.append(company_df)
            company_frame = company if company_frame is None or company_frame.empty else company_frame.append(company)
        else:
            company_frame = company
    
    company_frame.drop_duplicates(['Tick', 'Date'], keep='first', inplace=True)
    company_frame.rename(columns={'Tick': 'Tick'}, inplace=True)
    company_frame['DateIndex'] = company_frame['Date'].apply(lambda x: x.strftime('%y-%m-%d'))
    #company_frame['year_low_date'] = company_frame['year_low_date'].apply(lambda x: x.strftime('%y-%m-%d'))
    #company_frame['year_high_date'] = company_frame['year_high_date'].apply(lambda x: x.strftime('%y-%m-%d'))
    company_frame = company_frame.reset_index(drop=True)
    company_frame['index'] = company_frame.index
    company_frame.to_pickle(company_pkl)
    return company_frame

def get_entityset(holding_data, price_data, trans_data, company_data):
    ''' Construct an entityset data model from different data frames '''

    company_data = company_data.drop(['listing_date', 'delisting_date', 'last_trade_date', 'indices'], axis=1)

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
    es = es.entity_from_dataframe(entity_id="companies",
                                    dataframe=company_data,
                                    index='index',
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
    holdings_companies = ft.Relationship(es["holdings"]["Tick"], es["companies"]["Tick"])
    es = es.add_relationship(holdings_companies)
    holdings_prices = ft.Relationship(es["holdings"]["Tick"], es["prices"]["Tick"])
    es = es.add_relationship(holdings_prices)
    return es
