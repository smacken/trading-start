'''
 trading start data importer
'''
import os, json, sys
from pathlib import Path
import data

if len(sys.argv) < 2:
    sys.exit('Usage: %s config-path' % sys.argv[0])

if not os.path.exists(sys.argv[1]):
    sys.exit('ERROR: Database %s was not found!' % sys.argv[1])

pwd = sys.argv[1]
root = Path(pwd).parent
data_path = ''
print('building dataset')

with open(os.path.join(root, 'config.json')) as json_data:
    d = json.load(json_data)
    data_path = d['destinationPath']

print('data path: ', data_path)
try:
    trans_data = data.get_transaction_frame(data_path)
    trans_data['index'] = trans_data.index
    
    print('holdings data')
    holding_data = data.get_holdings_frame(data_path)
    holding_data = holding_data.rename(columns={'Code': 'Tick'})
    holding_data['index'] = holding_data.index
    holding_data = holding_data[holding_data.Date == holding_data.Date.max()]

    print('account data')
    account_data = data.get_account_frame(data_path)
    price_data = data.get_price_frame(data_path)
    company_data = data.get_companies_frame(data_path)

    es = data.get_entityset(holding_data, price_data, trans_data, company_data)
    print(es)
except Exception as ex:
    print(str(ex))