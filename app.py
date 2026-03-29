import streamlit as st
import pandas as pd
import joblib
import time
import bcrypt
import urllib.parse
from sqlalchemy import text

# --- 1. SETUP PAGE CONFIG & SESSION STATE ---
st.set_page_config(page_title="SmartSacco AI", page_icon="💰", layout="wide")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "auth_mode" not in st.session_state:
    st.session_state.auth_mode = "login"

# --- 2. AUTHENTICATION FUNCTIONS & UI ---
def hash_password(password):
    """Returns a securely hashed password."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password, hashed_password):
    """Verifies a password against a hash."""
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

def switch_auth_mode(mode):
    st.session_state.auth_mode = mode

def auth_page():
    """Handles both the Login and Sign Up UI."""
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.image("https://cdn-icons-png.flaticon.com/512/4149/4149667.png", width=80)
        
        try:
            conn = st.connection('tidb', type='sql')
        except Exception as e:
            st.error(f"⚠️ Database connection failed. Check your secrets.toml file. Error: {e}")
            return

        # LOGIN MODE
        if st.session_state.auth_mode == "login":
            st.title("🔒 Login to SmartSacco")
            with st.form("login_form"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                submit = st.form_submit_button("Log In", use_container_width=True)

                if submit:
                    try:
                        query = "SELECT * FROM users WHERE username = :user"
                        user_data = conn.query(query, params={"user": username}, ttl=0)
                        
                        if not user_data.empty:
                            stored_hash = user_data.iloc[0]['password']
                            if verify_password(password, stored_hash):
                                st.session_state.logged_in = True
                                st.rerun()
                            else:
                                st.error("❌ Invalid password.")
                        else:
                            st.error("❌ User not found.")
                    except Exception as e:
                        st.error(f"⚠️ Query error: {e}")
            
            st.write("Don't have an account?")
            st.button("Sign Up Here", on_click=switch_auth_mode, args=("signup",))

        # SIGNUP MODE
        elif st.session_state.auth_mode == "signup":
            st.title("📝 Create an Account")
            with st.form("signup_form"):
                new_username = st.text_input("Choose a Username")
                new_password = st.text_input("Choose a Password", type="password")
                confirm_password = st.text_input("Confirm Password", type="password")
                submit = st.form_submit_button("Sign Up", use_container_width=True)

                if submit:
                    if new_password != confirm_password:
                        st.error("❌ Passwords do not match.")
                    elif len(new_username) < 3 or len(new_password) < 6:
                        st.error("❌ Username must be 3+ chars, Password must be 6+ chars.")
                    else:
                        try:
                            # Check if user already exists
                            check_query = "SELECT * FROM users WHERE username = :user"
                            existing_user = conn.query(check_query, params={"user": new_username}, ttl=0)
                            
                            if not existing_user.empty:
                                st.error("❌ Username already exists. Choose another.")
                            else:
                                # Hash and insert new user
                                hashed_pwd = hash_password(new_password)
                                with conn.session as session:
                                    session.execute(
                                        text("INSERT INTO users (username, password) VALUES (:user, :pwd)"),
                                        {"user": new_username, "pwd": hashed_pwd}
                                    )
                                    session.commit()
                                st.success("✅ Account created successfully! You can now log in.")
                                time.sleep(1.5)
                                switch_auth_mode("login")
                                st.rerun()
                        except Exception as e:
                            st.error(f"⚠️ Registration error: {e}")
            
            st.write("Already have an account?")
            st.button("Back to Login", on_click=switch_auth_mode, args=("login",))

# --- 3. MAIN APPLICATION ---
def main_app():
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

    # --- SIDEBAR (SEARCH) ---
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/4149/4149667.png", width=80)
        st.title("SmartSacco Credit Manager")
        
        # --- LOGOUT BUTTON (Added inside sidebar) ---
        if st.button("🚪 Log Out", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()
            
        st.divider()
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

    # --- MAIN DASHBOARD ---
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
                st.session_state.loan_input = 50000.0
                
            # 1. Calculate the Strict Limit (3x Savings)
            max_eligible = savings * 3
            
            # 2. Safety Check
            safe_max = max(max_eligible, 1000.0)
                
            loan_request = st.number_input(
                f"Enter Loan Amount (Limit: KES {max_eligible:,.0f})", 
                min_value=1000.0,
                max_value=float(safe_max), 
                step=5000.0,
                key="loan_input",
                help="System strictly limits request to 3x Total Savings."
            )
            
            # 3. Visual Feedback
            if max_eligible < 1000:
                st.caption("⚠️ Member has insufficient savings to borrow.")
                
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

               # --- E. EMAIL FUNCTIONALITY ---
                st.divider()
                st.subheader("📧 Email Notification")

                # Create a clean subject line
                subject = f"Loan Application Status - {found_member['first_name']} {found_member['last_name']}"
                
                # Encode the body text so it fits in a URL
                safe_subject = urllib.parse.quote(subject)
                safe_body = urllib.parse.quote(email_body)
                
                # Create the "mailto" link
                mailto_link = f"mailto:{found_member['email']}?subject={safe_subject}&body={safe_body}"

                # Display the Preview and the Button
                with st.expander("👀 Preview Email Draft", expanded=True):
                    st.text_area("Message Content", email_body, height=200, disabled=True)
                    st.link_button("📤 Open in Email App", mailto_link, type="primary", use_container_width=True)
                    
    # --- START SCREEN ---
    else:
        st.info("← Please search for a member in the sidebar to begin.")
        st.markdown("### Latest Member Activity")
        # Safety check: Display sample data only if df is loaded
        if 'df' in locals() and not df.empty:
            st.dataframe(df.sample(5)[['member_id', 'first_name', 'total_savings', 'credit_score']].reset_index(drop=True), use_container_width=True)

# --- 4. ROUTING LOGIC ---
if not st.session_state.logged_in:
    auth_page()
else:
    main_app()