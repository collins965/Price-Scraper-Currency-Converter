import requests
from bs4 import BeautifulSoup
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import time
import csv

# Constants for the scraping and currency conversion
BASE_URL = "https://books.toscrape.com/catalogue/page-{}.html"
EXCHANGE_API_BASE = "https://api.exchangerate-api.com/v4/latest/GBP"
HEADERS = {'User-Agent': 'Mozilla/5.0'}

# Scrapes book names and GBP prices from paginated book listing site
def scrape_books(target_count=10):
    products = []
    page = 1  # Start from the first page

    while len(products) < target_count:
        try:
            url = BASE_URL.format(page)
            res = requests.get(url, headers=HEADERS, timeout=5)
            res.raise_for_status()
            soup = BeautifulSoup(res.text, "html.parser")

            books = soup.select(".product_pod")
            for book in books:
                name = book.h3.a["title"]
                price_text = book.select_one(".price_color").text.strip()  # e.g., £51.77
                price_gbp = float(price_text.replace("£", ""))
                products.append({"name": name, "price_gbp": price_gbp})

                # Stop collecting once we reach the target count
                if len(products) >= target_count:
                    break

            page += 1  # Move to the next page
        except requests.exceptions.RequestException as e:
            print(f"Error fetching page {page}: {e}")
            time.sleep(1)  # Short delay before stopping
            break

    return products

# Retrieves the exchange rate between GBP and the given target currency
def get_exchange_rate(target_currency):
    try:
        res = requests.get(EXCHANGE_API_BASE, timeout=5)
        res.raise_for_status()
        data = res.json()
        rate = data['rates'].get(target_currency.upper(), None)
        if rate is None:
            raise ValueError(f"Currency '{target_currency}' not supported.")
        return rate
    except Exception as e:
        # If API fails, return a fallback rate (e.g., for KES)
        print(f"Failed to fetch exchange rate ({e}), using fallback rate.")
        return 180.0  # fallback value

# Adds converted currency price and timestamp to each product
def convert_prices(products, rate, target_currency):
    for product in products:
        product[f"price_{target_currency.lower()}"] = round(product["price_gbp"] * rate, 2)
        product["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return products

# Writes product data to a CSV file
def save_to_csv(products, filename="converted_prices.csv"):
    keys = products[0].keys()
    with open(filename, "w", newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(products)

# Displays the prices in GBP and target currency in a table format
def display_table(products, target_currency):
    df = pd.DataFrame(products)
    print(f"\nProduct Prices (GBP to {target_currency.upper()}):\n")
    cols = ["name", "price_gbp", f"price_{target_currency.lower()}", "timestamp"]
    print(df[cols])
    return df

# Plots a bar chart comparing GBP and target currency prices for each product
def plot_prices(df, target_currency):
    plt.figure(figsize=(10, 5))
    plt.bar(df["name"], df["price_gbp"], label="GBP", alpha=0.6)
    plt.bar(df["name"], df[f"price_{target_currency.lower()}"], label=target_currency.upper(), alpha=0.6)
    plt.xticks(rotation=90)
    plt.ylabel("Price")
    plt.title(f"Product Prices in GBP vs {target_currency.upper()}")
    plt.legend()
    plt.tight_layout()
    plt.show()

# Main function that handles input, processing, and flow control
def main():
    print("=== Price Scraper + Currency Converter ===")
    
    # Get number of products to scrape, default to 10 on invalid input
    try:
        num_products = int(input("Enter number of products to scrape (min 10): "))
        if num_products < 1:
            raise ValueError
    except ValueError:
        num_products = 10
        print("Invalid input. Defaulting to 10 products.")

    # Get target currency or default to KES
    target_currency = input("Enter target currency code (e.g., KES, USD, EUR): ").strip().upper()
    if not target_currency:
        target_currency = "KES"
        print("No input provided. Defaulting to KES.")

    print("Scraping product prices...")
    products = scrape_books(num_products)

    if not products:
        print("No products found.")
        return

    print(f"Fetching exchange rate GBP to {target_currency}...")
    rate = get_exchange_rate(target_currency)
    print(f"Exchange rate: 1 GBP = {rate} {target_currency}")

    products = convert_prices(products, rate, target_currency)
    save_to_csv(products)

    df = display_table(products, target_currency)

    # Ask user if they want to see a chart
    plot_choice = input("Would you like to see a bar chart? (y/n): ").strip().lower()
    if plot_choice == 'y':
        plot_prices(df, target_currency)

if __name__ == "__main__":
    main()
