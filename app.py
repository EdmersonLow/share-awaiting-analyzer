import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import re
import io

# Page config
st.set_page_config(
    page_title="Share Awaiting Analyzer",
    page_icon="📊",
    layout="wide"
)

# Configuration
LOCAL_CURRENCIES = ['SGD', 'MYR']
FOREIGN_CURRENCIES = ['USD', 'CAD', 'EUR', 'GBP', 'JPY', 'AUD', 'HKD', 'CNY']

# ============================================================================
# PROCESSING FUNCTIONS (From your notebook)
# ============================================================================

def extract_account_type(full_info_string):
    if pd.isna(full_info_string): return 'UNKNOWN'
    info_str = str(full_info_string).upper()
    
    if '@KC' in info_str or '*@KC' in info_str: return 'KC'
    elif '@M' in info_str or '*@M' in info_str: return 'M'
    elif '*C' in info_str or '@C' in info_str: return 'C'
    elif 'CC' in info_str: return 'CC'
    elif '@V' in info_str or '*V' in info_str or ' V ' in info_str: return 'V'
    elif re.search(r'\d{2}@', info_str): return 'XX'
    elif re.search(r'@\d{2}', info_str): return 'XX'
    elif re.search(r'\*?[A-Z]@', info_str):
        match = re.search(r'\*?([A-Z])@', info_str)
        return match.group(1) if match else 'REGULAR'
    return 'REGULAR'

def get_contra_flag(account_type):
    if account_type in ['XX', 'KC', 'C', 'V']: return 'Y'
    elif account_type in ['M', 'CC']: return 'N'
    elif account_type and len(account_type) == 1 and account_type.isalpha(): return 'Y'
    return 'UNKNOWN'

def parse_share_awaiting_file(file_path):
    df_raw = pd.read_excel(file_path, header=None)
    header_row_idx = None
    for idx, row in df_raw.iterrows():
        if 'Contract Date' in str(row.values):
            header_row_idx = idx
            break
    
    transactions = []
    current_account = None
    
    for idx in range(header_row_idx + 1, len(df_raw)):
        row = df_raw.iloc[idx]
        first_col = str(row[0]) if pd.notna(row[0]) else ''
        if first_col == '' or first_col == 'nan': continue
        
        if re.match(r'^\d{7}', first_col):
            parts = first_col.split('/')
            account_num = parts[0].strip()
            rest = '/'.join(parts[1:]).strip() if len(parts) > 1 else ''
            
            account_type_code = extract_account_type(first_col)
            contra_flag = get_contra_flag(account_type_code)
            
            name_match = re.match(r'([^@*]+)', rest)
            name = name_match.group(1).strip() if name_match else 'Unknown'
            
            current_account = {
                'account_number': account_num,
                'account_name': name,
                'account_type_code': account_type_code,
                'contra_flag': contra_flag
            }
            
        elif current_account is not None and re.match(r'^\d{2}/\d{2}/\d{2}$', first_col):
            try:
                transaction = {
                    'account_number': current_account['account_number'],
                    'account_name': current_account['account_name'],
                    'account_type_code': current_account['account_type_code'],
                    'contra_flag': current_account['contra_flag'],
                    'security_name': row[2],
                    'quantity': row[6],
                    'settle_currency': row[7],
                    'settle_amount': row[8],
                    'days': row[9],
                    'payment_ref': row[11],
                    'margin_pu': row[12],
                }
                transactions.append(transaction)
            except:
                continue
    
    return pd.DataFrame(transactions)

def normalize_currency(currency):
    if pd.isna(currency): return 'UNKNOWN'
    currency = str(currency).strip().upper()
    if currency in ['S$', 'SGD', 'SG']: return 'SGD'
    elif currency in ['US$', 'USD', 'US']: return 'USD'
    elif currency in ['MYR', 'MY', 'RM']: return 'MYR'
    elif currency in ['HK$', 'HKD', 'HK']: return 'HKD'
    elif currency in ['CDN', 'CAD', 'C$']: return 'CAD'
    return currency

def convert_days_to_int(days_value):
    if pd.isna(days_value): return None
    try: return int(float(str(days_value)))
    except: return None

def is_payment_arranged(row):
    if pd.notna(row['payment_ref']):
        ref_str = str(row['payment_ref']).strip()
        if len(ref_str) > 0 and ref_str.lower() != 'nan':
            return True
    
    account_type = row['account_type_code']
    if account_type in ['V', 'M']:
        margin_pu = str(row.get('margin_pu', '')).strip().upper()
        if margin_pu == '' or margin_pu == 'NAN' or pd.isna(row.get('margin_pu')):
            return True
    
    return False

def analyze_transaction(row):
    if is_payment_arranged(row):
        return None
    
    currency = normalize_currency(row['settle_currency'])
    days = convert_days_to_int(row['days'])
    account_type = row['account_type_code']
    contra_flag = row['contra_flag']
    
    # Check margin accounts
    if account_type in ['V', 'M']:
        margin_pu = str(row.get('margin_pu', '')).strip().upper()
        if margin_pu == 'NO':
            is_local = currency in LOCAL_CURRENCIES
            if is_local:
                if days >= 2: return 'FORCE_SELLING'
                elif days >= 1: return 'REMINDER'
            else:
                if days >= 1: return 'FORCE_SELLING'
                elif days >= 0: return 'REMINDER'
    
    # Check non-margin accounts
    if account_type not in ['V', 'M'] and contra_flag != 'Y':
        return None
    
    is_local = currency in LOCAL_CURRENCIES
    is_foreign = currency in FOREIGN_CURRENCIES
    
    if days is None:
        return None
    
    if is_local:
        if days >= 2: return 'FORCE_SELLING'
        elif days == 1: return 'REMINDER'
    elif is_foreign:
        if days >= 1: return 'FORCE_SELLING'
        elif days == 0: return 'REMINDER'
    
    return None

def generate_message(row, action_type):
    name = row['account_name']
    quantity = row['quantity']
    security = row['security_name']
    
    if action_type == 'REMINDER':
        return f"""Good morning Mr/Ms {name}, please note that your purchase for {quantity} shares of {security} is due for contra/settlement today.

Thank you"""
    
    elif action_type == 'FORCE_SELLING':
        return f"""Good morning Mr/Ms {name}, please be informed that today is forceselling day for your purchase for {quantity} shares of {security}.

Kindly inform us if you are keen to pick up the purchase. If so, please make payment via Paynow or FAST transfer and send us proof of payment before 2pm today.

If opting to force sell instead, please inform us and do not sell the shares yourself. Please note that forceselling will result in a buy suspension for 7 days.

Thank you"""
    
    return ''

def create_excel_output(df_action, df_messages_reminder, df_messages_forcesell):
    """Create Excel file with 3 sheets"""
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Sheet 1: Action Summary
        df_summary = df_action[['account_name', 'account_number', 'action_needed']].copy()
        df_summary.columns = ['Name', 'Account', 'Action Needed']
        df_summary['Action Needed'] = df_summary['Action Needed'].replace({
            'REMINDER': 'Yes, last day for contra/settlement.',
            'FORCE_SELLING': 'Yes, forcesell day'
        })
        df_summary.to_excel(writer, sheet_name='Action Summary', index=False)
        
        # Sheet 2: Reminder Messages
        df_messages_reminder.to_excel(writer, sheet_name='Reminder Messages', index=False)
        
        # Sheet 3: Force Selling Messages
        df_messages_forcesell.to_excel(writer, sheet_name='Force Selling Messages', index=False)
    
    output.seek(0)
    return output

# ============================================================================
# STREAMLIT UI
# ============================================================================

st.title("📊 Share Awaiting Account Analyzer")
st.markdown("Upload your Share Awaiting Excel file to generate action items and client messages")

# # Sidebar
# with st.sidebar:
#     st.header("ℹ️ About")
#     st.markdown("""
#     This tool analyzes share awaiting accounts and generates:
#     - **Reminder messages for Contra / Settlement** for Day 1 (LOCAL) / Day 0 (FOREIGN)
#     - **Force selling alerts** for Day 2+ (LOCAL) / Day 1+ (FOREIGN)
    
#     ### Business Logic:
#     - ✅ Checks Payment Reference
#     - ✅ Checks Margin PU for V/M accounts
#     - ✅ Applies currency-specific rules
#     - ✅ Generates ready-to-send messages
#     """)
    
#     st.header("🌍 Currencies")
#     st.markdown(f"""
#     **Local:** {', '.join(LOCAL_CURRENCIES)}
    
#     **Foreign:** {', '.join(FOREIGN_CURRENCIES)}
#     """)

# File upload
uploaded_file = st.file_uploader(
    "Upload Excel file",
    type=['xlsx', 'xls'],
    help="Upload your Share Awaiting Excel file"
)

if uploaded_file is not None:
    try:
        with st.spinner("Processing file..."):
            # Parse file
            df_transactions = parse_share_awaiting_file(uploaded_file)
            
            # Analyze
            df_transactions['action_needed'] = df_transactions.apply(analyze_transaction, axis=1)
            df_transactions['currency'] = df_transactions['settle_currency'].apply(normalize_currency)
            
            # Filter action required
            df_action = df_transactions[df_transactions['action_needed'].notna()].copy()
            
        # Display results
        st.success(f"✅ Analysis complete!")
        
        # Metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Transactions", len(df_transactions))
        
        with col2:
            st.metric("Action Required", len(df_action))
        
        with col3:
            reminders = len(df_action[df_action['action_needed'] == 'REMINDER'])
            st.metric("Reminders", reminders)
        
        with col4:
            force_sell = len(df_action[df_action['action_needed'] == 'FORCE_SELLING'])
            st.metric("Force Selling", force_sell, delta_color="inverse")
        
        if len(df_action) > 0:
            # Generate messages
            df_action['message'] = df_action.apply(
                lambda row: generate_message(row, row['action_needed']), axis=1
            )
            
            # Prepare message dataframes
            df_messages_reminder = df_action[df_action['action_needed'] == 'REMINDER'][[
                'account_name', 'account_number', 'security_name', 
                'quantity', 'currency', 'settle_amount', 'message'
            ]].copy()
            df_messages_reminder.columns = [
                'Client Name', 'Account Number', 'Security', 
                'Quantity', 'Currency', 'Amount', 'Message'
            ]
            
            df_messages_forcesell = df_action[df_action['action_needed'] == 'FORCE_SELLING'][[
                'account_name', 'account_number', 'security_name', 
                'quantity', 'currency', 'settle_amount', 'message'
            ]].copy()
            df_messages_forcesell.columns = [
                'Client Name', 'Account Number', 'Security', 
                'Quantity', 'Currency', 'Amount', 'Message'
            ]
            
            # Tabs for different views
            tab1, tab2, tab3 = st.tabs(["📋 Action Summary", "💬 Reminder Messages", "🔴 Force Selling Messages"])
            
            with tab1:
                st.subheader("Action Summary")
                summary_df = df_action[['account_name', 'account_number', 'action_needed']].copy()
                summary_df.columns = ['Name', 'Account', 'Action Needed']
                # Replace action codes with display text
                summary_df['Action Needed'] = summary_df['Action Needed'].replace({
                    'REMINDER': 'Yes, last day for contra/settlement.',
                    'FORCE_SELLING': 'Yes, forcesell day'
                })
                st.dataframe(summary_df, use_container_width=True, height=400)
            
            with tab2:
                st.subheader("Reminder Messages")
                if len(df_messages_reminder) > 0:
                    st.dataframe(df_messages_reminder, use_container_width=True, height=400)
                    
                    # Show sample message
                    with st.expander("📄 View Sample Message"):
                        st.text(df_messages_reminder.iloc[0]['Message'])
                else:
                    st.info("No reminder messages needed")
            
            with tab3:
                st.subheader("Force Selling Messages")
                if len(df_messages_forcesell) > 0:
                    st.dataframe(df_messages_forcesell, use_container_width=True, height=400)
                    
                    # Show sample message
                    with st.expander("📄 View Sample Message"):
                        st.text(df_messages_forcesell.iloc[0]['Message'])
                else:
                    st.info("No force selling messages needed")
            
            # Download button
            st.markdown("---")
            excel_file = create_excel_output(df_action, df_messages_reminder, df_messages_forcesell)
            
            st.download_button(
                label="📥 Download Excel Report",
                data=excel_file,
                file_name=f'Share_Awaiting_Messages_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx',
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                type="primary",
                use_container_width=True
            )
            
        else:
            st.success("✅ All accounts are settled - no actions required!")
            
    except Exception as e:
        st.error(f"Error processing file: {str(e)}")
        st.exception(e)

else:
    # Show instructions when no file uploaded
    st.info("👆 Upload your Share Awaiting Excel file to get started")
    
    with st.expander("📖 How to use"):
        st.markdown("""
        1. **Upload** your Share Awaiting Excel file
        2. **Review** the analysis results
        3. **Download** the Excel report with messages
        
        The report contains 3 sheets:
        - **Action Summary**: Quick list of all accounts requiring action
        - **Reminder Messages**: Ready-to-send reminder messages
        - **Force Selling Messages**: Urgent force selling alerts
        """)
