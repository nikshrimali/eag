import json
import re
from google.oauth2 import service_account
from googleapiclient.discovery import build

def create_f1_standings_sheet(data_json):
    """
    Creates a Google Sheet with F1 standings data and returns the public link.
    
    Args:
        data_json: JSON string containing markdown formatted F1 standings data
    
    Returns:
        String URL to the created Google Sheet
    """
    # Parse the JSON input
    data = json.loads(data_json)
    markdown_text = data.get('markdown', '')
    
    # Process the markdown to extract structured data
    rows = []
    headers = ["Position", "Driver", "Code", "Nationality", "Team", "Points"]
    
    # Split the markdown into lines and process each line
    for line in markdown_text.strip().split('\n'):
        # Extract data using regex
        match = re.match(r'(\d+) \| ([A-Za-z ]+)([A-Z]{3}) \| ([A-Z]{3}) \| (.*) \| (\d+) \|', line)
        if match:
            position = match.group(1)
            driver = match.group(2).strip()
            code = match.group(3)
            nationality = match.group(4)
            team = match.group(5).strip()
            points = match.group(6)
            
            rows.append([position, driver, code, nationality, team, points])
    
    # Set up credentials
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    SERVICE_ACCOUNT_FILE = 'credentials.json'  # You need to create this service account file
    
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    
    # Create the Sheets API client
    sheets_service = build('sheets', 'v4', credentials=credentials)
    drive_service = build('drive', 'v3', credentials=credentials)
    
    # Create a new spreadsheet
    spreadsheet = {
        'properties': {
            'title': 'Formula 1 Driver Standings'
        }
    }
    spreadsheet = sheets_service.spreadsheets().create(body=spreadsheet).execute()
    spreadsheet_id = spreadsheet.get('spreadsheetId')
    
    # Prepare the data for batch update
    values = [headers] + rows
    
    body = {
        'values': values
    }
    
    # Update the sheet with data
    result = sheets_service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range='Sheet1!A1',
        valueInputOption='RAW',
        body=body
    ).execute()
    
    # Format the sheet
    requests = [
        {
            'updateSheetProperties': {
                'properties': {
                    'gridProperties': {
                        'frozenRowCount': 1
                    }
                },
                'fields': 'gridProperties.frozenRowCount'
            }
        },
        {
            'repeatCell': {
                'range': {
                    'startRowIndex': 0,
                    'endRowIndex': 1
                },
                'cell': {
                    'userEnteredFormat': {
                        'textFormat': {
                            'bold': True
                        },
                        'backgroundColor': {
                            'red': 0.8,
                            'green': 0.8,
                            'blue': 0.8
                        }
                    }
                },
                'fields': 'userEnteredFormat(textFormat,backgroundColor)'
            }
        },
        {
            'autoResizeDimensions': {
                'dimensions': {
                    'sheetId': 0,
                    'dimension': 'COLUMNS',
                    'startIndex': 0,
                    'endIndex': 6
                }
            }
        }
    ]
    
    sheets_service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={'requests': requests}
    ).execute()
    
    # Make the spreadsheet publicly viewable
    drive_service.permissions().create(
        fileId=spreadsheet_id,
        body={
            'type': 'anyone',
            'role': 'reader'
        }
    ).execute()
    
    # Get the spreadsheet URL
    spreadsheet_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}"
    
    return {
        "success": True,
        "message": "Formula 1 standings sheet created successfully",
        "spreadsheet_url": spreadsheet_url
    }

# Example usage
if __name__ == "__main__":
    test_data = '{"markdown": "1 | Max VerstappenVER | NED | Red Bull Racing Honda RBPT | 437 |\\n2 | Lando NorrisNOR | GBR | McLaren Mercedes | 374 |\\n3 | Charles LeclercLEC | MON | Ferrari | 356 |"}'
    result = create_f1_standings_sheet(test_data)
    print(result)
