"""Pemeriksaan mandiri modul ekstraksi jawaban Anggota 4."""

import json
from pathlib import Path

from Anggota2_Pertanyaan.question_processing import proses_pertanyaan
from Anggota3_Retrieval.retrieval import Retrieval

from .ekstraksi import EkstraktorJawaban
from .simbolik import ekstrak_rumus, evaluasi_tabel, normalisasi_bilangan

ROOT = Path(__file__).resolve().parents[1]


def jalankan_uji() -> None:
    # 1. Uji komponen simbolik.
    assert normalisasi_bilangan("paling lama empat belas semester") == "paling lama 14 semester"
    assert normalisasi_bilangan("maksimal 15 (lima belas) menit") == "maksimal 15 menit"
    assert normalisasi_bilangan("minimal satu publikasi dan salah satu syarat") == "minimal 1 publikasi dan salah satu syarat"

    assert evaluasi_tabel(
        "Nilai angka (N) dengan rentang 75 < N ≤ 80 dikonversi menjadi nilai huruf B+.",
        "Apa nilai huruf untuk nilai angka 78?",
        "NILAI_HURUF",
    ) == "B+"
    assert evaluasi_tabel(
        "Jika Indeks Prestasi (IP) semester sebelumnya IP ≥ 3,00, beban studi maksimum yang boleh diambil pada semester berikutnya adalah 24 sks.",
        "Berapa sks beban studi maksimum jika IP semester sebelumnya 3,20?",
        "ANGKA",
    ) == "24 sks"
    assert evaluasi_tabel(
        "Dalam perhitungan Indeks Prestasi, nilai huruf B+ memiliki bobot 3,5.",
        "Berapa bobot nilai huruf B+?",
        "ANGKA",
    ) == "3,5"
    assert ekstrak_rumus("IP = Σ (K_i × Na_i) / Σ K_i, dengan i = 1 sampai n.") == "IP = Σ (K_i × Na_i) / Σ K_i."

    # 2. Uji penanganan input tidak siap atau kandidat kosong.
    ext = EkstraktorJawaban()
    kosong = ext.ekstrak(proses_pertanyaan("Apa?"), [])
    assert kosong["status"] == "TIDAK_DITEMUKAN"

    # 3. Uji isolasi pada 11 pertanyaan rujukan (Anggota 2, 3, 4).
    korpus_dir = ROOT / "Anggota1_Korpus" / "data"
    dokumen = json.loads((korpus_dir / "dokumen.json").read_text(encoding="utf-8"))
    with (korpus_dir / "passages.jsonl").open(encoding="utf-8") as berkas:
        passages = [json.loads(baris) for baris in berkas if baris.strip()]
    p_by_id = {p["id"]: p for p in passages}
    ext = EkstraktorJawaban(dokumen, nlp=ext.nlp)

    berkas_uji = (
        ROOT / "Anggota2_Pertanyaan" / "data" / "pertanyaan_anggota2.json",
        ROOT / "Anggota3_Retrieval" / "data" / "pertanyaan_anggota3.json",
        ROOT / "Anggota4" / "data" / "pertanyaan_anggota4.json",
    )
    ekspetasi_inti = {
        "Berapa sks minimal untuk menyelesaikan studi sarjana?": "144 sks",
        "Berapa lama waktu maksimal untuk Ujian Skripsi?": "75 menit",
        "Apa nilai huruf untuk nilai angka 78?": "B+",
        "Berapa lama waktu maksimal untuk menyelesaikan studi sarjana?": "14 semester",
        "Apa rumus indeks prestasi semester?": "IP = Σ (K_i × Na_i) / Σ K_i.",
        "Berapa persentase kehadiran minimal agar mahasiswa boleh mengikuti UAS?": "80%",
        "Berapa menit batas maksimal keterlambatan mengikuti ujian?": "15 menit",
        "Berapa bobot nilai huruf B+?": "3,5",
        "Siapa yang menetapkan pengecualian Dosen Pembimbing Skripsi?": "Dekan",
    }

    total = 0
    for path in berkas_uji:
        for item in json.loads(path.read_text(encoding="utf-8")):
            hq = proses_pertanyaan(item["pertanyaan"])
            kandidat = [
                {
                    **p_by_id[pid],
                    "passage_id": pid,
                    "rank": idx,
                    "score": 1.0,
                    "sumber": dict(dokumen[p_by_id[pid]["dok_id"]]),
                }
                for idx, pid in enumerate(item["passage_id"], start=1)
            ]
            out = ext.ekstrak(hq, kandidat)
            assert out["status"] == "DITEMUKAN"
            if item["pertanyaan"] in ekspetasi_inti:
                assert out["jawaban"] == ekspetasi_inti[item["pertanyaan"]], (
                    f"Gagal pada '{item['pertanyaan']}': dapat '{out['jawaban']}'"
                )
            total += 1

    # 4. Uji integrasi end-to-end dengan Retrieval (top_k=5) untuk 4 pertanyaan Anggota 4.
    retrieval = Retrieval(passages, dokumen)
    for item in json.loads((ROOT / "Anggota4" / "data" / "pertanyaan_anggota4.json").read_text(encoding="utf-8")):
        hq = proses_pertanyaan(item["pertanyaan"])
        kandidat = retrieval.cari_passage(hq, top_k=5)
        out = ext.ekstrak(hq, kandidat)
        assert out["jawaban"] == item["jawaban"], (
            f"End-to-end gagal pada '{item['pertanyaan']}': dapat '{out['jawaban']}'"
        )

    print(f"Semua pemeriksaan lolos ({total} pertanyaan rujukan isolasi + 4 end-to-end Anggota 4).")


if __name__ == "__main__":
    jalankan_uji()
