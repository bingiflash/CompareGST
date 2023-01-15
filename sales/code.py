import pandas as pd

raw_gov_xl = pd.ExcelFile('gov.xlsx')

b2b_sheetname = ""
for sheet in raw_gov_xl.sheet_names:
    if "b2b" in sheet:
        b2b_sheetname = sheet

raw_gov = raw_gov_xl.parse(b2b_sheetname, skiprows=3)
raw_local = pd.read_excel("local.xls",sheet_name="b2b")

raw_gov.columns = map(str.lower, raw_gov.columns)
raw_local.columns = map(str.lower, raw_local.columns)

local = raw_local[['gstin/uin of recipient', 'invoice number', 'invoice date', 'invoice value', 'rate', 'taxable value']]
gov = raw_gov[['gstin/uin of recipient', 'invoice number', 'invoice date', 'invoice value', 'rate', 'taxable value']]

unique_column_names = ['GSTIN', 'I-Number','I-Date','I-Value','Tax-Rate','Taxable-Value']

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

l_b_g_s_df = local_merge[local_merge['_merge']!='both']
g_b_l_s_df = gov_merge[gov_merge['_merge']!='both']

l_b_g_s = (l_b_g_s_df).to_string(index=False)
g_b_l_s = (g_b_l_s_df).to_string(index=False)

f = open('results.txt','w')
f.write('\n\n')
f.write(f'----------------------Local but not gov - {len(l_b_g_s_df.index)}-------------------------------------\n')
f.write(l_b_g_s)
f.write('\n----------------------------------------------------------------------------')

f.write('\n\n')
f.write(f'----------------------Gov but not local - {len(g_b_l_s_df.index)}-------------------------------------\n')
f.write(g_b_l_s)
f.write('\n----------------------------------------------------------------------------')

f.close()