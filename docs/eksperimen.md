# Eksperimen pencarian passage

## Data dan metode

Korpus terdiri dari 396 passage Pedoman Akademik FILKOM 2020, 26 passage Tata Tertib UTS/UAS, dan 18 passage Pedoman Penilaian PTIIK 2015. Setiap passage membawa ID, lokasi halaman, dan teks asli. Saat membuat indeks, sistem menggabungkan judul subbab, konteks, dan teks. [Spesifikasi korpus](../Anggota1_Korpus/SPEK_PASSAGE.md)

Preprocessing kedua sisi memakai normalisasi Unicode, case folding, tokenisasi regex, penyamaan singkatan, dan penyaringan stopword. Angka desimal, negasi, tanda pembanding, dan nilai huruf seperti B+ dipertahankan. Sistem membuat vektor TF-IDF unigram untuk 440 passage, lalu mengurutkan kandidat dengan cosine similarity. Skor yang sama diurutkan berdasarkan ID. [Preprocessing](../Anggota2_Pertanyaan/preprocess.py) · [Retrieval](../Anggota3_Retrieval/retrieval.py)

## Hasil baseline

Peringkat dihitung dari kandidat berskor positif. Bukti pertama adalah kandidat berperingkat tertinggi yang ID-nya ada dalam data rujukan. Hit@5 menghitung proporsi pertanyaan dengan setidaknya satu bukti di lima besar. MRR adalah rata-rata kebalikan peringkat bukti pertama, dengan nilai nol jika bukti absen.

| Penanya | Pertanyaan | Peringkat bukti pertama |
|---|---|---:|
| Anggota 2 | Berapa sks minimal untuk menyelesaikan studi sarjana? | 3 |
| Anggota 2 | Berapa lama waktu maksimal untuk Ujian Skripsi? | 1 |
| Anggota 2 | Apa itu skripsi? | 19 |
| Anggota 2 | Apa nilai huruf untuk nilai angka 78? | 6 |
| Anggota 3 | Berapa lama waktu maksimal untuk menyelesaikan studi sarjana? | 2 |
| Anggota 3 | Kapan batas pengajuan cuti akademik setelah daftar ulang? | 1 |
| Anggota 3 | Apa rumus indeks prestasi semester? | 25 |

**Hit@5 = 4/7 (57,1%)** dan **MRR = 0,442**. Angka ini mengukur penemuan bukti pada tujuh pertanyaan awal. Evaluasi jawaban akhir membutuhkan modul penentu jawaban dan set uji kelompok. [Data Anggota 2](../Anggota2_Pertanyaan/data/pertanyaan_anggota2.json) · [Data Anggota 3](../Anggota3_Retrieval/data/pertanyaan_anggota3.json)

## Analisis tiga contoh

- **Definisi skripsi** hanya menghasilkan token skripsi. Banyak passage prosedural memakai istilah itu, sehingga passage definisi berada di peringkat 19.
- **Konversi nilai 78** membutuhkan pencocokan rentang 75 < N ≤ 80. Kemiripan token memberi skor tinggi pada beberapa baris dari tabel yang sama. Bukti pertama ada di peringkat 6.
- **Rumus IP** berada di peringkat 25. Tabel beban studi memakai token IP dan semester berulang, sehingga beberapa baris tabel muncul lebih awal daripada rumus.

Ulangi evaluasi dari root repositori dengan `uv run --locked python -m scripts.evaluasi_retrieval`. [Skrip evaluasi](../scripts/evaluasi_retrieval.py)
