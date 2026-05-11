import pytest
import pandas as pd
from unittest.mock import patch, MagicMock, call
import gspread
import sys
import os

"""Tambahkan ROOT project ke sys.path — konvensi sama seperti test service lain
sehingga import bisa pakai full path: loader.load"""

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# Import target — dari subfolder loader
from loader.load import (
    save_to_csv,
    save_to_postgresql,
    connect_gsheet,
    fix_timestamp_only,
    save_to_gsheet_by_id,
)



# Fixtures — data dummy yang dipakai di banyak test

@pytest.fixture
def sample_df():
    """DataFrame sederhana dengan kolom Timestamp untuk keperluan test."""
    return pd.DataFrame({
        "Timestamp": pd.to_datetime(["2024-01-01 10:00:00", "2024-01-02 11:00:00"]),
        "Name": ["Alice", "Bob"],
        "Score": [90, 85],
    })


@pytest.fixture
def sample_df_no_timestamp():
    """DataFrame tanpa kolom Timestamp."""
    return pd.DataFrame({"Name": ["Alice", "Bob"], "Score": [90, 85]})



# 1. save_to_csv
class TestSaveToCsv:

    def test_saves_csv_successfully(self, sample_df, tmp_path):
        """Pastikan DataFrame disimpan ke file CSV tanpa error."""
        out = tmp_path / "output.csv"
        save_to_csv(sample_df, str(out))
        assert out.exists(), "File CSV harus terbuat"
        loaded = pd.read_csv(str(out))
        assert list(loaded.columns) == list(sample_df.columns)

    def test_csv_row_count_matches(self, sample_df, tmp_path):
        """Jumlah baris CSV harus sama dengan DataFrame sumber."""
        out = tmp_path / "output.csv"
        save_to_csv(sample_df, str(out))
        loaded = pd.read_csv(str(out))
        assert len(loaded) == len(sample_df)

    def test_raises_on_invalid_path(self, sample_df):
        """Jika path tidak valid, exception harus di-raise (bukan ditelan)."""
        with pytest.raises(Exception):
            save_to_csv(sample_df, "/non_existent_dir/out.csv")

    def test_raises_on_io_error(self, sample_df, tmp_path):
        """to_csv gagal → exception harus di-propagate ke caller.
        Pakai patch.object karena pd.DataFrame.to_csv tidak bisa di-patch
        lewat string path — method-nya ada di objek pandas, bukan di loader.load.
        """
        with patch.object(pd.DataFrame, "to_csv", side_effect=OSError("disk full")):
            with pytest.raises(OSError, match="disk full"):
                save_to_csv(sample_df, str(tmp_path / "x.csv"))



# 2. save_to_postgresql

class TestSaveToPostgresql:

    @patch("loader.load.create_engine")
    def test_saves_to_db_successfully(self, mock_engine, sample_df):
        """
        Pastikan create_engine dipanggil sekali dan df.to_sql dieksekusi
        dengan parameter yang benar.
        """
        engine_instance = MagicMock()
        mock_engine.return_value = engine_instance

        with patch.object(sample_df, "to_sql") as mock_to_sql:
            save_to_postgresql(sample_df, "my_table")

        mock_engine.assert_called_once()
        mock_to_sql.assert_called_once_with(
            name="my_table",
            con=engine_instance,
            if_exists="replace",
            index=False,
        )

    @patch("loader.load.create_engine", side_effect=Exception("connection refused"))
    def test_does_not_raise_on_db_error(self, mock_engine, sample_df, capsys):
        """
        Sesuai implementasi, fungsi mencetak error tapi TIDAK re-raise.
        Test ini memvalidasi behaviour tersebut.
        """
        # Tidak boleh raise ke luar
        save_to_postgresql(sample_df, "my_table")
        captured = capsys.readouterr()
        assert "connection refused" in captured.out

    @patch("loader.load.create_engine")
    def test_uses_correct_database_url(self, mock_engine, sample_df):
        """create_engine harus menerima DATABASE_URL dari config."""
        engine_instance = MagicMock()
        mock_engine.return_value = engine_instance

        with patch.object(sample_df, "to_sql"):
            save_to_postgresql(sample_df, "tbl")

        # Argumen pertama create_engine adalah DATABASE_URL
        args, kwargs = mock_engine.call_args
        assert args[0] is not None  # DATABASE_URL pasti di-pass


# 3. connect_gsheet
class TestConnectGsheet:

    @patch("loader.load.gspread.authorize")
    @patch("loader.load.Credentials.from_service_account_file")
    def test_returns_gspread_client(self, mock_creds, mock_auth):
        """Harus mengembalikan client gspread yang valid."""
        mock_client = MagicMock()
        mock_auth.return_value = mock_client

        result = connect_gsheet("fake_creds.json")

        mock_creds.assert_called_once_with(
            "fake_creds.json",
            scopes=["https://www.googleapis.com/auth/spreadsheets"],
        )
        mock_auth.assert_called_once()
        assert result == mock_client

    @patch("loader.load.Credentials.from_service_account_file",
           side_effect=FileNotFoundError("file not found"))
    def test_raises_when_credentials_missing(self, mock_creds):
        """Jika file credentials tidak ada, exception harus di-propagate."""
        with pytest.raises(FileNotFoundError):
            connect_gsheet("missing.json")

    @patch("loader.load.gspread.authorize", side_effect=Exception("auth failed"))
    @patch("loader.load.Credentials.from_service_account_file")
    def test_raises_on_auth_failure(self, mock_creds, mock_auth):
        """Jika gspread.authorize gagal, exception harus naik ke caller."""
        with pytest.raises(Exception, match="auth failed"):
            connect_gsheet("creds.json")

# 4. fix_timestamp_only
class TestFixTimestampOnly:

    def test_converts_timestamp_column_to_str(self, sample_df):
        """Kolom Timestamp harus dikonversi menjadi string.
        Pandas terbaru (2.x+) + Python 3.14 bisa return StringDtype bukan object,
        jadi pakai is_string_dtype() agar kompatibel di semua versi.
        """
        result = fix_timestamp_only(sample_df)
        assert pd.api.types.is_string_dtype(result["Timestamp"]), (
            "Kolom Timestamp harus bertipe string (object atau StringDtype)"
        )

    def test_does_not_mutate_original_df(self, sample_df):
        """Fungsi harus bekerja pada copy — DataFrame asli tidak berubah."""
        original_dtype = sample_df["Timestamp"].dtype
        fix_timestamp_only(sample_df)
        assert sample_df["Timestamp"].dtype == original_dtype

    def test_no_timestamp_column_passthrough(self, sample_df_no_timestamp):
        """DataFrame tanpa kolom Timestamp harus dikembalikan apa adanya."""
        result = fix_timestamp_only(sample_df_no_timestamp)
        assert list(result.columns) == list(sample_df_no_timestamp.columns)

    def test_other_columns_unchanged(self, sample_df):
        """Kolom selain Timestamp tidak boleh berubah."""
        result = fix_timestamp_only(sample_df)
        pd.testing.assert_series_equal(result["Name"], sample_df["Name"])
        pd.testing.assert_series_equal(result["Score"], sample_df["Score"])

    def test_returns_dataframe(self, sample_df):
        """Return value harus tetap bertipe DataFrame."""
        result = fix_timestamp_only(sample_df)
        assert isinstance(result, pd.DataFrame)

# 5. save_to_gsheet_by_id
class TestSaveToGsheetById:

    def _make_mock_client(self, worksheet=None, raise_spreadsheet=False,
                          raise_worksheet=False):
        """Helper: buat mock gspread client yang bisa dikonfigurasi."""
        mock_ws = worksheet or MagicMock()
        mock_sheet = MagicMock()

        mock_client = MagicMock()

        if raise_spreadsheet:
            # open_by_key harus di-set di mock_CLIENT (bukan mock_sheet)
            # karena client.open_by_key() yang dipanggil di fungsi asli
            mock_client.open_by_key.side_effect = Exception("not found")
        else:
            mock_client.open_by_key.return_value = mock_sheet
            if raise_worksheet:
                mock_sheet.worksheet = MagicMock(
                    side_effect=gspread.WorksheetNotFound
                )
            else:
                mock_sheet.worksheet.return_value = mock_ws

        return mock_client, mock_ws

    @patch("loader.load.connect_gsheet")
    def test_uploads_data_to_worksheet(self, mock_connect, sample_df):
        """Data (header + rows) harus di-update ke worksheet."""
        mock_client, mock_ws = self._make_mock_client()
        mock_connect.return_value = mock_client

        save_to_gsheet_by_id(sample_df, "creds.json", "sheet_id_123")

        mock_ws.clear.assert_called_once()
        mock_ws.update.assert_called_once()

        # Cek bahwa data yang diupload dimulai dengan header kolom
        uploaded_data = mock_ws.update.call_args[0][0]
        assert uploaded_data[0] == list(sample_df.columns)

    @patch("loader.load.connect_gsheet")
    def test_uses_custom_sheet_name(self, mock_connect, sample_df):
        """Parameter sheet_name harus diteruskan ke spreadsheet.worksheet()."""
        mock_client, _ = self._make_mock_client()
        mock_connect.return_value = mock_client

        save_to_gsheet_by_id(sample_df, "creds.json", "sid", sheet_name="Data")

        mock_client.open_by_key.return_value.worksheet.assert_called_with("Data")

    @patch("loader.load.connect_gsheet")
    def test_raises_file_not_found_on_invalid_spreadsheet(
        self, mock_connect, sample_df
    ):
        """Spreadsheet ID tidak valid → harus raise FileNotFoundError."""
        mock_client, _ = self._make_mock_client(raise_spreadsheet=True)
        mock_connect.return_value = mock_client

        with pytest.raises(FileNotFoundError, match="Spreadsheet ID invalid"):
            save_to_gsheet_by_id(sample_df, "creds.json", "bad_id")

    @patch("loader.load.connect_gsheet")
    def test_raises_value_error_on_missing_sheet(self, mock_connect, sample_df):
        """Sheet name tidak ditemukan → harus raise ValueError."""
        mock_client, _ = self._make_mock_client(raise_worksheet=True)
        mock_connect.return_value = mock_client

        with pytest.raises(ValueError, match="not found in spreadsheet"):
            save_to_gsheet_by_id(sample_df, "creds.json", "sid", "WrongSheet")

    @patch("loader.load.connect_gsheet")
    def test_clears_worksheet_before_upload(self, mock_connect, sample_df):
        """
        worksheet.clear() harus dipanggil SEBELUM worksheet.update()
        supaya data lama tidak bercampur dengan data baru.
        """
        mock_client, mock_ws = self._make_mock_client()
        mock_connect.return_value = mock_client

        call_order = []
        mock_ws.clear.side_effect = lambda: call_order.append("clear")
        mock_ws.update.side_effect = lambda *a, **kw: call_order.append("update")

        save_to_gsheet_by_id(sample_df, "creds.json", "sid")

        assert call_order == ["clear", "update"], (
            "clear() harus dipanggil dulu sebelum update()"
        )

    @patch("loader.load.connect_gsheet")
    def test_timestamp_converted_before_upload(self, mock_connect, sample_df):
        """
        Kolom Timestamp di-convert ke str sebelum dikirim ke Sheets
        agar tidak ada error serialisasi tipe data.
        """
        mock_client, mock_ws = self._make_mock_client()
        mock_connect.return_value = mock_client

        save_to_gsheet_by_id(sample_df, "creds.json", "sid")

        uploaded_data = mock_ws.update.call_args[0][0]
        # Row pertama = header, row selanjutnya = data
        # Nilai Timestamp di row data harus berupa string
        ts_col_idx = uploaded_data[0].index("Timestamp")
        for row in uploaded_data[1:]:
            assert isinstance(row[ts_col_idx], str), (
                "Timestamp harus sudah dikonversi ke str sebelum upload"
            )

    @patch("loader.load.connect_gsheet")
    def test_raises_on_update_failure(self, mock_connect, sample_df):
        """Jika worksheet.update() gagal, exception harus naik ke caller."""
        mock_client, mock_ws = self._make_mock_client()
        mock_ws.update.side_effect = Exception("quota exceeded")
        mock_connect.return_value = mock_client

        with pytest.raises(Exception, match="quota exceeded"):
            save_to_gsheet_by_id(sample_df, "creds.json", "sid")