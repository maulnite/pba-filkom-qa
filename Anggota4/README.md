# Anggota 4 — Ekstraksi Jawaban (Hybrid Linguistic-Symbolic)

Modul ini mengekstrak jawaban ringkas dari kandidat passage hasil pencarian Anggota 3 berdasarkan `tipe_jawaban` dari Anggota 2, tanpa LLM generatif.

## Arsitektur Hybrid

1. **Jalur Simbolik (`simbolik.py`)**:
   - Menangani passage bertipe `tabel` (evaluasi rentang interval seperti `75 < N ≤ 80` untuk `NILAI_HURUF` maupun `IP ≥ 3,00`, serta lookup bobot huruf mutu).
   - Mengekstrak ekspresi `RUMUS` (mis. `IP = Σ (K_i × Na_i) / Σ K_i.`).
   - Menormalisasi angka dalam kata (`empat belas semester` $\rightarrow$ `14 semester`) serta angka berulang dalam kurung (`15 (lima belas) menit` $\rightarrow$ `15 menit`).
2. **Jalur Linguistik (`ekstraksi.py` — `spacy-udpipe` model `id`)**:
   - Membedah kalimat narasi (`butir`, `paragraf`) menggunakan POS tagging dan Universal Dependencies (*dependency parsing*).
   - Memilih kandidat span terbaik berdasarkan kombinasi skor jarak leksikal (*lexical proximity*), kecocokan induk sintaksis (*dependency head*), cakupan kata kunci kalimat, dan peringkat retrieval.
3. **Jalur Fallback**:
   - Mengembalikan kalimat dengan kecocokan kata kunci tertinggi jika pola spesifik tidak ditemukan pada kandidat teratas.

## Cara menjalankan

Dari root repositori:

```bash
uv sync
uv run python -m Anggota4.uji_ekstraksi
```

## Pemakaian dari aplikasi utama

```python
from Anggota2_Pertanyaan.question_processing import proses_pertanyaan
from Anggota3_Retrieval.retrieval import Retrieval
from Anggota4.ekstraksi import EkstraktorJawaban

retrieval = Retrieval(passages, dokumen)
ekstraktor = EkstraktorJawaban(dokumen)

hasil_tanya = proses_pertanyaan("Siapa yang menetapkan pengecualian Dosen Pembimbing Skripsi?")
kandidat = retrieval.cari_passage(hasil_tanya, top_k=5)
jawaban = ekstraktor.ekstrak(hasil_tanya, kandidat)
```

Keluaran berisi `jawaban`, `metode` (`simbolik`, `linguistik_udpipe`, atau `fallback_kalimat`), `skor`, `passage_id`, `kutipan`, `sumber`, dan `status`.

## Berkas

- `simbolik.py`: normalisasi bilangan kata, evaluator interval tabel, dan ekstraktor rumus.
- `ekstraksi.py`: router Hybrid, pemroses dependency tree UDPipe, dan skoring proximity.
- `data/pertanyaan_anggota4.json`: 4 pertanyaan evaluasi rujukan beserta `passage_id` bukti.
- `uji_ekstraksi.py`: pemeriksaan otomatis komponen simbolik, 11 soal rujukan isolasi, dan 4 soal end-to-end.
- `Anggota4_Jawaban.ipynb`: notebook demonstrasi dan evaluasi.
