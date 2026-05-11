# main.py

import os
import pandas as pd

from extractor.extract import scrape_products
from transformer.transform import transform_products


# variable path
RAW_DATA_PATH = "./data/raw/fashion_products.csv"
CLEAN_DATA_PATH = "./data/clean/clean_fashion_products.csv"


# main function program
def main():

    print("\nSTART PIPELINE\n")


    # cek raw data
    if os.path.exists(RAW_DATA_PATH):

        print("Raw CSV ditemukan")

        try:

            raw_df = pd.read_csv(RAW_DATA_PATH)

            print("Raw CSV berhasil dibaca")

        except Exception as e:

            print(f"Gagal membaca raw CSV: {e}")

            return

    else:

        print("Raw CSV tidak ditemukan")
        print("Mulai scraping...\n")


        # scaraping jika tidak ada
        raw_products = scrape_products()

        if not raw_products:

            print("Tidak ada data berhasil di scrape")

            return

        print(f"\nTotal raw data: {len(raw_products)}")

        # convert ke dataframe

        raw_df = pd.DataFrame(raw_products)

        # save data to csv file

        try:

            raw_df.to_csv(
                RAW_DATA_PATH,
                index=False,
                encoding="utf-8-sig"
            )

            print("\nRaw CSV berhasil disimpan")

        except Exception as e:

            print(f"Gagal menyimpan raw CSV: {e}")

            return

    # transform data
    try:

        clean_df = transform_products(raw_df)

    except Exception as e:

        print(f"Transform Error: {e}")

        return

    # save clean csv

    try:

        clean_df.to_csv(
            CLEAN_DATA_PATH,
            index=False,
            encoding="utf-8-sig"
        )

        print("\nClean CSV berhasil disimpan")

    except Exception as e:

        print(f"Gagal menyimpan clean CSV: {e}")


# run program
if __name__ == "__main__":
    main()