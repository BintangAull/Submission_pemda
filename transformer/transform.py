# transformer/transform.py
import numpy as np
import pandas as pd

# copy data raw
def copy_dataframe(df):
    try:
        print("\n copying dataframe")

        return df.copy()

    except Exception as e:

        print(f"Error at copy_dataframe: {e}")

        return df

# remove exact duplikat
def remove_exact_duplicates(df):

    try:

        print("\n removing exact duplicates")

        before = len(df)

        df = df.drop_duplicates()

        after = len(df)

        removed = before - after

        print(f"Duplicated removed: {removed}")

        return df

    except Exception as e:

        print(f"Error at remove_exact_duplicates: {e}")

        return df

# handle pseudo missing value like unknown produk etc
def handle_missing_values(df):

    try:

        print("\n handle missing values")

        df["Title"] = df["Title"].replace(
            "Unknown Product",
            np.nan
        )

        df["Price"] = df["Price"].replace(
            "Price Unavailable",
            np.nan
        )

        df["Rating"] = df["Rating"].replace(
            "Rating: ⭐ Invalid Rating / 5",
            np.nan
        )

        df["Rating"] = df["Rating"].replace(
            "Rating: Not Rated",
            np.nan
        )

        return df

    except Exception as e:

        print(f"Error at handle_missing_values: {e}")

        return df

# Remove missing value

def remove_missing_values(df):

    try:
        print("\n Remove Missing Values")

        before = len(df)

        # Drop semua row yang punya NaN
        df = df.dropna()

        after = len(df)

        removed = before - after

        print(f"Rows removed: {removed}")

        return df

    except Exception as e:
        print(f"Error at remove_missing_values: {e}")
        return df




# clean price struktur
def clean_price(df):

    try:

        print("\n Clean Price Structure")

        df["Price"] = df["Price"].str.replace(
            "$",
            "",
            regex=False
        )

        df["Price"] = pd.to_numeric(
            df["Price"],
            errors="coerce"
        )

        df["Price"] = df["Price"] * 16000

        return df

    except Exception as e:

        print(f"Error at clean_price: {e}")

        return df

# clean rating struktur
def clean_rating(df):

    try:
        print("\n Clean Rating Struktur")

        # Extract numeric rating
        df["Rating"] = df["Rating"].str.extract(
            r"(\d+\.\d+)"
        )

        return df
    except Exception as e:
        print(f"Error at clean_rating: {e}")
        return df


# Clean colors Struktur
def clean_colors(df):

    try:
        print("\n Clean Colors")

        df["Colors"] = df["Colors"].str.extract(
            r"(\d+)"
        )

        return df
    except Exception as e:
        print(f"Error at clean_colors: {e}")
        return df



# Clean Size Struktur
def clean_size(df):


    try:
        print("\n Clean Size Struktur")

        df["Size"] = df["Size"].str.replace(
            "Size:",
            "",
            regex=False
        )

        df["Size"] = df["Size"].str.strip()

        return df
    except Exception as e:
        print(f"Error at clean_size: {e}")
        return df




# Clean gender Struktur
def clean_gender(df):

    try:
        print("\n Clean Gender Struktur")

        df["Gender"] = df["Gender"].str.replace(
            "Gender:",
            "",
            regex=False
        )

        df["Gender"] = df["Gender"].str.strip()

        return df
    except Exception as e:
        print(f"Error at clean_gender: {e}")
        return df



# Standarisasi data
def standardize_data(df):

    try:
        print("\n Standardization")

        # title
        df["Title"] = df["Title"].str.title()

        # Size
        df["Size"] = df["Size"].str.upper()

        # gender
        df["Gender"] = df["Gender"].str.title()

        return df
    except Exception as e:
        print(f"Error at standardize_data: {e}")
        return df




# konversi tipe data
def convert_datatypes(df):

    try:

        print("\n convert datatypes")

        df["Price"] = df["Price"].astype("float64")

        df["Rating"] = df["Rating"].astype("float64")

        df["Colors"] = df["Colors"].astype("int64")

        df["Title"] = df["Title"].astype("object")

        df["Size"] = df["Size"].astype("object")

        df["Gender"] = df["Gender"].astype("object")

        return df

    except Exception as e:

        print(f"Error at convert_datatypes: {e}")

        return df


# validasi data
def validate_data(df):

    try:

        print("\n Validasi data")

        negative_price = df[df["Price"] < 0]

        print(f"Negative price rows: {len(negative_price)}")

        invalid_rating = df[df["Rating"] > 5]

        print(f"Invalid rating rows: {len(invalid_rating)}")

        return df

    except Exception as e:

        print(f"Error at validate_data: {e}")

        return df


# TRANSFORM DATA PIPELINE
def transform_products(raw_df):

    try:
        print("\nSTART TRANSFORMATION\n")

        # copy dataframe
        clean_df = copy_dataframe(raw_df)

        # remove exact duplikat
        clean_df = remove_exact_duplicates(
            clean_df
        )

        # handle missing values
        clean_df = handle_missing_values(
            clean_df
        )

        # remove null/nan data
        clean_df = remove_missing_values(
            clean_df
        )

        # celaning data

        clean_df = clean_price(clean_df)

        clean_df = clean_rating(clean_df)

        clean_df = clean_colors(clean_df)

        clean_df = clean_size(clean_df)

        clean_df = clean_gender(clean_df)

        # Standarisasi data
        clean_df = standardize_data(clean_df)

        # Konversi tipe data
        clean_df = convert_datatypes(clean_df)

        # Valdidasi data
        clean_df = validate_data(clean_df)

        print("\nTRANSFORMATION SUCCESS")

        return clean_df

    except Exception as e:
        print(f"Error at transform_products: {e}")

        raise Exception( " \n Data gagal di transformasi ")

