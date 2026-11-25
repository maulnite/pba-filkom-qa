# Demo web (FastAPI + htmx)

Lapisan demo untuk pipeline Anggota 2-4. Tidak ada berkas Anggota 1-6 yang diubah;
`web/pipeline.py` hanya memanggil API publik tahap sebelumnya.

## Jalankan

```bash
uv sync --locked
uv run uvicorn web.app:app --reload
```

Buka <http://127.0.0.1:8000>.

| Rute | Isi |
|---|---|
| `/` | Kotak tanya + 20 pertanyaan uji yang bisa diklik |
| `POST /tanya` | Fragmen htmx: jawaban, jejak tahap 2, kandidat tahap 3 |
| `GET /tanya?q=` | Fragmen yang sama tanpa JavaScript |
| `/evaluasi` | Hit@5, MRR, akurasi, tabel per tipe dan per metode |
| `/sehat` | Status JSON: kesiapan UDPipe, jumlah passage, jumlah pertanyaan uji |

## Tanpa cache

Setiap permintaan menjalankan pipeline penuh: pemrosesan pertanyaan, retrieval TF-IDF,
lalu ekstraksi jawaban. Tidak ada cache hasil, tidak ada jejak tersimpan. Model UDPipe
dimuat sekali saat server hidup supaya permintaan pertama tidak menanggung unduhan model,
bukan untuk menyimpan hasil.

Waktu satu permintaan pada mesin pengembangan: sekitar 0,2-0,3 detik setelah model siap.

## Docker

```bash
docker build -t pba-filkom-demo .
docker run --rm -p 7860:7860 pba-filkom-demo
```

Model UDPipe diunduh saat build, jadi container siap dipakai tanpa jaringan.
