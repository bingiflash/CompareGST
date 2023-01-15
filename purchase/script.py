import pandas as pd

gov_column_names = ['GSTIN of supplier', 'Trade/Legal name', 'Invoice number', 'Invoice type', 'Invoice Date', 'Invoice Value(₹)', 'Place of supply', 'Supply Attract Reverse Charge', 'Rate(%)', 'Taxable Value (₹)', 'Integrated Tax(₹)', 'Central Tax(₹)', 'State/UT Tax(₹)', 'Cess(₹)', 'GSTR-1/IFF/GSTR-5 Period', 'GSTR-1/IFF/GSTR-5 Filing Date', 'ITC Availability', 'Reason', 'Applicable % of Tax Rate', 'Source', 'IRN', 'IRN Date']

loc_column_names = ['Date', 'V-Code', 'BillNo', 'Particulars','GSTIN', 'BasicValue','CGST','SGST','IGST','TotGST','Cess','Ref.No','Tax%','RefDate']

raw_gov = pd.read_excel("gov.xlsx",sheet_name="B2B",skiprows=5, names=gov_column_names)
raw_loc = pd.read_excel("local.xlsx", header=None, names=loc_column_names)

# create a new column invoice number in local data with V-Code and BillNo
raw_loc['Invoice number'] = raw_loc['V-Code'].astype(str) + '/' +raw_loc['BillNo'].astype(str)

cdnr_column_names = ['GSTIN of supplier','Trade/Legal name','Note number','Note type','Note Supply type','Note date','Note Value (₹)', 'Place of supply','Supply Attract Reverse Charge','Rate(%)','Taxable Value (₹)','Integrated Tax(₹)','Central Tax(₹)','State/UT Tax(₹)','Cess(₹)','GSTR-1/IFF/GSTR-5 Period','GSTR-1/IFF/GSTR-5 Filing Date','ITC Availability','Reason','Applicable % of Tax Rate','Source','IRN','IRN Date']
raw_gov_cdnr = pd.read_excel("gov.xlsx",sheet_name="B2B-CDNR",skiprows=6, names=cdnr_column_names)

from collections import defaultdict

gstin_to_name = defaultdict(str)
for i in range(len(raw_gov)):
    gstin_to_name[raw_gov['GSTIN of supplier'][i]] = raw_gov['Trade/Legal name'][i]

gov_cdnr = raw_gov_cdnr[['GSTIN of supplier','Note number','Note date','Taxable Value (₹)','Integrated Tax(₹)','Central Tax(₹)','State/UT Tax(₹)']]
gov_cdnr

gov = raw_gov[['GSTIN of supplier', 'Invoice number', 'Invoice Date', 'Taxable Value (₹)', 'Integrated Tax(₹)', 'Central Tax(₹)', 'State/UT Tax(₹)']]
loc_temp = raw_loc[['GSTIN', 'Invoice number', 'Date', 'BasicValue', 'CGST','SGST','IGST']]

unique_column_names = ['GSTIN',  'I-Number','I-Date','I-Value','CGST','SGST','IGST']
loc_temp.columns = unique_column_names
gov.columns = unique_column_names

loc_cdnr = loc_temp[loc_temp['I-Value'] < 0]
loc = loc_temp[loc_temp['I-Value'] > 0]

loc_cdnr['I-Value'] = loc_cdnr['I-Value'].apply(lambda x: -x if x < 0 else x)
loc_cdnr['CGST'] = loc_cdnr['CGST'].apply(lambda x: -x if x < 0 else x)
loc_cdnr['SGST'] = loc_cdnr['SGST'].apply(lambda x: -x if x < 0 else x)
loc_cdnr['IGST'] = loc_cdnr['IGST'].apply(lambda x: -x if x < 0 else x)

loc.reset_index(drop=True, inplace=True)
loc_cdnr.reset_index(drop=True, inplace=True)

loc_summary = loc.groupby('GSTIN', as_index=False)['I-Value', 'CGST', 'SGST', 'IGST'].sum()
gov_summary = gov.groupby('GSTIN', as_index=False)['I-Value', 'CGST', 'SGST', 'IGST'].sum()

summary_merged = pd.merge(loc_summary, gov_summary, on='GSTIN', how='outer', suffixes=('_local', '_gov'))
summary_merged.fillna(0, inplace=True)
# is_same True if I_Value_local and I_Value_gov differ by 10 rupees or less and sum of cgst, sgst, igst differ by 10 rupees or less
summary_merged['is_same'] = (abs(summary_merged['I-Value_local'] - summary_merged['I-Value_gov']) <= 10) & (abs(summary_merged['CGST_local'] + summary_merged['SGST_local'] + summary_merged['IGST_local'] - summary_merged['CGST_gov'] - summary_merged['SGST_gov'] - summary_merged['IGST_gov']) <= 10)
summary_merged['is_same'] = summary_merged['is_same'].apply(lambda x: 'Yes' if x else 'No')
# filter out rows where is_same is No into a new dataframe
non_matching = summary_merged[summary_merged['is_same'] == 'No']
# add name column
non_matching['Name'] = non_matching['GSTIN'].apply(lambda x: gstin_to_name[x])

gstin_list = non_matching['GSTIN'].tolist()

non_matching_loc = loc[loc['GSTIN'].isin(gstin_list)]
non_matching_gov = gov[gov['GSTIN'].isin(gstin_list)]

partial_non_matching_loc = non_matching_loc[['GSTIN','I-Value']]
partial_non_matching_gov = non_matching_gov[['GSTIN','I-Value']]

floored_partial_nm_loc = partial_non_matching_loc.copy()
floored_partial_nm_loc['I-Value'] = partial_non_matching_loc['I-Value'].apply(lambda x: round(x,-1))

floored_partial_nm_gov = partial_non_matching_gov.copy()
floored_partial_nm_gov['I-Value'] = partial_non_matching_gov['I-Value'].apply(lambda x: round(x,-1))

# add a column to floored_partial_nm_loc and floored_partial_nm_gov that is the same as the index
floored_partial_nm_loc['index'] = floored_partial_nm_loc.index
floored_partial_nm_gov['index'] = floored_partial_nm_gov.index

loc_also_gov = pd.merge(floored_partial_nm_loc, floored_partial_nm_gov, how='inner', on=['GSTIN','I-Value'])
intersection = set(loc_also_gov['index_x'].tolist())
loc_only = set(floored_partial_nm_loc.index.tolist())
loc_but_gov_indices = loc_only-intersection
loc_but_gov = non_matching_loc[non_matching_loc.index.isin(loc_but_gov_indices)]

gov_also_loc = pd.merge(floored_partial_nm_gov, floored_partial_nm_loc, how='inner', on=['GSTIN','I-Value'])
intersection = set(gov_also_loc['index_x'].tolist())
gov_only = set(floored_partial_nm_gov.index.tolist())
gov_but_loc_indices = gov_only-intersection
gov_but_loc = non_matching_gov[non_matching_gov.index.isin(gov_but_loc_indices)]

gstin_list = set(non_matching['GSTIN'].tolist()).union(set(non_matching['GSTIN'].tolist()))

# sort by gstin and i-value
loc_but_gov.sort_values(by=['GSTIN','I-Value'], inplace=True)
gov_but_loc.sort_values(by=['GSTIN','I-Value'], inplace=True)

tab_len = 40
for gstin in gstin_list:
    print(gstin, '-', gstin_to_name[gstin])
    print("Local but not Gov:"," "*60,"Gov but not Local:")
    for i in range(0, max(len(loc_but_gov[loc_but_gov['GSTIN'] == gstin]), len(gov_but_loc[gov_but_loc['GSTIN'] == gstin]))):
        try:
            row = loc_but_gov[loc_but_gov['GSTIN'] == gstin].iloc[i]
            print(row['I-Date'], row['I-Number'], row['I-Value'], row['CGST'], row['SGST'], row['IGST'], sep=" | ", end=" "*tab_len)
        except:
            print(" "*tab_len, end=" "*tab_len)
        try:
            row = gov_but_loc[gov_but_loc['GSTIN'] == gstin].iloc[i]
            print(row['I-Date'], row['I-Number'], row['I-Value'], row['CGST'], row['SGST'], row['IGST'], sep=" | ")
        except:
            print(" "*tab_len)
    print("--------------------"," "*60,"--------------------\n\n")