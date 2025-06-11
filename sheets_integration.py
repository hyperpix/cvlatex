import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import pickle
import json
from datetime import datetime

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

def get_google_sheets_service():
    """Get or create Google Sheets service with credentials."""
    creds = None
    # The file token.pickle stores the user's access and refresh tokens
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return build('sheets', 'v4', credentials=creds)

def save_cv_to_sheets(cv_data, spreadsheet_id):
    """
    Save CV data to Google Sheets.
    
    Args:
        cv_data (dict): The parsed CV data
        spreadsheet_id (str): The ID of the Google Spreadsheet to save to
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        service = get_google_sheets_service()
        
        # Prepare the data for the sheet
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Basic information
        basic_info = [
            timestamp,
            cv_data.get('name', ''),
            cv_data.get('email', ''),
            cv_data.get('phone', ''),
            cv_data.get('linkedin', ''),
            cv_data.get('github', ''),
            cv_data.get('website', ''),
            cv_data.get('address', '')
        ]
        
        # Education
        education_rows = []
        for edu in cv_data.get('education', []):
            education_rows.append([
                edu.get('degree', ''),
                edu.get('institution', ''),
                edu.get('date', ''),
                edu.get('location', ''),
                edu.get('gpa', ''),
                edu.get('details', '')
            ])
        
        # Experience
        experience_rows = []
        for exp in cv_data.get('experience', []):
            experience_rows.append([
                exp.get('title', ''),
                exp.get('company', ''),
                exp.get('date', ''),
                exp.get('location', ''),
                exp.get('description', '')
            ])
        
        # Skills
        skills = cv_data.get('skills', {})
        skills_row = [
            ', '.join(skills.get('languages', [])),
            ', '.join(skills.get('frameworks', [])),
            ', '.join(skills.get('tools', [])),
            ', '.join(skills.get('databases', [])),
            ', '.join(skills.get('other', []))
        ]
        
        # Prepare the batch update
        values = [
            ['Timestamp', 'Name', 'Email', 'Phone', 'LinkedIn', 'GitHub', 'Website', 'Address'],
            basic_info,
            [''],
            ['Education'],
            ['Degree', 'Institution', 'Date', 'Location', 'GPA', 'Details']
        ] + education_rows + [
            [''],
            ['Experience'],
            ['Title', 'Company', 'Date', 'Location', 'Description']
        ] + experience_rows + [
            [''],
            ['Skills'],
            ['Languages', 'Frameworks', 'Tools', 'Databases', 'Other'],
            skills_row
        ]
        
        body = {
            'values': values
        }
        
        # Append the data to the sheet
        result = service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id,
            range='Sheet1!A1',  # Start from A1
            valueInputOption='RAW',
            insertDataOption='INSERT_ROWS',
            body=body
        ).execute()
        
        print(f"✅ CV data saved to Google Sheets: {result.get('updates', {}).get('updatedRows', 0)} rows updated")
        return True
        
    except Exception as e:
        print(f"❌ Error saving CV data to Google Sheets: {e}")
        return False 
