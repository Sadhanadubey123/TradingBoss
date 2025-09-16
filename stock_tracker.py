# stock_tracker.py

import yfinance as yf
import requests
import csv
import os
from datetime import datetime
from config import STOCKS, BOT_TOKEN, CHAT_ID, LOG_FILE


def get_stock_updates():
    """Fetch stock updates for all tickers in config."""
    messages = []
    updates_list = []  # for logging

    for name, ticker in STOCKS.items():
        try:
            stock = yf.Ticker(ticker)
            data = stock.history(period="1d")
            if data.empty:
                continue

            last_quote = data.iloc[-1]
            price = round(last_quote["Close"], 2)
            open_price = round(last_quote["Open"], 2)
            change = round(((price - open_price) / open_price) * 100, 2)

            msg = f"{name} ({ticker})\nPrice: {price}\nChange: {change}%"
            messages.append(msg)

            updates_list.append({
                "date": datetime.now().strftime("%Y-%m-%d"),
                "stock": name,
                "ticker": ticker,
                "price": price,
                "open_price": open_price,
                "change_percent": change
            })

        except Exception:
            messages.append(f"{name}: Error fetching data")

    return "\n\n".join(messages), updates_list


def send_telegram_message(message):
    """Send message to Telegram bot."""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message}
    requests.post(url, data=payload)


def log_to_csv(updates_list):
    """Append daily updates to CSV file."""
    file_exists = os.path.isfile(LOG_FILE)
    with open(LOG_FILE, mode="a", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=["date", "stock", "ticker", "price", "open_price", "change_percent"])
        if not file_exists:
            writer.writeheader()
        for row in updates_list:
            writer.writerow(row)


def run_daily_update():
    """Main reusable function to run daily stock update."""
    updates, updates_list = get_stock_updates()
    today = datetime.now().strftime("%d-%m-%Y")
    final_message = f"Daily Stock Updates ({today})\n\n{updates}"

    # Send to Telegram
    send_telegram_message(final_message)

    # Save to CSV
    log_to_csv(updates_list)
