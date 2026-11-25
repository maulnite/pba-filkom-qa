# Sistem Tanya Jawab Akademik FILKOM UB

Proyek Pemrosesan Bahasa Alami Universitas Brawijaya. Sistem ini mencari bukti dan mengekstrak jawaban untuk pertanyaan factoid tentang akademik dan ujian FILKOM tanpa LLM. Repositori memuat pekerjaan Anggota 1–4, dari PDF sumber hingga ekstraksi jawaban ringkas.

**Status saat ini** · 440 passage · 11 pertanyaan rujukan · Modul retrieval & ekstraksi Hybrid aktif

## Coba eksperimen

Gunakan Python 3.11+ dan uv. Jalankan perintah berikut dari root repositori.

```powershell
uv sync --locked
uv run --locked python -m scripts.evaluasi_retrieval
```

Program menampilkan pertanyaan, peringkat bukti pertama, Hit@5, dan MRR. Ketujuh pertanyaan berasal dari berkas rujukan Anggota 2 dan 3. Ekstraksi jawaban dan evaluasi akhir 20 pertanyaan merupakan tahap lanjutan proyek. [Hasil dan batasan eksperimen](docs/eksperimen.md)

## Cara kerja

| Tahap | Masukan dan keluaran | Dokumentasi |
|---|---|---|
| **1. Korpus · Orie** | PDF → teks per halaman → 440 passage JSONL dengan ID, konteks, dan halaman sumber. | [Spesifikasi korpus](Anggota1_Korpus/SPEK_PASSAGE.md) · [Notebook](Anggota1_Korpus/Anggota1_Korpus.ipynb) |
| **2. Pertanyaan · Rio** | Pertanyaan → token pencarian, jenis pertanyaan, dan tipe jawaban. Fungsi yang sama menyiapkan token passage. | [Dokumentasi](Anggota2_Pertanyaan/README.md) · [Notebook](Anggota2_Pertanyaan/Anggota2_Pertanyaan.ipynb) |
| **3. Pencarian · Affan** | Token → TF-IDF dan cosine similarity → kandidat berperingkat dengan teks asli dan metadata sumber. | [Dokumentasi](Anggota3_Retrieval/README.md) · [Notebook](Anggota3_Retrieval/Anggota3_Retrieval.ipynb) |
| **4. Ekstraksi Jawaban · Rimba** | Kandidat passage + `tipe_jawaban` → arsitektur Hybrid (Simbolik + Dependency Parsing UDPipe) → jawaban ringkas dan sumber. | [Dokumentasi](Anggota4/README.md) · [Notebook](Anggota4/Anggota4_Jawaban.ipynb) |

## Data

| Data | Isi |
|---|---|
| [PDF korpus aktif](Anggota1_Korpus/korpus_raw) | Pedoman Akademik FILKOM 2020, Tata Tertib UTS/UAS, dan Pedoman Penilaian PTIIK 2015. |
| [Data korpus](Anggota1_Korpus/data) | Passage, metadata dokumen, dan transkripsi manual untuk tabel, rumus, serta PDF hasil pindai. |
| [Teks hasil ekstraksi](Anggota1_Korpus/korpus_txt) | Teks dua dokumen PDF per halaman untuk pemeriksaan. |
| [Ekspor Anggota 2](Anggota2_Pertanyaan/output) | 440 passage bertoken dan 12 contoh hasil pemrosesan pertanyaan. |
| Pertanyaan rujukan | Empat dari [Anggota 2](Anggota2_Pertanyaan/data/pertanyaan_anggota2.json), tiga dari [Anggota 3](Anggota3_Retrieval/data/pertanyaan_anggota3.json), dan empat dari [Anggota 4](Anggota4/data/pertanyaan_anggota4.json). |
| [Referensi tambahan](referensi_korpus) | Enam PDF kandidat korpus yang tersedia untuk rujukan. |

Jawaban merujuk pada edisi dokumen dalam korpus. Tahun dan halaman ikut disimpan agar bukti dapat ditelusuri.

## Jalankan notebook

Untuk notebook Anggota 2 dan 3, jalankan `uv sync --locked --group notebook` dari root repositori, lalu pilih kernel dari `.venv`. Buka notebook dari folder masing-masing dan jalankan seluruh sel.

Untuk meregenerasi korpus, gunakan lingkungan khusus Anggota 1.

```powershell
cd Anggota1_Korpus
uv sync --locked
uv run --locked jupyter nbconvert --to notebook --execute --inplace Anggota1_Korpus.ipynb
```

Untuk Colab, buat ZIP dari root repositori dengan `git archive --format=zip --output=PBA_FILKOM_Anggota1-3.zip HEAD`, lalu unggah ZIP tersebut melalui panel **Files** sebelum menjalankan notebook Anggota 3.
