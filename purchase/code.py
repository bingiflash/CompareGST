import pandas as pd

gov_column_names = ['GSTIN of supplier', 'Trade/Legal name', 'Invoice number', 'Invoice type', 'Invoice Date', 'Invoice Value(₹)', 'Place of supply', 'Supply Attract Reverse Charge', 'Rate(%)', 'Taxable Value (₹)', 'Integrated Tax(₹)', 'Central Tax(₹)', 'State/UT Tax(₹)', 'Cess(₹)', 'GSTR-1/IFF/GSTR-5 Period', 'GSTR-1/IFF/GSTR-5 Filing Date', 'ITC Availability', 'Reason', 'Applicable % of Tax Rate', 'Source', 'IRN', 'IRN Date']

raw_local = pd.read_excel("local.xls",sheet_name="b2b")
raw_gov = pd.read_excel("gov.xlsx",sheet_name="B2B",skiprows=5, names=gov_column_names)

local = raw_local[['GSTIN/UIN of Recipient', 'Invoice Number', 'Invoice date', 'Invoice Value', 'Rate', 'Taxable Value']]
gov = raw_gov[['GSTIN of supplier', 'Invoice number', 'Invoice Date', 'Invoice Value(₹)', 'Rate(%)', 'Taxable Value (₹)']]

unique_column_names = ['GSTIN',  'I-Number','I-Date','I-Value','Tax-Rate','Taxable-Value']
local.columns = unique_column_names
gov.columns = unique_column_names

local = local[['I-Date','GSTIN','I-Number','I-Value','Taxable-Value','Tax-Rate']]
gov = gov[['I-Date','GSTIN','I-Number','I-Value','Taxable-Value','Tax-Rate']]

local[['I-Value','Taxable-Value','Tax-Rate']] = local[['I-Value','Taxable-Value','Tax-Rate']].astype(float)
local['I-Date'] = pd.to_datetime(local['I-Date'])

gov[['I-Value','Taxable-Value','Tax-Rate']] = gov[['I-Value','Taxable-Value','Tax-Rate']].astype(float)
gov['I-Date'] = pd.to_datetime(gov['I-Date'])

local_merge = pd.merge(local, gov, how='left', indicator=True)
local_merge = local_merge.sort_values(by=['I-Date','GSTIN','I-Number'])

gov_merge = pd.merge(gov, local, how='left', indicator=True)
gov_merge = gov_merge.sort_values(by=['I-Date','GSTIN','I-Number'])

l_b_g_s = (local_merge[local_merge['_merge']!='both']).to_string(index=False)
g_b_l_s = (gov_merge[gov_merge['_merge']!='both']).to_string(index=False)

f = open('results.txt','w')
f.write('\n\n')
f.write('----------------------Local but not gov-------------------------------------\n')
f.write(l_b_g_s)
f.write('\n----------------------------------------------------------------------------')

f.write('\n\n')
f.write('----------------------Gov but not local-------------------------------------\n')
f.write(g_b_l_s)
f.write('\n----------------------------------------------------------------------------')

f.close()