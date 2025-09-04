import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Function to authenticate and get the data from Google Sheets
def get_google_sheet_data(sheet_url):
    # Use credentials from Firebase service account
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name('path/to/your/serviceAccountKey.json', scope)
    client = gspread.authorize(creds)

    # Open Google Sheet by URL
    spreadsheet = client.open_by_url(sheet_url)
    
    # Accessing the first sheet (you can adjust this based on your sheet structure)
    worksheet = spreadsheet.get_worksheet(0)
    
    # Fetch all records
    data = worksheet.get_all_records()
    return data
