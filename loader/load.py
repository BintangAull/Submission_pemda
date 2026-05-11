# loader/load.py
import gspread
from google.oauth2.service_account import Credentials
from sqlalchemy import create_engine
from config import DATABASE_URL

# save to flat file csv
def save_to_csv(df, file_path):

    try:

        print(f"\nSaving CSV to: {file_path}")
        df.to_csv(
            file_path,
            index=False,
            encoding="utf-8-sig"
        )

        print("CSV saved successfully")

    except Exception as e:

        print(f"Error saving CSV: {e}")

        raise


def save_to_postgresql(df, table_name):
    try:
        print("\nConnecting to PostgreSQL...")
        engine = create_engine(
            DATABASE_URL,
            connect_args={
                "client_encoding": "utf8"
            }
        )
        print("Connection successful")

        df.to_sql(
            name=table_name,
            con=engine,
            if_exists="replace",
            index=False
        )

        print(f"Data successfully saved to table: {table_name}")

    except Exception as e:
        print(f"Error saving to PostgreSQL: {e}")


# Connect ke google sheet
def connect_gsheet(credentials_file):
    try:
        creds = Credentials.from_service_account_file(
            credentials_file,
            scopes=[
                "https://www.googleapis.com/auth/spreadsheets"
            ]
        )

        client = gspread.authorize(creds)

        print("Google Sheets authenticated successfully")

        return client

    except Exception as e:
        print(f"Error authenticating Google Sheets: {e}")
        raise

# fungsi ini untuk ubah tipe time stamp agar kolom TimeStamp dapat di insert ke database spreadsheet
def fix_timestamp_only(df):

    try:
        df = df.copy()

        if "Timestamp" in df.columns:
            df["Timestamp"] = df["Timestamp"].astype(str)

        return df
    except Exception as e:
        print(f"Error fixing timestamp only. Error: {e}")
        raise

# save to sjeet by id
def save_to_gsheet_by_id(df, credentials_file, spreadsheet_id, sheet_name="Sheet1"):
    try:
        client = connect_gsheet(credentials_file)

        print("Opening spreadsheet by ID...")

        spreadsheet = client.open_by_key(spreadsheet_id)

    except Exception as e:
        print("Spreadsheet not found or cannot be accessed.")
        raise FileNotFoundError(
            f"Spreadsheet ID invalid or not accessible: {spreadsheet_id}"
        ) from e

    try:
        worksheet = spreadsheet.worksheet(sheet_name)

    except gspread.WorksheetNotFound:
        raise ValueError(f"Sheet '{sheet_name}' not found in spreadsheet")

    try:
        print("Uploading data...")

        worksheet.clear()

        df = fix_timestamp_only(df)

        data = [df.columns.values.tolist()] + df.values.tolist()

        worksheet.update(data)

        print("Data successfully saved to Google Sheets")

    except Exception as e:
        print(f"Error writing to Google Sheets: {e}")
        raise




