# import libraries

import numpy as np
import numpy_financial as npf
import pandas as pd
import requests
import json
import datetime
import seaborn as sns
import streamlit as st

st.title("Property Investment Calculator")

st.header("Inputs")

ca1,ca2 = st.columns(2)

with ca1:

    tax_nation = st.radio("Country",["UK","USA"])

with ca2:
    if tax_nation == "UK":

        tax_region = st.radio("Region",["England","Wales","Scotland","N Ireland"])

    else:

        tax_region = st.radio("Region",["Currently not available"])
    
with st.form(key="inputs"):

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.subheader("Appraisal")
        appraisal_term = int(st.number_input('Appraisal period (yrs)',value=10,min_value=0,max_value=100))

        st.subheader("Property Value")
        purchase_price = st.number_input('Purchase Price',value=100000,min_value=1)
        y1_capital_growth = st.number_input("First Year Property Value Growth %")/100
        capital_growth = st.number_input("Ongoing Annual Property Value Growth %")/100
        property_investment = st.number_input("Other Upfront investment",min_value=0)

    with c2:

        st.subheader("Mortgage")
        st.radio("Mortgage Type","")
        LTV = st.number_input("LTV %",min_value=0,max_value=100,value=75)
        starting_mortgage_rate = st.number_input("Starting Mortgage Rate %",min_value=0,value=5)/100
        mortgage_term = int(st.number_input("Fixed Term (yrs)",min_value=1,max_value=25))
        refinance_toggle = st.toggle("Refinance after Fixed Term")
        ongoing_mortgage_rate = st.number_input("Ongoing Mortgage Rate %",min_value=0,value=3)/100
        mortgage_fees_percentage = st.number_input("Mortgage Fees %")/100
        legal_fees_percentage = st.number_input("Legal Fees %",min_value=0,value=1)/100

    with c3:

        st.subheader("Income")
        monthly_income = st.number_input("Monthly Gross Rental Income",value=500,min_value=1)            
        rental_growth = st.number_input("Annual Rental Growth %")/100
        
        st.subheader("Costs")
        mgmt_fee_percentage = st.number_input("Management Fee %",min_value=0,value=10)/100
        other_fee_percentage = st.number_input("Other Costs %",min_value=0)/100
        inflation = st.number_input("Annual Cost Inflation %",value=2)/100

    with c4:

        st.subheader("Tax")
        
        if tax_region == "England":
        
            tax_regime = st.selectbox("Applicable Tax Regime",["No Tax",
                                                    "Personal Basic rate (20%)",
                                                   "Personal Higher rate (40%)",
                                                   "Personal Add'l rate (45%)",
                                                   "Corporation Tax (25%)"])
            
        else:
            
            tax_regime = st.selectbox("Applicable Tax Regime",["Other"])

    st.form_submit_button("Calculate")

if (purchase_price!=0)|(LTV!=0)|(monthly_income!=0):

    mortgage = LTV/100 * purchase_price
    deposit = purchase_price - mortgage
    legal_fees = purchase_price * legal_fees_percentage
    monthly_mgmt_fee = monthly_income * mgmt_fee_percentage
    monthly_other_fee = monthly_income * other_fee_percentage
    mortgage_fees = mortgage * mortgage_fees_percentage
    starting_monthly_mortgage_cost = (mortgage + mortgage_fees) * starting_mortgage_rate / 12
    
    if refinance_toggle == True:
        
        refinance_amount = (purchase_price * (1 + y1_capital_growth) * (1 + capital_growth) ** (mortgage_term - 1)) - purchase_price
        
    else:
        
        refinance_amount = 0
    
    ongoing_monthly_mortgage_cost = (mortgage + refinance_amount + mortgage_fees*2) * ongoing_mortgage_rate / 12
    monthly_pre_tax = monthly_income - monthly_mgmt_fee - monthly_other_fee - starting_monthly_mortgage_cost
    gross_initial_yield = (monthly_income * 12) / purchase_price
    net_initial_yield = (monthly_pre_tax * 12) / purchase_price
    ROI = (monthly_pre_tax * 12) / (deposit + legal_fees)
    cash_return = 1 / ROI
    
else:
    
    print()

cash_flow = pd.DataFrame(columns=["Year","Upfront Costs","Income","Costs","Mortgage"])

for i in range(0,101):
    
    cash_flow.at[i,"Year"] = i

cash_flow["Upfront Costs"] = np.where(cash_flow["Year"]==0,
                     -(deposit+legal_fees+property_investment),
                    0)

cash_flow["Income"] = np.where(cash_flow["Year"]==0,
                              0,
                              monthly_income*12)

for i in range(1,len(cash_flow)):
               
    cash_flow.at[i,"Income"] = cash_flow.at[i,"Income"] * (1+rental_growth)**(cash_flow.at[i,"Year"]-1)

cash_flow["Costs"] = cash_flow["Income"] * -(mgmt_fee_percentage + other_fee_percentage)

for i in range(1,len(cash_flow)):
               
    cash_flow.at[i,"Costs"] = cash_flow.at[i,"Costs"] * (1+(inflation-rental_growth))**(cash_flow.at[i,"Year"]-1)

cash_flow["Mortgage"] = 0

for i in range(1,len(cash_flow)):
    
    if cash_flow.at[i,"Year"] <= mortgage_term:
    
        cash_flow.at[i,"Mortgage"] = -starting_monthly_mortgage_cost*12
        
    else:
        
        cash_flow.at[i,"Mortgage"] = -ongoing_monthly_mortgage_cost*12

  irr_cash_flow = cash_flow.copy()[cash_flow["Year"]<=appraisal_term]

irr_cash_flow["Exit Sale Price"] = np.where(irr_cash_flow["Year"]==appraisal_term,
                     (purchase_price * (1 + y1_capital_growth) * (1 + capital_growth) ** (appraisal_term - 1)) - mortgage,
                    0)

irr_cash_flow["Total Cash Flow"] = irr_cash_flow["Upfront Costs"] + irr_cash_flow["Exit Sale Price"] + irr_cash_flow["Income"] + irr_cash_flow["Costs"] + irr_cash_flow["Mortgage"]

payback_cash_flow = cash_flow

payback_cash_flow["Refinance Income"] = np.where(refinance_toggle==True,
                                            refinance_amount,0)

payback_cash_flow["Exit Sale Price"] = np.where(payback_cash_flow["Year"]==100,
                     (purchase_price * (1 + y1_capital_growth) * (1 + capital_growth) ** 99) - mortgage,
                    0)

payback_cash_flow["Total Cash Flow"] = payback_cash_flow["Upfront Costs"] + payback_cash_flow["Exit Sale Price"] + payback_cash_flow["Income"] + payback_cash_flow["Costs"] + payback_cash_flow["Mortgage"]

try:
    
    payback = payback_cash_flow["Year"][payback_cash_flow["Cumulative Cash Flow"]>=0].reset_index(drop=True)[0]
    
except:
    
    payback = "n/a"

irr = npf.irr(irr_cash_flow["Total Cash Flow"])

capital_return = capital_growth * 100
income_return = (((sum(irr_cash_flow["Income"])+
                  sum(irr_cash_flow["Costs"])+
                  sum(irr_cash_flow["Mortgage"])+
                 purchase_price)/purchase_price) ** (1/appraisal_term) - 1) * 100
total_return = capital_return + income_return

st.header("Outputs")
col1, col2, col3 = st.columns(3)

if (purchase_price==0)|(LTV==0)|(monthly_income==0):
    
    with col1:
        st.metric("Cash Payback (yrs)",0)
        st.metric(str(appraisal_term)+"yr IRR",0)
    with col2:
        st.metric("Net Initial Yield",0)
        st.metric("Gross Initial Yield",0)
    with col3:
        st.metric("Capital Return",0)
        st.metric("Income Return",0)
        st.metric("Total Return",0)
else:
    with col1:
        st.metric("Cash Payback (yrs)",payback)
        st.metric(str(appraisal_term)+"yr IRR",str(round(irr*100,1))+"%")
    with col2:
        st.metric("Net Initial Yield",str(round(net_initial_yield*100,1))+"%")
        st.metric("Gross Initial Yield",str(round(gross_initial_yield*100,1))+"%")
    with col3:
        st.metric("Capital Return",str(round(capital_return,1))+"%")
        st.metric("Income Return",str(round(income_return,1))+"%")
        st.metric("Total Return",str(round(total_return,1))+"%")

st.header(str(appraisal_term) + " Year Cash Flows")
irr_cash_flow.style.hide_index()
irr_cash_flow

