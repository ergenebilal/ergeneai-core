"""
Google API integration module.
Handles authentication, Gmail, Calendar, Drive, and Sheets.
"""
import os
import pickle
import datetime

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


# === CONFIGURATION ===
GOOGLE_CREDENTIALS = os.path.expanduser("~/.google/credentials.json")
GOOGLE_TOKEN = os.path.expanduser("~/.google/token.pickle")
GOOGLE_SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/spreadsheets",
]


def authenticate():
    """Google API authentication — uses cached token if available, returns error otherwise.

    Returns:
        tuple: (credentials, error_message) — if error is not None, credentials is None
    """
    creds = None
    if os.path.exists(GOOGLE_TOKEN):
        with open(GOOGLE_TOKEN, "rb") as f:
            creds = pickle.load(f)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open(GOOGLE_TOKEN, "wb") as f:
                pickle.dump(creds, f)
            return creds, None
        return None, "❌ Google token invalid. Re-auth required: use get_auth_url() to get link."
    return creds, None


def get_auth_url():
    """Generates a new OAuth authorization URL (for manual click-through).

    Returns:
        str: Authorization URL or error message
    """
    try:
        flow = InstalledAppFlow.from_client_secrets_file(
            GOOGLE_CREDENTIALS, GOOGLE_SCOPES,
            redirect_uri="https://n8n.aiergene.xyz/webhook/google-oauth"
        )
        auth_url, _ = flow.authorization_url(
            access_type='offline', include_granted_scopes='true', prompt='consent'
        )
        return auth_url
    except Exception as e:
        return f"❌ Auth URL could not be created: {str(e)}"


def send_email(recipient, subject, body, html=False):
    """Sends an email via Gmail API.

    Args:
        recipient: Email address of the recipient
        subject: Email subject line
        body: Message body (plain text or HTML)
        html: True to send in HTML format

    Returns:
        str: Success or error message
    """
    try:
        creds, error = authenticate()
        if error:
            return error
        service = build("gmail", "v1", credentials=creds)
        import base64
        from email.mime.text import MIMEText
        message = MIMEText(body, "html" if html else "plain")
        message["to"] = recipient
        message["subject"] = subject
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        service.users().messages().send(userId="me", body={"raw": raw}).execute()
        return f"✅ Email sent: {recipient} -> {subject}"
    except Exception as e:
        return f"❌ Gmail error: {str(e)}"


def read_emails(max_results=5):
    """Fetches subject lines of recent emails from the inbox.

    Args:
        max_results: Maximum number of results (default: 5)

    Returns:
        list: List of dicts with 'id' and 'subject' keys, or error string
    """
    try:
        creds, error = authenticate()
        if error:
            return error
        service = build("gmail", "v1", credentials=creds)
        result = service.users().messages().list(userId="me", maxResults=max_results).execute()
        messages = result.get("messages", [])
        items = []
        for m in messages:
            detail = service.users().messages().get(userId="me", id=m["id"]).execute()
            subject = ""
            for h in detail.get("payload", {}).get("headers", []):
                if h["name"] == "Subject":
                    subject = h["value"]
                    break
            items.append({"id": m["id"][:8], "subject": subject})
        return items
    except Exception as e:
        return f"❌ Gmail read error: {str(e)}"


def add_calendar_event(title, start_time, end_time, description=""):
    """Adds an event to Google Calendar.

    Args:
        title: Event name
        start_time: ISO format start time (e.g. "2026-06-03T10:00:00")
        end_time: ISO format end time
        description: Optional description

    Returns:
        str: Success or error message
    """
    try:
        creds, error = authenticate()
        if error:
            return error
        service = build("calendar", "v3", credentials=creds)
        event = {
            "summary": title,
            "description": description,
            "start": {"dateTime": start_time, "timeZone": "Europe/Istanbul"},
            "end": {"dateTime": end_time, "timeZone": "Europe/Istanbul"},
        }
        service.events().insert(calendarId="primary", body=event).execute()
        return f"✅ Calendar event added: {title}"
    except Exception as e:
        return f"❌ Calendar error: {str(e)}"


def list_calendar_events(max_results=10):
    """Lists upcoming calendar events.

    Args:
        max_results: Maximum number of results (default: 10)

    Returns:
        list: List of dicts with 'title' and 'start' keys, or error string
    """
    try:
        creds, error = authenticate()
        if error:
            return error
        service = build("calendar", "v3", credentials=creds)
        now = datetime.datetime.utcnow().isoformat() + "Z"
        result = service.events().list(
            calendarId="primary", timeMin=now,
            maxResults=max_results, singleEvents=True,
            orderBy="startTime"
        ).execute()
        return [
            {"title": e.get("summary", ""),
             "start": e["start"].get("dateTime", e["start"].get("date"))}
            for e in result.get("items", [])
        ]
    except Exception as e:
        return f"❌ Calendar list error: {str(e)}"


def list_drive_files(folder_id="root", max_results=10):
    """Lists files in Google Drive.

    Args:
        folder_id: Folder ID (default: "root")
        max_results: Maximum number of files

    Returns:
        list: List of file dicts or error string
    """
    try:
        creds, error = authenticate()
        if error:
            return error
        service = build("drive", "v3", credentials=creds)
        result = service.files().list(
            q=f"'{folder_id}' in parents and trashed=false",
            pageSize=max_results,
            fields="files(id, name, mimeType, size, createdTime)"
        ).execute()
        files = result.get("files", [])
        if not files:
            return "📂 No files found in Drive."
        return [
            {
                "id": d["id"],
                "name": d["name"],
                "type": d["mimeType"].split(".")[-1] if "." in d["mimeType"] else d["mimeType"],
                "size": f"{int(d.get('size', 0)) / 1024:.1f} KB" if d.get("size") else "unknown"
            }
            for d in files
        ]
    except Exception as e:
        return f"❌ Drive list error: {str(e)}"


def upload_drive_file(file_path, target_folder="root"):
    """Uploads a local file to Google Drive.

    Args:
        file_path: Path to the file to upload
        target_folder: Target folder ID (default: "root")

    Returns:
        str: Success or error message
    """
    try:
        if not os.path.exists(file_path):
            return f"❌ File not found: {file_path}"
        creds, error = authenticate()
        if error:
            return error
        service = build("drive", "v3", credentials=creds)
        from googleapiclient.http import MediaFileUpload
        file_name = os.path.basename(file_path)
        media = MediaFileUpload(file_path, resumable=True)
        metadata = {"name": file_name, "parents": [target_folder]}
        file = service.files().create(body=metadata, media_body=media, fields="id,name").execute()
        return f"✅ Uploaded to Drive: {file['name']} (ID: {file['id'][:20]}...)"
    except Exception as e:
        return f"❌ Drive upload error: {str(e)}"


def read_sheet(sheet_id, sheet_name="Sheet1", cell_range="A1:Z100"):
    """Reads data from Google Sheets.

    Args:
        sheet_id: The sheet ID (long code from URL)
        sheet_name: Sheet name (default: Sheet1)
        cell_range: Cell range (default: A1:Z100)

    Returns:
        list: List of rows or error string
    """
    try:
        creds, error = authenticate()
        if error:
            return error
        service = build("sheets", "v4", credentials=creds)
        range_name = f"{sheet_name}!{cell_range}"
        result = service.spreadsheets().values().get(
            spreadsheetId=sheet_id, range=range_name
        ).execute()
        values = result.get("values", [])
        if not values:
            return "📊 No data found in sheet."
        return values
    except Exception as e:
        return f"❌ Sheet read error: {str(e)}"


def write_sheet(sheet_id, sheet_name="Sheet1", cell_range="A1", data=None):
    """Writes data to Google Sheets.

    Args:
        sheet_id: The sheet ID
        sheet_name: Sheet name (default: Sheet1)
        cell_range: Starting cell range (default: A1)
        data: 2D list [[row1_col1, row1_col2], [row2_col1, row2_col2]]

    Returns:
        str: Success or error message
    """
    if data is None:
        return "❌ Data required"
    try:
        creds, error = authenticate()
        if error:
            return error
        service = build("sheets", "v4", credentials=creds)
        range_name = f"{sheet_name}!{cell_range}"
        body = {"values": data}
        result = service.spreadsheets().values().update(
            spreadsheetId=sheet_id, range=range_name,
            valueInputOption="USER_ENTERED", body=body
        ).execute()
        return f"✅ Written to sheet: {result.get('updatedCells', 0)} cells updated"
    except Exception as e:
        return f"❌ Sheet write error: {str(e)}"


def append_sheet(sheet_id, sheet_name="Sheet1", data=None):
    """Appends new rows to Google Sheets.

    Args:
        sheet_id: The sheet ID
        sheet_name: Sheet name (default: Sheet1)
        data: 2D list [[h1, h2], [h3, h4]]

    Returns:
        str: Success or error message
    """
    if data is None:
        return "❌ Data required"
    try:
        creds, error = authenticate()
        if error:
            return error
        service = build("sheets", "v4", credentials=creds)
        range_name = f"{sheet_name}!A1"
        body = {"values": data}
        result = service.spreadsheets().values().append(
            spreadsheetId=sheet_id, range=range_name,
            valueInputOption="USER_ENTERED", insertDataOption="INSERT_ROWS",
            body=body
        ).execute()
        return f"✅ Appended to sheet: {result.get('updates', {}).get('updatedRows', 0)} rows"
    except Exception as e:
        return f"❌ Sheet append error: {str(e)}"
