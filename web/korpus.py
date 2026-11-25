"""Ekstraksi dan penyusunan korpus akademik FILKOM."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pdfplumber.page import Page


BATAS_KATA = 150
TOLERANSI_X = 6.0
TOLERANSI_LANJUTAN = 1.0
TOLERANSI_Y = 5.0


def jumlah_kata(teks: str) -> int:
    return len(teks.split())


DOKUMEN = {
    "pa2020": {
        "judul": "Buku Pedoman Akademik Fakultas Ilmu Komputer Universitas Brawijaya",
        "tahun": 2020,
        "file": "Buku-Pedoman-Akademik-FILKOM-2020.pdf",
        "url": "https://filkom.ub.ac.id/wp-content/uploads/2021/09/Buku-Pedoman-Akademik-FILKOM-2020.pdf",
        "metode": "pdf",
        "halaman_mulai": 9,
        "pola_mulai": r"^VISI, MISI, DAN TUJUAN",
        "pola_buang": [],
    },
    "tatatertib": {
        "judul": "Tata Tertib Pelaksanaan Ujian (UTS & UAS) FILKOM UB",
        "tahun": 2016,
        "file": "Tata_Tertib_Pelaksanaan_UTS_dan_UAS_2.pdf",
        "url": "https://filkom.ub.ac.id/wp-content/uploads/2021/04/Tata_Tertib_Pelaksanaan_UTS_dan_UAS_2.pdf",
        "metode": "pdf",
        "halaman_mulai": 1,
        "pola_mulai": r"^PENGUMUMAN",
        "pola_buang": [r"^Demikian tata tertib"],
    },
    "penilaian": {
        "judul": "Pedoman Penilaian dan Perhitungan Indeks Prestasi PTIIK",
        "tahun": 2015,
        "file": "Pedoman_Penilaian_dan_Perhitungan_Indeks_Prestasi_PTIIK.pdf",
        "url": "https://filkom.ub.ac.id/wp-content/uploads/2021/04/Pedoman_Penilaian_dan_Perhitungan_Indeks_Prestasi_PTIIK.pdf",
        "metode": "manual",
    },
}


@dataclass
class Baris:
    teks: str
    x0: float
    hal: int


def bukan_rumus(obj: dict) -> bool:

    if obj.get("object_type") != "char":
        return True
    return "TimesNewRomanPS-Italic" not in obj.get("fontname", "") and obj["text"] != ""


def ekstrak_baris_halaman(halaman: Page, nomor: int) -> list[Baris]:
    kata = halaman.filter(bukan_rumus).extract_words()
    kata.sort(key=lambda k: (k["top"], k["x0"]))

    kelompok: list[list[dict]] = []
    for k in kata:
        if kelompok and abs(k["top"] - kelompok[-1][0]["top"]) <= TOLERANSI_Y:
            kelompok[-1].append(k)
        else:
            kelompok.append([k])

    hasil = []
    for anggota in kelompok:
        anggota.sort(key=lambda k: k["x0"])
        teks = " ".join(k["text"] for k in anggota)
        hasil.append(Baris(teks=teks, x0=round(anggota[0]["x0"], 1), hal=nomor))
    return hasil


def ekstrak_pdf(path: Path) -> list[Baris]:
    import pdfplumber

    with pdfplumber.open(path) as pdf:
        return [b for i, hlm in enumerate(pdf.pages, start=1) for b in ekstrak_baris_halaman(hlm, i)]


def potong_awal(baris: list[Baris], cfg: dict) -> list[Baris]:
    kandidat = [b for b in baris if b.hal >= cfg["halaman_mulai"]]
    pola = re.compile(cfg["pola_mulai"])
    for i, b in enumerate(kandidat):
        if pola.search(b.teks):
            return kandidat[i:]
    raise ValueError(f"Pola awal {cfg['pola_mulai']!r} tidak ditemukan")


POLA_SISA_RUMUS = re.compile(r"[=+.\s\d]+")
POLA_PENANDA_SAJA = re.compile(r"\d{1,2}\.")

def buang_sampah(baris: list[Baris], cfg: dict) -> list[Baris]:
    pola_buang = [re.compile(pola) for pola in cfg["pola_buang"]]
    return [
        b for b in baris
        if b.teks != str(b.hal)
        and (not POLA_SISA_RUMUS.fullmatch(b.teks) or POLA_PENANDA_SAJA.fullmatch(b.teks))
        and not any(pola.search(b.teks) for pola in pola_buang)
    ]


PETA_SIMBOL = str.maketrans({"": "≥", "": "≤"})

PERBAIKAN_EKSTRAKSI = [
    (re.compile(r"\blPK\b"), "IPK"),
    (re.compile(r"\blP\b"), "IP"),
    (re.compile(r"\blndeks\b"), "Indeks"),
    (re.compile(r"\bIImu\b"), "Ilmu"),
    (re.compile(r"\bl \((satu)\)"), r"1 (\1)"),
]
POLA_SIMBOL_PEMBANDING = re.compile(r"\s*([≥≤])\s*")
POLA_SPASI_KATA_ULANG = re.compile(r"(?<=[a-z])- (?=[a-z])")
POLA_SPASI_SEBELUM_TANDA_BACA = re.compile(r"\s+([.,;:])")
POLA_SPASI_GANDA = re.compile(r"\s{2,}")


def normalisasi(teks: str) -> str:
    teks = teks.translate(PETA_SIMBOL)
    for pola, ganti in PERBAIKAN_EKSTRAKSI:
        teks = pola.sub(ganti, teks)
    teks = POLA_SIMBOL_PEMBANDING.sub(r" \1 ", teks)
    teks = POLA_SPASI_KATA_ULANG.sub("-", teks)
    teks = POLA_SPASI_SEBELUM_TANDA_BACA.sub(r"\1", teks)
    teks = POLA_SPASI_GANDA.sub(" ", teks)
    return teks.strip()


def potong_tabel(baris: list[Baris], daftar_tabel: list[dict]) -> list[Baris]:
    for tabel in daftar_tabel:
        mulai = next(i for i, b in enumerate(baris) if re.search(tabel["mulai"], b.teks))
        sampai = next(i for i in range(mulai + 1, len(baris)) if re.search(tabel["sampai"], baris[i].teks))
        baris = baris[:mulai] + baris[sampai:]
    return baris


def sisipkan_rumus(baris: list[Baris], daftar_rumus: list[dict]) -> list[Baris]:
    for rumus in daftar_rumus:
        i = next(i for i, b in enumerate(baris) if re.search(rumus["setelah"], b.teks))
        pengantar = baris[i]
        sisipan = Baris(rumus["teks"], x0=pengantar.x0 + 18, hal=rumus["halaman"])
        baris = baris[: i + 1] + [sisipan] + baris[i + 1:]
    return baris


POLA_BAB = re.compile(r"^BAB\s+([IVX]+)$")
POLA_SUBBAB = re.compile(r"^([A-Z])\.\s+(.+)$")
POLA_BUTIR = re.compile(r"^(\d{1,2}|[a-z]|[ivx]{1,4})\.\s+(.*)$")


def huruf_kapital_semua(teks: str) -> bool:
    huruf = [c for c in teks if c.isalpha()]
    return len(huruf) >= 3 and all(c.isupper() for c in huruf)


def klasifikasi(teks: str) -> tuple[str, re.Match | None]:
    if m := POLA_BAB.match(teks):
        return "bab", m
    if (m := POLA_SUBBAB.match(teks)) and huruf_kapital_semua(m[2]):
        return "subbab", m
    if m := POLA_BUTIR.match(teks):
        return "butir", m
    if huruf_kapital_semua(teks) and teks[-1].isalpha():
        return "judul", None
    return "lanjutan", None


@dataclass
class Butir:
    penanda: str
    x0: float
    hal: int
    isi: list["str | Butir"] = field(default_factory=list)

    @property
    def anak(self) -> list["Butir"]:
        return [x for x in self.isi if isinstance(x, Butir)]


@dataclass
class Bagian:
    kode: str
    bab: str
    judul_bab: str
    subbab: str
    judul_subbab: str
    hal: int
    paragraf: list[tuple[int, str]] = field(default_factory=list)
    butir: list[Butir] = field(default_factory=list)


def gabung_baris(daftar: list[str]) -> str:

    teks = ""
    for baris in daftar:
        if teks.endswith("-") and baris[:1].islower():
            teks += baris
        else:
            teks = f"{teks} {baris}".strip()
    return teks


def segmen(butir: Butir) -> list[str | Butir]:

    hasil: list[str | Butir] = []
    kumpulan: list[str] = []
    for x in butir.isi:
        if isinstance(x, str):
            kumpulan.append(x)
            continue
        if kumpulan:
            hasil.append(gabung_baris(kumpulan))
            kumpulan = []
        hasil.append(x)
    if kumpulan:
        hasil.append(gabung_baris(kumpulan))
    return hasil


class ParserDokumen:
    def __init__(self) -> None:
        self.bagian: list[Bagian] = []
        self.stack: list[Butir] = []
        self.bab = ""
        self.judul_bab = ""
        self.mode_judul: str | None = None
        self.nomor_judul = 0


    def _bagian_baru(self, kode: str, subbab: str, judul: str, hal: int) -> None:
        self.bagian.append(Bagian(kode, self.bab, self.judul_bab, subbab, judul, hal))
        self.stack = []

    @property
    def aktif(self) -> Bagian:
        return self.bagian[-1]


    def _bab(self, m: re.Match, b: Baris) -> None:
        self.bab, self.judul_bab = m[1], ""
        self._bagian_baru("0", "", "", b.hal)
        self.mode_judul = "bab"

    def _subbab(self, m: re.Match, b: Baris) -> None:
        self._bagian_baru(m[1], m[1], m[2], b.hal)
        self.mode_judul = "subbab"

    def _judul(self, b: Baris) -> None:
        if self.mode_judul == "bab":
            self.judul_bab = f"{self.judul_bab} {b.teks}".strip()
            self.aktif.judul_bab = self.judul_bab
            return
        satu_kata = len(b.teks.split()) == 1
        if self.mode_judul == "subbab" and not satu_kata:
            self.aktif.judul_subbab = f"{self.aktif.judul_subbab} {b.teks}"
            return
        self.nomor_judul += 1
        self._bagian_baru(f"S{self.nomor_judul}", "", b.teks, b.hal)
        self.mode_judul = "subbab"

    def _butir(self, m: re.Match, b: Baris) -> None:
        baru = Butir(m[1], b.x0, b.hal, [m[2]])
        while self.stack and self.stack[-1].x0 > b.x0 + TOLERANSI_X:
            self.stack.pop()
        if self.stack and abs(self.stack[-1].x0 - b.x0) <= TOLERANSI_X:
            self.stack.pop()
        if self.stack:
            self.stack[-1].isi.append(baru)
        else:
            self.aktif.butir.append(baru)
        self.stack.append(baru)

    def _lanjutan(self, b: Baris) -> None:
        while self.stack and self.stack[-1].x0 > b.x0 + TOLERANSI_LANJUTAN:
            self.stack.pop()
        if self.stack:
            target = self.stack[-1]
        elif self.aktif.butir:
            target = self.aktif.butir[-1]
        else:
            self.aktif.paragraf.append((b.hal, b.teks))
            return
        target.isi.append(b.teks)


    def parse(self, baris: list[Baris]) -> list[Bagian]:
        self._bagian_baru("0", "", "", baris[0].hal)
        for b in baris:
            jenis, m = klasifikasi(b.teks)
            if jenis != "judul":
                self.mode_judul = None if jenis in ("butir", "lanjutan") else self.mode_judul
            if jenis == "bab":
                self._bab(m, b)
            elif jenis == "subbab":
                self._subbab(m, b)
            elif jenis == "judul":
                self._judul(b)
            elif jenis == "butir":
                self._butir(m, b)
            else:
                self._lanjutan(b)
        return [bg for bg in self.bagian if bg.paragraf or bg.butir]


SINGKATAN = {"No", "Prof", "Dr", "Ir", "Eng", "dll", "dsb", "dkk", "Jl", "JL", "Telp", "S", "M", "T", "Kom"}
POLA_BATAS_KALIMAT = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9“\"(])")


def pecah_kalimat(teks: str) -> list[str]:
    kalimat: list[str] = []
    for bagian_teks in POLA_BATAS_KALIMAT.split(teks):
        kata_terakhir = kalimat[-1].rstrip(".").split()[-1] if kalimat else ""
        if kalimat and kata_terakhir.split(".")[-1] in SINGKATAN:
            kalimat[-1] += " " + bagian_teks
        else:
            kalimat.append(bagian_teks)
    return kalimat


def kelompokkan_kalimat(kalimat: list[str], batas: int = BATAS_KATA) -> list[str]:
    kelompok, sekarang = [], []
    for k in kalimat:
        if sekarang and jumlah_kata(" ".join(sekarang + [k])) > batas:
            kelompok.append(" ".join(sekarang))
            sekarang = []
        sekarang.append(k)
    if sekarang:
        kelompok.append(" ".join(sekarang))
    return kelompok


def teks_sendiri(butir: Butir) -> str:

    pertama = segmen(butir)[0]
    return f"{butir.penanda}. {pertama}" if isinstance(pertama, str) else f"{butir.penanda}."


def teks_lengkap(butir: Butir) -> str:
    potongan = [f"{butir.penanda}."]
    for x in segmen(butir):
        potongan.append(teks_lengkap(x) if isinstance(x, Butir) else x)
    return " ".join(potongan)


def buat_passage(dok: str, bg: Bagian, butir_id: str, teks: str, konteks: list[str], hal: int, jenis: str) -> dict:
    kode_bab = bg.bab or "X"
    return {
        "id": f"{dok}-{kode_bab}-{bg.kode}-{butir_id}",
        "dok_id": dok,
        "halaman": hal,
        "bab": bg.bab,
        "judul_bab": bg.judul_bab,
        "subbab": bg.subbab,
        "judul_subbab": bg.judul_subbab,
        "butir": butir_id if jenis == "butir" else "",
        "konteks": " › ".join(konteks),
        "teks": teks,
        "jenis": jenis,
    }


def passage_dari_butir(dok: str, bg: Bagian, butir: Butir, jalur: list[str], konteks: list[str]) -> list[dict]:
    jalur = jalur + [butir.penanda]
    lengkap = teks_lengkap(butir)
    if jumlah_kata(lengkap) <= BATAS_KATA or not butir.anak:
        return [buat_passage(dok, bg, ".".join(jalur), lengkap, konteks, butir.hal, "butir")]


    konteks_induk = konteks + [teks_sendiri(butir)]
    isi = segmen(butir)
    if isinstance(isi[0], str):
        isi = isi[1:]
    hasil, pengantar, nomor_teks = [], None, 0
    for i, x in enumerate(isi):
        if isinstance(x, Butir):
            k = konteks_induk + ([pengantar] if pengantar else [])
            hasil += passage_dari_butir(dok, bg, x, jalur, k)
        elif any(isinstance(y, Butir) for y in isi[i + 1:]):
            pengantar = x
        else:
            nomor_teks += 1
            butir_id = ".".join(jalur + [f"t{nomor_teks}"])
            hasil.append(buat_passage(dok, bg, butir_id, x, konteks_induk, butir.hal, "butir"))
    return hasil


def passage_dari_bagian(dok: str, bg: Bagian) -> list[dict]:
    hasil, pengantar = [], []
    if bg.paragraf:
        kalimat = pecah_kalimat(gabung_baris([t for _, t in bg.paragraf]))
        if bg.butir and kalimat[-1].endswith(":"):
            pengantar = [kalimat.pop()]
        for i, kelompok in enumerate(kelompokkan_kalimat(kalimat), start=1):
            hasil.append(buat_passage(dok, bg, f"p{i}", kelompok, [], bg.paragraf[0][0], "paragraf"))
    for butir in bg.butir:
        hasil += passage_dari_butir(dok, bg, butir, [], pengantar)
    return hasil


def passage_dari_tabel(dok: str, tabel: dict, bab: str = "", judul_bab: str = "",
                       subbab: str = "", judul_subbab: str = "") -> list[dict]:
    hasil = []
    for i, baris in enumerate(tabel["baris"], start=1):
        hasil.append({
            "id": f"{dok}-{tabel['id']}-{i}",
            "dok_id": dok,
            "halaman": tabel["halaman"],
            "bab": bab,
            "judul_bab": judul_bab,
            "subbab": subbab,
            "judul_subbab": judul_subbab,
            "butir": "",
            "konteks": tabel["judul"],
            "teks": tabel["templat"].format(**baris),
            "jenis": "tabel",
        })
    return hasil


def bangun_korpus(
    direktori_pdf: Path, berkas_transkripsi: Path
) -> tuple[list[dict], dict, dict[str, list[Baris]]]:
    transkripsi = json.loads(berkas_transkripsi.read_text(encoding="utf-8"))
    dokumen_pdf = [dok for dok, cfg in DOKUMEN.items() if cfg["metode"] == "pdf"]
    baris_mentah = {dok: ekstrak_pdf(direktori_pdf / DOKUMEN[dok]["file"]) for dok in dokumen_pdf}

    hasil_parse = {}
    for dok, baris in baris_mentah.items():
        isi = potong_awal(baris, DOKUMEN[dok])
        bersih = buang_sampah(isi, DOKUMEN[dok])
        normal = []
        for b in bersih:
            teks = normalisasi(b.teks)
            if teks:
                normal.append(Baris(teks, b.x0, b.hal))
        manual = transkripsi.get(dok, {})
        tanpa_tabel = potong_tabel(normal, manual.get("tabel", []))
        hasil_parse[dok] = ParserDokumen().parse(sisipkan_rumus(tanpa_tabel, manual.get("rumus", [])))

    passages: list[dict] = []


    for dok in dokumen_pdf:
        for bg in hasil_parse[dok]:
            passages += passage_dari_bagian(dok, bg)


    for dok in dokumen_pdf:
        for tabel in transkripsi.get(dok, {}).get("tabel", []):
            bagian = next(bg for bg in hasil_parse[dok] if bg.bab == tabel["bab"] and bg.kode == tabel["subbab"])
            passages += passage_dari_tabel(
                dok, tabel, bagian.bab, bagian.judul_bab, bagian.subbab, bagian.judul_subbab
            )


    for dok, cfg in DOKUMEN.items():
        if cfg["metode"] != "manual":
            continue
        manual = transkripsi[dok]
        for i, par in enumerate(manual.get("paragraf", []), start=1):
            passages.append({
                "id": f"{dok}-p{i}", "dok_id": dok, "halaman": par["halaman"],
                "bab": "", "judul_bab": "", "subbab": "", "judul_subbab": par["judul_subbab"],
                "butir": "", "konteks": "", "teks": par["teks"], "jenis": "paragraf",
            })
        for tabel in manual.get("tabel", []):
            passages += passage_dari_tabel(dok, tabel, judul_subbab=tabel["judul_subbab"])

    dokumen = {
        dok: {k: cfg[k] for k in ("judul", "tahun", "url", "file", "metode")}
        | ({"catatan": transkripsi[dok]["catatan"]} if "catatan" in transkripsi.get(dok, {}) else {})
        for dok, cfg in DOKUMEN.items()
    }
    return passages, dokumen, baris_mentah
