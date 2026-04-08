import streamlit as st
import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import pandas as pd

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

    with st.expander("Reasoning (Explainable AI)"):
        st.write("The Inference Engine evaluated the following crisp inputs against the fuzzy rule matrix:")
        
        # We calculate the fuzzy membership of the user's exact inputs
        inc_level = "High" if in_income > 80 else "Low" if in_income < 40 else "Medium"
        debt_level = "High" if in_debt > 60 else "Low" if in_debt < 30 else "Medium"
        cred_level = "Excellent" if in_credit > 700 else "Poor" if in_credit < 550 else "Fair"
        
        st.markdown(f"""
        * **Income ({in_income}k):** Classified primarily as **{inc_level}**
        * **Debt Ratio ({in_debt}%):** Classified primarily as **{debt_level}**
        * **Credit Score ({in_credit}):** Classified primarily as **{cred_level}**
        """)
        
        st.write(f"Based on the Center of Gravity (Centroid) defuzzification, the aggregated rules resulted in a final crisp output of **{final_score:.1f}**.")
    

    st.divider()
    dev_mode = st.toggle("Developer Mode (Show Math Graphs)")

    if dev_mode:
        st.subheader("Fuzzification & Defuzzification Visualizer")

        #Plotting the Input Memberships
        st.markdown("#### 1. Input Fuzzy Sets (Fuzzification)")
        col1, col2, col3 = st.columns(3)

        #let scikit-fuzzy draw, we grab it, resize it, send it to Streamlit, then wipe the canvas for next plot.
        with col1:
            income.view(sim=risk_simulation) 
            fig_inc = plt.gcf() 
            fig_inc.set_size_inches(5, 3) 
            st.pyplot(fig_inc) 
            plt.close() 

        with col2:
            debt.view(sim=risk_simulation)
            fig_debt = plt.gcf()
            fig_debt.set_size_inches(5, 3)
            st.pyplot(fig_debt)
            plt.close()

        with col3:
            credit_history.view(sim=risk_simulation) 
            fig_cred = plt.gcf()
            fig_cred.set_size_inches(5, 3)
            st.pyplot(fig_cred)
            plt.close()

        # Plotting the Aggregated Output
        st.markdown("#### 2. The Inference Engine (Aggregated Output)")
        st.write("This graph shows how your active rules clipped the Risk triangles, and the thick black line represents the final **Center of Gravity (Centroid)**.")

        risk.view(sim=risk_simulation) # Pass the simulation to show the active math
        fig_risk = plt.gcf()
        fig_risk.set_size_inches(10, 4)
        st.pyplot(fig_risk)
        plt.close()

except (ValueError, KeyError):
    st.info("💡 Move the sliders! The current combination isn't covered by our logic rules yet.")

st.divider()
st.header("📂 Batch Applicant Processing")
st.write("Upload a CSV containing multiple applicants to run them through the AI simultaneously.")
st.info("Your CSV should have three columns exactly named: Income, Debt, and Credit.")
uploaded_file = st.file_uploader("Upload Applicant Data", type=["csv"])
if uploaded_file is not None:
    # Read the CSV
    if uploaded_file is not None:
        try:
            # Try standard UTF-8 first, and tell Pandas to ignore broken rows
            df = pd.read_csv(uploaded_file, on_bad_lines='skip')
        except UnicodeDecodeError:
            # Switch to Windows encoding, and also ignore broken rows
            uploaded_file.seek(0) 
            df = pd.read_csv(uploaded_file, encoding='latin-1', on_bad_lines='skip')
    
    # We will store the final scores back into the dataframe
    scores = []
    categories = []
    
    # Create a progress bar for the "Wow" factor
    progress_text = "Processing applicants through AI Engine..."
    my_bar = st.progress(0, text=progress_text)
    
    # Loop through every row in the CSV
    for index, row in df.iterrows():
        try:
            # Feed the row data into the AI
            risk_simulation.input['income'] = row['Income']
            risk_simulation.input['debt'] = row['Debt']
            risk_simulation.input['credit_history'] = row['Credit']
            
            risk_simulation.compute()
            score = risk_simulation.output['risk']
            scores.append(score)
            
            # Categorize them exactly like your UI
            if score < 40:
                categories.append("Safe")
            elif score < 70:
                categories.append("Moderate")
            else:
                categories.append("High")
                
        except (ValueError, KeyError):
            # If a row has an edge case our rules don't cover
            scores.append(None)
            categories.append("Error: Missing Rule")
            
        # Update progress bar
        my_bar.progress((index + 1) / len(df), text=progress_text)
        
    my_bar.empty() # Clear the progress bar when done
    
    # Add the results to the dataframe
    df['AI_Score'] = scores
    df['Risk_Level'] = categories
    
    st.success(f"Successfully processed {len(df)} applicants!")
    
    # --- THE TABS UI YOU REQUESTED ---
    tab_safe, tab_mod, tab_high = st.tabs(["✅ Safe Space", "⚠️ Moderate Risk", "❌ High Risk"])
    
    with tab_safe:
        safe_df = df[df['Risk_Level'] == 'Safe']
        st.metric("Total Safe Applicants", len(safe_df))
        for index, row in safe_df.iterrows():
            with st.expander(f"Applicant #{index + 1} - Score: {row['AI_Score']:.1f}"):
                st.write(f"**Income:** {row['Income']}k | **Debt:** {row['Debt']}% | **Credit:** {row['Credit']}")
                
                # Re-compute for this specific row so the graph is accurate
                risk_simulation.input['income'] = row['Income']
                risk_simulation.input['debt'] = row['Debt']
                risk_simulation.input['credit_history'] = row['Credit']
                risk_simulation.compute()
                
                # Draw the final aggregated output graph
                risk.view(sim=risk_simulation)
                fig_risk = plt.gcf()
                fig_risk.set_size_inches(6, 2.5) # Smaller size to fit the expander nicely
                st.pyplot(fig_risk)
                plt.close()
                
    with tab_mod:
        mod_df = df[df['Risk_Level'] == 'Moderate']
        st.metric("Total Moderate Applicants", len(mod_df))
        for index, row in mod_df.iterrows():
            with st.expander(f"Applicant #{index + 1} - Score: {row['AI_Score']:.1f}"):
                st.write(f"**Income:** {row['Income']}k | **Debt:** {row['Debt']}% | **Credit:** {row['Credit']}")
                
                risk_simulation.input['income'] = row['Income']
                risk_simulation.input['debt'] = row['Debt']
                risk_simulation.input['credit_history'] = row['Credit']
                risk_simulation.compute()
                
                risk.view(sim=risk_simulation)
                fig_risk = plt.gcf()
                fig_risk.set_size_inches(6, 2.5)
                st.pyplot(fig_risk)
                plt.close()
                
    with tab_high:
        high_df = df[df['Risk_Level'] == 'High']
        st.metric("Total High Risk Applicants", len(high_df))
        for index, row in high_df.iterrows():
            with st.expander(f"Applicant #{index + 1} - Score: {row['AI_Score']:.1f}"):
                st.write(f"**Income:** {row['Income']}k | **Debt:** {row['Debt']}% | **Credit:** {row['Credit']}")
                
                risk_simulation.input['income'] = row['Income']
                risk_simulation.input['debt'] = row['Debt']
                risk_simulation.input['credit_history'] = row['Credit']
                risk_simulation.compute()
                
                risk.view(sim=risk_simulation)
                fig_risk = plt.gcf()
                fig_risk.set_size_inches(6, 2.5)
                st.pyplot(fig_risk)
                plt.close()