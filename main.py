import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

# Load Google Sheets API setup from Streamlit secrets
secrets = st.secrets["gcp"]
creds_dict = {
    "type": st.secrets["gcp"]["type"],
    "project_id": st.secrets["gcp"]["project_id"],
    "private_key_id": st.secrets["gcp"]["private_key_id"],
    "private_key": st.secrets["gcp"]["private_key"],
    "client_email": st.secrets["gcp"]["client_email"],
    "client_id": st.secrets["gcp"]["client_id"],
    "auth_uri": st.secrets["gcp"]["auth_uri"],
    "token_uri": st.secrets["gcp"]["token_uri"],
    "auth_provider_x509_cert_url": st.secrets["gcp"]["auth_provider_x509_cert_url"],
    "client_x509_cert_url": st.secrets["gcp"]["client_x509_cert_url"],
    "universe_domain": st.secrets["gcp"]["universe_domain"],
}

# Create credentials using the JSON from secrets
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict)
client = gspread.authorize(creds)

# Access the Google Sheet
sheet = client.open("Imara Expense Reimbursement Request (Responses)").sheet1  # First worksheet in your Google Sheet

# Function to load data
def load_data():
    records = sheet.get_all_records()
    if not records:
        # If the sheet is empty, return an empty DataFrame with expected columns
        return pd.DataFrame(columns=[
            'Timestamp', 'Request ID', 'Your Email', 'What is this request for?',
            'Total amount requested?', 'Attach all receipts (only PDF or Image format is allowed)',
            'Status', 'Changer Name', 'Reason', 'Previous Status'
        ])
    return pd.DataFrame(records)

# Set the page title and favicon
st.set_page_config(page_title="Imara Expense Reimbursement", page_icon="🧾")

# Page Layout
st.sidebar.image("icon.jpg", use_column_width=True)  # Add your image path here
st.sidebar.title("Pages: ")
page = st.sidebar.radio("Go to", ["Submitted Requests", "Approved Requests", "Not Approved Requests", "Paid Requests", "All Records"], index=0) 

# Initialize session state for data and refresh flag
if 'data' not in st.session_state:
    st.session_state.data = load_data()
if 'show_refresh_button' not in st.session_state:
    st.session_state.show_refresh_button = False
if 'selected_request_id' not in st.session_state:
    st.session_state.selected_request_id = None
if 'update_mode' not in st.session_state:
    st.session_state.update_mode = False

# Function to create proof links
def create_proof_links(proof_links):
    if pd.isna(proof_links):
        return "No proofs attached"
    links = proof_links.split(', ')
    proof_html = ""
    for i, link in enumerate(links):
        proof_html += f'<a href="{link.strip()}" target="_blank">View Proof {i + 1}</a> '
    return proof_html

# Function to display requests
def display_requests(filtered_data, status):
    if filtered_data.empty:
        st.info(f"No {status} requests found.")
        return

    for index, row in filtered_data.iterrows():
        update_key = f"update_{row['Request ID']}"
        
        with st.container():
            proof_links = create_proof_links(row.get('Attach all receipts (only PDF or Image format is allowed)', ''))
            st.markdown(f"""
            <div style="border: 1px solid #ddd; border-radius: 10px; padding: 15px; margin-bottom: 15px; background-color: #010203;">
                <h4>Request ID: {row['Request ID']}</h4>
                <p><strong>Email Address:</strong> {row['Your Email']}</p>
                <p><strong>Purpose of Request:</strong> {row['What is this request for?']}</p>
                <p><strong>Amount:</strong> Rs. {row['Total amount requested?']}</p>
                <p><strong>Timestamp:</strong> {row['Timestamp']}</p>
                <p><strong>Status:</strong> {row['Status']}</p>
                <p><strong>Changer Name:</strong> {row.get('Changer Name', 'N/A')}</p>
                <p><strong>Attached proof:</strong> {proof_links}</p>
            </div>
            """, unsafe_allow_html=True)
        if status != 'Paid':
            if st.button(f"Update Status for {row['Request ID']}", key=update_key):
                st.session_state.selected_request_id = row['Request ID']
                st.session_state.update_mode = True
            
            if st.session_state.get("update_mode") and st.session_state.get("selected_request_id") == row['Request ID']:
                handle_status_update(row, index)

# Function to handle status updates
def handle_status_update(row, index):
    with st.form(key=f"form_{row['Request ID']}"):
        st.markdown(f"**Update Status for Request ID: {row['Request ID']}**")
        
        changer_name = st.text_input("Enter your name:", key=f"name_{row['Request ID']}")
        
        current_status = row['Status']
        if current_status == 'Submitted':
            new_status_options = ["Approved", "Not Approved"]
        elif current_status == 'Approved':
            new_status_options = ["Paid"]
        elif current_status == 'Not Approved':
            new_status_options = ["Approved"]
        else:
            new_status_options = [current_status]  # No change allowed for other statuses
        
        new_status = st.selectbox("Select new status:", new_status_options, key=f"select_{row['Request ID']}")
        
        reason = ""
        if new_status == "Not Approved":
            reason = st.text_area("Enter the Reason if you are not approving:", key=f"reason_{row['Request ID']}")

        submit_button = st.form_submit_button("Update")

        if submit_button and changer_name:
            update_sheet(row, index, new_status, changer_name, reason)

# Function to update the Google Sheet
def update_sheet(row, index, new_status, changer_name, reason):
    row_number = index + 2  # Because first row is the header
    status_col = st.session_state.data.columns.get_loc("Status") + 1
    changer_name_col = st.session_state.data.columns.get_loc("Changer Name") + 1

    sheet.update_cell(row_number, status_col, new_status)
    sheet.update_cell(row_number, changer_name_col, changer_name)
    
    if new_status == "Not Approved" and reason:
        reason_col = st.session_state.data.columns.get_loc("Reason") + 1
        sheet.update_cell(row_number, reason_col, reason)

    st.success(f"Status updated to {new_status} by {changer_name} for Request ID: {row['Request ID']}")
    
    st.session_state.show_refresh_button = True
    st.session_state.data = load_data()
    st.session_state.update_mode = False
    st.session_state.selected_request_id = None

# Main app logic
if st.session_state.data.empty:
    st.warning("The Google Sheet is currently empty. No requests to display.")
else:
    if page == "Submitted Requests":
        st.title("Submitted Requests")
        submitted_data = st.session_state.data[st.session_state.data['Status'] == 'Submitted']
        display_requests(submitted_data, "Submitted")

    elif page == "Approved Requests":
        st.title("Approved Requests")
        approved_data = st.session_state.data[st.session_state.data['Status'] == 'Approved']
        display_requests(approved_data, "Approved")

    elif page == "Not Approved Requests":
        st.title("Not Approved Requests")
        not_approved_data = st.session_state.data[st.session_state.data['Status'] == 'Not Approved']
        display_requests(not_approved_data, "Not Approved")

    elif page == "Paid Requests":
        st.title("Paid Requests")
        paid_data = st.session_state.data[st.session_state.data['Status'] == 'Paid']
        display_requests(paid_data, "Paid")  

    elif page == "All Records":
        st.title("All Records")
        columns_to_display = {
            "Timestamp": "Timestamp",
            "Request ID": "Request ID",
            "What is this request for?": "Requested For",
            "Your Email": "Requester Mail",
            "Total amount requested?": "Amount Rs.",
            "Status": "Current Status",
            "Previous Status": "Previous Status",
            "Changer Name": "Changer Name",
        }
        all_records_data = st.session_state.data[list(columns_to_display.keys())].rename(columns=columns_to_display)
        st.dataframe(all_records_data)

    if st.session_state.show_refresh_button:
        if st.button("Refresh Data"):
            st.session_state.data = load_data()
            st.session_state.show_refresh_button = False
            st.rerun()
