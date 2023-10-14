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

tab1, tab2, tab3 = st.tabs(["Main", "Monte Carlo Simulation", "Sensitivity Analysis"])

with tab1:

  st.header("Inputs")
    
  with st.form(key="inputs"):
  
      c1, c2, c3 = st.columns(3)
  
      with c1:
          st.subheader("Appraisal")
          appraisal_term = int(st.number_input('Appraisal period (yrs)',value=10,min_value=0,max_value=100))
  
          st.subheader("Property Value")
          purchase_price = st.number_input('Purchase Price',value=100000,min_value=1)
          purchase_tax_rate = st.number_input('Property Purchase Tax % (e.g. stamp duty)',value=5,min_value=0)/100
          property_investment = st.number_input("Other Upfront investment",min_value=0)
          y1_capital_growth = st.number_input("First Year Property Value Growth %")/100
          capital_growth = st.number_input("Ongoing Annual Property Value Growth %")/100
          sale_tax_rate = st.number_input("Propert Sale Tax % (e.g. capital gains tax)",value=20,min_value=0,max_value=100)/100
  
      with c2:
  
          st.subheader("Mortgage")
          st.radio("Mortgage Type",["Interest Only"])
          LTV = st.number_input("LTV %",min_value=0,max_value=100,value=75)
          starting_mortgage_rate = st.number_input("Starting Mortgage Rate %",min_value=0,value=6)/100
          mortgage_term = int(st.number_input("Fixed Term (yrs)",min_value=1,max_value=25))
          refinance_toggle = st.toggle("Equity Release after Fixed Term")
          ongoing_mortgage_rate = st.number_input("Ongoing Mortgage Rate %",min_value=0,value=4)/100
          mortgage_fees_percentage = st.number_input("Mortgage Fees %")/100
          legal_fees_percentage = st.number_input("Legal Fees %",min_value=0,value=1)/100
  
      with c3:
  
          st.subheader("Income")
          monthly_income = st.number_input("Monthly Gross Rental Income",value=500,min_value=1)            
          rental_growth = st.number_input("Annual Rental Growth %")/100
          vacancy_rate = st.number_input("Average Vacancy Rate %",min_value=0)/100
          
          st.subheader("Costs")
          mgmt_fee_percentage = st.number_input("Management Fee %",min_value=0,value=10)/100
          other_fee_percentage = st.number_input("Other Costs %",min_value=0)/100
          inflation = st.number_input("Annual Cost Inflation %",value=2)/100
          tax_rate = st.number_input("Tax Rate %",min_value=0)/100
          tax_application = st.selectbox("Tax Rate Applied to",("Income only",
                                                                "Income less expenses (excl mortgage costs)",
                                                                "Income less expenses (incl mortgage costs)"))
  
      st.form_submit_button("Calculate")
  
  if (purchase_price!=0)|(LTV!=0)|(monthly_income!=0):
  
      mortgage = LTV/100 * purchase_price
      deposit = purchase_price - mortgage
      legal_fees = purchase_price * legal_fees_percentage
      purchase_tax = purchase_price * purchase_tax_rate
      monthly_mgmt_fee = monthly_income * mgmt_fee_percentage
      monthly_other_fee = monthly_income * other_fee_percentage
      mortgage_fees = mortgage * mortgage_fees_percentage
      starting_monthly_mortgage_cost = (mortgage + mortgage_fees) * starting_mortgage_rate / 12
      
      if refinance_toggle == True:
          
          refinance_amount = (purchase_price * (1 + y1_capital_growth) * (1 + capital_growth) ** (mortgage_term - 1)) - purchase_price
          
      else:
          
          refinance_amount = 0
      
      ongoing_mortgage_fees = (mortgage + refinance_amount) * mortgage_fees_percentage
      ongoing_monthly_mortgage_cost = (mortgage + refinance_amount + ongoing_mortgage_fees) * ongoing_mortgage_rate / 12
      monthly_pre_tax = monthly_income*(1-vacancy_rate) - monthly_mgmt_fee - monthly_other_fee - starting_monthly_mortgage_cost
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
                       -(deposit+legal_fees+property_investment+purchase_tax),
                      0)
  
  cash_flow["Income"] = np.where(cash_flow["Year"]==0,
                                0,
                                monthly_income*12*(1-vacancy_rate))
  
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
  
  cash_flow["Tax"] = np.where(tax_application=="Income Only",
                              cash_flow["Income"] * tax_rate * -1,
                              np.where(tax_application=="Income less expenses (excl mortgage costs)",
                                       (cash_flow["Income"] + cash_flow["Costs"]) * tax_rate * -1,
                                       (cash_flow["Income"] + cash_flow["Costs"] + cash_flow["Mortgage"]) * tax_rate * -1))
  
  cash_flow["Refinance Income"] = np.where((refinance_toggle==True)&(cash_flow["Year"]==mortgage_term),
                                              refinance_amount,0)
  
  irr_cash_flow = cash_flow.copy()[cash_flow["Year"]<=appraisal_term]
  
  irr_cash_flow["Exit Sale Price"] = np.where(irr_cash_flow["Year"]==appraisal_term,
                       (purchase_price * (1 + y1_capital_growth) * (1 + capital_growth) ** (appraisal_term - 1)) - mortgage - refinance_amount,
                      0)
  
  irr_cash_flow["Exit Tax"] = irr_cash_flow["Exit Sale Price"] * sale_tax_rate * -1
  
  irr_cash_flow["Total Cash Flow"] = irr_cash_flow["Upfront Costs"] + irr_cash_flow["Exit Sale Price"] + irr_cash_flow["Income"] + irr_cash_flow["Costs"] + irr_cash_flow["Mortgage"] + irr_cash_flow["Tax"] + irr_cash_flow["Refinance Income"] + irr_cash_flow["Exit Tax"]
  
  payback_cash_flow = cash_flow
  
  payback_cash_flow["Exit Sale Price"] = np.where(payback_cash_flow["Year"]==100,
                       (purchase_price * (1 + y1_capital_growth) * (1 + capital_growth) ** 99) - mortgage - refinance_amount,
                      0)
                      
  payback_cash_flow["Exit Tax"] = payback_cash_flow["Exit Sale Price"] * sale_tax_rate * -1
  
  payback_cash_flow["Total Cash Flow"] = payback_cash_flow["Upfront Costs"] + payback_cash_flow["Exit Sale Price"] + payback_cash_flow["Income"] + payback_cash_flow["Costs"] + payback_cash_flow["Mortgage"] + payback_cash_flow["Tax"] + payback_cash_flow["Refinance Income"] + payback_cash_flow["Exit Tax"]
  
  payback_cash_flow["Cumulative Cash Flow"] = payback_cash_flow["Total Cash Flow"]
  
  for i in range(1,len(payback_cash_flow)):
    
    payback_cash_flow.at[i,"Cumulative Cash Flow"] = payback_cash_flow.at[i,"Total Cash Flow"] + payback_cash_flow.at[i - 1,"Cumulative Cash Flow"]
  
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
  
  irr_cash_flow

with tab2:

  st.header("Monte Carlo Simulation - Inputs")

  st.text("Select which variables to model within the simulation:")

  monte_carlo_df = pd.DataFrame(
    [
      {"Metric":"Other Upfront Investment", "Simuate?":True, "Base": property_investment, "Min Value": max(property_investment - 5000.0,0.0), "Max Value": property_investment+5000.0},
      {"Metric":"First Year Property Value Growth %", "Simuate?":True, "Base": y1_capital_growth*100, "Min Value": y1_capital_growth*100 - 1.0, "Max Value": y1_capital_growth*100 + 1.0},
      {"Metric":"Ongoing Annual Property Value Growth %", "Simuate?":True, "Base": capital_growth*100, "Min Value": capital_growth*100 - 1.0, "Max Value": capital_growth*100 + 1.0},
      {"Metric":"Ongoing Mortgage Rate %", "Simuate?":True, "Base": ongoing_mortgage_rate*100, "Min Value": max(ongoing_mortgage_rate*100 - 1.0,0.0), "Max Value": ongoing_mortgage_rate*100 + 1.0},
      {"Metric":"Monthly Gross Rental Income", "Simuate?":True, "Base": monthly_income, "Min Value": max(monthly_income - 100.0,0), "Max Value": monthly_income + 100.0},
      {"Metric":"Annual Rental Growth %", "Simuate?":True, "Base": rental_growth*100, "Min Value": rental_growth*100 -1.0, "Max Value": rental_growth*100 + 1.0},
      {"Metric":"Average Vacancy Rate %", "Simuate?":True, "Base": vacancy_rate*100, "Min Value": max(vacancy_rate*100 - 1.0,0.0), "Max Value": vacancy_rate*100 +1.0},
      {"Metric":"Other Costs %", "Simuate?":True, "Base": other_fee_percentage*100, "Min Value": max(other_fee_percentage*100 - 1.0,0.0), "Max Value": other_fee_percentage*100 - 1.0},
      {"Metric":"Annual Cost Inflation %", "Simuate?":True, "Base": inflation*100, "Min Value": inflation*100 - 1.0, "Max Value": inflation * 100 + 1.0},
    ]
  )

adj_monte_carlo_df = st.data_editor(
  monte_carlo_df,
  column_config={
    "Metric":"Metric",
    "Simulate?":st.column_config.CheckboxColumn("Simulate?",help="Select whether to include in simulation",default=True),
    "Base":"Base",
    "Min Value":st.column_config.NumberColumn("Min Value",help="Enter minimum value for simulation (must be less than Max Value and no greater than Base)"),
    "Max Value":st.column_config.NumberColumn("Max Value",help="Enter maximum value for simulation (must be greater than Min Value and no less than Base)"),
  },
  disabled=["Metric","Base"],
  hide_index=True
)

