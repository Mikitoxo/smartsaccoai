import streamlit as st
import pandas as pd
import joblib
import time

# --- 1. SETUP & LOAD RESOURCES ---
st.set_page_config(page_title="SmartSacco AI", page_icon="💰", layout="wide")

@st.cache_resource
def load_resources():
    # Load the AI Model
    try:
        model = joblib.load('smartsacco_brain_v2.pkl')
    except FileNotFoundError:
        st.error("⚠️ Error: 'smartsacco_brain_v2.pkl' not found.")
        st.stop()
        
    # Load the Database (CSV)
    try:
        # Ensure your CSV filename matches exactly!
        df = pd.read_csv('MOCK_DATA.csv')
        # Convert ID to string for easier searching
        if 'member_id' in df.columns:
            df['member_id'] = df['member_id'].astype(str)
    except FileNotFoundError:
        st.error("⚠️ Error: 'MOCK_DATA.csv' not found. Please put your dataset in this folder.")
        st.stop()
        
    return model, df

model, df = load_resources()

# --- model reasoning---
def get_rejection_reasons(savings, request, credit_score, guarantors, g_score, defaulted):
    reasons = []
    
    # Rule 1: The Multiplier (Most common reason)
    # Avoid division by zero
    if savings == 0:
        multiplier = 100 
    else:
        multiplier = request / savings
        
    if multiplier > 3.0:
        reasons.append(f"⚠️ **Over-Leveraged:** Request is {multiplier:.1f}x their savings. (Limit is 3x)")
        
    # Rule 2: Credit Score
    if credit_score < 600:
        reasons.append(f"⚠️ **Credit Risk:** Member score ({credit_score}) is below the acceptable threshold of 600.")
        
    # Rule 3: Guarantor Quantity
    if guarantors < 2:
        reasons.append(f"⚠️ **Insufficient Security:** {guarantors} guarantors provided. Minimum required is 2.")
        
    # Rule 4: Guarantor Quality
    if g_score < 600:
        reasons.append(f"⚠️ **Weak Guarantors:** Average guarantor score ({g_score}) is too low.")
        
    # Rule 5: History
    if defaulted:
        reasons.append("⚠️ **Blacklisted:** Member has a record of previous default.")

    # Fallback: If AI says NO but rules look okay
    if not reasons:
        reasons.append("⚠️ **General Risk Profile:** The AI detected a pattern of high risk not captured by standard rules.")
        
    return reasons

# --- 2. SIDEBAR (SEARCH) ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/4149/4149667.png", width=80)
    st.title("SmartSacco Credit Manager")
    st.header("Find Member🔎")
    
    search_query = st.text_input("Enter Member ID or Name", placeholder="e.g., John or 105")
    
    found_member = None
    if search_query:
        results = df[
            df['first_name'].str.contains(search_query, case=False, na=False) |
            df['last_name'].str.contains(search_query, case=False, na=False) |
            df['member_id'].str.contains(search_query, na=False)
        ]
        
        if not results.empty:
            st.success(f"Found {len(results)} member(s).")
            member_id_selection = st.selectbox("Select Member", results['member_id'].values)
            found_member = results[results['member_id'] == member_id_selection].iloc[0]
        else:
            st.warning("No member found.")

# --- 3. MAIN DASHBOARD ---
if found_member is not None:
    # --- A. MEMBER PROFILE ---
    st.markdown(f"## 👤 {found_member['first_name']} {found_member['last_name']}")
    st.caption(f"Member ID: {found_member['member_id']} | Email: {found_member['email']}")
    st.divider()

    # Extract Data from the CSV Row
    savings = float(found_member['total_savings'])
    credit_score = int(found_member['credit_score'])
    guarantors = int(found_member['guarantor_count'])
    g_score = int(found_member['guarantor_avg_credit_score'])
    defaulted = bool(found_member['has_defaulted_before'])

    # Display Read-Only Metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Savings 💰", f"KES {savings:,.0f}")
    col2.metric("Credit Score 📊", credit_score, delta_color="normal" if credit_score > 600 else "inverse")
    col3.metric("Guarantors", guarantors)
    col4.metric("Risk Status", "Defaulted ‼" if defaulted else "Clean ✓")

    st.divider()

    # --- B. LOAN APPLICATION ---
    st.subheader("New Loan Request")

    def reset_loan_amount():
        st.session_state.loan_input = 50000

    col_input, col_analyze, col_clear = st.columns([3, 1, 1], vertical_alignment="bottom")
    
    with col_input:
        if "loan_input" not in st.session_state:
            st.session_state.loan_input = 50000
            
        loan_request = st.number_input(
            "Enter Loan Amount (KES)", 
            min_value=1000, 
            step=5000, 
            key="loan_input"
        )
        
    with col_analyze:
        analyze_btn = st.button("Analyze", type="primary", use_container_width=True)

    with col_clear:
        st.button("Clear", on_click=reset_loan_amount, use_container_width=True)

    # --- C. AI ANALYSIS ---
    if analyze_btn:
        with st.spinner("Consulting AI Model..."):
            time.sleep(1) 
            
            input_data = pd.DataFrame({
                'total_savings': [savings],
                'loan_amount_requested': [loan_request],
                'credit_score': [credit_score],
                'guarantor_count': [guarantors],
                'guarantor_avg_credit_score': [g_score],
                'has_defaulted_before': [1 if defaulted else 0]
            })
            
            prediction = model.predict(input_data)[0]
            probs = model.predict_proba(input_data)
            confidence = probs[0][1] * 100 if probs.shape[1] == 2 else (100 if prediction == 1 else 0)

            # --- D. RESULTS & EMAIL ---
            st.divider()
            
            email_subject = f"Loan Application Status - {found_member['first_name']}"
            
            if prediction == 1:
                st.success(f"### APPROVED ✓ (Confidence: {confidence:.1f}%)")
                st.balloons()
                
                email_body = f"""Dear {found_member['first_name']},
                
Congratulations! Your loan application for KES {loan_request:,.0f} has been APPROVED.

Next Steps: Please visit our branch to sign the release forms.

Regards,
SmartSacco Team"""
            else:
                st.error(f"### REJECTED ✕ (Confidence: {100-confidence:.1f}%)")
                
                st.write("#### 🔍 Why was this rejected?")
                reasons = get_rejection_reasons(savings, loan_request, credit_score, guarantors, g_score, defaulted)
                
                for reason in reasons:
                    st.error(reason, icon="🚫")
                
                reason_list = "\n- ".join([r.replace("⚠️ ", "").replace("**", "") for r in reasons])
                
                email_body = f"""Dear {found_member['first_name']},
                
We regret to inform you that your loan application for KES {loan_request:,.0f} was declined due to the following reasons:

- {reason_list}

Please contact the credit office if you wish to appeal this decision.

Regards,
SmartSacco Team"""

           # --- E. EMAIL FUNCTIONALITY (Updated) ---
            st.divider()
            st.subheader("📧 Email Notification")

            # 1. Prepare the email content safely
            # We must encode newlines so they work in the URL (replace enter with %0A)
            import urllib.parse
            
            # Create a clean subject line
            subject = f"Loan Application Status - {found_member['first_name']} {found_member['last_name']}"
            
            # Encode the body text so it fits in a URL
            safe_subject = urllib.parse.quote(subject)
            safe_body = urllib.parse.quote(email_body)
            
            # 2. Create the "mailto" link
            # Format: mailto:someone@example.com?subject=...&body=...
            mailto_link = f"mailto:{found_member['email']}?subject={safe_subject}&body={safe_body}"

            # 3. Display the Preview and the Button
            with st.expander("👀 Preview Email Draft", expanded=True):
                st.text_area("Message Content", email_body, height=200, disabled=True)
                
                # The Magic Button: Opens the User's Default Email App
                st.link_button("📤 Open in Email App", mailto_link, type="primary", use_container_width=True)
                
# --- 4. START SCREEN (CORRECTED INDENTATION) ---
else:
    st.info("← Please search for a member in the sidebar to begin.")
    st.markdown("### Latest Member Activity")
    # Safety check: Display sample data only if df is loaded
    if 'df' in locals() and not df.empty:
        st.dataframe(df.sample(5)[['member_id', 'first_name', 'total_savings', 'credit_score']].reset_index(drop=True), use_container_width=True)