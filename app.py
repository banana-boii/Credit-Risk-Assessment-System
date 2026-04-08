import streamlit as st
import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl
import plotly.graph_objects as go

# --- 1. STREAMLIT UI SETUP ---
st.title("🏦 AI Credit Risk Assessment System")
st.markdown("Adjust the applicant's details below to calculate their fuzzy risk score.")

st.sidebar.header("Applicant Details")
# Sliders for user input
in_income = st.sidebar.slider("Monthly Income (₹ Thousands)", 0, 150, 50)
in_debt = st.sidebar.slider("Debt-to-Income Ratio (%)", 0, 100, 40)
in_credit = st.sidebar.slider("Credit History Score (CIBIL)", 300, 850, 650)

# --- 2. FUZZY LOGIC VARIABLES ---
# Inputs (Antecedents)
income = ctrl.Antecedent(np.arange(0, 151, 1), 'income')
debt = ctrl.Antecedent(np.arange(0, 101, 1), 'debt')
credit_history = ctrl.Antecedent(np.arange(300, 851, 1), 'credit_history')

# Output (Consequent)
risk = ctrl.Consequent(np.arange(0, 101, 1), 'risk')

# Auto-generate Low/Medium/High categories based on the ranges above
income.automf(names=['low', 'medium', 'high'])
debt.automf(names=['low', 'medium', 'high'])
credit_history.automf(names=['poor', 'fair', 'excellent'])

# Custom categories for the Final Risk Score (0-100)
risk['safe'] = fuzz.trimf(risk.universe, [0, 0, 50])
risk['moderate'] = fuzz.trimf(risk.universe, [20, 50, 80])
risk['high'] = fuzz.trimf(risk.universe, [50, 100, 100])

# --- 3. THE RULE BASE (THE AI BRAIN) ---

# SAFE RULES (Low Risk)
rule1 = ctrl.Rule(income['high'] & debt['low'] & credit_history['excellent'], risk['safe'])
rule2 = ctrl.Rule(income['high'] & debt['medium'] & credit_history['excellent'], risk['safe'])
rule3 = ctrl.Rule(income['medium'] & debt['low'] & credit_history['excellent'], risk['safe'])

# MODERATE RULES (Medium Risk)
rule4 = ctrl.Rule(income['medium'] & debt['medium'] & credit_history['fair'], risk['moderate'])
rule5 = ctrl.Rule(income['low'] & debt['low'] & credit_history['fair'], risk['moderate'])
rule6 = ctrl.Rule(income['high'] & debt['high'] & credit_history['fair'], risk['moderate'])

# HIGH RISK RULES
rule7 = ctrl.Rule(income['low'] & debt['high'], risk['high']) # Notice we drop credit history here; if income is low and debt is high, it's always high risk!
rule8 = ctrl.Rule(credit_history['poor'], risk['high']) # If credit is poor, automatically high risk regardless of income.
rule9 = ctrl.Rule(income['medium'] & debt['high'] & credit_history['poor'], risk['high'])
rule10 = ctrl.Rule(income['high'] & debt['high'] & credit_history['excellent'], risk['moderate'])

# --- 4. THE INFERENCE ENGINE ---
# Make sure to add the new rules to the ControlSystem array!
risk_ctrl = ctrl.ControlSystem([rule1, rule2, rule3, rule4, rule5, rule6, rule7, rule8, rule9, rule10])
risk_simulation = ctrl.ControlSystemSimulation(risk_ctrl)

# Pass the Streamlit slider values directly into the AI
risk_simulation.input['income'] = in_income
risk_simulation.input['debt'] = in_debt
risk_simulation.input['credit_history'] = in_credit

# Calculate and display the result
st.divider()
st.subheader("Assessment Result")

try:
    risk_simulation.compute()
    final_score = risk_simulation.output['risk']
    
    #Plotly Gauge Chart
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=final_score,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Credit Risk Score", 'font': {'size': 24}},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color': "black"},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 40], 'color': "#71F055"},  
                {'range': [40, 70], 'color': "#f6fc42"},  
                {'range': [70, 100], 'color': "#ee5561"}  
            ]
        }
    ))

    # Shock Absorber 
    # smooth 500ms glide
    fig.update_layout(
        transition={'duration': 500, 'easing': 'cubic-in-out'},
        margin=dict(l=20, r=20, t=50, b=20),
        height=350
    )

    # render
    st.plotly_chart(fig, use_container_width=True)
    
    # text feedback 
    if final_score < 40:
        st.success("✅ Low Risk: Loan Candidate Looks Solid")
    elif final_score < 70:
        st.warning("⚠️ Moderate Risk: Requires Manual Review")
    else:
        st.error("❌ High Risk: Strongly Consider Rejecting")
        
except (ValueError, KeyError):
    st.info("💡 Move the sliders! The current combination isn't covered by our logic rules yet.")