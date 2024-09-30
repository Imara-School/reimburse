import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import os
import json
from google.oauth2 import service_account

# Google Sheets API setup
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

# Load the JSON string from the environment variable
creds_json = os.getenv("GOOGLE_CREDENTIALS")

# Parse the JSON string into a dictionary
creds_dict = json.loads(creds_json)

# Use the credentials dict to create the credentials object
creds = service_account.Credentials.from_service_account_info(creds_dict, scopes=scope)
client = gspread.authorize(creds)

# Access the Google Sheet
sheet = client.open("Imara Expense Reimbursement Request (Responses)").sheet1  # First worksheet in your Google Sheet

# Function to load data
def load_data():
    return pd.DataFrame(sheet.get_all_records())

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
    links = proof_links.split(', ')
    proof_html = ""
    for i, link in enumerate(links):
        proof_html += f'<a href="{link.strip()}" target="_blank">View Proof {i + 1}</a> '
    return proof_html

#page of submitted reuests
# Page of submitted requests
if page == "Submitted Requests":
    st.title("Submitted Requests")

    submitted_data = st.session_state.data[st.session_state.data['Status'] == 'Submitted']
    
    for index, row in submitted_data.iterrows():
        # Unique key for managing state
        update_key = f"update_{row['Request ID']}"

        # Create a card-like layout
        with st.container():
            proof_links = create_proof_links(row['Attach all receipts (only PDF or Image format is allowed)'])
            st.markdown(f"""
            <div style="border: 1px solid #ddd; border-radius: 10px; padding: 15px; margin-bottom: 15px; background-color: #010203;">
                <h4>Request ID: {row['Request ID']}</h4>
                <p><strong>Email Address:</strong> {row['Your Email']}</p>
                <p><strong>Purpose of Request:</strong> {row['What is this request for?']}</p>
                <p><strong>Amount:</strong> Rs. {row['Total amount requested?']}</p>
                <p><strong>Timestamp:</strong> {row['Timestamp']}</p>
                <p><strong>Status:</strong> {row['Status']}</p>
                <p><strong>Attached proof:</strong> {proof_links}</p>
            </div>
            """, unsafe_allow_html=True)

        # Button to trigger status update
        if st.button(f"Update Status for {row['Request ID']}", key=update_key):
            st.session_state.selected_request_id = row['Request ID']
            st.session_state.update_mode = True
            
        if st.session_state.get("update_mode") and st.session_state.get("selected_request_id") == row['Request ID']:
            with st.form(key=f"form_{row['Request ID']}"):
                st.markdown(f"**Update Status for Request ID: {row['Request ID']}**")
                
                # Input for the user's name
                changer_name = st.text_input("Enter your name:", key=f"name_{row['Request ID']}")
                
                # Dropdown for selecting the new status
                new_status = st.selectbox("Select new status:", ["Approved", "Not Approved"], key=f"select_{row['Request ID']}")
                
                # Always visible reason textbox with a hint
                reason = st.text_area("Enter the Reason if you are not approving:", key=f"reason_{row['Request ID']}")

                submit_button = st.form_submit_button("Update")

                if submit_button and changer_name:
                    # Update the sheet with the new status and the name of the person changing it
                    row_number = index + 2  # Because first row is the header
                    status_col = st.session_state.data.columns.get_loc("Status") + 1
                    changer_name_col = st.session_state.data.columns.get_loc("Changer Name") + 1

                    # Update the "Status" and "Changer Name"
                    sheet.update_cell(row_number, status_col, new_status)
                    sheet.update_cell(row_number, changer_name_col, changer_name)
                    
                    # If the status is 'Not Approved', update the "Reason" column as well
                    if new_status == "Not Approved":
                        reason_col = st.session_state.data.columns.get_loc("Reason") + 1
                        sheet.update_cell(row_number, reason_col, reason)

                    st.success(f"Status updated to {new_status} by {changer_name} for Request ID: {row['Request ID']}")
                    
                    # Set flag to show refresh button
                    st.session_state.show_refresh_button = True
                    # Reload the data
                    st.session_state.data = load_data()
                    # Reset update mode and selected request ID
                    st.session_state.update_mode = False
                    st.session_state.selected_request_id = None

            # Show the refresh button below the current popup
            if st.session_state.show_refresh_button:
                if st.button("Refresh Data", key=f"refresh_{row['Request ID']}"):
                    st.session_state.data = load_data()
                    st.session_state.show_refresh_button = False  # Hide the button again after refresh

#page of approved requests
elif page == "Approved Requests":
    st.title("Approved Requests")
    
    approved_data = st.session_state.data[st.session_state.data['Status'] == 'Approved']
    
    for index, row in approved_data.iterrows():
        # Unique key for managing state
        update_key = f"update_{row['Request ID']}"

        # Create a card-like layout
        with st.container():
            proof_links = create_proof_links(row['Attach all receipts (only PDF or Image format is allowed)'])
            st.markdown(f"""
            <div style="border: 1px solid #ddd; border-radius: 10px; padding: 15px; margin-bottom: 15px; background-color: #010203;">
                <h4>Request ID: {row['Request ID']}</h4>
                <p><strong>Email Address:</strong> {row['Your Email']}</p>
                <p><strong>Purpose of Request:</strong> {row['What is this request for?']}</p>
                <p><strong>Amount:</strong> Rs. {row['Total amount requested?']}
                <p><strong>Timestamp:</strong> {row['Timestamp']}</p>
                <p><strong>Status:</strong> {row['Status']}</p>
                <p><strong>Changer Name:</strong> {row['Changer Name']}</p>
                <p><strong>Attached proof:</strong> {proof_links}</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Button to trigger status update
        if st.button(f"Update Status for {row['Request ID']}", key=update_key):
            st.session_state.selected_request_id = row['Request ID']
            st.session_state.update_mode = True
            
        if st.session_state.get("update_mode") and st.session_state.get("selected_request_id") == row['Request ID']:
            with st.form(key=f"form_{row['Request ID']}"):
                st.markdown(f"**Update Status for Request ID: {row['Request ID']}**")
                
                # Input for the user's name
                changer_name = st.text_input("Enter your name:", key=f"name_{row['Request ID']}")
                
                new_status = st.selectbox("Select new status:", ["Paid"], key=f"select_{row['Request ID']}")
                submit_button = st.form_submit_button("Update")

                if submit_button and changer_name:
                    # Update the sheet with the new status and the name of the person changing it
                    row_number = index + 2  # Because first row is the header
                    status_col = st.session_state.data.columns.get_loc("Status") + 1
                    changer_name_col = st.session_state.data.columns.get_loc("Changer Name") + 1

                    sheet.update_cell(row_number, status_col, new_status)
                    sheet.update_cell(row_number, changer_name_col, changer_name)

                    st.success(f"Status updated to {new_status} by {changer_name} for Request ID: {row['Request ID']}")
                    
                    # Set flag to show refresh button
                    st.session_state.show_refresh_button = True
                    # Reload the data
                    st.session_state.data = load_data()
                    # Reset update mode and selected request ID
                    st.session_state.update_mode = False
                    st.session_state.selected_request_id = None

            # Show the refresh button below the current popup
            if st.session_state.show_refresh_button:
                if st.button("Refresh Data", key=f"refresh_{row['Request ID']}"):
                    st.session_state.data = load_data()
                    st.session_state.show_refresh_button = False  # Hide the button again after refresh

elif page == "Not Approved Requests":
    st.title("Not Approved Requests")
    
    notapproved_data = st.session_state.data[st.session_state.data['Status'] == 'Not Approved']
    
    for index, row in notapproved_data.iterrows():
        # Unique key for managing state
        update_key = f"update_{row['Request ID']}"

        # Create a card-like layout
        with st.container():
            proof_links = create_proof_links(row['Attach all receipts (only PDF or Image format is allowed)'])
            st.markdown(f"""
            <div style="border: 1px solid #ddd; border-radius: 10px; padding: 15px; margin-bottom: 15px; background-color: #010203;">
                <h4>Request ID: {row['Request ID']}</h4>
                <p><strong>Email Address:</strong> {row['Your Email']}</p>
                <p><strong>Purpose of Request:</strong> {row['What is this request for?']}</p>
                <p><strong>Amount:</strong> Rs. {row['Total amount requested?']}
                <p><strong>Timestamp:</strong> {row['Timestamp']}</p>
                <p><strong>Status:</strong> {row['Status']}</p>
                <p><strong>Changer Name:</strong> {row['Changer Name']}</p>
                <p><strong>Reason:</strong> {row['Reason']}</p>
                <p><strong>Attached proof:</strong> {proof_links}</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Button to trigger status update
        if st.button(f"Update Status for {row['Request ID']}", key=update_key):
            st.session_state.selected_request_id = row['Request ID']
            st.session_state.update_mode = True
            
        if st.session_state.get("update_mode") and st.session_state.get("selected_request_id") == row['Request ID']:
            with st.form(key=f"form_{row['Request ID']}"):
                st.markdown(f"**Update Status for Request ID: {row['Request ID']}**")
                
                # Input for the user's name
                changer_name = st.text_input("Enter your name:", key=f"name_{row['Request ID']}")
                
                new_status = st.selectbox("Select new status:", ["Approved"], key=f"select_{row['Request ID']}")
                submit_button = st.form_submit_button("Update")

                if submit_button and changer_name:
                    # Update the sheet with the new status and the name of the person changing it
                    row_number = index + 2  # Because first row is the header
                    status_col = st.session_state.data.columns.get_loc("Status") + 1
                    changer_name_col = st.session_state.data.columns.get_loc("Changer Name") + 1

                    sheet.update_cell(row_number, status_col, new_status)
                    sheet.update_cell(row_number, changer_name_col, changer_name)

                    st.success(f"Status updated to {new_status} by {changer_name} for Request ID: {row['Request ID']}")
                    
                    # Set flag to show refresh button
                    st.session_state.show_refresh_button = True
                    # Reload the data
                    st.session_state.data = load_data()
                    # Reset update mode and selected request ID
                    st.session_state.update_mode = False
                    st.session_state.selected_request_id = None

            # Show the refresh button below the current popup
            if st.session_state.show_refresh_button:
                if st.button("Refresh Data", key=f"refresh_{row['Request ID']}"):
                    st.session_state.data = load_data()
                    st.session_state.show_refresh_button = False  # Hide the button again after refresh

elif page == "Paid Requests":
    st.title("Paid Requests")
    
    # Filter paid requests
    paid_data = st.session_state.data[st.session_state.data['Status'] == 'Paid']
    
    for index, row in paid_data.iterrows():
        # Create a card-like layout for each request
        with st.container():
            proof_links = create_proof_links(row['Attach all receipts (only PDF or Image format is allowed)'])
            st.markdown(f"""
            <div style="border: 1px solid #ddd; border-radius: 10px; padding: 15px; margin-bottom: 15px; background-color: #010203;">
                <h4>Request ID: {row['Request ID']}</h4>
                <p><strong>Email Address:</strong> {row['Your Email']}</p>
                <p><strong>Purpose of Request:</strong> {row['What is this request for?']}</p>
                <p><strong>Amount:</strong> Rs. {row['Total amount requested?']}</p>
                <p><strong>Timestamp:</strong> {row['Timestamp']}</p>
                <p><strong>Status:</strong> {row['Status']}</p>
                <p><strong>Payment Done By:</strong> {row['Changer Name']}</p>
                <p><strong>Attached proof:</strong> {proof_links}</p>
            </div>
            """, unsafe_allow_html=True)


# All Records Page
elif page == "All Records":
    st.title("All Records")

    # Specify the columns to display in the order you want
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

    # Select only the relevant columns and rename them for display
    all_records_data = st.session_state.data[list(columns_to_display.keys())].rename(columns=columns_to_display)

    # Display the data as a table
    st.dataframe(all_records_data)

