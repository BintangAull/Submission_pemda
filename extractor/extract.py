import requests
from bs4 import BeautifulSoup
import random
import time

from config import (
    BASE_URL,
    MAX_PAGE,
    REQUEST_TIMEOUT,
    MIN_DELAY,
    MAX_DELAY,
    HEADERS
)

session = requests.Session()

session.headers.update(HEADERS)

# Fungsi ini untuk melakukan request ke
# halaman web yang akan di scrapping

def get_html(url):

    # variable untuk percobaan kalo ternyata server
    # kasih response sibuk 429
    max_retry = 3

    for attempt in range(max_retry):
        try:
            print(f"Request -> {url}")

            response = session.get(
                url,
                timeout=REQUEST_TIMEOUT
            )
            print(f"Status Code: {response.status_code}")

            # handle rate limit apabila ternyata server kasih kode 429
            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After")
                if retry_after:
                    wait_time = int(retry_after)
                else:
                    wait_time = (2 ** attempt) + random.uniform(1, 3)

                print(f"Kena rate limit")
                print(f"Waiting {wait_time:.2f} detik")
                time.sleep(wait_time)
                continue

            # Kalau status bukan 200
            response.raise_for_status()
            return response.text

        except requests.exceptions.RequestException as e:

            print(f"Request Error: {e}")

            # Exponential Backoff
            wait_time = (2 ** attempt) + random.uniform(1, 3)

            print(f"Retry dalam {wait_time:.2f} detik")

            time.sleep(wait_time)

    return None


# Fungsi ini untuk parsing produk yang diambil setelah
# melakukan request
def parse_products(html):
    soup = BeautifulSoup(html, "lxml")
    cards = soup.find_all(
        "div",
        class_="collection-card"
    )

    products = []

    for card in cards:

        try:
            # title
            title = card.find(
                "h3",
                class_="product-title"
            ).text.strip()

            # price
            price_element = card.find(
                class_="price"
            )

            price = price_element.text.strip()

            # Paragraf data
            paragraphs = card.find_all("p")

            rating = paragraphs[0].text.strip()
            colors = paragraphs[1].text.strip()
            size = paragraphs[2].text.strip()
            gender = paragraphs[3].text.strip()

            # struktur final data
            product = {
                "title": title,
                "price": price,
                "rating": rating,
                "colors": colors,
                "size": size,
                "gender": gender
            }

            products.append(product)

        except Exception as e:

            print("Parse Product Error")
            print(e)

    return products


# fungsi untuk menejalankan semua fungsi extract
# agar file main hanya fokus pada flow aplikasi saja tidak menangani logic berat
def scrape_products():

    all_products = []

    for page in range(1, MAX_PAGE + 1):

        print("\n" + "=" * 50)
        print(f"SCRAPING PAGE {page}")
        print("=" * 50)

        # page url
        if page == 1:

            url = BASE_URL

        else:

            url = f"{BASE_URL}/page{page}"

        # get html
        html = get_html(url)

        if html is None:

            print("HTML gagal diambil")

            continue

        # parsing data
        products = parse_products(html)

        print(f"Products ditemukan: {len(products)}")

        all_products.extend(products)

        # random delay
        sleep_time = random.uniform(
            MIN_DELAY,
            MAX_DELAY
        )

        print(f"Sleep {sleep_time:.2f} detik")

        time.sleep(sleep_time)

    return all_products