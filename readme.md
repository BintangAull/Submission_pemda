# 📊 ETL Pipeline — Fashion Product Scraping Project

## 🧾 Deskripsi Proyek

Proyek ini merupakan bagian dari **DBS Coding Camp 2026 Submission (Data Processing Module)**.

Tujuan proyek ini adalah membangun **ETL (Extract, Transform, Load) pipeline** yang lengkap untuk:

- Mengekstrak data produk fashion dari: [https://fashion-studio.dicoding.dev](https://fashion-studio.dicoding.dev)
- Mentransformasi data mentah menjadi format bersih dan terstruktur
- Memuat data ke berbagai destinasi:
  - CSV (penyimpanan lokal)
  - Database PostgreSQL
  - Google Sheets API
- Dilengkapi **unit testing dengan coverage >90%**

Proyek ini mendemonstrasikan **alur kerja data engineering** di dunia nyata, meliputi web scraping, pembersihan & transformasi data, validasi data, arsitektur ETL modular, dan pengujian otomatis.

---

## 🏗️ Struktur Proyek

```
root/
├── data/
│   ├── raw/                 # Data mentah hasil scraping
│   └── clean/               # Data bersih setelah transformasi
├── extractor/               # Web scraping (tahap EXTRACT)
├── transformer/             # Pembersihan & transformasi (tahap TRANSFORM)
├── loader/                  # Penyimpanan data (tahap LOAD)
├── tests/                   # Unit test setiap komponen ETL
├── config.py                # Konfigurasi berbasis environment
├── main.py                  # Runner utama pipeline
├── requirements.txt         # Dependensi Python
├── submission.txt           # Cara menjalankan & instruksi pengujian
├── .env.example             # Contoh environment variables
└── google-sheets-api.json   # Kredensial service account Google
```

---

## ⚙️ Gambaran Umum Pipeline ETL

### 1. Extract

Mengambil data produk dari [fashion-studio.dicoding.dev](https://fashion-studio.dicoding.dev) dengan paginasi otomatis.

Field yang diekstrak: Title, Price, Rating, Colors, Size, Gender, Timestamp.

### 2. Transform

Langkah pembersihan data:

- Menghapus duplikat
- Menangani pseudo missing values
- Membersihkan format yang tidak valid
- Menstandarkan format teks
- Konversi tipe data: Price → float (IDR), Rating → float, Colors → integer, Timestamp → datetime

### 3. Load

Data disimpan ke tiga destinasi secara modular dan independen:

- 📁 File CSV (penyimpanan lokal)
- 🐘 Database PostgreSQL
- 📊 Google Sheets API

---

## 🚀 Petunjuk Setup

### 1. Clone Repository

```bash
git clone <repo-url>
cd <project-folder>
```

### 2. Buat Virtual Environment

```bash
python -m venv .venv
```

Aktifkan — **Windows:**
```bash
.venv\Scripts\activate
```

Aktifkan — **Mac/Linux:**
```bash
source .venv/bin/activate
```

### 3. Install Dependensi

```bash
pip install -r requirements.txt
```

---

## 🔐 Konfigurasi Environment

Buat file `.env` berdasarkan `.env.example`:

```env
DATABASE_URL=postgresql+psycopg2://postgres:12345678@localhost:5432/fashion_db
```

| Variable     | Deskripsi                                           |
| ------------ | --------------------------------------------------- |
| DATABASE_URL | String koneksi PostgreSQL yang digunakan SQLAlchemy |

---

## 📊 Setup Google Sheets

1. Aktifkan Google Sheets API
2. Buat Service Account
3. Unduh credentials JSON dan rename menjadi `google-sheets-api.json`
4. Bagikan Google Sheet ke email service account

---

## ▶️ Cara Menjalankan

```bash
python main.py
```

Pipeline akan: scraping data → transformasi → simpan ke CSV, PostgreSQL, dan Google Sheets.

---

## 🧪 Unit Testing

```bash
python -m pytest tests/file_test.py(silahkan pilih) -v --cov --cov-report=html
```

Coverage: **>90%** — mencakup extractor, transformer, dan loader tests.

Lihat `submission.txt` untuk instruksi lengkap.

---

## 📌 Fitur Utama

- Arsitektur ETL modular (Extract, Transform, Load)
- Web scraping dengan dukungan paginasi
- Pembersihan & normalisasi data otomatis
- Multi-destination storage (CSV, PostgreSQL, Google Sheets)
- Konfigurasi aman berbasis environment
- Unit testing coverage >90%

---

## 📎 Lisensi

Proyek edukasi — DBS Coding Camp 2026.