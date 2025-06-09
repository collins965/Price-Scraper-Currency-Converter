import requests
from bs4 import BeautifulSoup
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import time
import csv

# Constants
BASE_URL = "https://books.toscrape.com/catalogue/page-{}.html"
EXCHANGE_RATE_API = "https://api.exchangerate-api.com/v4/latest/GBP"
TARGET_CURRENCY = "KES"  # You can change this
HEADERS = {'User-Agent': 'Mozilla/5.0'}

def scrape_books(pages=1):
    products = []

    for page in range(1, pages + 1):
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

                if len(products) >= 10:
                    return products

        except requests.exceptions.RequestException as e:
            print(f"Error fetching page {page}: {e}")
            time.sleep(1)
    return products

def get_exchange_rate():
    try:
        res = requests.get(EXCHANGE_RATE_API, timeout=5)
        res.raise_for_status()
        data = res.json()
        return data['rates'].get(TARGET_CURRENCY, None)
    except Exception as e:
        print(f"Failed to fetch exchange rate: {e}")
        return 180.0  # fallback value for GBP to KES

def convert_prices(products, rate):
    for product in products:
        product["price_kes"] = round(product["price_gbp"] * rate, 2)
        product["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return products

def save_to_csv(products, filename="converted_prices.csv"):
    keys = products[0].keys()
    with open(filename, "w", newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(products)

def display_table(products):
    df = pd.DataFrame(products)
    print("\nProduct Prices (GBP to KES):\n")
    print(df[["name", "price_gbp", "price_kes", "timestamp"]])
    return df

def plot_prices(df):
    plt.figure(figsize=(10, 5))
    plt.bar(df["name"], df["price_gbp"], label="GBP", alpha=0.6)
    plt.bar(df["name"], df["price_kes"], label="KES", alpha=0.6)
    plt.xticks(rotation=90)
    plt.ylabel("Price")
    plt.title("Product Prices in GBP vs KES")
    plt.legend()
    plt.tight_layout()
    plt.show()

def main():
    print("Scraping product prices...")
    products = scrape_books()
    
    if not products:
        print("No products found.")
        return

    print("Fetching exchange rate...")
    rate = get_exchange_rate()

    print(f"Exchange Rate GBP to {TARGET_CURRENCY}: {rate}")
    products = convert_prices(products, rate)
    save_to_csv(products)

    df = display_table(products)
    plot_prices(df)

if __name__ == "__main__":
    main()
