# Anggota 5 — Set Uji dan Evaluasi Retrieval

Bagian ini menyiapkan 20 pertanyaan factoid dan mengukur apakah retrieval TF-IDF menemukan passage bukti di antara lima hasil teratas. Sebelas pertanyaan pertama disalin dari data Anggota 2, 3, dan 4. Empat soal ditulis sebagai kontribusi Faris. Lima soal terakhir adalah tambahan yang disusun untuk melengkapi set, tanpa atribusi kepada anggota lain.

## Berkas

- [`data/pertanyaan_uji.json`](data/pertanyaan_uji.json) berisi 20 pertanyaan, jawaban rujukan, kutipan, dan satu atau lebih ID passage relevan. ID yang memiliki bukti alternatif tetap dicantumkan. `bukti_per_passage` memuat kutipan verbatim per ID alternatif.
- [`Anggota5_Evaluasi_Retrieval.ipynb`](Anggota5_Evaluasi_Retrieval.ipynb) membaca urutan kandidat Anggota 3 dan menghitung peringkat serta metrik dari ID bukti.
- [`output/hasil_retrieval.json`](output/hasil_retrieval.json) menyimpan hasil per ID pertanyaan, lima kandidat berurutan lengkap dengan field passage dan metadata sumber dari API Anggota 3, peringkat bukti pertama, dan metrik.

Jalankan `uv sync --locked --group notebook` dari root repositori. Buka notebook, pilih kernel Python dari `.venv`, lalu jalankan **Run All** dengan direktori kerja `Anggota5_Evaluasi_Retrieval`. Untuk menjalankan semua sel dan menyimpan keluarannya dari terminal, gunakan perintah berikut dari root repositori. Nbconvert memakai direktori notebook saat menjalankan sel.

```bash
uv run --locked --group notebook jupyter nbconvert --to notebook --execute --inplace Anggota5_Evaluasi_Retrieval/Anggota5_Evaluasi_Retrieval.ipynb
```

Bagian **Jawaban Bot** menampilkan jawaban yang diekspor Anggota 4 bersama rujukan dan peringkat bukti. Ubah `id_contoh` untuk mencoba ID lain dari tabel.

## Definisi metrik

- **Hit@5** adalah proporsi pertanyaan yang memiliki setidaknya satu passage relevan dalam lima kandidat teratas.
- **MRR** adalah rata-rata nilai kebalikan peringkat passage relevan pertama pada seluruh hasil berskor positif. Pertanyaan tanpa bukti memperoleh nol.
- **Precision@5 macro** menghitung jumlah passage relevan yang ditemukan dibagi lima untuk setiap soal, lalu merata-ratakan 20 nilai itu.
- **Recall@5 macro** menghitung jumlah passage relevan yang ditemukan dibagi seluruh ID bukti yang dicatat untuk soal tersebut, lalu merata-ratakan nilainya.

Retriever membuang skor nol, mengurutkan skor cosine dari tertinggi, dan memakai `passage_id` untuk memecahkan skor seri. Metrik menggunakan set rujukan yang dibekukan dalam JSON. Penambahan ID bukti alternatif bisa mengubah skor dan harus disertai kutipan yang cocok dengan korpus.

## Asal data dan batas cakupan

Korpus uji berisi 440 passage dari Pedoman Akademik FILKOM 2020, Tata Tertib UTS/UAS, dan Pedoman Penilaian PTIIK 2015. Sebelas soal awal beserta jawabannya berasal dari file masing-masing anggota. Penambahan Faris dan lima soal pelengkap berfokus pada angka, durasi, nilai, dan aturan yang dapat dibuktikan langsung pada korpus. Set ini tidak menguji aturan terbaru, kalender akademik, atau informasi nama orang yang tidak tersedia dalam sumber.

Lebih dari satu passage mendukung beberapa jawaban, termasuk syarat minimum kelulusan 144 SKS, batas kehadiran 80% untuk mengikuti UAS, evaluasi akhir tahun pertama, bobot B+, dan konversi nilai 78 menjadi B+.

## Hasil evaluasi

Pada 20 soal, **Hit@5 = 17/20 (85%)**, **MRR = 0,780**, **Precision@5 macro = 0,200**, dan **Recall@5 macro = 0,808**.

| ID | Pertanyaan | Peringkat bukti pertama |
|---|---|---:|
| A2-003 | Apa itu skripsi? | 19 |
| A2-004 | Apa nilai huruf untuk nilai angka 78? | 6 |
| A3-003 | Apa rumus indeks prestasi semester? | 25 |

Pertanyaan definisi hanya menghasilkan token “skripsi”, yang juga muncul di banyak passage prosedural. Angka 78 harus dicocokkan dengan rentang pada tabel konversi. Pada pertanyaan rumus IP, baris tabel beban studi memakai istilah “IP” dan “semester” berulang kali.

## Masukan untuk Anggota 6

Gabungkan `hasil_per_pertanyaan` dari [hasil retrieval](output/hasil_retrieval.json) dengan [jawaban Anggota 4](../Anggota4/output/hasil_ekstraksi.json) berdasarkan `id_pertanyaan`.
