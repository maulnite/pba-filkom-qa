# Anggota 6 — Penilaian Jawaban Akhir

Priyambodo Arundaya Satmika · 245150201111011

Tahap penutup mengukur ketepatan jawaban akhir. Notebook membandingkan jawaban Anggota 4 dengan rujukan secara otomatis, lalu mengaitkan putusan dengan peringkat bukti dari Anggota 5.

Modul ini melengkapi tahap yang disebut pada [README proyek](../README.md) dan bagian **Masukan untuk Anggota 6** di [dokumentasi Anggota 5](../Anggota5_Evaluasi_Retrieval/README.md).

## Berkas dan cara menjalankan

| Berkas | Fungsi |
| --- | --- |
| `evaluasi_jawaban.py` | Normalisasi jawaban, aturan empat tingkat kecocokan, penghitungan akurasi, rekap per tipe jawaban dan per metode, dan penulisan hasil. |
| `uji_evaluasi_jawaban.py` | Pemeriksaan mandiri: normalisasi, aturan kecocokan, dan rekaman angka hasil atas 20 soal. |
| `Anggota6_Evaluasi_Jawaban.ipynb` | Penjelasan tahapan, tabel penilaian per soal, analisis kegagalan, dan penyimpanan hasil. |
| `output/hasil_evaluasi.json` | Ringkasan metrik, rekap per tipe dan per metode, serta satu baris per soal. |

Dari root repositori:

```bash
uv sync --locked --group notebook
uv run --locked python -m Anggota6_Evaluasi_Jawaban.evaluasi_jawaban
uv run --locked python -m Anggota6_Evaluasi_Jawaban.uji_evaluasi_jawaban
```

Menjalankan seluruh notebook dari terminal (direktori kerja mengikuti folder notebook):

```bash
uv run --locked --group notebook jupyter nbconvert --to notebook --execute --inplace Anggota6_Evaluasi_Jawaban/Anggota6_Evaluasi_Jawaban.ipynb
```

Notebook membaca `hasil_ekstraksi.json` dari Anggota 4 dan `hasil_retrieval.json` dari Anggota 5. Perintah Python `evaluasi_jawaban` menjalankan ulang ekstraktor secara mandiri dan dapat mengunduh UDPipe pada pemakaian pertama.

## Aturan penilaian

Jawaban sistem dan jawaban rujukan dinormalisasi lebih dulu: Unicode NFKC, case folding, penanda butir seperti `1.` atau `a.` dibuang, tanda kutip diseragamkan, spasi dirapikan, dan tanda baca di tepi dibuang. Isi jawaban tidak diubah dan tidak diringkas.

| Tingkat | Aturan | Ikut dihitung pada |
| --- | --- | --- |
| `COCOK_PERSIS` | Sama setelah normalisasi. | Akurasi ketat, inti, longgar |
| `COCOK_INTI` | Salah satu jawaban memuat jawaban lain sebagai deret token utuh, misalnya `14 semester` di dalam `14 semester sejak pertama kali terdaftar …` | Akurasi inti, longgar |
| `MIRIP_PARAFRASA` | F1 bag-of-token ≥ 0,70 tanpa kecocokan persis atau inti, misalnya `setelah berakhirnya masa daftar ulang` dan `setelah masa daftar ulang berakhir` | Akurasi longgar |
| `TIDAK_COCOK` | Di bawah semua ambang. | — |

Tiga angka akurasi dilaporkan karena satu aturan saja menyesatkan. Akurasi ketat menghukum jawaban benar yang lebih ringkas daripada rujukan, sedangkan akurasi longgar memberi kredit pada jawaban yang benar tetapi disusun berbeda. Ambang 0,70 dipilih setelah memeriksa sebaran F1: parafrasa benar pada set ini bernilai 0,80–0,89, sedangkan jawaban salah yang berbagi satuan bernilai ≤ 0,50.

Penilaian tidak memakai LLM karena jawaban akhir harus dapat diperiksa ulang. Setiap keputusan menyimpan `tingkat`, `skor_f1`, jawaban sistem, dan jawaban rujukan pada `output/hasil_evaluasi.json`.

## Hasil

Pada 20 soal, jawaban sistem benar pada **13 soal (akurasi inti 13/20 = 65,0%)**, dengan **akurasi ketat 8/20 (40,0%)** dan **akurasi longgar 15/20 (75,0%)**. **F1 token macro = 0,696**.

| Metrik | Nilai |
| --- | ---: |
| Akurasi ketat (`COCOK_PERSIS`) | 8/20 (40,0%) |
| Akurasi inti (`COCOK_PERSIS` + `COCOK_INTI`) | 13/20 (65,0%) |
| Akurasi longgar (ditambah `MIRIP_PARAFRASA`) | 15/20 (75,0%) |
| F1 token macro | 0,696 |
| Jawaban tidak cocok | 5 soal |

Sebagai pembanding, retrieval Anggota 5 menemukan bukti di lima besar pada 17/20 soal (85,0%) dengan MRR 0,780. Selisih 85,0% ke 65,0% berasal dari lima soal yang dibahas di bawah.

### Penilaian per soal

| ID | Tipe | Metode | Peringkat bukti | Putusan | F1 |
| --- | --- | --- | ---: | --- | ---: |
| A2-001 | ANGKA | linguistik UDPipe | 3 | `COCOK_PERSIS` | 1,000 |
| A2-002 | DURASI | linguistik UDPipe | 1 | `COCOK_PERSIS` | 1,000 |
| A2-003 | DEFINISI | fallback kalimat | 19 | `TIDAK_COCOK` | 0,000 |
| A2-004 | NILAI_HURUF | fallback kalimat | 6 | `TIDAK_COCOK` | 0,000 |
| A3-001 | DURASI | linguistik UDPipe | 2 | `COCOK_INTI` | 0,400 |
| A3-002 | WAKTU | linguistik UDPipe | 1 | `MIRIP_PARAFRASA` | 0,889 |
| A3-003 | RUMUS | fallback kalimat | 25 | `TIDAK_COCOK` | 0,133 |
| A4-001 | PERSENTASE | linguistik UDPipe | 1 | `COCOK_PERSIS` | 1,000 |
| A4-002 | DURASI | linguistik UDPipe | 1 | `COCOK_PERSIS` | 1,000 |
| A4-003 | ANGKA | simbolik | 1 | `COCOK_PERSIS` | 1,000 |
| A4-004 | JABATAN | linguistik UDPipe | 2 | `COCOK_PERSIS` | 1,000 |
| FARIS-001 | DURASI | linguistik UDPipe | 1 | `COCOK_INTI` | 0,800 |
| FARIS-002 | DURASI | linguistik UDPipe | 1 | `COCOK_INTI` | 0,800 |
| FARIS-003 | ANGKA | linguistik UDPipe | 1 | `TIDAK_COCOK` | 0,500 |
| FARIS-004 | DURASI | linguistik UDPipe | 1 | `COCOK_INTI` | 0,800 |
| SUP-001 | WAKTU | linguistik UDPipe | 1 | `MIRIP_PARAFRASA` | 0,800 |
| SUP-002 | ANGKA | linguistik UDPipe | 1 | `COCOK_INTI` | 0,800 |
| SUP-003 | NILAI_HURUF | fallback kalimat | 1 | `TIDAK_COCOK` | 0,000 |
| SUP-004 | DURASI | linguistik UDPipe | 1 | `COCOK_PERSIS` | 1,000 |
| SUP-005 | ANGKA | simbolik | 1 | `COCOK_PERSIS` | 1,000 |

Empat jawaban `COCOK_INTI` berbentuk jawaban ringkas dari rujukan yang memuat kualifikasi tambahan, misalnya `2 semester` untuk `2 semester kumulatif` dan `30 hari` untuk `30 hari kalender`. Keduanya dinilai benar pada tingkat inti dan terlihat pada tabel ini.

### Akurasi per tipe jawaban

| Tipe | Soal | Persis | Inti | Parafrasa | Akurasi inti |
| --- | ---: | ---: | ---: | ---: | ---: |
| ANGKA | 5 | 3 | 4 | 0 | 80,0% |
| DURASI | 7 | 3 | 7 | 0 | 100,0% |
| DEFINISI | 1 | 0 | 0 | 0 | 0,0% |
| JABATAN | 1 | 1 | 1 | 0 | 100,0% |
| NILAI_HURUF | 2 | 0 | 0 | 0 | 0,0% |
| PERSENTASE | 1 | 1 | 1 | 0 | 100,0% |
| RUMUS | 1 | 0 | 0 | 0 | 0,0% |
| WAKTU | 2 | 0 | 0 | 2 | 0,0% |

### Akurasi per metode ekstraksi

| Metode | Soal | Persis | Inti | Longgar | Akurasi inti |
| --- | ---: | ---: | ---: | ---: | ---: |
| `simbolik` | 2 | 2 | 2 | 2 | 100,0% |
| `linguistik_udpipe` | 14 | 6 | 11 | 13 | 78,6% |
| `fallback_kalimat` | 4 | 0 | 0 | 0 | 0,0% |

## Analisis lima soal yang gagal

Kegagalan dipisahkan menurut penyebabnya, bukan menurut angkanya.

| ID | Peringkat bukti | Penyebab |
| --- | ---: | --- |
| A2-003 | 19 | Retrieval. Pertanyaan definisi hanya menghasilkan token `skripsi`, sehingga passage prosedural muncul lebih dulu; fallback kalimat memilih kalimat tentang format skripsi. |
| A2-004 | 6 | Retrieval. Bukti berada di luar lima besar karena soal konversi nilai 78 harus dicocokkan dengan rentang `75 < N ≤ 80`, bukan dengan kemiripan token. |
| A3-003 | 25 | Retrieval. Baris tabel beban studi berulang kali memuat `IP` dan `semester`, sehingga rumus tertinggal; sistem menjawab dengan kalimat tentang Indeks Prestasi. |
| FARIS-003 | 1 | Ekstraksi. Bukti sudah peringkat satu, tetapi jalur linguistik memilih angka lain pada passage yang sama: `120 sks` untuk pertanyaan `138 sks`. |
| SUP-003 | 1 | Ekstraksi. Tipe `NILAI_HURUF` tidak punya pola simbolik pada passage tersebut, sehingga jatuh ke fallback dan mengembalikan seluruh kalimat tentang ujian khusus alih-alih `C`. |

Dua temuan yang perlu dibawa ke laporan:

1. **Tiga dari lima kegagalan adalah masalah retrieval**, konsisten dengan metrik Anggota 5. Perbaikan di sisi retrieval berpotensi menaikkan akurasi akhir tanpa mengubah ekstraktor.
2. **Jalur `fallback_kalimat` belum pernah benar** (0/4) dan selalu mengembalikan kalimat panjang. Jalur `simbolik` benar pada semua soal yang ditanganinya (2/2), sedangkan jalur linguistik benar pada 11 dari 14 soal.

### Kebenaran jawaban menurut posisi bukti

| Kelompok | Soal | Jawaban benar (inti) |
| --- | ---: | ---: |
| Bukti di lima besar | 17 | 13 (76,5%) |
| Bukti di luar lima besar | 3 | 0 (0,0%) |

Artinya, begitu passage bukti masuk lima besar, ekstraktor menjawab benar pada 76,5% soal. Tanpa bukti di lima besar, jawaban tidak pernah benar pada set ini.

## Batasan

1. Penilaian memakai aturan string dan token, bukan penilaian manusia. Jawaban yang benar tetapi memakai sinonim penuh (`ketua program studi` dan `kaprodi`) akan dinilai salah; peninjauan manual pada `output/hasil_evaluasi.json` tetap diperlukan sebelum angka ini masuk laporan.
2. Jawaban rujukan Anggota 5 dianggap benar. Kekeliruan pada data rujukan tidak terdeteksi modul ini.
3. `COCOK_INTI` menghitung jawaban lebih ringkas sebagai benar walaupun kualifikasi hilang, misalnya `2 semester` untuk `2 semester kumulatif`. Perbedaan ini terlihat pada kolom putusan, bukan disembunyikan.
4. Ambang F1 0,70 ditentukan dari sebaran 20 soal ini. Ambang yang sama perlu diperiksa ulang bila set uji diperluas.
5. Setiap tipe jawaban diuji oleh sedikit soal (DEFINISI, RUMUS, JABATAN, dan PERSENTASE masing-masing satu soal), sehingga akurasi per tipe belum stabil secara statistik.
6. Angka pada `uji_evaluasi_jawaban.py` adalah rekaman hasil saat modul dibuat. Bila korpus, retrieval, atau ekstraktor berubah, jalankan ulang notebook lalu perbarui angka dan tabel di README ini.

## Rujukan

Jurafsky, D. and Martin, J.H. (2021) 'Question Answering', in *Speech and Language Processing*. 3rd edn draft, 29 December, Chapter 23. Available at: [Stanford, Chapter 23](https://web.stanford.edu/~jurafsky/slp3/old_dec21/23.pdf) (Accessed on 22 November 2026).

Manning, C.D., Raghavan, P. and Schütze, H. (2008) *Introduction to Information Retrieval*. Cambridge: Cambridge University Press, Chapters 8 and 21 (evaluation of ranked retrieval and answer extraction).

Rujukan di atas mendukung konsep evaluasi; aturan penilaian pada modul ini dirancang khusus untuk korpus dan set uji proyek, bukan reproduksi metrik baku.
