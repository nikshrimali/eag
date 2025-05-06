from mcp.server.fastmcp import FastMCP, Context
import httpx
from bs4 import BeautifulSoup
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
import urllib.parse
import sys
import traceback
import asyncio
from datetime import datetime, timedelta
import time
import re
import json  # For parsing JSON data
import re  # For regular expression pattern matching
from google.oauth2 import service_account  # For handling Google service account authentication
from googleapiclient.discovery import build  # For building Google API service clients

import os

from dotenv import load_dotenv
# Load environment variables from .env file
load_dotenv()

from logging import Logger
# Initialize logger
logger = Logger(__name__)

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


@dataclass
class SearchResult:
    title: str
    link: str
    snippet: str
    position: int


class RateLimiter:
    def __init__(self, requests_per_minute: int = 30):
        self.requests_per_minute = requests_per_minute
        self.requests = []

    async def acquire(self):
        now = datetime.now()
        # Remove requests older than 1 minute
        self.requests = [
            req for req in self.requests if now - req < timedelta(minutes=1)
        ]

        if len(self.requests) >= self.requests_per_minute:
            # Wait until we can make another request
            wait_time = 60 - (now - self.requests[0]).total_seconds()
            if wait_time > 0:
                await asyncio.sleep(wait_time)

        self.requests.append(now)


class DuckDuckGoSearcher:
    BASE_URL = "https://html.duckduckgo.com/html"
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    def __init__(self):
        self.rate_limiter = RateLimiter()

    def format_results_for_llm(self, results: List[SearchResult]) -> str:
        """Format results in a natural language style that's easier for LLMs to process"""
        if not results:
            return "No results were found for your search query. This could be due to DuckDuckGo's bot detection or the query returned no matches. Please try rephrasing your search or try again in a few minutes."

        output = []
        output.append(f"Found {len(results)} search results:\n")

        for result in results:
            output.append(f"{result.position}. {result.title}")
            output.append(f"   URL: {result.link}")
            output.append(f"   Summary: {result.snippet}")
            output.append("")  # Empty line between results

        return "\n".join(output)

    async def search(
        self, query: str, ctx: Context, max_results: int = 10
    ) -> List[SearchResult]:
        try:
            # Apply rate limiting
            await self.rate_limiter.acquire()

            # Create form data for POST request
            data = {
                "q": query,
                "b": "",
                "kl": "",
            }

            await ctx.info(f"Searching DuckDuckGo for: {query}")

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.BASE_URL, data=data, headers=self.HEADERS, timeout=30.0
                )
                response.raise_for_status()

            # Parse HTML response
            soup = BeautifulSoup(response.text, "html.parser")
            if not soup:
                await ctx.error("Failed to parse HTML response")
                return []

            results = []
            for result in soup.select(".result"):
                title_elem = result.select_one(".result__title")
                if not title_elem:
                    continue

                link_elem = title_elem.find("a")
                if not link_elem:
                    continue

                title = link_elem.get_text(strip=True)
                link = link_elem.get("href", "")

                # Skip ad results
                if "y.js" in link:
                    continue

                # Clean up DuckDuckGo redirect URLs
                if link.startswith("//duckduckgo.com/l/?uddg="):
                    link = urllib.parse.unquote(link.split("uddg=")[1].split("&")[0])

                snippet_elem = result.select_one(".result__snippet")
                snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""

                results.append(
                    SearchResult(
                        title=title,
                        link=link,
                        snippet=snippet,
                        position=len(results) + 1,
                    )
                )

                if len(results) >= max_results:
                    break

            await ctx.info(f"Successfully found {len(results)} results")
            return results

        except httpx.TimeoutException:
            await ctx.error("Search request timed out")
            return []
        except httpx.HTTPError as e:
            await ctx.error(f"HTTP error occurred: {str(e)}")
            return []
        except Exception as e:
            await ctx.error(f"Unexpected error during search: {str(e)}")
            traceback.print_exc(file=sys.stderr)
            return []


class WebContentFetcher:
    def __init__(self):
        self.rate_limiter = RateLimiter(requests_per_minute=20)

    async def fetch_and_parse(self, url: str, ctx: Context) -> str:
        """Fetch and parse content from a webpage"""
        try:
            await self.rate_limiter.acquire()

            await ctx.info(f"Fetching content from: {url}")

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                    },
                    follow_redirects=True,
                    timeout=30.0,
                )
                response.raise_for_status()

            # Parse the HTML
            soup = BeautifulSoup(response.text, "html.parser")

            # Remove script and style elements
            for element in soup(["script", "style", "nav", "header", "footer"]):
                element.decompose()

            # Get the text content
            text = soup.get_text()

            # Clean up the text
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = " ".join(chunk for chunk in chunks if chunk)

            # Remove extra whitespace
            text = re.sub(r"\s+", " ", text).strip()

            # Truncate if too long
            if len(text) > 8000:
                text = text[:8000] + "... [content truncated]"

            await ctx.info(
                f"Successfully fetched and parsed content ({len(text)} characters)"
            )
            return text

        except httpx.TimeoutException:
            await ctx.error(f"Request timed out for URL: {url}")
            return "Error: The request timed out while trying to fetch the webpage."
        except httpx.HTTPError as e:
            await ctx.error(f"HTTP error occurred while fetching {url}: {str(e)}")
            return f"Error: Could not access the webpage ({str(e)})"
        except Exception as e:
            await ctx.error(f"Error fetching content from {url}: {str(e)}")
            return f"Error: An unexpected error occurred while fetching the webpage ({str(e)})"


# Initialize FastMCP server
mcp = FastMCP("ddg-search")
searcher = DuckDuckGoSearcher()
fetcher = WebContentFetcher()


@mcp.tool()
async def search(query: str, ctx: Context, max_results: int = 10) -> str:
    """
    Search DuckDuckGo and return formatted results.

    Args:
        query: The search query string
        max_results: Maximum number of results to return (default: 10)
        ctx: MCP context for logging
    """
    try:
        results = await searcher.search(query, ctx, max_results)
        return searcher.format_results_for_llm(results)
    except Exception as e:
        traceback.print_exc(file=sys.stderr)
        return f"An error occurred while searching: {str(e)}"


@mcp.tool()
async def fetch_content(url: str, ctx: Context) -> str:
    """
    Fetch and parse content from a webpage URL.

    Args:
        url: The webpage URL to fetch content from
        ctx: MCP context for logging
    """
    return await fetcher.fetch_and_parse(url, ctx)


@mcp.tool()
def create_google_sheet_with_data(str_data: str|Dict) -> Dict[str, Any]:
    """
    Creates a Google Sheet with data and returns the public link.
    Usage: create_google_sheet_with_data| str_data='{"markdown": "1 | Max VerstappenVER | NED | Red Bull Racing Honda RBPT | 437 |\\n2 | Lando NorrisNOR | GBR | McLaren Mercedes | 374 |\\n3 | Charles LeclercLEC | MON | Ferrari | 356 |"}'
    
    Args:
        str_data: raw json string containing markdown formatted F1 standings data
    
    Returns:
        Dictionary with success status, message and spreadsheet URL
    """
    # Parse the JSON input - converts the JSON string into a Python dictionary

        # Parse the JSON input
    if isinstance(str_data, str):
        # If the input is a string, parse it as JSON
        try:
            data = json.loads(str_data)
        except json.JSONDecodeError:
            return {
                "success": False,
                "message": "Invalid JSON format"
            }
    # data = json.loads(data_json)
    # data = str_data
    
    # print(f"\n\n@@@###$$$$$ Received data for processing: {str_data}")
    # data = json.loads(str_data)
    data = str_data
    # print(data)
    
    # Extract the markdown text from the dictionary using the key 'markdown'
    # If the key doesn't exist, an empty string is returned as default
    markdown_text = data.get('markdown', '')
    logger.info(f"\n\nGot the markdown: {markdown_text}")
    
    # Initialize an empty list to store the rows of data we'll extract
    rows = []
    
    # Define column headers for our spreadsheet
    headers = ["Position", "Driver", "Code", "Nationality", "Team", "Points"]
    
    # Split the markdown text into lines and process each line
    for line in markdown_text.strip().split('\n'):
        # Use regular expression to extract data from each line
        # This pattern matches the specific format of the F1 standings data
        match = re.match(r'(\d+) \| ([A-Za-z ]+)([A-Z]{3}) \| ([A-Z]{3}) \| (.*) \| (\d+) \|', line)
        
        if match:
            # Extract each piece of data from the matched groups
            position = match.group(1)  # The driver's position (1st group in regex)
            driver = match.group(2).strip()  # Driver name (2nd group), removing extra spaces
            code = match.group(3)  # Driver code like VER, NOR, etc. (3rd group)
            nationality = match.group(4)  # Nationality code like NED, GBR (4th group)
            team = match.group(5).strip()  # Team name (5th group), removing extra spaces
            points = match.group(6)  # Points (6th group)
            
            # Add this row of data to our rows list
            rows.append([position, driver, code, nationality, team, points])
    
    print(rows)
    # Define the OAuth scopes we need
    # These determine what our application is allowed to do with Google's APIs
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    
    # Path to the service account credentials file
    SERVICE_ACCOUNT_FILE = '../credentials.json'
    
    # Create credentials object from the service account file
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    
    # Build the Google Sheets API client
    sheets_service = build('sheets', 'v4', credentials=credentials)
    
    # Build the Google Drive API client (needed for permission settings)
    drive_service = build('drive', 'v3', credentials=credentials)
    
    # Define a new spreadsheet with title "Formula 1 Driver Standings"
    spreadsheet = {
        'properties': {
            'title': 'Formula 1 Driver Standings'
        }
    }
    
    # Create the new spreadsheet using the Sheets API
    spreadsheet = sheets_service.spreadsheets().create(body=spreadsheet).execute()
    
    # Get the ID of the created spreadsheet (we'll need this for further operations)
    spreadsheet_id = spreadsheet.get('spreadsheetId')
    
    # Combine headers and data rows for insertion into spreadsheet
    values = [headers] + rows

    print(values)
    
    # Prepare the data for the update request
    body = {
        'values': values
    }
    
    # Update the spreadsheet with our data, starting at cell A1
    result = sheets_service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range='Sheet1!A1',  # Start at the first cell of Sheet1
        valueInputOption='RAW',  # Insert the values as-is without parsing
        body=body
    ).execute()
    
    # Format the spreadsheet with several operations
    requests = [
        # Freeze the first row (headers)
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
        # Make the header row bold with gray background
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
        # Auto-resize all columns to fit content
        {
            'autoResizeDimensions': {
                'dimensions': {
                    'sheetId': 0,  # First sheet in the spreadsheet
                    'dimension': 'COLUMNS',
                    'startIndex': 0,
                    'endIndex': 6  # We have 6 columns
                }
            }
        }
    ]
    
    # Execute the formatting operations in a batch
    sheets_service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={'requests': requests}
    ).execute()
    
    # Set permission to make the spreadsheet publicly viewable by anyone with the link
    drive_service.permissions().create(
        fileId=spreadsheet_id,
        body={
            'type': 'anyone',  # Share with anyone
            'role': 'reader'   # Read-only access
        }
    ).execute()
    
    # Construct the URL to the spreadsheet
    spreadsheet_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}"
    
    # Return a dictionary with information about the operation
    return {
        "success": True,
        "message": "Formula 1 standings sheet created successfully",
        "spreadsheet_url": spreadsheet_url
    }


@mcp.tool()
def send_email_with_sheet_link_smtp(recipient_email, sheet_url):
    """
    Sends an email with the Google Sheet link using SMTP.
    
    Args:
        recipient_email: Email address to send to
        sheet_url: URL of the Google Sheet to share
    
    Returns:
        Dictionary with success status and message
    """
    try:
        # Your Gmail credentials
        # Access your API key and initialize Gemini client correctly
        sender_email = os.getenv("SENDER_EMAIL")
        sender_pwd = os.getenv("SENDER_PWD")
                
        # Create message
        message = MIMEMultipart()
        message["From"] = sender_email
        message["To"] = recipient_email
        message["Subject"] = "Formula 1 Standings Sheet"
        
        # Email body
        body = f"""
        Hello,
        
        I've created a Google Sheet with Formula 1 driver standings data.
        
        You can access it here: {sheet_url}
        
        Regards,
        F1 Data Service
        """
        
        # Attach body to message
        message.attach(MIMEText(body, "plain"))
        
        # Connect to Gmail's SMTP server
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            # Login
            server.login(sender_email, sender_pwd)
            
            # Send email
            server.sendmail(
                sender_email, 
                recipient_email, 
                message.as_string()
            )
            
        return {
            "success": True,
            "message": f"Email sent successfully to {recipient_email}"
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Error sending email: {str(e)}"
        }




if __name__ == "__main__":
    print("mcp_server_3.py starting")
    if len(sys.argv) > 1 and sys.argv[1] == "dev":
            mcp.run()  # Run without transport for dev server
    else:
        mcp.run(transport="stdio")  # Run with stdio for direct execution
        print("\nShutting down...")