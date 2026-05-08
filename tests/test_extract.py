import unittest
from unittest.mock import patch, MagicMock
import requests
import types
import sys
import os

#  Path setup
# Tambahkan ROOT project ke sys.path agar `extractor` dan `config` bisa diimport
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# ── Config stub ────────────────────────────────────────────────────────────────
# Harus diinjeksi ke sys.modules SEBELUM mengimport extractor.extract,
# karena extract.py melakukan `import config` saat modul dimuat.
config_stub = types.ModuleType("config")
config_stub.BASE_URL         = "https://example.com"
config_stub.MAX_PAGE         = 3
config_stub.REQUEST_TIMEOUT  = 10
config_stub.MIN_DELAY        = 1
config_stub.MAX_DELAY        = 3
config_stub.HEADERS          = {"User-Agent": "TestBot/1.0"}
sys.modules["config"] = config_stub

# Import target
# Patch `requests.Session` sebelum modul dimuat supaya `session` di dalam
# extract.py tidak membuat koneksi nyata saat import.
with patch("requests.Session"):
    from extractor import extract  # noqa: E402  (import setelah sys.path diset)


# HTML helper
def make_product_html(
    title="Sepatu Keren",
    price="Rp 250.000",
    rating="4.5 / 5",
    colors="2 Colors",
    size="M",
    gender="Unisex",
    n=1,
):
    cards = ""
    for _ in range(n):
        cards += f"""
        <div class="collection-card">
            <h3 class="product-title">{title}</h3>
            <span class="price">{price}</span>
            <p>{rating}</p>
            <p>{colors}</p>
            <p>{size}</p>
            <p>{gender}</p>
        </div>
        """
    return f"<html><body>{cards}</body></html>"



# TestGetHtml

class TestGetHtml(unittest.TestCase):

    @patch("extractor.extract.session")
    def test_sukses_200(self, mock_session):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = "<html>OK</html>"
        mock_resp.raise_for_status = MagicMock()
        mock_session.get.return_value = mock_resp

        result = extract.get_html("https://example.com")

        self.assertEqual(result, "<html>OK</html>")
        mock_session.get.assert_called_once_with(
            "https://example.com", timeout=config_stub.REQUEST_TIMEOUT
        )

    @patch("extractor.extract.time.sleep")
    @patch("extractor.extract.session")
    def test_rate_limit_429_dengan_retry_after(self, mock_session, mock_sleep):
        resp_429 = MagicMock()
        resp_429.status_code = 429
        resp_429.headers = {"Retry-After": "5"}

        resp_200 = MagicMock()
        resp_200.status_code = 200
        resp_200.text = "<html>Retry OK</html>"
        resp_200.raise_for_status = MagicMock()

        mock_session.get.side_effect = [resp_429, resp_200]

        result = extract.get_html("https://example.com")

        self.assertEqual(result, "<html>Retry OK</html>")
        mock_sleep.assert_called_once_with(5)

    @patch("extractor.extract.random.uniform", return_value=1.0)
    @patch("extractor.extract.time.sleep")
    @patch("extractor.extract.session")
    def test_rate_limit_429_tanpa_retry_after(self, mock_session, mock_sleep, mock_uniform):
        resp_429 = MagicMock()
        resp_429.status_code = 429
        resp_429.headers = {}

        resp_200 = MagicMock()
        resp_200.status_code = 200
        resp_200.text = "<html>OK</html>"
        resp_200.raise_for_status = MagicMock()

        mock_session.get.side_effect = [resp_429, resp_200]

        result = extract.get_html("https://example.com")

        self.assertEqual(result, "<html>OK</html>")
        mock_sleep.assert_called_once_with(2.0)

    @patch("extractor.extract.random.uniform", return_value=1.0)
    @patch("extractor.extract.time.sleep")
    @patch("extractor.extract.session")
    def test_request_exception_semua_retry_gagal(self, mock_session, mock_sleep, mock_uniform):
        mock_session.get.side_effect = requests.exceptions.RequestException("Connection error")

        result = extract.get_html("https://example.com")

        self.assertIsNone(result)
        self.assertEqual(mock_session.get.call_count, 3)

    @patch("extractor.extract.random.uniform", return_value=1.0)
    @patch("extractor.extract.time.sleep")
    @patch("extractor.extract.session")
    def test_sukses_setelah_dua_kali_exception(self, mock_session, mock_sleep, mock_uniform):
        err = requests.exceptions.RequestException("Err")
        resp_200 = MagicMock()
        resp_200.status_code = 200
        resp_200.text = "<html>Late OK</html>"
        resp_200.raise_for_status = MagicMock()

        mock_session.get.side_effect = [err, err, resp_200]

        result = extract.get_html("https://example.com")

        self.assertEqual(result, "<html>Late OK</html>")
        self.assertEqual(mock_session.get.call_count, 3)

    @patch("extractor.extract.session")
    def test_raise_for_status_dipanggil(self, mock_session):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = "<html/>"
        mock_resp.raise_for_status = MagicMock()
        mock_session.get.return_value = mock_resp

        extract.get_html("https://example.com")

        mock_resp.raise_for_status.assert_called_once()

    # @patch("extractor.extract.random.uniform", return_value=1.0)
    # @patch("extractor.extract.time.sleep")
    # @patch("extractor.extract.session")
    # def test_exponential_backoff_meningkat(self, mock_session, mock_sleep, mock_uniform):
    #     mock_session.get.side_effect = requests.exceptions.RequestException("Err")
    #
    #     extract.get_html("https://example.com")
    #
    #     sleep_calls = [c[0][0] for c in mock_sleep.call_args_list]
    #     # attempt 0 → 2^0 + 1.0 - 1 = 1.0 ... kita pakai rumus: 2^attempt + uniform - MIN_DELAY
    #     # uniform=1.0, MIN_DELAY=1 → 2^0+1.0-1=1.0, 2^1+1.0-1=2.0, 2^2+1.0-1=4.0
    #     self.assertEqual(sleep_calls, [1.0, 2.0, 4.0])



# TestParseProducts

class TestParseProducts(unittest.TestCase):

    def test_parse_satu_produk(self):
        html = make_product_html()
        products = extract.parse_products(html)

        self.assertEqual(len(products), 1)
        p = products[0]
        self.assertEqual(p["Title"], "Sepatu Keren")
        self.assertEqual(p["Price"], "Rp 250.000")
        self.assertEqual(p["Rating"], "4.5 / 5")
        self.assertEqual(p["Colors"], "2 Colors")
        self.assertEqual(p["Size"], "M")
        self.assertEqual(p["Gender"], "Unisex")
        self.assertIn("Timestamp", p)

    def test_parse_banyak_produk(self):
        html = make_product_html(n=3)
        products = extract.parse_products(html)
        self.assertEqual(len(products), 3)

    def test_parse_html_kosong(self):
        products = extract.parse_products("<html><body></body></html>")
        self.assertEqual(products, [])

    def test_parse_card_tidak_lengkap_dilewati(self):
        bad_html = """
        <html><body>
            <div class="collection-card">
                <h3 class="product-title">Produk Rusak</h3>
            </div>
        </body></html>
        """
        products = extract.parse_products(bad_html)
        self.assertEqual(products, [])

    def test_timestamp_format_iso(self):
        from datetime import datetime
        html = make_product_html()
        products = extract.parse_products(html)
        ts = products[0]["Timestamp"]
        parsed = datetime.fromisoformat(ts)
        self.assertIsInstance(parsed, datetime)

    def test_whitespace_di_strip(self):
        html = """
        <html><body>
            <div class="collection-card">
                <h3 class="product-title">  Sepatu Bersih  </h3>
                <span class="price">  Rp 100.000  </span>
                <p>  5 / 5  </p>
                <p>  3 Colors  </p>
                <p>  L  </p>
                <p>  Pria  </p>
            </div>
        </body></html>
        """
        products = extract.parse_products(html)
        self.assertEqual(products[0]["Title"], "Sepatu Bersih")
        self.assertEqual(products[0]["Price"], "Rp 100.000")

    def test_kunci_struktur_produk(self):
        html = make_product_html()
        products = extract.parse_products(html)
        expected_keys = {"Title", "Price", "Rating", "Colors", "Size", "Gender", "Timestamp"}
        self.assertEqual(set(products[0].keys()), expected_keys)

    def test_mixed_valid_invalid_cards(self):
        html = """
        <html><body>
            <div class="collection-card">
                <h3 class="product-title">Valid</h3>
                <span class="price">Rp 50.000</span>
                <p>4/5</p><p>1 Color</p><p>S</p><p>Wanita</p>
            </div>
            <div class="collection-card">
                <h3 class="product-title">Broken</h3>
            </div>
        </body></html>
        """
        products = extract.parse_products(html)
        self.assertEqual(len(products), 1)
        self.assertEqual(products[0]["Title"], "Valid")



# TestScrapeProducts

class TestScrapeProducts(unittest.TestCase):

    @patch("extractor.extract.time.sleep")
    @patch("extractor.extract.random.uniform", return_value=1.5)
    @patch("extractor.extract.parse_products")
    @patch("extractor.extract.get_html")
    def test_scrape_semua_halaman(self, mock_get_html, mock_parse, mock_uniform, mock_sleep):
        mock_get_html.return_value = "<html/>"
        mock_parse.return_value = [{"Title": "Produk X"}]

        results = extract.scrape_products()

        self.assertEqual(mock_get_html.call_count, config_stub.MAX_PAGE)
        self.assertEqual(len(results), config_stub.MAX_PAGE)

    @patch("extractor.extract.time.sleep")
    @patch("extractor.extract.random.uniform", return_value=1.0)
    @patch("extractor.extract.get_html")
    def test_url_halaman_pertama_tanpa_slash_page(self, mock_get_html, mock_uniform, mock_sleep):
        mock_get_html.return_value = "<html/>"
        with patch("extractor.extract.parse_products", return_value=[]):
            extract.scrape_products()

        first_call_url = mock_get_html.call_args_list[0][0][0]
        self.assertEqual(first_call_url, config_stub.BASE_URL)

    @patch("extractor.extract.time.sleep")
    @patch("extractor.extract.random.uniform", return_value=1.0)
    @patch("extractor.extract.get_html")
    def test_url_halaman_berikutnya_dengan_page(self, mock_get_html, mock_uniform, mock_sleep):
        mock_get_html.return_value = "<html/>"
        with patch("extractor.extract.parse_products", return_value=[]):
            extract.scrape_products()

        second_call_url = mock_get_html.call_args_list[1][0][0]
        self.assertEqual(second_call_url, f"{config_stub.BASE_URL}/page2")

    @patch("extractor.extract.time.sleep")
    @patch("extractor.extract.random.uniform", return_value=1.0)
    @patch("extractor.extract.parse_products")
    @patch("extractor.extract.get_html", return_value=None)
    def test_html_none_halaman_dilewati(self, mock_get_html, mock_parse, mock_uniform, mock_sleep):
        results = extract.scrape_products()
        mock_parse.assert_not_called()
        self.assertEqual(results, [])

    @patch("extractor.extract.time.sleep")
    @patch("extractor.extract.random.uniform", return_value=2.0)
    @patch("extractor.extract.parse_products", return_value=[])
    @patch("extractor.extract.get_html", return_value="<html/>")
    def test_sleep_dipanggil_tiap_halaman(self, mock_get_html, mock_parse, mock_uniform, mock_sleep):
        extract.scrape_products()
        self.assertEqual(mock_sleep.call_count, config_stub.MAX_PAGE)
        mock_sleep.assert_called_with(2.0)

    @patch("extractor.extract.time.sleep")
    @patch("extractor.extract.random.uniform", return_value=1.0)
    @patch("extractor.extract.parse_products")
    @patch("extractor.extract.get_html")
    def test_produk_dari_semua_halaman_digabung(self, mock_get_html, mock_parse, mock_uniform, mock_sleep):
        mock_get_html.return_value = "<html/>"
        mock_parse.side_effect = [
            [{"Title": "A"}, {"Title": "B"}],
            [{"Title": "C"}],
            [{"Title": "D"}, {"Title": "E"}],
        ]

        results = extract.scrape_products()

        self.assertEqual(len(results), 5)
        titles = [p["Title"] for p in results]
        self.assertEqual(titles, ["A", "B", "C", "D", "E"])

    @patch("extractor.extract.time.sleep")
    @patch("extractor.extract.random.uniform", return_value=1.0)
    @patch("extractor.extract.parse_products", return_value=[])
    @patch("extractor.extract.get_html")
    def test_url_halaman_ketiga(self, mock_get_html, mock_parse, mock_uniform, mock_sleep):
        mock_get_html.return_value = "<html/>"
        extract.scrape_products()

        third_call_url = mock_get_html.call_args_list[2][0][0]
        self.assertEqual(third_call_url, f"{config_stub.BASE_URL}/page3")


if __name__ == "__main__":
    unittest.main(verbosity=2)