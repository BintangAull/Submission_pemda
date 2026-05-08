import pandas as pd

from extractor.extract import scrape_products
from transformer.transform import transform_products


def main():

    print("\nSTART PIPELINE\n")
    raw_products = scrape_products()

    if not raw_products:

        print("Tidak ada data berhasil di scrape")

        return

    print(f"\nTotal raw data: {len(raw_products)}")

    # TRANSFORM
    clean_products = transform_products(
        raw_products
    )
    try:
        # SAVE RAW CSV
        df = pd.DataFrame(clean_products)

        df.to_csv(
            "./data/raw/fashion_products.csv",
            index=False,
            encoding="utf-8-sig"
        )

        print("\nCSV berhasil disimpan")
    except Exception as e:
        print(f"error: {e}")

if __name__ == "__main__":
    main()