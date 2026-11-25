# Anggota 2 — Pemrosesan Pertanyaan

Bagian ini menyiapkan pertanyaan untuk sistem QA factoid tanpa LLM berdasarkan
korpus Anggota 1. Pertanyaan menghasilkan kata kunci, jenis pertanyaan, dan tipe
jawaban yang diharapkan. Modul siap diuji saat integrasi dengan Anggota 3–5.

## Berkas dan cara menjalankan

| Berkas | Fungsi |
| --- | --- |
| `Anggota2_Pertanyaan.ipynb` | Penjelasan tahapan, contoh, bukti ground truth, dan pemeriksaan yang bisa dijalankan ulang. |
| `preprocess.py` | Normalisasi, tokenisasi regex, alias istilah, dan stopword removal bersama. |
| `question_processing.py` | Deteksi jenis pertanyaan dan tipe jawaban berbasis aturan. |
| `data/pertanyaan_anggota2.json` | Empat pertanyaan, jawaban rujukan, kutipan, dan daftar passage ID. |
| `output/hasil_pertanyaan.json` | Dua belas contoh keluaran pemrosesan pertanyaan. |
| `output/passages_preprocessed.jsonl` | Token pencarian seluruh 440 passage, disertai ID dan metadata lokasi. |

Struktur folder yang diharapkan:

```text
pba-filkom-qa/
├── Anggota1_Korpus/data/
│   ├── passages.jsonl
│   └── dokumen.json
└── Anggota2_Pertanyaan/
    ├── Anggota2_Pertanyaan.ipynb
    ├── preprocess.py
    ├── question_processing.py
    ├── README.md
    ├── data/pertanyaan_anggota2.json
    └── output/
```

Dari folder `Anggota2_Pertanyaan`:

```powershell
py -X utf8 question_processing.py "Berapa IPK minimal untuk lulus?"
```

Modul utama hanya membutuhkan **Python >= 3.10**, tanpa pip install, model, API,
atau akses internet. Untuk contoh lengkap, buka notebook di VS Code/Jupyter,
pilih kernel Python yang tersedia di komputer sendiri, lalu **Run All**.
Notebook dapat dijalankan dari root repositori atau folder Anggota2_Pertanyaan.
Lingkungan `.venv` Anggota 1 yang disalin dari komputer lain tidak dijadikan syarat.
Semua kode implementasi berada pada dua modul Python; notebook mengimpornya agar
tidak ada dua versi logika yang berbeda.

## Penjelasan metode untuk bagian Bab II–IV

### Dasar teori

Pemrosesan pertanyaan mempunyai dua fungsi utama di sini: menyusun kata kunci
pencarian dan memperkirakan tipe jawaban. Modul PBA14 slide 35–36 menguraikan kedua
fungsi ini, sedangkan slide 43–44 membahas deteksi tipe berbasis aturan dan regex.
Slide 47 menjelaskan query formulation. Pemisahan pemrosesan pertanyaan dari
pencarian dan penentuan jawaban juga dijelaskan oleh Jurafsky dan Martin (2021,
Chapter 23). Modul PBA02 slide 2 menjadi acuan topik preprocessing.

Implementasi **tidak menggunakan POS tagging, NER, dependency parsing, atau
stemming**. Jangan menyebut pengenalan SIAPA sebagai NER: program hanya membaca
pola pertanyaan, belum menandai entitas pada passage. Label domain di bawah
merupakan rancangan implementasi kelompok, bukan reproduksi lengkap taksonomi
Li dan Roth.

### Alur dan keputusan implementasi

1. Validasi masukan: nilai harus string dan tidak kosong.
2. Normalisasi Unicode NFKC, case folding, dan spasi. `>=`/`<=` disamakan
   menjadi `≥`/`≤`. Desimal titik di antara digit disamakan menjadi koma.
3. Kenali penanda tanya pada teks sebelum stopword removal.
4. Tentukan target berdasarkan penanda utama, lalu objek pertanyaannya.
   Contoh: pertanyaan bobot nilai huruf meminta ANGKA; pertanyaan konversi ke
   nilai huruf meminta NILAI_HURUF. Pertanyaan IPK tetap ANGKA walaupun menyebut
   semester sebagai konteks.
5. Untuk pencarian, samakan singkatan, tokenisasi dengan regex, lalu buang
   stopword menggunakan daftar kecil yang terlihat pada `preprocess.py`.
6. Kembalikan hasil terstruktur. Beberapa penanda tanya, kata kunci kosong, atau
   pola tidak dikenal menghasilkan `PERLU_KLARIFIKASI`.

Penyamaan istilah diterapkan ke query **dan** passage:

| Bentuk panjang | Token |
| --- | --- |
| indeks prestasi kumulatif; IP kumulatif | ipk |
| indeks prestasi | ip |
| satuan kredit semester; sistem kredit semester | sks |
| ujian akhir semester | uas |
| ujian tengah semester | uts |
| program studi | prodi |

Satuan dan sistem kredit semester sama-sama disingkat SKS. Arti yang dimaksud
tetap perlu dibedakan lewat konteks, terutama pada pertanyaan definisi.

Angka, simbol pembanding, tanda persen, nilai seperti `B+` dan `D+`, serta negasi
seperti `tidak` dipertahankan. Kata `minimal`, `maksimal`, `kurang`, dan `lebih`
juga tidak dibuang. `empat belas semester` dipertahankan sebagai tiga token;
konversinya menjadi angka 14 adalah tanggung jawab ekstraksi jawaban.
Teks sumber tidak ditulis ulang sehingga kapitalisasi dan kutipan aslinya tetap
dapat digunakan Anggota 4.

Tidak memakai stemming adalah keputusan baseline agar singkatan/nilai domain
tidak berubah dan modul dapat dijalankan tanpa model tambahan. Kelemahannya:
kata berimbuhan dan sinonim belum otomatis cocok. Jika stemming ditambahkan,
ubah fungsi bersama dan bangun ulang seluruh indeks, bukan hanya query.

### Library dan bagian implementasi

| Library | Peran |
| --- | --- |
| `re` | Tokenisasi, penanda tanya, dan aturan tipe jawaban. |
| `unicodedata` | Normalisasi Unicode. |
| `json` | Membaca korpus/ground truth dan menulis keluaran terstruktur. |
| `pathlib`, `sys` | Lokasi data, impor modul, dan pemanggilan terminal. |
| `hashlib` | Memastikan berkas input tetap sama selama notebook berjalan. |
| `IPython.display` | Tabel contoh dalam notebook; tidak diperlukan oleh modul utama. |

Daftar stopword, alias domain, regex, prioritas aturan, kontrak keluaran, dan
pemeriksaan dirancang khusus untuk korpus ini; tidak ada model terlatih.
**Implementasi disiapkan dengan bantuan AI.** Dokumen tugas membatasi penggunaan
AI. Pelajari dan tinjau kode, catat kontribusi sebenarnya, dan sesuaikan penggunaannya
dengan ketentuan dosen. Penjelasan ini bukan pernyataan bahwa kode ditulis mandiri
oleh mahasiswa.

## Kontrak keluaran

```python
from question_processing import proses_pertanyaan

hasil = proses_pertanyaan("Berapa IPK minimal untuk lulus?")
# hasil["kata_kunci"]       -> ["ipk", "minimal", "lulus"]
# hasil["jenis_pertanyaan"] -> "BERAPA"
# hasil["tipe_jawaban"]     -> "ANGKA"
# hasil["query"]            -> "ipk minimal lulus"
# hasil["status"]           -> "SIAP_RETRIEVAL"
```

| Field | Tipe | Penggunaan |
| --- | --- | --- |
| `pertanyaan` | str | Masukan asli untuk modul jawaban. |
| `normalisasi` | str | Huruf/Unicode/spasi dinormalisasi, sebelum alias/tokenisasi. |
| `token` | list[str] | Token setelah alias, sebelum stopword removal. |
| `token_pencarian` | list[str] | Token setelah stopword removal, urutan/frekuensi dipertahankan. |
| `kata_kunci` | list[str] | Token pencarian unik, sesuai urutan muncul. |
| `query` | str | Gabungan token pencarian dengan spasi. |
| `jenis_pertanyaan` | str | Bentuk penanda tanya utama. |
| `penanda_tanya` | str | Penanda yang ditemukan pada masukan. |
| `tipe_jawaban` | str | Target yang diteruskan ke Anggota 4. |
| `aturan_tipe` | str | Aturan yang terpicu; bukan confidence atau hasil jawaban. |
| `status` | str | SIAP_RETRIEVAL atau PERLU_KLARIFIKASI. |
| `catatan` | list[str] | Batasan pola dan cakupan sumber. |
| `versi_preprocess` | str | Versi fungsi bersama, saat ini 1.0. |

Jenis pertanyaan: `BERAPA`, `APA`, `SIAPA`, `KAPAN`, `DI_MANA`,
`BAGAIMANA`, `MENGAPA`, `YA_TIDAK`, `MANA`, dan `TIDAK_DIKENALI`.
MANA tanpa bentuk lokasi belum dipetakan ke target khusus.

| Tipe jawaban | Target/contoh |
| --- | --- |
| ANGKA | Jumlah sks, IPK, skor, bobot, atau rentang angka. |
| DURASI | Lama studi/ujian, semester, menit, bulan, atau tahun. |
| PERSENTASE | Persen kehadiran atau batas persentase. |
| NILAI_HURUF | A, B+, B, dan sebagainya. |
| DEFINISI | Penjelasan istilah seperti skripsi. |
| JABATAN | Ketua Program Studi, Ketua Jurusan, Dekan; asumsi domain untuk SIAPA. |
| ORANG | Nama orang apabila diminta eksplisit; cakupan sangat terbatas. |
| WAKTU | Tanggal, tahun, atau peristiwa; kalender akademik tidak tersedia. |
| LOKASI | Tempat kegiatan atau lokasi. |
| SYARAT | Persyaratan kegiatan akademik. |
| PROSEDUR | Cara atau tahapan. |
| RUMUS | Rumus atau cara perhitungan. |
| DAFTAR | Beberapa item. |
| ALASAN | Sebab; dapat melampaui factoid. |
| YA_TIDAK | Konfirmasi, memerlukan penanganan jawaban khusus. |
| TIDAK_DIKENALI | Klarifikasi diperlukan. |

Label ini **usulan kontrak integrasi**, belum berarti anggota lain sudah menyetujuinya.
Ground truth tetap memakai field `tipe` seperti rekomendasi Anggota 1; isinya sama
dengan `tipe_jawaban`. Pertanyaan kompleks boleh dikenali, tetapi mengenali tipe
tidak berarti modul jawaban sudah mendukungnya.

## Integrasi Anggota 3: satu fungsi preprocessing

Dari root repositori:

```python
from Anggota2_Pertanyaan.preprocess import preprocess, teks_index
from Anggota2_Pertanyaan.question_processing import proses_pertanyaan

hasil = proses_pertanyaan("Berapa sks minimal untuk lulus?")
if hasil["status"] == "PERLU_KLARIFIKASI":
    print("Mohon tulis satu pertanyaan yang lebih spesifik.")
else:
    token_query = hasil["token_pencarian"]
    token_passage = [preprocess(teks_index(p)) for p in passages]
    # Teruskan token ini ke metode pencarian milik Anggota 3.
```

Jangan hanya menggunakan `p["teks"]`: `teks_index` menggabungkan
`judul_subbab + konteks + teks`. Jangan menambah preprocessing berbeda hanya pada
satu sisi. Jangan memperlakukan `query` sebagai daftar kandidat jawaban.

Jika Anggota 3 memilih scikit-learn yang sudah tersedia di lingkungannya,
konfigurasi berikut menjaga tokenizer yang sama. Ini contoh penghubung,
bukan implementasi pemeringkatan passage:

```python
from sklearn.feature_extraction.text import TfidfVectorizer
from Anggota2_Pertanyaan.preprocess import preprocess, teks_index

vectorizer = TfidfVectorizer(
    tokenizer=preprocess,
    token_pattern=None,
    preprocessor=None,
    lowercase=False,
)
matriks_passage = vectorizer.fit_transform([teks_index(p) for p in passages])
vektor_query = vectorizer.transform([hasil["pertanyaan"]])
```

Vectorizer menerima pertanyaan asli agar `preprocess` dijalankan tepat sekali.
Contoh ini tidak mewajibkan scikit-learn dan belum menghitung skor retrieval.
Alternatifnya, gunakan daftar `token_pencarian` pada ekspor secara langsung.

## Integrasi Anggota 4 dan 5

- **Anggota 4:** gunakan tipe sebagai petunjuk kandidat, lalu periksa passage
  pendukung. ANGKA tidak selalu integer: pertahankan `2,00`, pembanding, dan
  konteks. DURASI dapat berupa `empat belas semester`. Modul ini tidak memilih,
  menghitung, atau mengarang jawaban.
- **Anggota 5:** gabungkan empat data ground truth dengan milik anggota lain.
  Daftar `passage_id` dapat memiliki beberapa sumber yang sama-sama relevan.
  Simpan indeks baris ekspor sejajar dengan ID. Periksa duplikasi pertanyaan
  sebelum menetapkan 20 pertanyaan akhir.
- Setelah korpus/aturan diubah, jalankan ulang notebook, ekspor, dan indeks.
  Anggota 3 memakai fungsi ini untuk membangun indeks dan memeriksa kecocokan ekspor.

## Pemeriksaan yang sudah dijalankan

Notebook telah dijalankan dari kernel baru Python 3.13.7, 9 sel kode, berurutan:

- 29 kasus regresi klasifikasi lolos.
- Desimal, simbol, nilai B+/D+, negasi, angka kata, konteks, dan input kosong/non-string diperiksa.
- Seluruh 440 passage berhasil diproses tanpa token kosong.
- Empat ground truth cocok dengan ID/kutipan korpus; nilai 78 berada pada rentang B+.
- Ekspor memuat 12 contoh pertanyaan dan 440 passage.
- SHA256 kedua berkas data sumber tidak berubah selama eksekusi.

Angka 29 menghitung kasus regresi yang dirancang untuk aturan ini. Percobaan
retrieval paket gabungan tercatat di [hasil eksperimen](../docs/eksperimen.md).
Lingkungan Jupyter lokal sempat mencetak pesan libzmq saat kernel ditutup;
seluruh sel selesai, output tersimpan, dan tidak ada error output pada notebook.

## Keterbatasan

Aturan bergantung susunan kata dan belum menangani semua parafrasa, typo,
sinonim, pertanyaan tanpa kata tanya, atau multi-intent. Lebih dari satu
penanda tanya meminta klarifikasi secara konservatif; belum ada parsing
klausa. Pemetaan APA ke DEFINISI dan SIAPA ke JABATAN dapat salah.
Pengenalan jenis tidak membuktikan ketersediaan jawaban: bahkan pertanyaan
di luar topik dapat terklasifikasi secara sintaktis.

Desimal titik diasumsikan desimal, bukan ribuan; `2,0` dan `2,00` belum disamakan.
`15 (lima belas)` tetap memuat kedua bentuk, belum digabung menjadi satu nilai.
Jangan gunakan korpus ini sebagai pernyataan aturan terbaru.

## Rujukan

Adikara, P.P., Setiawan, B.D. and Adinugroho, S. (n.d.) *Pemrosesan Teks*.
Bahan kuliah Pemrosesan Bahasa Alami, Universitas Brawijaya, slide 2.

Adikara, P.P., Setiawan, B.D. and Adinugroho, S. (n.d.) *Sistem Tanya Jawab
(Question Answer System)*. Bahan kuliah Pemrosesan Bahasa Alami,
Universitas Brawijaya, slide 35–36 dan 43–47.

Jurafsky, D. and Martin, J.H. (2021) 'Question Answering', in *Speech and Language
Processing*. 3rd edn draft, 29 December, Chapter 23. Available at:
[Stanford, Chapter 23](https://web.stanford.edu/~jurafsky/slp3/old_dec21/23.pdf)
(Accessed: 22 November 2026).

Tahun tidak terlihat pada sampul modul, sehingga digunakan n.d.
Rujukan mendukung konsep; aturan Indonesia dan hasil pengujian harus dijelaskan
sebagai implementasi pada korpus ini.
