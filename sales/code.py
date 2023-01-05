import pandas as pd

raw_local = pd.read_excel("local.xls",sheet_name="b2b")
raw_gov = pd.read_excel("gov.xlsx",sheet_name="b2b",skiprows=3)

local = raw_local[['GSTIN/UIN of Recipient', 'Invoice Number', 'Invoice date', 'Invoice Value', 'Rate', 'Taxable Value']]
gov = raw_gov[['GSTIN/UIN of Recipient', 'Invoice Number', 'Invoice date', 'Invoice Value', 'Rate', 'Taxable Value']]

unique_column_names = ['GSTIN',  'I-Number','I-Date','I-Value','Tax-Rate','Taxable-Value']

local.columns = unique_column_names
gov.columns = unique_column_names

local[['I-Value','Tax-Rate']] = local[['I-Value','Tax-Rate']].astype(float)
local['Taxable-Value'] = local['Taxable-Value'].astype(int)
local['I-Date'] = pd.to_datetime(local['I-Date'])

gov['I-Date'] = pd.to_datetime(gov['I-Date'])
gov['Taxable-Value'] = gov['Taxable-Value'].astype(int)

local_merge = pd.merge(local, gov, how='left', indicator=True)
local_merge = local_merge.sort_values(by=['I-Date','I-Number'])

gov_merge = pd.merge(gov, local, how='left', indicator=True)
gov_merge = gov_merge.sort_values(by=['I-Date','I-Number'])

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