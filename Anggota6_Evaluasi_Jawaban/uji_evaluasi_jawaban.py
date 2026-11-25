"""Pemeriksaan mandiri modul penilaian jawaban akhir Anggota 6."""

import json
from pathlib import Path

from Anggota6_Evaluasi_Jawaban.evaluasi_jawaban import (
    AMBANG_F1,
    BERKAS_RETRIEVAL,
    cocok_inti,
    cocok_persis,
    evaluasi,
    f1_token,
    normalisasi_jawaban,
    putusan_jawaban,
)

ROOT = Path(__file__).resolve().parents[1]

def jalankan_uji() -> None:
    # 1. Normalisasi tidak boleh mengubah isi jawaban.
    assert normalisasi_jawaban("  144 SKS.  ") == "144 sks"
    assert normalisasi_jawaban("Nilai 2,00") == "nilai 2,00"
    assert normalisasi_jawaban("a. Dekan") == "dekan"
    assert normalisasi_jawaban("B+") == "b+"
    assert normalisasi_jawaban(None) == ""

    # 2. Tingkat kecocokan.
    assert cocok_persis("144 sks", "144 SKS.")
    assert not cocok_persis("144 sks", "144 sks lulus")
    assert cocok_inti("14 semester", "14 semester sejak pertama kali terdaftar sebagai mahasiswa.")
    assert cocok_inti("48 sks", "48 sks lulus")
    assert not cocok_inti("120 sks", "138 sks")
    assert not cocok_inti("B+", "A")
    assert f1_token("Paling lambat 1 bulan setelah berakhirnya masa daftar ulang.",
                    "Paling lambat 1 bulan setelah masa daftar ulang berakhir.") >= AMBANG_F1

    contoh = [
        ("144 sks", "144 sks", "COCOK_PERSIS"),
        ("14 semester", "14 semester sejak pertama kali terdaftar sebagai mahasiswa.", "COCOK_INTI"),
        ("Paling lambat 1 bulan setelah berakhirnya masa daftar ulang.",
         "Paling lambat 1 bulan setelah masa daftar ulang berakhir.", "MIRIP_PARAFRASA"),
        ("120 sks", "138 sks", "TIDAK_COCOK"),
        ("", "80%", "TIDAK_COCOK"),
    ]
    for jawaban_sistem, jawaban_rujukan, tingkat in contoh:
        assert putusan_jawaban(jawaban_sistem, jawaban_rujukan)["tingkat"] == tingkat, (
            f"Gagal pada '{jawaban_sistem}' vs '{jawaban_rujukan}'"
        )

    # 3. Evaluasi penuh atas keluaran Anggota 5.
    hasil_retrieval = json.loads(BERKAS_RETRIEVAL.read_text(encoding="utf-8"))
    hasil = evaluasi(hasil_retrieval)
    ringkasan = hasil["ringkasan"]
    baris = hasil["hasil_per_pertanyaan"]

    assert ringkasan["jumlah_pertanyaan"] == 20
    assert len(baris) == len(hasil_retrieval["hasil_per_pertanyaan"])
    assert all(item["tipe_jawaban"] for item in baris)
    assert all(item["status"] in ("DITEMUKAN", "TIDAK_DITEMUKAN") for item in baris)

    # Angka rujukan di bawah adalah rekaman hasil saat modul ini dibuat.
    # Perbarui bila korpus, retrieval, atau ekstraktor berubah.
    assert ringkasan["jumlah_persis"] == 8
    assert ringkasan["jumlah_cocok_inti"] == 13
    assert ringkasan["jumlah_benar_longgar"] == 15
    assert ringkasan["buktidi_top5"] == 17
    assert ringkasan["benar_inti_di_top5"] == 13
    assert abs(ringkasan["f1_token_macro"] - 0.6961) < 1e-3
    assert set(ringkasan["per_tipe_jawaban"]) >= {"ANGKA", "DURASI", "JABATAN", "NILAI_HURUF"}
    assert set(ringkasan["per_metode"]) >= {"simbolik", "linguistik_udpipe", "fallback_kalimat"}

    id_gagal = {item["id_pertanyaan"] for item in baris if item["tingkat"] == "TIDAK_COCOK"}
    assert id_gagal == {"A2-003", "A2-004", "A3-003", "FARIS-003", "SUP-003"}

    print(
        "Semua pemeriksaan lolos "
        f"({ringkasan['jumlah_pertanyaan']} soal dinilai, "
        f"akurasi inti {ringkasan['jumlah_cocok_inti']}/{ringkasan['jumlah_pertanyaan']})."
    )

if __name__ == "__main__":
    jalankan_uji()
