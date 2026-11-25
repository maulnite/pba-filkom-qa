# Anggota 3 — Pencarian passage

Affan Abyarahman

- `retrieval.py`: mengurutkan passage berdasarkan TF-IDF dan cosine similarity.
- `Anggota3_Retrieval.ipynb`: memeringkat passage untuk 20 pertanyaan berdasarkan token keluaran Anggota 2.
- `output/hasil_pencarian.json`: lima kandidat lengkap per soal beserta skor cosine dan urutan ID seluruh kandidat berskor positif.
- `data/pertanyaan_anggota3.json`: tiga pertanyaan evaluasi beserta bukti. Nomor 1–3 adalah nomor lokal; sesuaikan saat digabung.

Jalankan notebook dengan direktori kerja `Anggota3_Retrieval` dan kernel dari lingkungan proyek.

## Cara panggil dari aplikasi utama

Jalankan dari folder proyek, dengan `passages` dan `dokumen` yang sudah dibaca dari data Orie:

```python
from Anggota2_Pertanyaan.question_processing import proses_pertanyaan
from Anggota3_Retrieval.retrieval import Retrieval

retrieval = Retrieval(passages, dokumen)  # buat sekali
hasil_pertanyaan = proses_pertanyaan("Berapa lama waktu maksimal untuk Ujian Skripsi?")
kandidat = retrieval.cari_passage(hasil_pertanyaan, top_k=5)
```

Kirim `kandidat` dan `hasil_pertanyaan["tipe_jawaban"]` ke modul penentu jawaban. Setiap kandidat menyimpan `rank`, `score`, `passage_id`, teks asli (`teks`), `halaman`, dan metadata `sumber` (`judul`, `tahun`, `url`). Daftar kosong berarti tidak ada kandidat dengan skor positif atau pertanyaan masih perlu klarifikasi.

## Hasil uji awal

Pada empat pertanyaan Rio, passage rujukan pertama muncul pada peringkat **3, 1, 19, dan 6**. Jadi **2 dari 4** pertanyaan menemukan bukti pada lima besar. Ini hasil pencarian bukti, bukan akurasi jawaban akhir. Definisi yang hanya menghasilkan satu kata kunci dan konversi nilai yang perlu pencocokan rentang adalah kasus yang perlu perhatian saat integrasi.
