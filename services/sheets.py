import gspread
from oauth2client.service_account import ServiceAccountCredentials

scope = [
"https://spreadsheets.google.com/feeds",
"https://www.googleapis.com/auth/drive"
]

creds = ServiceAccountCredentials.from_json_keyfile_name(
"credentials.json",
scope
)

client = gspread.authorize(creds)

sheet = client.open("ClanDatabase")

players = sheet.worksheet("players")
history = sheet.worksheet("history")