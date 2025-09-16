# stock_tracker.py

import yfinance as yf
import requests
import csv
import os
from datetime import datetime
from config import STOCKS, BOT_TOKEN, CHAT_ID, LOG_FILE
import warnings

# Suppress yfinance UserWarnings for missing/delisted stocks
warnings.simplefilter(action='ignore', category=UserWarning)


def get_stock_updates():
    """
    Fetch stock updates for all tickers in config.
    Returns:
        message_str (str): Formatted stock updates for Telegram.
        updates_list (list): List of dicts for CSV logging.
    """
    messages = []
    updates_list = []

    for name, ticker in STOCKS.items():
        try:
            stock = yf.Ticker(ticker)
            data = stock.history(period="1d")

            if data.empty:
                messages.append(f"{name} ({ticker}): No data available today")
                continue

            last_quote = data.iloc[-1]
            price = round(last_quote["Close"], 2)
            open_price = round(last_quote["Open"], 2)
            change = round(((price - open_price) / open_price) * 100, 2)

            msg = f"{name} ({ticker})\nPrice: ₹{price}\nChange: {change}%"
            messages.append(msg)

            updates_list.append({
                "date": datetime.now().strftime("%Y-%m-%d"),
                "stock": name,
                "ticker": ticker,
                "price": price,
                "open_price": open_price,
                "change_percent": change
            })

        except Exception as e:
            messages.append(f"{name} ({ticker}): Error fetching data - {e}")

    return "\n\n".join(messages), updates_list


def send_telegram_message(message):
    """
    Send message to Telegram bot.
    Args:
        message (str): Text to send.
    """
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
        response = requests.post(url, data=payload)
        if not response.ok:
            print(f"Failed to send Telegram message: {response.text}")
    except Exception as e:
        print(f"Telegram send error: {e}")


def log_to_csv(updates_list):
    """
    Append daily updates to CSV file.
    Args:
        updates_list (list): List of stock update dicts.
    """
    try:
        file_exists = os.path.isfile(LOG_FILE)
        with open(LOG_FILE, mode="a", newline="") as file:
            writer = csv.DictWriter(file,
                                    fieldnames=["date", "stock", "ticker", "price", "open_price", "change_percent"])
            if not file_exists:
                writer.writeheader()
            for row in updates_list:
                writer.writerow(row)
    except PermissionError:
        print(f"Permission denied: Cannot write to {LOG_FILE}. Close the file if open and check folder permissions.")
    except Exception as e:
        print(f"Error writing CSV: {e}")


def run_daily_update():
    """
    Main reusable function to run daily stock update.
    Fetches data, sends Telegram message, and logs CSV.
    """
    updates, updates_list = get_stock_updates()
    if not updates_list:
        print("No updates to process today.")
        return

    today = datetime.now().strftime("%d-%m-%Y")
    final_message = f"*Daily Stock Updates ({today})*\n\n{updates}"

    # Send Telegram
    send_telegram_message(final_message)

    # Log CSV
    log_to_csv(updates_list)
    print(f"Stock updates logged for {today}")


if __name__ == "__main__":
    run_daily_update()
