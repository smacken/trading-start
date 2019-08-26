'''
 trading start data importer
'''
import os, json
import os.path
from pathlib import Path
import data

root = Path(os.path.abspath('')).parent
data_path = ''

with open(os.path.join(root, 'config.json')) as json_data:
    d = json.load(json_data)
    data_path = d['destinationPath']

trans_data = data.get_transaction_frame(data_path)
trans_data['index'] = trans_data.index

holding_data = data.get_holdings_frame(data_path)
holding_data = holding_data.rename(columns={'Code': 'Tick'})
holding_data['index'] = holding_data.index
holding_data = holding_data[holding_data.Date == holding_data.Date.max()]

account_data = data.get_account_frame(data_path)
price_data = data.get_price_frame(data_path)

es = data.get_entityset(holding_data, price_data, trans_data)
print(es)