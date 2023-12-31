import numpy as np
import numpy_financial as npf
import pandas as pd
import requests
import json
import datetime

def calculation(appraisal_term,
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
                tax_application):
                  
  mortgage = LTV/100 * purchase_price
  deposit = purchase_price - mortgage
  legal_fees = purchase_price * legal_fees_percentage
  purchase_tax = purchase_price * purchase_tax_rate
  monthly_mgmt_fee = monthly_income * mgmt_fee_percentage
  monthly_other_fee = monthly_income * other_fee_percentage
  mortgage_fees = mortgage * mortgage_fees_percentage
  starting_monthly_mortgage_cost = (mortgage + mortgage_fees) * starting_mortgage_rate / 12
  
  refinance_amount = ((purchase_price * (1 + y1_capital_growth) * (1 + capital_growth) ** (mortgage_term - 1)) - purchase_price) * refinance_toggle
  
  ongoing_mortgage_fees = (mortgage + refinance_amount) * mortgage_fees_percentage
  ongoing_monthly_mortgage_cost = (mortgage + refinance_amount + ongoing_mortgage_fees) * ongoing_mortgage_rate / 12
  monthly_pre_tax = monthly_income*(1-vacancy_rate) - monthly_mgmt_fee - monthly_other_fee - starting_monthly_mortgage_cost
  gross_initial_yield = (monthly_income * 12) / purchase_price
  net_initial_yield = (monthly_pre_tax * 12) / purchase_price
  ROI = (monthly_pre_tax * 12) / (deposit + legal_fees)
  cash_return = 1 / ROI

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
  
  cash_flow["Refinance Income"] = np.where(cash_flow["Year"]==mortgage_term,
                                            refinance_amount,0)
  
  irr_cash_flow = cash_flow.copy()[cash_flow["Year"]<=appraisal_term]
  
  irr_cash_flow["Exit Sale Price"] = np.where(irr_cash_flow["Year"]==appraisal_term,
                     (purchase_price * (1 + y1_capital_growth) * (1 + capital_growth) ** (appraisal_term - 1)) - mortgage - refinance_amount,
                    0)
  
  irr_cash_flow["Exit Tax"] = np.where(irr_cash_flow["Year"]==appraisal_term,
                     ((purchase_price * (1 + y1_capital_growth) * (1 + capital_growth) ** (appraisal_term - 1)) - purchase_price) * sale_tax_rate * -1,
                    0)
  
  irr_cash_flow["Total Cash Flow"] = irr_cash_flow["Upfront Costs"] + irr_cash_flow["Exit Sale Price"] + irr_cash_flow["Income"] + irr_cash_flow["Costs"] + irr_cash_flow["Mortgage"] + irr_cash_flow["Tax"] + irr_cash_flow["Refinance Income"] + irr_cash_flow["Exit Tax"]

  value_irr_cash_flow = irr_cash_flow.copy()

  value_irr_cash_flow.at[0,"Total Cash Flow"] = value_irr_cash_flow.at[0,"Total Cash Flow"] - mortgage
  value_irr_cash_flow.at[appraisal_term,"Total Cash Flow"] = value_irr_cash_flow.at[appraisal_term,"Total Cash Flow"] + mortgage + refinance_amount
                  
  payback_cash_flow = cash_flow
  
  payback_cash_flow["Exit Sale Price"] = np.where(payback_cash_flow["Year"]==100,
                     (purchase_price * (1 + y1_capital_growth) * (1 + capital_growth) ** 99) - mortgage - refinance_amount,
                    0)
                    
  payback_cash_flow["Exit Tax"] = np.where(payback_cash_flow["Year"]==100,
                     ((purchase_price * (1 + y1_capital_growth) * (1 + capital_growth) ** 99) - purchase_price) * sale_tax_rate * -1,
                    0)
  
  payback_cash_flow["Total Cash Flow"] = payback_cash_flow["Upfront Costs"] + payback_cash_flow["Exit Sale Price"] + payback_cash_flow["Income"] + payback_cash_flow["Costs"] + payback_cash_flow["Mortgage"] + payback_cash_flow["Tax"] + payback_cash_flow["Refinance Income"] + payback_cash_flow["Exit Tax"]
  
  payback_cash_flow["Cumulative Cash Flow"] = payback_cash_flow["Total Cash Flow"]
  
  for i in range(1,len(payback_cash_flow)):
  
    payback_cash_flow.at[i,"Cumulative Cash Flow"] = payback_cash_flow.at[i,"Total Cash Flow"] + payback_cash_flow.at[i - 1,"Cumulative Cash Flow"]
  
  try:
    
    payback = payback_cash_flow["Year"][payback_cash_flow["Cumulative Cash Flow"]>=0].reset_index(drop=True)[0]
    
  except:
    
    payback = "n/a"
  
  irr = npf.irr(irr_cash_flow["Total Cash Flow"])
  irr_value = npf.irr(value_irr_cash_flow["Total Cash Flow"])
  
  capital_return_value = (((1 + y1_capital_growth) * (1 + capital_growth) ** (appraisal_term - 1)) ** (1 / appraisal_term) - 1) * 100
  income_return_value = (((sum(irr_cash_flow["Income"])+
                  sum(irr_cash_flow["Costs"])+
                  sum(irr_cash_flow["Mortgage"])+
                 purchase_price)/purchase_price) ** (1/appraisal_term) - 1) * 100
  total_return_value = capital_return_value + income_return_value
  
  capital_return = (((((purchase_price * (1 + y1_capital_growth) * (1 + capital_growth) ** (appraisal_term - 1)) - purchase_price) / (deposit + legal_fees + property_investment)) + 1) ** (1 / appraisal_term) - 1) * 100
  income_return = (((sum(irr_cash_flow["Income"])+
                      sum(irr_cash_flow["Costs"])+
                      sum(irr_cash_flow["Mortgage"])+
                      (deposit + legal_fees + property_investment))/(deposit + legal_fees + property_investment)) ** (1/appraisal_term) - 1) * 100
  total_return = capital_return + income_return
  total_cash_profit = sum(irr_cash_flow["Total Cash Flow"])
  
  return payback, appraisal_term, irr, net_initial_yield, gross_initial_yield, capital_return, income_return, total_return, irr_cash_flow, total_cash_profit, irr_value, capital_return_value, income_return_value, total_return_value


def calculation_mcs(appraisal_term,
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
                tax_application):
                  
  mortgage = LTV/100 * purchase_price
  deposit = purchase_price - mortgage
  legal_fees = purchase_price * legal_fees_percentage
  purchase_tax = purchase_price * purchase_tax_rate
  monthly_mgmt_fee = monthly_income * mgmt_fee_percentage
  monthly_other_fee = monthly_income * other_fee_percentage
  mortgage_fees = mortgage * mortgage_fees_percentage
  starting_monthly_mortgage_cost = (mortgage + mortgage_fees) * starting_mortgage_rate / 12
      
  refinance_amount = ((purchase_price * (1 + y1_capital_growth) * (1 + capital_growth) ** (mortgage_term - 1)) - purchase_price) * refinance_toggle
  
  ongoing_mortgage_fees = (mortgage + refinance_amount) * mortgage_fees_percentage
  ongoing_monthly_mortgage_cost = (mortgage + refinance_amount + ongoing_mortgage_fees) * ongoing_mortgage_rate / 12
  monthly_pre_tax = monthly_income*(1-vacancy_rate) - monthly_mgmt_fee - monthly_other_fee - starting_monthly_mortgage_cost
  gross_initial_yield = (monthly_income * 12) / purchase_price
  net_initial_yield = (monthly_pre_tax * 12) / purchase_price
  ROI = (monthly_pre_tax * 12) / (deposit + legal_fees)
  cash_return = 1 / ROI

  cf_upfront_costs = -(deposit+legal_fees+property_investment+purchase_tax)
  cf_income = sum([(monthly_income * 12 * (1 - vacancy_rate)) * (1 + rental_growth)**x for x in range(0,appraisal_term)])
  cf_costs = (cf_income * -(mgmt_fee_percentage + other_fee_percentage)) * (1+(inflation-rental_growth))**appraisal_term
  cf_mortgage = -starting_monthly_mortgage_cost*12*mortgage_term - ongoing_monthly_mortgage_cost*12*(appraisal_term - mortgage_term)
  cf_tax = np.where(tax_application=="Income Only",
                            cf_income * -tax_rate,
                            np.where(tax_application=="Income less expenses (excl mortgage costs)",
                                     (cf_income + cf_costs) * -tax_rate,
                                     (cf_income + cf_costs + cf_mortgage) * -tax_rate))
  cf_refinance_amount = refinance_amount
  cf_exit_sale_price = (purchase_price * (1 + y1_capital_growth) * (1 + capital_growth) ** (appraisal_term - 1)) - mortgage - refinance_amount
  cf_exit_tax = ((purchase_price * (1 + y1_capital_growth) * (1 + capital_growth) ** (appraisal_term - 1)) - purchase_price) * sale_tax_rate * -1
  cf_total_cash_flow = cf_upfront_costs + cf_income + cf_costs + cf_mortgage + cf_tax + cf_refinance_amount + cf_exit_sale_price + cf_exit_tax                  

  capital_return = (((((purchase_price * (1 + y1_capital_growth) * (1 + capital_growth) ** (appraisal_term - 1)) - purchase_price) / (deposit + legal_fees + property_investment)) + 1) ** (1 / appraisal_term) - 1) * 100
  income_return = (((cf_income + cf_costs + cf_mortgage + (deposit + legal_fees + property_investment)) / (deposit + legal_fees + property_investment)) ** (1/appraisal_term) - 1) * 100
  total_return = capital_return + income_return
  
  return net_initial_yield, gross_initial_yield, capital_return, income_return, total_return, cf_total_cash_flow, cf_income, cf_costs, cf_mortgage, cf_tax, purchase_price

