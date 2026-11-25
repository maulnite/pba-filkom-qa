"""Orkestrasi pipeline Anggota 2-4 untuk demo web.

Modul ini hanya memanggil API publik tahap sebelumnya; berkas Anggota 1-6
tidak diubah sama sekali.
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path

from Anggota2_Pertanyaan.question_processing import proses_pertanyaan
from Anggota3_Retrieval.retrieval import Retrieval
from Anggota4.ekstraksi import EkstraktorJawaban, load_udpipe

AKAR = Path(__file__).resolve().parents[1]
BERKAS_PASSAGES = AKAR / "Anggota1_Korpus" / "data" / "passages.jsonl"
BERKAS_DOKUMEN = AKAR / "Anggota1_Korpus" / "data" / "dokumen.json"
BERKAS_UJI = AKAR / "Anggota5_Evaluasi_Retrieval" / "data" / "pertanyaan_uji.json"
BERKAS_RETRIEVAL = AKAR / "Anggota5_Evaluasi_Retrieval" / "output" / "hasil_retrieval.json"
BERKAS_EVALUASI = AKAR / "Anggota6_Evaluasi_Jawaban" / "output" / "hasil_evaluasi.json"

PANJANG_CUPLIKAN = 320
PANJANG_KUTIPAN_RINGKAS = 260

LABEL_METODE = {
    "simbolik": "simbolik · tabel/rumus",
    "linguistik_udpipe": "linguistik · dependency parsing UDPipe",
    "fallback_kalimat": "fallback kalimat",
    "tidak_tersedia": "tidak ditemukan",
}


def _baca_json(berkas: Path):
    return json.loads(berkas.read_text(encoding="utf-8"))


def muat_passages() -> list[dict]:
    with BERKAS_PASSAGES.open(encoding="utf-8") as berkas:
        return [json.loads(baris) for baris in berkas if baris.strip()]


def muat_dokumen() -> dict:
    return _baca_json(BERKAS_DOKUMEN)


def muat_set_uji() -> list[dict]:
    return _baca_json(BERKAS_UJI)


def muat_evaluasi() -> dict:
    """Gabungkan hasil Anggota 5 (retrieval) dan Anggota 6 (jawaban) per soal."""
    retrieval = _baca_json(BERKAS_RETRIEVAL)
    jawaban = _baca_json(BERKAS_EVALUASI)
    peta_retrieval = {baris["id_pertanyaan"]: baris for baris in retrieval["hasil_per_pertanyaan"]}

    baris = []
    for butir in jawaban["hasil_per_pertanyaan"]:
        r = peta_retrieval.get(butir["id_pertanyaan"], {})
        baris.append({
            "id": butir["id_pertanyaan"],
            "pertanyaan": butir["pertanyaan"],
            "tipe": butir["tipe_jawaban"],
            "metode": butir["metode"],
            "tingkat": butir["tingkat"],
            "jawaban_sistem": butir["jawaban_sistem"],
            "jawaban_rujukan": butir["jawaban_rujukan"],
            "peringkat_bukti": r.get("peringkat_bukti_pertama"),
            "bukti_di_top5": butir.get("bukti_di_top5"),
            "recall_at_5": r.get("recall_at_5"),
            "skor_f1": butir.get("skor_f1"),
            "sumber": butir.get("sumber", ""),
        })

    return {
        "ringkasan_retrieval": retrieval["ringkasan"],
        "ringkasan_jawaban": jawaban["ringkasan"],
        "baris": baris,
    }


def _norm(teks: str) -> str:
    return " ".join((teks or "").casefold().split())


def buang_kutipan_duplikat(jawaban: str, ringkas: str) -> str:
    """Kosongkan kutipan bila isinya sudah terbaca pada jawaban panjang."""
    j, r = _norm(jawaban), _norm(ringkas)
    if len(j) >= 90 and r and j in r:
        return ""
    return ringkas


def kunci_pertanyaan(teks: str) -> str:
    return " ".join((teks or "").split()).casefold()


def ringkas_kutipan(teks: str) -> str:
    """Ambil satu sampai dua kalimat pertama sebagai bukti ringkas."""
    teks = (teks or "").strip()
    if not teks:
        return ""
    potongan = [k.strip() for k in re.split(r"(?<=[.!?])\s+", teks) if k.strip()]
    # Abaikan pecahan pendek seperti penanda butir "a." atau "1.".
    kalimat = [k for k in potongan if len(k) >= 25] or potongan
    ringkas = kalimat[0] if kalimat else teks
    if len(ringkas) > PANJANG_KUTIPAN_RINGKAS:
        return ringkas[:PANJANG_KUTIPAN_RINGKAS].rsplit(" ", 1)[0] + "…"
    if len(kalimat) > 1 and len(ringkas) + 1 + len(kalimat[1]) <= PANJANG_KUTIPAN_RINGKAS:
        ringkas = f"{ringkas} {kalimat[1]}"
    if len(ringkas) < len(teks):
        ringkas = f"{ringkas} …"
    return ringkas


class _DokumenKosong:
    """Dokumen tiruan agar jalur linguistik dilewati tanpa galat."""

    def __iter__(self):
        return iter(())

    def __len__(self) -> int:
        return 0


class _NlpKosong:
    """Pengganti model UDPipe saat model tidak tersedia."""

    def __call__(self, teks: str) -> _DokumenKosong:
        return _DokumenKosong()


class SistemQA:
    """Muat korpus dan model sekali, lalu jalankan satu jejak pipeline per pertanyaan."""

    def __init__(self) -> None:
        self.passages = muat_passages()
        self.dokumen = muat_dokumen()
        self.set_uji = muat_set_uji()
        self.peta_uji = {kunci_pertanyaan(q["pertanyaan"]): q for q in self.set_uji}
        self.retrieval = Retrieval(self.passages, self.dokumen)
        self.ekstraktor = EkstraktorJawaban(dokumen=self.dokumen)
        self.udpipe_siap = False
        self.catatan_udpipe = ""
        self.waktu_siap_ms = 0.0

    def siapkan(self) -> None:
        """Muat model UDPipe sekali di awal agar permintaan pertama tidak lambat."""
        mulai = time.perf_counter()
        try:
            nlp = load_udpipe()
            self.ekstraktor = EkstraktorJawaban(dokumen=self.dokumen, nlp=nlp)
            self.udpipe_siap = True
        except Exception as exc:  # noqa: BLE001 - model bisa gagal diunduh
            self.ekstraktor = EkstraktorJawaban(dokumen=self.dokumen, nlp=_NlpKosong())
            self.udpipe_siap = False
            self.catatan_udpipe = (
                f"Model UDPipe tidak tersedia ({type(exc).__name__}); "
                "jalur linguistik dilewati, hanya jalur simbolik dan fallback."
            )
        self.waktu_siap_ms = round((time.perf_counter() - mulai) * 1000, 1)

    def status(self) -> dict:
        return {
            "udpipe_siap": self.udpipe_siap,
            "catatan_udpipe": self.catatan_udpipe,
            "jumlah_passage": len(self.passages),
            "jumlah_pertanyaan_uji": len(self.set_uji),
            "waktu_siap_ms": self.waktu_siap_ms,
            "id_model_udpipe": "indonesian-gsd-ud-2.5-191206",
        }

    def trace(self, pertanyaan: str, top_k: int = 5) -> dict:
        """Jalankan tahap 2-4 dan kembalikan satu jejak siap-render."""
        pertanyaan = " ".join((pertanyaan or "").split())
        kunci = kunci_pertanyaan(pertanyaan)

        jejak: dict = {
            "pertanyaan": pertanyaan,
            "galat": None,
            "proses": None,
            "kandidat": [],
            "jawaban": None,
            "uji": self.peta_uji.get(kunci),
            "waktu": {"proses_ms": 0.0, "retrieval_ms": 0.0, "ekstraksi_ms": 0.0, "total_ms": 0.0},
            "bendera": self.status(),
        }

        mulai = time.perf_counter()
        try:
            proses = proses_pertanyaan(pertanyaan)
        except (ValueError, TypeError) as exc:
            jejak["galat"] = f"Pertanyaan tidak bisa diproses: {exc}"
            return jejak
        selesai_proses = time.perf_counter()

        if proses["status"] == "SIAP_RETRIEVAL":
            kandidat = self.retrieval.cari_passage(proses, top_k=int(top_k))
        else:
            kandidat = []
        selesai_retrieval = time.perf_counter()

        jawaban = self._ekstrak(proses, kandidat)
        jawaban["kutipan_ringkas"] = buang_kutipan_duplikat(
            jawaban.get("jawaban", ""),
            ringkas_kutipan(jawaban.get("kutipan", "")),
        )
        selesai_ekstraksi = time.perf_counter()

        skor_maks = max((k["score"] for k in kandidat), default=0.0) or 1.0
        bukti_rujukan = set(jejak["uji"]["passage_id"]) if jejak["uji"] else set()
        terpilih = jawaban.get("passage_id", "")

        kandidat_kaya = []
        for k in kandidat:
            dok = self.dokumen.get(k["dok_id"], {})
            halaman = k.get("halaman")
            url = dok.get("url")
            teks = k.get("teks", "")
            kandidat_kaya.append({
                "rank": k["rank"],
                "passage_id": k["passage_id"],
                "score": round(float(k["score"]), 4),
                "skor_bar": round(100.0 * float(k["score"]) / skor_maks, 1),
                "jenis": k.get("jenis", ""),
                "judul_bab": k.get("judul_bab", ""),
                "judul_subbab": k.get("judul_subbab", ""),
                "halaman": halaman,
                "dok_id": k["dok_id"],
                "judul_dokumen": dok.get("judul", k["dok_id"]),
                "tahun": dok.get("tahun"),
                "url_halaman": f"{url}#page={halaman}" if url and isinstance(halaman, int) else None,
                "cuplikan": teks[:PANJANG_CUPLIKAN],
                "terpotong": len(teks) > PANJANG_CUPLIKAN,
                "terpilih": k["passage_id"] == terpilih,
                "bukti_rujukan": k["passage_id"] in bukti_rujukan,
            })

        jejak.update({
            "proses": proses,
            "kandidat": kandidat_kaya,
            "jawaban": jawaban,
            "waktu": {
                "proses_ms": round((selesai_proses - mulai) * 1000, 1),
                "retrieval_ms": round((selesai_retrieval - selesai_proses) * 1000, 1),
                "ekstraksi_ms": round((selesai_ekstraksi - selesai_retrieval) * 1000, 1),
                "total_ms": round((selesai_ekstraksi - mulai) * 1000, 1),
            },
        })
        return jejak

    def _ekstrak(self, proses: dict, kandidat: list[dict]) -> dict:
        try:
            return self.ekstraktor.ekstrak(proses, kandidat)
        except Exception as exc:  # noqa: BLE001 - jalur UDPipe bisa gagal saat runtime
            cadangan = EkstraktorJawaban(dokumen=self.dokumen, nlp=_NlpKosong())
            keluaran = cadangan.ekstrak(proses, kandidat)
            keluaran["catatan_galat"] = (
                f"Jalur UDPipe gagal ({type(exc).__name__}); hasil memakai jalur simbolik/fallback."
            )
            return keluaran
