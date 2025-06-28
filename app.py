from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import pandas as pd
from oauth2client.file import Storage
import gspread
from oauth2client.client import flow_from_clientsecrets
from oauth2client.tools import run_flow, argparser
import os, json
from oauth2client.service_account import ServiceAccountCredentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials


app = Flask(__name__)

def authorize_oauth():
    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    flow = InstalledAppFlow.from_client_secrets_file(
        '/etc/secrets/client_secret.json', scopes=scope
    )

    # Run the flow in console mode (without storing token.json)
    creds = flow.run_console()

    return gspread.authorize(creds)
    # store = Storage('/etc/secrets/token.json')
    # creds = store.get()
    # if not creds or creds.invalid:
    #     flow = flow_from_clientsecrets('/etc/secrets/client_secret.json', scope)
    #     creds = run_flow(flow, store, argparser.parse_args([]))
    # return gspread.authorize(creds)

def load_sheet_data():
    client = authorize_oauth()
    sheet = client.open_by_url('https://docs.google.com/spreadsheets/d/1hdflZHrim-qPNHeCgPr3J_6OBbggccjftziVGawzgY8/edit')
    worksheet = sheet.worksheet("Summary")
    rows = worksheet.get_all_values()
    header = rows[2]
    data = rows[3:]
    return pd.DataFrame(data, columns=header)

def fetch_sku_data_by_parent(parent_code, df):
    matching = df[df['Parent Code'] == parent_code]
    if matching.empty:
        return f"No SKUs found for parent code '{parent_code}'."

    messages = [f"📦 *Parent Code: {parent_code}*"]
    for _, row in matching.iterrows():
        messages.append(
            f"\n🔹 *{row['SKU Code']}*\n"
            f"GT Available: {row['Available Quantity']} | Online Available: {row['Available Quantity.']}\n"
            f"GT Pendency: {row['Pendency GT']} | Online Pendency: {row['Pendency Online']}"
        )
    return "\n".join(messages)

@app.route("/whatsapp", methods=["POST"])
def whatsapp_bot():
    msg = request.values.get('Body', '').strip().upper()
    parent_code = msg.replace("CHECK", "").strip()

    df = load_sheet_data()
    reply = fetch_sku_data_by_parent(parent_code, df)

    resp = MessagingResponse()
    resp.message(reply)
    return str(resp)

if __name__ == "__main__":
    app.run(port=5000, debug=True)
