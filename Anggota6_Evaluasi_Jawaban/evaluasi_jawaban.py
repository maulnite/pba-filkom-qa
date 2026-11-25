"""Penilaian jawaban akhir: bandingkan keluaran Anggota 4 dengan jawaban rujukan Anggota 5."""

import json
import re
import unicodedata
from collections import Counter
from pathlib import Path
from statistics import mean

from Anggota2_Pertanyaan.question_processing import proses_pertanyaan
from Anggota4.ekstraksi import EkstraktorJawaban

ROOT = Path(__file__).resolve().parents[1]
BERKAS_RETRIEVAL = ROOT / "Anggota5_Evaluasi_Retrieval" / "output" / "hasil_retrieval.json"
BERKAS_DOKUMEN = ROOT / "Anggota1_Korpus" / "data" / "dokumen.json"
BERKAS_OUTPUT = ROOT / "Anggota6_Evaluasi_Jawaban" / "output" / "hasil_evaluasi.json"

# Ambang kemiripan token untuk jawaban yang benar tetapi diparafrasa.
AMBANG_F1 = 0.70

POLA_PENANDA_BUTIR = re.compile(r"^\s*(?:\d+(?:\.\d+)*|[a-zA-Z])[.)]\s+")
POLA_TANDA_TEPI = re.compile(r"^[\s.,;:]+|[\s.,;:]+$")
POLA_TOKEN = re.compile(r"\d+(?:[,.]\d+)?|[a-z]+|%|\+|≥|≤|>|<")

URUTAN_PUTUSAN = ("COCOK_PERSIS", "COCOK_INTI", "MIRIP_PARAFRASA", "TIDAK_COCOK")


def normalisasi_jawaban(teks: str) -> str:
    """Samakan bentuk jawaban sebelum dibandingkan tanpa mengubah isi."""
    if not isinstance(teks, str):
        return ""
    hasil = unicodedata.normalize("NFKC", teks).casefold()
    hasil = POLA_PENANDA_BUTIR.sub("", hasil)
    hasil = hasil.replace("\u2018", "'").replace("\u2019", "'").replace("\u201c", '"').replace("\u201d", '"')
    hasil = re.sub(r"\s+", " ", hasil)
    return POLA_TANDA_TEPI.sub("", hasil)


def token_jawaban(teks: str) -> list[str]:
    """Token untuk perbandingan urutan dan kemiripan."""
    return POLA_TOKEN.findall(normalisasi_jawaban(teks))


def _berisi_berurutan(jarum: list[str], jerami: list[str]) -> bool:
    """True bila seluruh token jarum muncul berurutan di jerami."""
    if not jarum or len(jarum) > len(jerami):
        return False
    for awal in range(len(jerami) - len(jarum) + 1):
        if jerami[awal : awal + len(jarum)] == jarum:
            return True
    return False


def cocok_persis(jawaban_sistem: str, jawaban_rujukan: str) -> bool:
    """Sama setelah normalisasi."""
    return bool(normalisasi_jawaban(jawaban_sistem)) and (
        normalisasi_jawaban(jawaban_sistem) == normalisasi_jawaban(jawaban_rujukan)
    )


def cocok_inti(jawaban_sistem: str, jawaban_rujukan: str) -> bool:
    """Salah satu jawaban memuat jawaban lain sebagai deret token utuh."""
    token_sistem = token_jawaban(jawaban_sistem)
    token_rujukan = token_jawaban(jawaban_rujukan)
    return _berisi_berurutan(token_sistem, token_rujukan) or _berisi_berurutan(
        token_rujukan, token_sistem
    )


def f1_token(jawaban_sistem: str, jawaban_rujukan: str) -> float:
    """Kemiripan bag-of-token; dipakai untuk jawaban benar yang diparafrasa."""
    token_sistem = token_jawaban(jawaban_sistem)
    token_rujukan = token_jawaban(jawaban_rujukan)
    if not token_sistem or not token_rujukan:
        return 0.0
    irisan = Counter(token_sistem) & Counter(token_rujukan)
    jumlah_irisan = sum(irisan.values())
    if jumlah_irisan == 0:
        return 0.0
    presisi = jumlah_irisan / len(token_sistem)
    recall = jumlah_irisan / len(token_rujukan)
    return 2 * presisi * recall / (presisi + recall)


def putusan_jawaban(jawaban_sistem: str, jawaban_rujukan: str, ambang_f1: float = AMBANG_F1) -> dict:
    """Tentukan tingkat kecocokan beserta buktinya."""
    skor_f1 = round(f1_token(jawaban_sistem, jawaban_rujukan), 4)
    if cocok_persis(jawaban_sistem, jawaban_rujukan):
        tingkat = "COCOK_PERSIS"
    elif cocok_inti(jawaban_sistem, jawaban_rujukan):
        tingkat = "COCOK_INTI"
    elif skor_f1 >= ambang_f1:
        tingkat = "MIRIP_PARAFRASA"
    else:
        tingkat = "TIDAK_COCOK"
    return {"tingkat": tingkat, "skor_f1": skor_f1}


def evaluasi_baris(baris: dict, ekstraktor: EkstraktorJawaban) -> dict:
    """Nilai satu baris keluaran Anggota 5."""
    hasil_pertanyaan = proses_pertanyaan(baris["pertanyaan"])
    keluaran = ekstraktor.ekstrak(hasil_pertanyaan, baris.get("kandidat_top5", []))
    putusan = putusan_jawaban(keluaran.get("jawaban", ""), baris.get("jawaban_rujukan", ""))
    peringkat = baris.get("peringkat_bukti_pertama")
    return {
        "id_pertanyaan": baris["id_pertanyaan"],
        "penanya": baris.get("penanya", ""),
        "pertanyaan": baris["pertanyaan"],
        "tipe_jawaban": hasil_pertanyaan["tipe_jawaban"],
        "jawaban_rujukan": baris.get("jawaban_rujukan", ""),
        "jawaban_sistem": keluaran.get("jawaban", ""),
        "metode": keluaran.get("metode", ""),
        "status": keluaran.get("status", ""),
        "passage_id": keluaran.get("passage_id", ""),
        "sumber": keluaran.get("sumber", ""),
        "peringkat_bukti_pertama": peringkat,
        "bukti_di_top5": bool(peringkat is not None and peringkat <= 5),
        **putusan,
    }


def _ringkasan_per_kunci(hasil: list[dict], kunci: str) -> dict:
    """Rekap akurasi per jenis pertanyaan atau per metode ekstraksi."""
    rekap: dict[str, dict] = {}
    for baris in hasil:
        label = baris[kunci] or "TIDAK_DIKENALI"
        sel = rekap.setdefault(
            label,
            {"jumlah": 0, "cocok_persis": 0, "cocok_inti": 0, "mirip_parafrasa": 0, "benar_longgar": 0},
        )
        sel["jumlah"] += 1
        if baris["tingkat"] == "COCOK_PERSIS":
            sel["cocok_persis"] += 1
        if baris["tingkat"] in ("COCOK_PERSIS", "COCOK_INTI"):
            sel["cocok_inti"] += 1
        if baris["tingkat"] == "MIRIP_PARAFRASA":
            sel["mirip_parafrasa"] += 1
        if baris["tingkat"] != "TIDAK_COCOK":
            sel["benar_longgar"] += 1

    for label, sel in rekap.items():
        sel["akurasi_persis"] = round(sel["cocok_persis"] / sel["jumlah"], 4)
        sel["akurasi_inti"] = round(sel["cocok_inti"] / sel["jumlah"], 4)
        sel["akurasi_longgar"] = round(sel["benar_longgar"] / sel["jumlah"], 4)
    return dict(sorted(rekap.items()))


def ringkas(hasil: list[dict], ambang_f1: float = AMBANG_F1) -> dict:
    """Hitung metrik akurasi jawaban akhir."""
    jumlah = len(hasil)
    hitung = Counter(baris["tingkat"] for baris in hasil)
    cocok_inti = hitung["COCOK_PERSIS"] + hitung["COCOK_INTI"]
    benar_longgar = jumlah - hitung["TIDAK_COCOK"]

    di_top5 = [baris for baris in hasil if baris["bukti_di_top5"]]
    luar_top5 = [baris for baris in hasil if not baris["bukti_di_top5"]]
    benar_inti_top5 = sum(
        1 for baris in di_top5 if baris["tingkat"] in ("COCOK_PERSIS", "COCOK_INTI")
    )
    benar_inti_luar = sum(
        1 for baris in luar_top5 if baris["tingkat"] in ("COCOK_PERSIS", "COCOK_INTI")
    )

    return {
        "jumlah_pertanyaan": jumlah,
        "akurasi_persis": round(hitung["COCOK_PERSIS"] / jumlah, 4) if jumlah else 0.0,
        "akurasi_inti": round(cocok_inti / jumlah, 4) if jumlah else 0.0,
        "akurasi_longgar": round(benar_longgar / jumlah, 4) if jumlah else 0.0,
        "jumlah_persis": hitung["COCOK_PERSIS"],
        "jumlah_cocok_inti": cocok_inti,
        "jumlah_mirip_parafrasa": hitung["MIRIP_PARAFRASA"],
        "jumlah_benar_longgar": benar_longgar,
        "jumlah_tidak_cocok": hitung["TIDAK_COCOK"],
        "f1_token_macro": round(mean(baris["skor_f1"] for baris in hasil), 4) if jumlah else 0.0,
        "ambang_f1_parafrasa": ambang_f1,
        "buktidi_top5": len(di_top5),
        "benar_inti_di_top5": benar_inti_top5,
        "akurasi_inti_di_top5": round(benar_inti_top5 / len(di_top5), 4) if di_top5 else 0.0,
        "bukti_luar_top5": len(luar_top5),
        "benar_inti_luar_top5": benar_inti_luar,
        "metode": "EkstraktorJawaban Hybrid (simbolik, linguistik UDPipe, fallback kalimat) Anggota 4",
        "catatan": "Akurasi ketat memakai kesamaan setelah normalisasi; akurasi inti menambah kecocokan sebagian; akurasi longgar menambah parafrasa dengan F1 token >= ambang.",
    }


def evaluasi(hasil_retrieval: dict, dokumen: dict | None = None, ambang_f1: float = AMBANG_F1) -> dict:
    """Nilai seluruh baris Anggota 5 lalu kembalikan hasil per soal dan ringkasannya."""
    if dokumen is None:
        dokumen = json.loads(BERKAS_DOKUMEN.read_text(encoding="utf-8"))
    ekstraktor = EkstraktorJawaban(dokumen)
    hasil = [evaluasi_baris(baris, ekstraktor) for baris in hasil_retrieval["hasil_per_pertanyaan"]]
    return {
        "ringkasan": {
            **ringkas(hasil, ambang_f1),
            "per_tipe_jawaban": _ringkasan_per_kunci(hasil, "tipe_jawaban"),
            "per_metode": _ringkasan_per_kunci(hasil, "metode"),
        },
        "hasil_per_pertanyaan": hasil,
    }


def main() -> None:
    hasil_retrieval = json.loads(BERKAS_RETRIEVAL.read_text(encoding="utf-8"))
    hasil = evaluasi(hasil_retrieval)
    ringkasan = hasil["ringkasan"]

    for baris in hasil["hasil_per_pertanyaan"]:
        print(
            f'{baris["id_pertanyaan"]} · {baris["pertanyaan"]}'
            f'\n   rujukan : {baris["jawaban_rujukan"]}'
            f'\n   sistem  : {baris["jawaban_sistem"]}'
            f'\n   putusan : {baris["tingkat"]} (F1 {baris["skor_f1"]:.3f}, {baris["metode"]})'
        )

    BERKAS_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    BERKAS_OUTPUT.write_text(json.dumps(hasil, indent=2, ensure_ascii=False), encoding="utf-8")

    jumlah = ringkasan["jumlah_pertanyaan"]
    print(f"\nSoal dinilai: {jumlah}")
    print(f'Akurasi ketat  : {ringkasan["jumlah_persis"]}/{jumlah} ({ringkasan["akurasi_persis"]:.1%})')
    print(f'Akurasi inti   : {ringkasan["jumlah_cocok_inti"]}/{jumlah} ({ringkasan["akurasi_inti"]:.1%})')
    print(f'Akurasi longgar: {ringkasan["jumlah_benar_longgar"]}/{jumlah} ({ringkasan["akurasi_longgar"]:.1%})')
    print(f'F1 token macro : {ringkasan["f1_token_macro"]:.3f}')
    print(f'Bukti di top5  : {ringkasan["buktidi_top5"]}/{jumlah}, benar inti di antaranya '
          f'{ringkasan["benar_inti_di_top5"]} ({ringkasan["akurasi_inti_di_top5"]:.1%})')
    print(f"Hasil disimpan di {BERKAS_OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
