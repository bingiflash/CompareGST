import datetime
import pandas as pd

gov_column_names = ['GSTIN of supplier', 'Trade/Legal name', 'Invoice number', 'Invoice type', 'Invoice Date', 'Invoice Value(₹)', 'Place of supply', 'Supply Attract Reverse Charge', 'Rate(%)', 'Taxable Value (₹)', 'Integrated Tax(₹)', 'Central Tax(₹)', 'State/UT Tax(₹)', 'Cess(₹)', 'GSTR-1/IFF/GSTR-5 Period', 'GSTR-1/IFF/GSTR-5 Filing Date', 'ITC Availability', 'Reason', 'Applicable % of Tax Rate', 'Source', 'IRN', 'IRN Date']

loc_column_names = ['Date', 'V-Code', 'BillNo', 'Particulars','GSTIN', 'BasicValue','CGST','SGST','IGST','TotGST','Cess','Ref.No','Tax%','RefDate']

raw_gov = pd.read_excel("gov.xlsx",sheet_name="B2B",skiprows=5, names=gov_column_names)
raw_loc = pd.read_excel("local.xlsx", header=None, names=loc_column_names)

# create a new column invoice number in local data with V-Code and BillNo
raw_loc['Invoice number'] = raw_loc['V-Code'].astype(str) + '/' +raw_loc['BillNo'].astype(str)

cdnr_gov_column_names = ['GSTIN of supplier','Trade/Legal name','Invoice number','Invoice type','Note Supply type','Invoice Date','Invoice Value (₹)', 'Place of supply','Supply Attract Reverse Charge','Rate(%)','Taxable Value (₹)','Integrated Tax(₹)','Central Tax(₹)','State/UT Tax(₹)','Cess(₹)','GSTR-1/IFF/GSTR-5 Period','GSTR-1/IFF/GSTR-5 Filing Date','ITC Availability','Reason','Applicable % of Tax Rate','Source','IRN','IRN Date']
raw_gov_cdnr = pd.read_excel("gov.xlsx",sheet_name="B2B-CDNR",skiprows=5, names=cdnr_gov_column_names)

# In raw_gov_cdnr, if Note Type is Credit Note, then make Taxable Value (₹), Integrated Tax(₹), Central Tax(₹), State/UT Tax(₹) negative
raw_gov_cdnr['Taxable Value (₹)'] = raw_gov_cdnr.apply(lambda x: -x['Taxable Value (₹)'] if x['Invoice type'] == 'Credit Note' else x['Taxable Value (₹)'], axis=1)
raw_gov_cdnr['Integrated Tax(₹)'] = raw_gov_cdnr.apply(lambda x: -x['Integrated Tax(₹)'] if x['Invoice type'] == 'Credit Note' else x['Integrated Tax(₹)'], axis=1)
raw_gov_cdnr['Central Tax(₹)'] = raw_gov_cdnr.apply(lambda x: -x['Central Tax(₹)'] if x['Invoice type'] == 'Credit Note' else x['Central Tax(₹)'], axis=1)
raw_gov_cdnr['State/UT Tax(₹)'] = raw_gov_cdnr.apply(lambda x: -x['State/UT Tax(₹)'] if x['Invoice type'] == 'Credit Note' else x['State/UT Tax(₹)'], axis=1)

raw_gov_cdnr.drop(columns=['Note Supply type'],inplace=True)
raw_gov_and_cdnr = pd.concat([raw_gov, raw_gov_cdnr], ignore_index=True)

gov = raw_gov_and_cdnr[['GSTIN of supplier', 'Invoice number', 'Invoice Date', 'Taxable Value (₹)', 'Central Tax(₹)', 'State/UT Tax(₹)', 'Integrated Tax(₹)']]
loc = raw_loc[['GSTIN', 'Invoice number', 'Date', 'BasicValue', 'CGST','SGST','IGST']]

from collections import defaultdict

gstin_to_name = defaultdict(str)
for i in range(len(raw_gov_and_cdnr)):
    gstin_to_name[raw_gov_and_cdnr['GSTIN of supplier'][i]] = raw_gov_and_cdnr['Trade/Legal name'][i]

unique_column_names = ['GSTIN',  'I_Number','I_Date','I_Value','CGST','SGST','IGST']
loc.columns = unique_column_names
gov.columns = unique_column_names

loc_summary = loc.groupby('GSTIN', as_index=False)['I_Value', 'CGST', 'SGST', 'IGST'].sum()
gov_summary = gov.groupby('GSTIN', as_index=False)['I_Value', 'CGST', 'SGST', 'IGST'].sum()

summary_merged = pd.merge(loc_summary, gov_summary, on='GSTIN', how='outer', suffixes=('_local', '_gov'))
summary_merged.fillna(0, inplace=True)
# is_same True if I_Value_local and I_Value_gov differ by 10 rupees or less and sum of cgst, sgst, igst differ by 10 rupees or less
summary_merged['is_same'] = (abs(summary_merged['I_Value_local'] - summary_merged['I_Value_gov']) <= 10) & (abs(summary_merged['CGST_local'] + summary_merged['SGST_local'] + summary_merged['IGST_local'] - summary_merged['CGST_gov'] - summary_merged['SGST_gov'] - summary_merged['IGST_gov']) <= 10)
summary_merged['is_same'] = summary_merged['is_same'].apply(lambda x: 'Yes' if x else 'No')
# filter out rows where is_same is No into a new dataframe
non_matching = summary_merged[summary_merged['is_same'] == 'No']
# add name column
non_matching['Name'] = non_matching['GSTIN'].apply(lambda x: gstin_to_name[x])

gstin_list = non_matching['GSTIN'].tolist()

non_matching_loc = loc[loc['GSTIN'].isin(gstin_list)]
non_matching_gov = gov[gov['GSTIN'].isin(gstin_list)]

partial_non_matching_loc = non_matching_loc[['GSTIN','I_Value']]
partial_non_matching_gov = non_matching_gov[['GSTIN','I_Value']]

floored_partial_nm_loc = partial_non_matching_loc.copy()
floored_partial_nm_loc['I_Value'] = partial_non_matching_loc['I_Value'].apply(lambda x: round(x,-1))

floored_partial_nm_gov = partial_non_matching_gov.copy()
floored_partial_nm_gov['I_Value'] = partial_non_matching_gov['I_Value'].apply(lambda x: round(x,-1))

# add a column to floored_partial_nm_loc and floored_partial_nm_gov that is the same as the index
floored_partial_nm_loc['index'] = floored_partial_nm_loc.index
floored_partial_nm_gov['index'] = floored_partial_nm_gov.index

loc_also_gov = pd.merge(floored_partial_nm_loc, floored_partial_nm_gov, how='inner', on=['GSTIN','I_Value'])
intersection = set(loc_also_gov['index_x'].tolist())
loc_only = set(floored_partial_nm_loc.index.tolist())
loc_but_gov_indices = loc_only-intersection
loc_but_gov = non_matching_loc[non_matching_loc.index.isin(loc_but_gov_indices)]

gov_also_loc = pd.merge(floored_partial_nm_gov, floored_partial_nm_loc, how='inner', on=['GSTIN','I_Value'])
intersection = set(gov_also_loc['index_x'].tolist())
gov_only = set(floored_partial_nm_gov.index.tolist())
gov_but_loc_indices = gov_only-intersection
gov_but_loc = non_matching_gov[non_matching_gov.index.isin(gov_but_loc_indices)]

gstin_list = set(loc_but_gov['GSTIN'].tolist()).union(set(gov_but_loc['GSTIN'].tolist()))

# drop duplicates
loc_but_gov.drop_duplicates(inplace=True)
gov_but_loc.drop_duplicates(inplace=True)

# sort by gstin and I_Value
loc_but_gov.sort_values(by=['GSTIN','I_Value'], inplace=True)
gov_but_loc.sort_values(by=['GSTIN','I_Value'], inplace=True)


for gstin in gstin_list:
    tot_i_val, tot_cgst, tot_sgst, tot_igst, tot_val = 0, 0, 0, 0, 0
    print("-"*50)
    print(gstin, '-', gstin_to_name[gstin])
    print("-"*50)
    loc_temp = loc_but_gov[loc_but_gov['GSTIN'] == gstin]
    print("Local but not Gov - ", len(loc_temp.index))
    for row in loc_temp.itertuples():
        date = ''
        if isinstance(row.I_Date, str):
            date = datetime.datetime.strptime(row.I_Date, '%d/%m/%Y').strftime('%d/%m/%Y')
        elif isinstance(row.I_Date, datetime.datetime):
            date = row.I_Date.strftime('%d/%m/%Y')
        print("{:10} | {:10} | {:10} | {:10} | {:10} | {:10}".format(date, row.I_Number, row.I_Value, row.CGST, row.SGST, row.IGST))
    
    print("\n")
    gov_temp = gov_but_loc[gov_but_loc['GSTIN'] == gstin]
    print("Gov but not Local - ",len(gov_temp.index))
    for row in gov_temp.itertuples():
        date = ''
        if isinstance(row.I_Date, str):
            date = datetime.datetime.strptime(row.I_Date, '%d/%m/%Y').strftime('%d/%m/%Y')
        elif isinstance(row.I_Date, datetime.datetime):
            date = row.I_Date.strftime('%d/%m/%Y')
        print("{:10} | {:10} | {:10} | {:10} | {:10} | {:10}".format(date, row.I_Number, row.I_Value, row.CGST, row.SGST, row.IGST))
    print('\n\n')
