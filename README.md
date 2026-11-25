# Sistem Tanya Jawab Akademik FILKOM UB

Proyek Pemrosesan Bahasa Alami Universitas Brawijaya. Sistem ini mencari bukti dan mengekstrak jawaban untuk pertanyaan factoid tentang akademik dan ujian FILKOM tanpa LLM. Repositori memuat korpus, pemrosesan pertanyaan, retrieval, ekstraksi jawaban, evaluasi retrieval, dan penilaian jawaban akhir.

**Status saat ini** · 440 passage · 20 pertanyaan dalam set uji · akurasi jawaban akhir 13/20 (65,0%) dengan 17/20 bukti di lima besar

## Coba eksperimen

Gunakan Python 3.11+ dan uv. Siapkan kernel dari root repositori.

```powershell
uv sync --locked --group notebook
```

Buka notebook Anggota 5, pilih kernel dari `.venv`, lalu jalankan **Run All**. Notebook mengevaluasi 20 pertanyaan dan menyimpan kandidat lima teratas per soal untuk penilaian jawaban akhir. [Notebook Anggota 5](Anggota5_Evaluasi_Retrieval/Anggota5_Evaluasi_Retrieval.ipynb)

Untuk mengulang baseline tujuh soal dari Anggota 2 dan 3, jalankan `uv run --locked python -m scripts.evaluasi_retrieval`. Untuk menilai jawaban akhir 20 soal, jalankan `uv run --locked python -m Anggota6_Evaluasi_Jawaban.evaluasi_jawaban`. [Hasil dan batasan baseline](docs/eksperimen.md)

## Demo web

Demo interaktif memakai FastAPI dan htmx. Setiap pertanyaan ditampilkan sebagai jejak pipeline: token pencarian, pilihan tipe jawaban, lima kandidat passage dengan skor cosine, lalu jawaban beserta passage, dokumen, dan halaman yang dipakai.

```bash
uv sync --locked
uv run --locked uvicorn web.app:app --reload
```

Buka <http://127.0.0.1:8000>. Halaman `/evaluasi` menampilkan Hit@5, MRR, akurasi, dan rincian 20 soal dari keluaran Anggota 5 dan 6. Setiap pertanyaan dijalankan penuh saat itu juga, tanpa cache atau hasil tersimpan. Detail ada di [web/README.md](web/README.md).

## Cara kerja

| Tahap | Masukan dan keluaran | Dokumentasi |
|---|---|---|
| **1. Korpus · Orie** | PDF → teks per halaman → 440 passage JSONL dengan ID, konteks, dan halaman sumber. | [Spesifikasi korpus](Anggota1_Korpus/SPEK_PASSAGE.md) · [Notebook](Anggota1_Korpus/Anggota1_Korpus.ipynb) |
| **2. Pertanyaan · Rio** | Pertanyaan → token pencarian, jenis pertanyaan, dan tipe jawaban. Fungsi yang sama menyiapkan token passage. | [Dokumentasi](Anggota2_Pertanyaan/README.md) · [Notebook](Anggota2_Pertanyaan/Anggota2_Pertanyaan.ipynb) |
| **3. Pencarian · Affan** | Token → TF-IDF dan cosine similarity → kandidat berperingkat dengan teks asli dan metadata sumber. | [Dokumentasi](Anggota3_Retrieval/README.md) · [Notebook](Anggota3_Retrieval/Anggota3_Retrieval.ipynb) |
| **4. Ekstraksi Jawaban · Rimba** | Kandidat passage + `tipe_jawaban` → arsitektur Hybrid (Simbolik + Dependency Parsing UDPipe) → jawaban ringkas dan sumber. | [Dokumentasi](Anggota4/README.md) · [Notebook](Anggota4/Anggota4_Jawaban.ipynb) |
| **5. Data Uji dan Evaluasi Retrieval · Faris** | Pertanyaan dan bukti terverifikasi → set uji 20 soal, peringkat bukti per soal, Hit@5, dan MRR. | [Dokumentasi](Anggota5_Evaluasi_Retrieval/README.md) · [Notebook](Anggota5_Evaluasi_Retrieval/Anggota5_Evaluasi_Retrieval.ipynb) |
| **6. Penilaian Jawaban Akhir** | Kandidat Anggota 5 + jawaban ekstraktor Anggota 4 → akurasi ketat, inti, dan longgar per soal, per tipe jawaban, dan per metode. | [Dokumentasi](Anggota6_Evaluasi_Jawaban/README.md) · [Notebook](Anggota6_Evaluasi_Jawaban/Anggota6_Evaluasi_Jawaban.ipynb) |

## Data

| Data | Isi |
|---|---|
| [PDF korpus aktif](Anggota1_Korpus/korpus_raw) | Pedoman Akademik FILKOM 2020, Tata Tertib UTS/UAS, dan Pedoman Penilaian PTIIK 2015. |
| [Data korpus](Anggota1_Korpus/data) | Passage, metadata dokumen, dan transkripsi manual untuk tabel, rumus, serta PDF hasil pindai. |
| [Teks hasil ekstraksi](Anggota1_Korpus/korpus_txt) | Teks dua dokumen PDF per halaman untuk pemeriksaan. |
| [Ekspor Anggota 2](Anggota2_Pertanyaan/output) | 440 passage bertoken dan 12 contoh hasil pemrosesan pertanyaan. |
| [Set uji retrieval](Anggota5_Evaluasi_Retrieval/data/pertanyaan_uji.json) | 11 pertanyaan yang sudah tersedia dari Anggota 2–4 dan 9 pertanyaan baru dengan bukti korpus. |
| [Hasil penilaian jawaban](Anggota6_Evaluasi_Jawaban/output/hasil_evaluasi.json) | Putusan per soal, akurasi per tipe jawaban, dan akurasi per metode ekstraksi. |
| [Referensi tambahan](referensi_korpus) | Enam PDF kandidat korpus yang tersedia untuk rujukan. |

Jawaban merujuk pada edisi dokumen dalam korpus. Tahun dan halaman ikut disimpan agar bukti dapat ditelusuri.

## Jalankan notebook

Untuk notebook Anggota 2 dan 3, jalankan `uv sync --locked --group notebook` dari root repositori, lalu pilih kernel dari `.venv`. Buka notebook dari folder masing-masing dan jalankan seluruh sel. Notebook Anggota 5 dan 6 dijalankan dari foldernya sendiri; notebook Anggota 6 memakai `output/hasil_retrieval.json` milik Anggota 5 sebagai masukan.

Untuk meregenerasi korpus, gunakan lingkungan khusus Anggota 1.

```powershell
cd Anggota1_Korpus
uv sync --locked
uv run --locked jupyter nbconvert --to notebook --execute --inplace Anggota1_Korpus.ipynb
```

Untuk Colab, buat ZIP dari root repositori dengan `git archive --format=zip --output=PBA_FILKOM_Anggota1-3.zip HEAD`, lalu unggah ZIP tersebut melalui panel **Files** sebelum menjalankan notebook Anggota 3.
