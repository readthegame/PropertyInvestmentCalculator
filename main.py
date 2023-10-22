# import libraries

import numpy as np
import numpy_financial as npf
import pandas as pd
import requests
import json
import datetime
import seaborn as sns
import streamlit as st
import matplotlib.pyplot as plt
from formulas import calculation, calculation_mcs

mcs_length = 50000

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
  
    calculations = calculation(appraisal_term,
                purchase_price,
                purchase_tax_rate,
                property_investment,
                y1_capital_growth,
                capital_growth,
                sale_tax_rate,
                LTV,
                starting_mortgage_rate,
                mortgage_term,
                refinance_toggle,
                ongoing_mortgage_rate,
                mortgage_fees_percentage,
                legal_fees_percentage,
                monthly_income,
                rental_growth,
                vacancy_rate,
                mgmt_fee_percentage,
                other_fee_percentage,
                inflation,
                tax_rate,
                tax_application)

  else:

    print()
  
  payback = calculations[0]
  appraisal_term = calculations[1]
  irr = calculations[2]
  net_initial_yield = calculations[3]
  gross_initial_yield = calculations[4]
  capital_return = calculations[5]
  income_return = calculations[6]
  total_return = calculations[7]
  irr_cash_flow = calculations[8]
  total_cash_profit = calculations[9]
  
  st.header("Outputs")
  col1, col2, col3 = st.columns(3)
  
  if (purchase_price==0)|(LTV==0)|(monthly_income==0):
      
      with col1:
          st.metric("Cash Payback (yrs)",0)
          st.metric(str(appraisal_term)+"yr IRR on Cash",0)
          st.metric("Total Cash Profit/(Loss) over "+str(appraisal_term)+"yrs",0)
      with col2:
          st.metric("Net Initial Yield",0)
          st.metric("Gross Initial Yield",0)
      with col3:
          st.metric("Capital Return on Cash",0)
          st.metric("Income Return on Cash",0)
          st.metric("Total Return on Cash",0)
  else:
      with col1:
          st.metric("Cash Payback (yrs)",payback)
          st.metric(str(appraisal_term)+"yr IRR on Cash",str(round(irr*100,1))+"%")
          st.metric("Total Cash Profit/(Loss) over "+str(appraisal_term)+"yrs",int(total_cash_profit))

      with col2:
          st.metric("Net Initial Yield",str(round(net_initial_yield*100,1))+"%")
          st.metric("Gross Initial Yield",str(round(gross_initial_yield*100,1))+"%")
      with col3:
          st.metric("Capital Return on Cash",str(round(capital_return,1))+"%")
          st.metric("Income Return on Cash",str(round(income_return,1))+"%")
          st.metric("Total Return on Cash",str(round(total_return,1))+"%")
  
  st.header(str(appraisal_term) + " Year Cash Flows")
  
  st.dataframe(irr_cash_flow, hide_index=True)

with tab2:

  st.header("Monte Carlo Simulation - Inputs")

  st.text("Select which variables to model within the simulation:")

  monte_carlo_df = pd.DataFrame(
    [
      {"Metric":"Other Upfront Investment", "Simulate?":True, "Base": property_investment, "Min Value": max(property_investment - 5000.0,0.0), "Max Value": property_investment+5000.0},
      {"Metric":"First Year Property Value Growth %", "Simulate?":True, "Base": y1_capital_growth*100, "Min Value": y1_capital_growth*100 - 1.0, "Max Value": y1_capital_growth*100 + 1.0},
      {"Metric":"Ongoing Annual Property Value Growth %", "Simulate?":True, "Base": capital_growth*100, "Min Value": capital_growth*100 - 1.0, "Max Value": capital_growth*100 + 1.0},
      {"Metric":"Ongoing Mortgage Rate %", "Simulate?":True, "Base": ongoing_mortgage_rate*100, "Min Value": max(ongoing_mortgage_rate*100 - 1.0,0.0), "Max Value": ongoing_mortgage_rate*100 + 1.0},
      {"Metric":"Monthly Gross Rental Income", "Simulate?":True, "Base": monthly_income, "Min Value": max(monthly_income - 100.0,0), "Max Value": monthly_income + 100.0},
      {"Metric":"Annual Rental Growth %", "Simulate?":True, "Base": rental_growth*100, "Min Value": rental_growth*100 -1.0, "Max Value": rental_growth*100 + 1.0},
      {"Metric":"Average Vacancy Rate %", "Simulate?":True, "Base": vacancy_rate*100, "Min Value": max(vacancy_rate*100 - 1.0,0.0), "Max Value": vacancy_rate*100 +1.0},
      {"Metric":"Other Costs %", "Simulate?":True, "Base": other_fee_percentage*100, "Min Value": max(other_fee_percentage*100 - 1.0,0.0), "Max Value": other_fee_percentage*100 + 1.0},
      {"Metric":"Annual Cost Inflation %", "Simulate?":True, "Base": inflation*100, "Min Value": inflation*100 - 1.0, "Max Value": inflation * 100 + 1.0},
    ]
  )

  with st.form(key="mcs_inputs"):
    adj_monte_carlo_df = st.data_editor(
      monte_carlo_df,
      column_config={
        "Metric":"Metric",
        "Simulate?":st.column_config.CheckboxColumn("Simulate?",help="Select whether to include in simulation - unticking means only the Base value will be used when running the simulations",default=True),
        "Base":"Base",
        "Min Value":st.column_config.NumberColumn("Min Value",help="Enter minimum value for simulation (must be less than Max Value and no greater than Base)"),
        "Max Value":st.column_config.NumberColumn("Max Value",help="Enter maximum value for simulation (must be greater than Min Value and no less than Base)"),
      },
      disabled=["Metric","Base"],
      hide_index=True
    )
    
    property_investment_copy = property_investment
    y1_capital_growth_copy = y1_capital_growth
    capital_growth_copy = capital_growth    
    ongoing_mortgage_rate_copy = ongoing_mortgage_rate
    monthly_income_copy = monthly_income            
    rental_growth_copy = rental_growth
    vacancy_rate_copy = vacancy_rate
    other_fee_percentage_copy = other_fee_percentage
    inflation_copy = inflation
    
    def rand_number(x):
    
      df_temp = np.random.triangular(left=adj_monte_carlo_df.at[x,"Min Value"] * adj_monte_carlo_df.at[x,"Simulate?"] + (1 - adj_monte_carlo_df.at[x,"Simulate?"]) * adj_monte_carlo_df.at[x,"Base"],
                                     mode= adj_monte_carlo_df.at[x,"Base"],
                                     right= adj_monte_carlo_df.at[x,"Max Value"] * adj_monte_carlo_df.at[x,"Simulate?"] + (1 - adj_monte_carlo_df.at[x,"Simulate?"]) * adj_monte_carlo_df.at[x,"Base"],
                                     size=mcs_length)
    
      return df_temp
    
    property_investment_rand = rand_number(0)
    y1_capital_growth_rand = rand_number(1)
    capital_growth_rand = rand_number(2)  
    ongoing_mortgage_rate_rand = rand_number(3)
    monthly_income_rand = rand_number(4)            
    rental_growth_rand = rand_number(5)
    vacancy_rate_rand = rand_number(6)
    other_fee_percentage_rand = rand_number(7)
    inflation_rand = rand_number(8)
    
    df_mcs = pd.DataFrame({
        
        "Other Upfront Investment":property_investment_rand,
       "First Year Property Value Growth %":y1_capital_growth_rand,
       "Ongoing Annual Property Value Growth %":capital_growth_rand,
       "Ongoing Mortgage Rate %":ongoing_mortgage_rate_rand,
       "Monthly Gross Rental Income":monthly_income_rand,
       "Annual Rental Growth %":rental_growth_rand,
       "Average Vacancy Rate %":vacancy_rate_rand,
       "Other Costs %":other_fee_percentage_rand,
       "Annual Cost Inflation %":inflation_rand
        
    })
    
    progress_text = "Operation in progress. Please wait."
    my_bar = st.progress(0.0, text="")
    
    button = st.form_submit_button("Run Simulation")    
    
    if button == True:
      
      for i in range(0,len(df_mcs)):
    
        calculations_mcs = calculation_mcs(appraisal_term,
                                      purchase_price,
                                      purchase_tax_rate,
                                      df_mcs.at[i,"Other Upfront Investment"],
                                      df_mcs.at[i,"First Year Property Value Growth %"]/100,
                                      df_mcs.at[i,"Ongoing Annual Property Value Growth %"]/100,
                                      sale_tax_rate,
                                      LTV,
                                      starting_mortgage_rate,
                                      mortgage_term,
                                      refinance_toggle,
                                      df_mcs.at[i,"Ongoing Mortgage Rate %"]/100,
                                      mortgage_fees_percentage,
                                      legal_fees_percentage,
                                      df_mcs.at[i,"Monthly Gross Rental Income"],
                                      df_mcs.at[i,"Annual Rental Growth %"]/100,
                                      df_mcs.at[i,"Average Vacancy Rate %"]/100,
                                      mgmt_fee_percentage,
                                      df_mcs.at[i,"Other Costs %"]/100,
                                      df_mcs.at[i,"Annual Cost Inflation %"]/100,
                                      tax_rate,
                                      tax_application)
        
        df_mcs.at[i,"NIY"] = calculations_mcs[0]
        df_mcs.at[i,"GIY"] = calculations_mcs[1]
        df_mcs.at[i,"Capital Return"] = calculations_mcs[2]
        df_mcs.at[i,"Income Return"] = calculations_mcs[3]
        df_mcs.at[i,"Total Return"] = calculations_mcs[4]
        df_mcs.at[i,"Total Cash Profit/(Loss)"] = calculations_mcs[5]
    
        my_bar.progress(round(i/mcs_length,1), text=progress_text)
      
      c1, c2 = st.columns(2)
  
      with c1:

        st.subheader("Total Returns")
        
        fig1, ax1 = plt.subplots()
        ax1.hist(df_mcs["Total Return"], bins=100)
  
        mean_tr = np.mean(df_mcs["Total Return"])
        std_tr = np.std(df_mcs["Total Return"])
    
        st.text("Average: "+str(round(mean_tr,1))+"%")
        st.text("68% likely within: "+str(round(mean_tr-std_tr,1))+" to "+str(round(mean_tr+std_tr,1))+"%")
        st.text("95% likely within: "+str(round((mean_tr-std_tr-std_tr),1))+" to "+str(round((mean_tr+std_tr+std_tr),1))+"%")
    
        st.pyplot(fig1)

      with c2:

        st.subheader("Total Cash Profit/(Loss)")
        
        fig2, ax2 = plt.subplots()
        ax2.hist(df_mcs["Total Cash Profit/(Loss)"], bins=100)
  
        mean_tcp = np.mean(df_mcs["Total Cash Profit/(Loss)"])
        std_tcp = np.std(df_mcs["Total Cash Profit/(Loss)"])
    
        st.text("Average: "+str(round(mean_tcp,0)))
        st.text("68% likely within: "+str(round(mean_tcp-std_tcp,0))+" to "+str(round(mean_tcp+std_tcp,0)))
        st.text("95% likely within: "+str(round((mean_tcp-std_tcp-std_tcp),0))+" to "+str(round((mean_tcp+std_tcp+std_tcp),0)))
    
        st.pyplot(fig2)
