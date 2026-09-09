import os
import requests
from dotenv import load_dotenv
import json
from pathlib import Path
from datetime import datetime, timezone

###############################
# Configuration
###############################

load_dotenv()

API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")

NOTION_TOKEN = os.getenv("NOTION_TOKEN")

NOTION_DATA_SOURCE_ID = os.getenv("NOTION_DATA_SOURCE_ID")

print("------------------------------------")
print("API key loaded:", API_KEY is not None)
print("API key length:", len(API_KEY) if API_KEY else 0)

THRESHOLD = 1.0

symbol = "VFV"

PRICE_FILE = Path(r"C:\Users\hyeri\Desktop\stock-notion-monitor\stock-notion-monitor\previous_prices.json")

# ==========================================
# LOAD PREVIOUS PRICE
# ==========================================

def load_previous_prices():

    if not PRICE_FILE.exists():
        return {}

    with open(PRICE_FILE, "r") as file:
        return json.load(file)


# ==========================================
# SAVE CURRENT PRICE
# ==========================================

def save_previous_prices(previous_prices):

    with open(PRICE_FILE, "w") as file:
        json.dump(previous_prices, file, indent=4)


# ==========================================
# GET CURRENT PRICE FROM ALPHA VANTAGE
# ==========================================

def get_current_price(symbol):

    url = "https://www.alphavantage.co/query"

    params = {
        "function": "GLOBAL_QUOTE",
        "symbol": symbol,
        "apikey": API_KEY
    }

    response = requests.get(url, params=params)

    response.raise_for_status()

    data = response.json()

    price = float(data["Global Quote"]["05. price"])

    return price


# ==========================================
# CALCULATE PERCENTAGE CHANGE
# ==========================================

def calculate_change(current_price, previous_price):

    if previous_price is None:
        return None

    return ((current_price - previous_price) / previous_price) * 100



# =====================================
# Creat a page under Notion Database
# =====================================
def send_alert_to_notion(
    symbol,
    current_price,
    previous_price,
    change_pct,
    direction
):

    url = "https://api.notion.com/v1/pages"

    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2026-03-11"
    }

    payload = {
        "parent": {
            "data_source_id": NOTION_DATA_SOURCE_ID
        },

        "properties": {

            "Stock": {
                "title": [
                    {
                        "text": {
                            "content": symbol
                        }
                    }
                ]
            },

            "Price": {
                "number": current_price
            },

            "Previous Price": {
                "number": previous_price
            },

            "Change %": {
                "number": change_pct
            },

            "Direction": {
                "select": {
                    "name": direction
                }
            },

            "Alert Time": {
                "date": {
                    "start": datetime.now(
                        timezone.utc
                    ).isoformat()
                }
            }
        }
    }


    response = requests.post(
        url,
        headers=headers,
        json=payload
    )

    print("Notion status code:", response.status_code)
    print("Notion response:")
    print(response.text)

    response.raise_for_status()

    print("Notion alert created successfully.")

    return response.json()


# ==========================================
# LOAD PREVIOUS PRICE
# ==========================================

previous_prices = load_previous_prices()

previous_price = previous_prices.get(symbol)


# ==========================================
# GET CURRENT PRICE
# ==========================================

current_price = get_current_price(symbol)


# ==========================================
# CALCULATE CHANGE
# ==========================================

change_pct = calculate_change(
    current_price,
    previous_price
)


# ==========================================
# CHECK THRESHOLD
# ==========================================

if change_pct is None:

    alert = False
    direction = None

elif change_pct >= THRESHOLD:

    alert = True
    direction = "Increase"

elif change_pct <= -THRESHOLD:

    alert = True
    direction = "Decrease"

else:

    alert = False
    direction = None



# ==========================================
# SEND ALERT TO NOTION
# ==========================================

if alert:

    send_alert_to_notion(
        symbol=symbol,
        current_price=current_price,
        previous_price=previous_price,
        change_pct=change_pct,
        direction=direction
    )


# ==========================================
# PRINT RESULT
# ==========================================

print("------------------------------------")

print(f"Ticker: {symbol}")
print(f"Current price: ${current_price:.2f}")
print(f"Previous price: ${previous_price}")

if change_pct is None:

    print("Change: N/A")

else:

    print(f"Change: {change_pct:+.2f}%")
    print(f"Threshold: ±{THRESHOLD:.2f}%")
    print(f"Alert: {'YES' if alert else 'NO'}")

    if alert:
        print(f"Direction: {direction}")

print("------------------------------------")


# ==========================================
# SAVE CURRENT PRICE FOR NEXT RUN
# ==========================================

previous_prices[symbol] = current_price

save_previous_prices(previous_prices)

print("Current price saved for next run.")
print("------------------------------------")