import requests  # HTTP requests
from bs4 import BeautifulSoup  # HTML parsing
import pandas as pd  # Data handling
import matplotlib.pyplot as plt  # Plotting
from datetime import datetime  # Timestamping
import csv  # CSV file operations
import time  # Delay handling

BASE_URL = "https://books.toscrape.com/catalogue/page-{}.html"  # URL template for book pages
EXCHANGE_API = "https://api.exchangerate-api.com/v4/latest/GBP"  # Exchange rate API URL
HEADERS = {'User-Agent': 'Mozilla/5.0'}  # Request headers for scraping

def scrape_books(count=10):
    # Scrape book titles and prices from multiple pages until count reached
    books = []
    page = 1

    while len(books) < count:
        try:
            response = requests.get(BASE_URL.format(page), headers=HEADERS, timeout=5)  # Fetch page
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")  # Parse HTML

            for book in soup.select(".product_pod"):  # Loop through books on page
                title = book.h3.a["title"]  # Extract book title
                price = float(book.select_one(".price_color").text.replace("£", ""))  # Extract price
                books.append({"name": title, "price_gbp": price})  # Add to list

                if len(books) == count:
                    break  # Stop if desired count reached

            page += 1  # Next page

        except Exception as e:
            print(f"Error fetching page {page}: {e}")  # Print error
            time.sleep(1)  # Wait before stopping
            break

    return books  # Return list of books

def get_rate(currency):
    # Fetch exchange rate for currency; fallback to default if fails
    try:
        response = requests.get(EXCHANGE_API, timeout=5)  # Request rates
        data = response.json()
        return data['rates'].get(currency.upper(), 180.0)  # Get rate or default
    except Exception as e:
        print(f"Could not get exchange rate: {e}")
        return 180.0

def convert(books, rate, currency):
    # Convert GBP prices to target currency and add timestamp
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for book in books:
        book[f"price_{currency.lower()}"] = round(book["price_gbp"] * rate, 2)
        book["timestamp"] = now
    return books

def save_csv(data, filename="converted_prices.csv"):
    # Save book data as CSV file
    with open(filename, "w", newline='', encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)

def show_table(data, currency):
    # Display book data as a pandas DataFrame and print key columns
    df = pd.DataFrame(data)
    print(df[["name", "price_gbp", f"price_{currency.lower()}", "timestamp"]])
    return df

def plot(df, currency):
    # Plot GBP and converted prices side by side in bar chart
    plt.bar(df["name"], df["price_gbp"], label="GBP", alpha=0.6)
    plt.bar(df["name"], df[f"price_{currency.lower()}"], label=currency.upper(), alpha=0.6)
    plt.xticks(rotation=90)  # Rotate x labels
    plt.title(f"GBP vs {currency.upper()} Prices")
    plt.tight_layout()
    plt.legend()
    plt.show()

def main():
    # Main workflow: input, scrape, convert, save, display, optionally plot
    print("=== Book Price Scraper + Converter ===")

    try:
        count = int(input("How many books to scrape? "))  # Number of books
        if count < 1:
            count = 10
    except:
        count = 10  # Default count
        print("Invalid input. Defaulting to 10.")

    currency = input("Target currency (e.g., USD): ").strip().upper() or "KES"  # Target currency

    books = scrape_books(count)  # Scrape books
    if not books:
        print("No books found. Exiting.")
        return

    rate = get_rate(currency)  # Get exchange rate
    print(f"1 GBP = {rate} {currency}")
    books = convert(books, rate, currency)  # Convert prices

    save_csv(books)  # Save data to CSV
    df = show_table(books, currency)  # Show data table

    if input("Show chart? (y/n): ").lower() == 'y':  # Optionally plot
        plot(df, currency)

if __name__ == "__main__":
    main()