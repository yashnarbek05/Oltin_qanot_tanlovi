from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from config import GOOGLE_SHEET_URL, KEYS_PATH, SHEET_NAME, WINNERS_COUNT

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

creds = Credentials.from_service_account_file(KEYS_PATH, scopes=SCOPES)

service = build("sheets", "v4", credentials=creds)
sheet = service.spreadsheets()


async def get_values_from_sheet():
    try:
        result = sheet.values().get(
            spreadsheetId=GOOGLE_SHEET_URL,
            range=f"{SHEET_NAME}!A2:D"
        ).execute()

        values = result.get("values", [])

        return values

    except HttpError as err:
        print(f"HTTP Error: {err}")
        return []

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return []

async def update_count(user_id):
    # count   = D row

    index = ''
    count = 0
    users = await get_values_from_sheet()

    for i in range (0,len(users)):
        if str(user_id) == users[i][0]:
            index = i
            count = users[i][3]
            break
     
    if index == '':
        return 0
    
    request = service.spreadsheets().values().update(spreadsheetId=GOOGLE_SHEET_URL, range=f'{SHEET_NAME}!D{index + 2}',
                                                     valueInputOption="RAW",
                                                     body={"values": [[int(count) + 1]]})
    response = request.execute()

    return response.get("updatedRows")

async def get_winnerss():
    users = await get_values_from_sheet()

    winners = sorted(
        users,
        key=lambda x: int(x[3]) if len(x) == 4  else 0,
        reverse=True)[:WINNERS_COUNT]
    
    return winners

async def get_count(user_id: int):

    users = await get_values_from_sheet()

    for user in users:
        if str(user_id) == user[0]:
            return user[3]
    
    return 0

async def is_registreted(user_id):
    
    users = await get_values_from_sheet()

    for user in users:
        if str(user_id) == user[0]:
            return True
    
    return False

async def add_user(user_id, contact, name):

    users = await get_values_from_sheet()

    request = service.spreadsheets().values().update(spreadsheetId=GOOGLE_SHEET_URL, range=f'{SHEET_NAME}!A{len(users) + 2}:D{len(users) + 2}',
                                                     valueInputOption="RAW",
                                                     body={"values": [[user_id, contact, name, 0]]})
    response = request.execute()

    return response.get("updatedRows")