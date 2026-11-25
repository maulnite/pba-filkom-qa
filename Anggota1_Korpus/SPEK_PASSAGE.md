# Spesifikasi Korpus Passage

Korpus sistem tanya jawab: Tugas Akhir PBA, QA Factoid tanpa LLM. Dibuat dan dikelola oleh **Anggota 1** (penyiapan korpus).

Dokumen ini menjelaskan isi `data/passages.jsonl` dan cara memakainya. Anggota 2–5 cukup membaca dokumen ini; detail proses pembuatannya ada di `Anggota1_Korpus.ipynb`.

---

## 1. Ringkasan

| | |
|---|---|
| **File utama** | `data/passages.jsonl` (satu passage per baris, UTF-8) |
| **Metadata dokumen** | `data/dokumen.json` |
| **Jumlah passage** | 440 |
| **Panjang passage** | 5–145 kata (median ±21) |
| **Bahasa** | Indonesia |

| `dok_id` | Dokumen | Tahun | Passage |
|---|---|---|---|
| `pa2020` | Buku Pedoman Akademik Fakultas Ilmu Komputer UB | 2020 | 396 |
| `tatatertib` | Tata Tertib Pelaksanaan Ujian (UTS & UAS) FILKOM UB | 2016 | 26 |
| `penilaian` | Pedoman Penilaian dan Perhitungan Indeks Prestasi PTIIK | 2015 | 18 |

Semua dokumen berasal dari [Dokumen Resmi FILKOM](https://filkom.ub.ac.id/profil/dokumen-resmi/). URL masing-masing file ada di `data/dokumen.json`.

---

## 2. Field setiap passage

```json
{
  "id": "pa2020-II-I-7",
  "dok_id": "pa2020",
  "halaman": 21,
  "bab": "II",
  "judul_bab": "SISTEM PENDIDIKAN",
  "subbab": "I",
  "judul_subbab": "EVALUASI KEBERHASILAN STUDI",
  "butir": "7",
  "konteks": "",
  "teks": "7. Seorang mahasiswa dinyatakan telah selesai mengikuti kuliah pada suatu Program Studi bilamana telah mengumpulkan jumlah nilai kredit minimal 144 sks, dengan syarat-syarat sebagai berikut: a. IPK ≥ 2,00. b. Telah lulus seluruh mata kuliah wajib. ...",
  "jenis": "butir"
}
```

| Field | Tipe | Isi | Boleh kosong? |
|---|---|---|---|
| `id` | str | ID unik passage (lihat bagian 3) | Tidak |
| `dok_id` | str | Kunci ke `data/dokumen.json` | Tidak |
| `halaman` | int | Nomor halaman PDF tempat passage dimulai | Tidak |
| `bab` | str | Nomor BAB romawi (`"II"`) | Ya, untuk bagian di luar BAB (Visi, Sejarah, Tata Tertib, Penilaian) |
| `judul_bab` | str | Judul BAB (`"SISTEM PENDIDIKAN"`) | Ya |
| `subbab` | str | Huruf subbab (`"I"`) | Ya, untuk pembuka BAB dan judul tanpa huruf |
| `judul_subbab` | str | Judul subbab atau judul bagian (`"VISI"`, `"SANKSI AKADEMIK"`) | Ya, untuk pembuka BAB |
| `butir` | str | Posisi butir: `"7"`, `"1.a"`, `"1.1"` | Ya, untuk `paragraf` dan `tabel` |
| `konteks` | str | Kalimat induk/pengantar, beberapa tingkat dipisah ` › ` | Ya (terisi di 145 passage) |
| `teks` | str | Isi passage | Tidak |
| `jenis` | str | `butir`, `paragraf`, atau `tabel` | Tidak |

### `konteks`: kapan terisi dan kenapa penting

`konteks` berisi kalimat yang **dibutuhkan untuk memahami passage, tetapi tidak ada di `teks`**. Field ini terisi pada tiga kasus:

1. **Butir panjang yang dipecah.** Butir > 150 kata dipecah per sub-butir, lalu kalimat pembuka induknya masuk ke `konteks`.
2. **Kalimat pengantar daftar.** Contoh: `"Untuk melaksanakan kegiatan pendidikan diperlukan administrasi akademik yang meliputi:"` menjadi `konteks` untuk `2. Penentuan rencana studi semester mahasiswa.`
3. **Tabel.** Judul tabel, misalnya `"Tabel 1. Beban Studi maksimal berdasarkan IP semester"`.

Contoh dengan dua tingkat konteks (`pa2020-III-J-1.1`):

```
konteks: "1. Perpindahan Mahasiswa di lingkungan Universitas Brawijaya Merupakan ... terdiri dari: › Adapun persyaratan dan prosedur yang harus dipenuhi dalam pengajuan perpindahan program studi di lingkungan UB antara lain:"
teks   : "1. Mahasiswa yang dapat mengajukan pindah program studi adalah telah mengikuti pendidikan secara terus menerus sekurang-kurangnya 2 semester ... a. Untuk 2 semester, 24 sks dengan IPK sekurang-kurangnya 2,75. b. ..."
```

> **Rekomendasi:** saat membuat index pencarian, gabungkan `judul_subbab + konteks + teks`. Jika hanya `teks` yang di-index, pertanyaan *"apa syarat pindah program studi?"* sulit menemukan passage di atas, karena kata *pindah program studi* hanya ada di `konteks`.

---

## 3. Skema ID

| Jenis | Pola | Contoh |
|---|---|---|
| Butir | `{dok}-{bab}-{kode}-{jalur}` | `pa2020-II-I-7`, `pa2020-I-0-1.a`, `pa2020-III-J-1.1` |
| Teks penutup setelah sub-butir* | `{dok}-{bab}-{kode}-{jalur}.t{n}` | (tidak ada di korpus saat ini) |
| Paragraf | `{dok}-{bab}-{kode}-p{n}` | `pa2020-II-0-p1`, `pa2020-X-S5-p3` |
| Tabel | `{dok}-{id_tabel}-{n}` | `pa2020-tabel1-2`, `penilaian-bobot-7` |
| Paragraf dokumen manual | `{dok}-p{n}` | `penilaian-p1` |

- `{bab}`: nomor BAB, atau `X` jika di luar BAB.
- `{kode}`: huruf subbab (`A`–`L`), `0` untuk pembuka BAB, atau `S1`, `S2`, … untuk bagian berjudul tanpa huruf (Visi, Misi, Sejarah, Tata Tertib, Sanksi).
- `{jalur}`: urutan penanda dari butir teratas, dipisah titik. `1.a` berarti sub-butir `a` di dalam butir `1`.

\* Dipakai jika ada teks setelah daftar sub-butir pada butir yang dipecah.

> ⚠️ **ID stabil selama korpus tidak diubah.** Jika Anggota 1 mengubah aturan pembentukan passage, ID bisa bergeser. Setiap perubahan korpus akan diumumkan ke grup, dan Anggota 5 sebaiknya menjalankan ulang pengecekan ground truth.

---

## 4. Tiga jenis passage

| `jenis` | Jumlah | Asal | Contoh `teks` |
|---|---|---|---|
| `butir` | 380 | Butir bernomor beserta sub-butirnya | `"10. Waktu yang disediakan untuk Ujian Skripsi paling lama 75 menit untuk masing-masing mahasiswa."` |
| `paragraf` | 14 | Teks tanpa nomor: pembuka BAB, Visi, Sejarah | `"Selanjutnya, pada tahun 2015, berdasarkan struktur Organisasi dan Tata Kelola ..."` |
| `tabel` | 46 | Satu baris tabel yang ditulis sebagai kalimat | `"Nilai angka (N) dengan rentang 75 < N ≤ 80 dikonversi menjadi nilai huruf B+."` |

---

## 5. Format isi `teks` (penting untuk Anggota 2, 3, dan 4)

`teks` disimpan **apa adanya**: tidak di-*lowercase*, tidak di-*stem*, dan stopword tidak dibuang.

| Hal | Bentuk di korpus | Contoh |
|---|---|---|
| Huruf besar/kecil | asli | `IPK`, `Ketua Program Studi` |
| Desimal | **koma** | `2,00`, `3,5`, `2,75` |
| Pembanding | `≥ ≤ < >` | `IPK ≥ 2,00`, `75 < N ≤ 80` |
| Angka dalam kata | kadang ditulis kata saja, kadang digit + kata dalam kurung | `empat belas semester`, `15 (lima belas) menit`, `6 (enam) bulan` |
| Persen | `%` | `minimal 80%` |
| Rumus | teks satu baris dengan `Σ` dan `×`, plus penjelasan kalimat | `IP = Σ (K_i × Na_i) / Σ K_i, dengan i = 1 sampai n. Artinya, ...` |
| Penanda butir | tetap ada di dalam teks | `"7. Seorang mahasiswa ... a. IPK ≥ 2,00. b. Telah lulus ..."` |
| Kata ulang | utuh | `syarat-syarat`, `sekurang-kurangnya` |

---

## 6. Cara membaca

```python
import json
from pathlib import Path

DIR_DATA = Path("Anggota1_Korpus/data")   # sesuaikan dengan lokasi folder

passages = [json.loads(baris) for baris in (DIR_DATA / "passages.jsonl").open(encoding="utf-8")]
dokumen = json.loads((DIR_DATA / "dokumen.json").read_text(encoding="utf-8"))

# akses cepat berdasarkan id
passage_by_id = {p["id"]: p for p in passages}

# teks yang disarankan untuk di-index
def teks_index(p: dict) -> str:
    return " ".join(x for x in (p["judul_subbab"], p["konteks"], p["teks"]) if x)

# menampilkan sumber jawaban
def sumber(p: dict) -> str:
    d = dokumen[p["dok_id"]]
    lokasi = f"BAB {p['bab']} {p['subbab']}".strip() if p["bab"] else p["judul_subbab"]
    return f"{d['judul']} ({d['tahun']}), {lokasi}, hlm. {p['halaman']}"

p = passage_by_id["pa2020-II-I-7"]
print(sumber(p))   # Buku Pedoman Akademik ... (2020), BAB II I, hlm. 21
```

---

## 7. Catatan untuk setiap anggota

**Anggota 2 (Pemrosesan Pertanyaan) dan Anggota 3 (Pencarian Passage)**
- Buat **satu fungsi preprocessing bersama** (mis. `preprocess.py`) yang dipakai untuk pertanyaan **dan** passage. Jika pertanyaan di-stem tetapi passage tidak (atau sebaliknya), pencarian gagal tanpa terlihat error.
- Tokenizer sebaiknya mempertahankan angka desimal berkoma (`2,00`) sebagai satu token, dan memperlakukan `≥`/`≤` sebagai token tersendiri.
- Untuk pertanyaan jenis *DEFINISI*, banyak jawaban ada di **BAB I** (`pa2020-I-0-*`) dengan pola `"X adalah ..."`.

**Anggota 4 (Penentuan Jawaban)**
- Regex angka perlu menangani digit berkoma (`\d+(?:,\d+)?`), satuan (`sks`, `semester`, `menit`, `bulan`, `tahun`, `%`), dan **angka dalam kata** (`empat belas semester`).
- Pertanyaan yang sama bisa cocok dengan dua sumber. Contohnya konversi nilai ada di `pa2020-tabel3-*` (FILKOM 2020) dan `penilaian-konversi-*` (PTIIK 2015), dengan isi yang sama kecuali batas bawah E (`0 ≤ N` vs `0 < N`). Gunakan `dok_id`/`dokumen.json` untuk menampilkan sumbernya.
- Untuk menampilkan jawaban beserta konteksnya, `konteks + teks` biasanya cukup sebagai "kutipan pendukung".

**Anggota 5 (Integrasi dan Evaluasi)**
- Untuk setiap pertanyaan ground truth, catat **`id` passage** yang memuat jawabannya, bukan hanya teks jawabannya. Dengan begitu evaluasi *retrieval* (Precision@k, Recall@k, MRR) bisa dihitung terpisah dari evaluasi jawaban.
- Format ground truth yang disarankan:

```json
{"no": 1, "penanya": "Anggota 1", "pertanyaan": "Berapa sks minimal untuk menyelesaikan studi sarjana?", "jawaban": "144 sks", "passage_id": ["pa2020-II-I-7"], "tipe": "ANGKA"}
```

---

## 8. Batasan dan keputusan manual

Bagian ini perlu disebut di laporan (Bab I batasan masalah, Bab IV implementasi).

1. **Cakupan aturan.** Jawaban mengacu pada Pedoman Akademik FILKOM **2020**, Tata Tertib Ujian, dan Pedoman Penilaian PTIIK **2015**. Aturan terbaru (mis. Pedoman UB 2023) tidak termasuk.
2. **Tidak termasuk:** sampul, Peraturan Dekan, daftar isi, kata pengantar, dan daftar tim penyusun (hlm. 1–8 Pedoman FILKOM).
3. **Ditranskripsi manual** (`data/transkripsi_manual.json`, dicek terhadap gambar PDF):
   - 4 tabel Pedoman FILKOM: Tabel 1 beban studi, Tabel 2 huruf mutu, Tabel 3 konversi nilai, dan tabel bobot nilai;
   - 2 rumus: Nilai Akhir (hlm. 18) dan Indeks Prestasi (hlm. 20);
   - seluruh dokumen Pedoman Penilaian PTIIK, karena hasil scan dengan OCR rusak.
4. **Koreksi data sumber:** bobot nilai D pada dokumen PTIIK tertulis `14`, dicatat sebagai `1` karena dianggap salah ketik (Pedoman FILKOM 2020 menetapkan D = 1,0).
5. **Perbaikan ekstraksi** (bukan perubahan isi): `lPK → IPK`, `lndeks → Indeks`, `l (satu) → 1 (satu)`, serta simbol font Symbol ` → ≥` dan ` → ≤`. Typo dari penulis dokumen asli **tidak** diperbaiki.

---

## 9. Membuat ulang korpus

```powershell
uv run --locked --group notebook jupyter nbconvert --to notebook --execute --inplace Anggota1_Korpus/Anggota1_Korpus.ipynb
```

Jalankan dari root proyek. Notebook membentuk passage dari PDF, memeriksa keunikan ID, lalu menyimpan `output/passages.jsonl` dan `output/dokumen.json`.
