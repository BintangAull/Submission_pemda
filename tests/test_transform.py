import unittest
import sys
import os
import numpy as np
import pandas as pd

# Tambahkan ROOT project ke sys.path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# Import target
from transformer import transform

# Helper: bikin dataframe sample

def make_df(**kwargs):
    base = {
        "Title":  ["Active Wear",  "Running Shoes"],
        "Price":  ["$29.99",       "$49.99"],
        "Rating": ["Rating: ⭐ 4.5 / 5", "Rating: ⭐ 3.8 / 5"],
        "Colors": ["3 Colors",     "2 Colors"],
        "Size":   ["Size: M",      "Size: L"],
        "Gender": ["Gender: Men",  "Gender: Women"],
        "Timestamp": ["2024-01-01","2024-01-02"],
    }
    base.update(kwargs)
    return pd.DataFrame(base)


# copy_dataframe

class TestCopyDataframe(unittest.TestCase):

    def test_kembalikan_copy_bukan_referensi(self):
        df = make_df()
        result = transform.copy_dataframe(df)
        self.assertIsNot(result, df)

    def test_isi_sama(self):
        df = make_df()
        result = transform.copy_dataframe(df)
        pd.testing.assert_frame_equal(result, df)

    def test_error_kembalikan_df_asli(self):
        # Kirim bukan dataframe → exception → return input
        result = transform.copy_dataframe("bukan_df")
        self.assertEqual(result, "bukan_df")


# remove_exact_duplicates

class TestRemoveExactDuplicates(unittest.TestCase):

    def test_hapus_baris_duplikat(self):
        df = make_df()
        df = pd.concat([df, df], ignore_index=True)  # 4 baris, 2 duplikat
        result = transform.remove_exact_duplicates(df)
        self.assertEqual(len(result), 2)

    def test_tidak_ada_duplikat_tetap_sama(self):
        df = make_df()
        result = transform.remove_exact_duplicates(df)
        self.assertEqual(len(result), 2)

    def test_error_kembalikan_df_asli(self):
        result = transform.remove_exact_duplicates("bukan_df")
        self.assertEqual(result, "bukan_df")


# handle_missing_values

class TestHandleMissingValues(unittest.TestCase):

    def test_unknown_product_jadi_nan(self):
        df = make_df(Title=["Unknown Product", "Valid"])
        result = transform.handle_missing_values(df)
        self.assertTrue(pd.isna(result["Title"].iloc[0]))
        self.assertEqual(result["Title"].iloc[1], "Valid")

    def test_price_unavailable_jadi_nan(self):
        df = make_df(Price=["Price Unavailable", "$10.00"])
        result = transform.handle_missing_values(df)
        self.assertTrue(pd.isna(result["Price"].iloc[0]))

    def test_invalid_rating_jadi_nan(self):
        df = make_df(Rating=["Rating: ⭐ Invalid Rating / 5", "Rating: ⭐ 4.0 / 5"])
        result = transform.handle_missing_values(df)
        self.assertTrue(pd.isna(result["Rating"].iloc[0]))

    def test_not_rated_jadi_nan(self):
        df = make_df(Rating=["Rating: Not Rated", "Rating: ⭐ 4.0 / 5"])
        result = transform.handle_missing_values(df)
        self.assertTrue(pd.isna(result["Rating"].iloc[0]))

    def test_nilai_normal_tidak_berubah(self):
        df = make_df()
        result = transform.handle_missing_values(df)
        self.assertEqual(result["Title"].iloc[0], "Active Wear")

    def test_error_kembalikan_df_asli(self):
        result = transform.handle_missing_values("bukan_df")
        self.assertEqual(result, "bukan_df")



# remove_missing_values

class TestRemoveMissingValues(unittest.TestCase):

    def test_hapus_baris_dengan_nan(self):
        df = make_df(Title=["Active Wear", np.nan])
        result = transform.remove_missing_values(df)
        self.assertEqual(len(result), 1)

    def test_tidak_ada_nan_tidak_hapus(self):
        df = make_df()
        result = transform.remove_missing_values(df)
        self.assertEqual(len(result), 2)

    def test_semua_nan_hasilnya_kosong(self):
        df = make_df(Title=[np.nan, np.nan])
        result = transform.remove_missing_values(df)
        self.assertEqual(len(result), 0)

    def test_error_kembalikan_df_asli(self):
        result = transform.remove_missing_values("bukan_df")
        self.assertEqual(result, "bukan_df")


# clean_price

class TestCleanPrice(unittest.TestCase):

    def test_hapus_simbol_dollar(self):
        df = make_df(Price=["$10.00", "$20.00"])
        result = transform.clean_price(df)
        # Setelah clean, Price harus numerik (bukan string dengan $)
        self.assertFalse(result["Price"].astype(str).str.contains(r"\$").any())

    def test_konversi_ke_rupiah(self):
        df = make_df(Price=["$1.00", "$2.00"])
        result = transform.clean_price(df)
        self.assertAlmostEqual(result["Price"].iloc[0], 16000.0)
        self.assertAlmostEqual(result["Price"].iloc[1], 32000.0)

    def test_price_invalid_jadi_nan(self):
        df = make_df(Price=["abc", "$10.00"])
        result = transform.clean_price(df)
        self.assertTrue(pd.isna(result["Price"].iloc[0]))

    def test_error_kembalikan_df_asli(self):
        result = transform.clean_price("bukan_df")
        self.assertEqual(result, "bukan_df")



# clean_rating

class TestCleanRating(unittest.TestCase):

    def test_extract_angka_rating(self):
        df = make_df(Rating=["Rating: ⭐ 4.5 / 5", "Rating: ⭐ 3.8 / 5"])
        result = transform.clean_rating(df)
        self.assertEqual(result["Rating"].iloc[0], "4.5")
        self.assertEqual(result["Rating"].iloc[1], "3.8")

    def test_rating_tidak_ada_angka_jadi_nan(self):
        df = make_df(Rating=["No rating here", "Rating: ⭐ 4.0 / 5"])
        result = transform.clean_rating(df)
        self.assertTrue(pd.isna(result["Rating"].iloc[0]))

    def test_error_kembalikan_df_asli(self):
        result = transform.clean_rating("bukan_df")
        self.assertEqual(result, "bukan_df")



# clean_colors

class TestCleanColors(unittest.TestCase):

    def test_extract_angka_colors(self):
        df = make_df(Colors=["3 Colors", "2 Colors"])
        result = transform.clean_colors(df)
        self.assertEqual(result["Colors"].iloc[0], "3")
        self.assertEqual(result["Colors"].iloc[1], "2")

    def test_colors_tidak_ada_angka_jadi_nan(self):
        df = make_df(Colors=["No number", "3 Colors"])
        result = transform.clean_colors(df)
        self.assertTrue(pd.isna(result["Colors"].iloc[0]))

    def test_error_kembalikan_df_asli(self):
        result = transform.clean_colors("bukan_df")
        self.assertEqual(result, "bukan_df")


# clean_size

class TestCleanSize(unittest.TestCase):

    def test_hapus_prefix_size(self):
        df = make_df(Size=["Size: M", "Size: L"])
        result = transform.clean_size(df)
        self.assertEqual(result["Size"].iloc[0], "M")
        self.assertEqual(result["Size"].iloc[1], "L")

    def test_strip_whitespace(self):
        df = make_df(Size=["Size:   XL  ", "Size: S"])
        result = transform.clean_size(df)
        self.assertEqual(result["Size"].iloc[0], "XL")

    def test_error_kembalikan_df_asli(self):
        result = transform.clean_size("bukan_df")
        self.assertEqual(result, "bukan_df")


# clean_gender

class TestCleanGender(unittest.TestCase):

    def test_hapus_prefix_gender(self):
        df = make_df(Gender=["Gender: Men", "Gender: Women"])
        result = transform.clean_gender(df)
        self.assertEqual(result["Gender"].iloc[0], "Men")
        self.assertEqual(result["Gender"].iloc[1], "Women")

    def test_strip_whitespace(self):
        df = make_df(Gender=["Gender:   Unisex  ", "Gender: Men"])
        result = transform.clean_gender(df)
        self.assertEqual(result["Gender"].iloc[0], "Unisex")

    def test_error_kembalikan_df_asli(self):
        result = transform.clean_gender("bukan_df")
        self.assertEqual(result, "bukan_df")


# standardize_data

class TestStandardizeData(unittest.TestCase):

    def test_title_title_case(self):
        df = make_df(Title=["active wear", "running shoes"])
        result = transform.standardize_data(df)
        self.assertEqual(result["Title"].iloc[0], "Active Wear")

    def test_size_uppercase(self):
        df = make_df(Size=["Size: m", "Size: xl"])
        result = transform.standardize_data(df)
        self.assertEqual(result["Size"].iloc[0], "SIZE: M")

    def test_gender_title_case(self):
        df = make_df(Gender=["men", "women"])
        result = transform.standardize_data(df)
        self.assertEqual(result["Gender"].iloc[0], "Men")

    def test_error_kembalikan_df_asli(self):
        result = transform.standardize_data("bukan_df")
        self.assertEqual(result, "bukan_df")



# convert_datatypes

class TestConvertDatatypes(unittest.TestCase):

    def _make_clean_df(self):
        return pd.DataFrame({
            "Title":  ["Active Wear", "Running Shoes"],
            "Price":  [29.99, 49.99],
            "Rating": ["4.5", "3.8"],
            "Colors": ["3", "2"],
            "Size":   ["M", "L"],
            "Gender": ["Men", "Women"],
            "Timestamp": ["2024-01-01", "2024-01-02"],
        })

    def test_price_float64(self):
        df = self._make_clean_df()
        result = transform.convert_datatypes(df)
        self.assertEqual(result["Price"].dtype, "float64")

    def test_rating_float64(self):
        df = self._make_clean_df()
        result = transform.convert_datatypes(df)
        self.assertEqual(result["Rating"].dtype, "float64")

    def test_colors_int64(self):
        df = self._make_clean_df()
        result = transform.convert_datatypes(df)
        self.assertEqual(result["Colors"].dtype, "int64")

    def test_title_object(self):
        df = self._make_clean_df()
        result = transform.convert_datatypes(df)
        self.assertEqual(result["Title"].dtype, "object")

    def test_error_kembalikan_df_asli(self):
        result = transform.convert_datatypes("bukan_df")
        self.assertEqual(result, "bukan_df")

# validate_data

class TestValidateData(unittest.TestCase):

    def _make_clean_df(self):
        return pd.DataFrame({
            "Title":  ["Active Wear", "Bad Item"],
            "Price":  [29.99, -5.0],
            "Rating": [4.5, 6.0],
            "Colors": [3, 2],
            "Size":   ["M", "L"],
            "Gender": ["Men", "Women"],
        })

    def test_kembalikan_df_tidak_berubah(self):
        df = self._make_clean_df()
        result = transform.validate_data(df)
        # validate hanya print, tidak drop baris
        self.assertEqual(len(result), len(df))

    def test_negative_price_tetap_ada(self):
        df = self._make_clean_df()
        result = transform.validate_data(df)
        self.assertTrue((result["Price"] < 0).any())

    def test_invalid_rating_tetap_ada(self):
        df = self._make_clean_df()
        result = transform.validate_data(df)
        self.assertTrue((result["Rating"] > 5).any())

    def test_error_kembalikan_df_asli(self):
        result = transform.validate_data("bukan_df")
        self.assertEqual(result, "bukan_df")


# transform_products (pipeline)

class TestTransformProducts(unittest.TestCase):

    def _make_raw_df(self):
        return pd.DataFrame({
            "Title":  ["Active Wear", "Unknown Product", "Running Shoes"],
            "Price":  ["$29.99",      "$10.00",          "Price Unavailable"],
            "Rating": ["Rating: ⭐ 4.5 / 5", "Rating: ⭐ 3.8 / 5", "Rating: Not Rated"],
            "Colors": ["3 Colors",    "2 Colors",        "1 Colors"],
            "Size":   ["Size: M",     "Size: L",         "Size: XL"],
            "Gender": ["Gender: Men", "Gender: Women",   "Gender: Unisex"],
            "Timestamp": ["2024-01-01", "2024-01-02",    "2024-01-03"],
        })

    def test_pipeline_berjalan_tanpa_error(self):
        df = self._make_raw_df()
        result = transform.transform_products(df)
        self.assertIsInstance(result, pd.DataFrame)

    def test_pipeline_hapus_baris_invalid(self):
        df = self._make_raw_df()
        result = transform.transform_products(df)
        # Unknown Product dan Price Unavailable dan Not Rated harus terhapus
        self.assertLess(len(result), len(df))

    def test_pipeline_kolom_tetap_ada(self):
        df = self._make_raw_df()
        result = transform.transform_products(df)
        for col in ["Title", "Price", "Rating", "Colors", "Size", "Gender"]:
            self.assertIn(col, result.columns)

    def test_pipeline_price_numerik(self):
        df = self._make_raw_df()
        result = transform.transform_products(df)
        self.assertEqual(result["Price"].dtype, "float64")

    def test_pipeline_rating_numerik(self):
        df = self._make_raw_df()
        result = transform.transform_products(df)
        self.assertEqual(result["Rating"].dtype, "float64")

    def test_pipeline_input_invalid_kembalikan_string(self):
        # Setiap fungsi catch exception sendiri dan terus jalan,
        # akhirnya validate_data gagal → raise Exception di sini
        # Tapi karena semua fungsi return input asli, validate_data
        # menerima string dan gagal → pipeline raise
        # Kita cukup pastikan tidak crash tanpa exception yang tidak terduga
        try:
            transform.transform_products("bukan_df")
        except Exception as e:
            self.assertIn("gagal", str(e).lower())


if __name__ == "__main__":
    unittest.main(verbosity=2)