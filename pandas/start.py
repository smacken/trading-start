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
holding_data = data.get_holdings_frame(data_path)
account_data = data.get_account_frame(data_path)

es = get_entityset(holding_data, price_data, trans_data)