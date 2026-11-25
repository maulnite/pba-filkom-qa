"""Preprocessing bersama untuk pertanyaan dan passage (Python >= 3.10)."""

import re
import unicodedata

VERSI_PREPROCESS = "1.0"

# Daftar kecil; negasi, pembatas, satuan, dan angka sengaja dipertahankan.
STOPWORDS = frozenset("""
yang dan atau dengan adalah merupakan sebagai pada di ke oleh ini itu tersebut
untuk saya aku tolong mohon jelaskan sebutkan dimaksud maksud
apa apakah siapakah siapa kapan kapankah dimana kemana darimana
mana manakah berapa berapakah bagaimana bagaimanakah mengapa kenapa saja
""".split())

ALIASES = (
    (r"\bindeks prestasi kumulatif\b|\bip kumulatif\b", "ipk"),
    (r"\bindeks prestasi\b", "ip"),
    (r"\bsatuan kredit semester\b|\bsistem kredit semester\b", "sks"),
    (r"\bujian akhir semester\b", "uas"),
    (r"\bujian tengah semester\b", "uts"),
    (r"\bprogram studi\b", "prodi"),
)

# B+ tetap satu token; 2,00 tetap satu token; operator tetap dapat diperiksa.
POLA_TOKEN = re.compile(
    r"\d+(?:,\d+)?|[^\W\d_]+(?:[-'][^\W\d_]+)*(?:\+)?|[≥≤<>=%×/+*−-]",
    re.UNICODE,
)


def normalisasi_teks(teks: str) -> str:
    """Samakan Unicode, huruf, spasi, operator ASCII, dan desimal titik."""
    if not isinstance(teks, str):
        raise TypeError("Teks harus berupa str.")
    hasil = unicodedata.normalize("NFKC", teks).casefold()
    hasil = hasil.replace(">=", "≥").replace("<=", "≤")
    # Satu titik di antara digit dianggap desimal; pemisah ribuan tidak didukung.
    hasil = re.sub(r"(?<=\d)\.(?=\d)", ",", hasil)
    return " ".join(hasil.split())


def tokenisasi(teks: str) -> list[str]:
    """Token sebelum stopword removal; dipakai pula untuk melihat tahapan."""
    hasil = normalisasi_teks(teks)
    for pola, pengganti in ALIASES:
        hasil = re.sub(pola, pengganti, hasil)
    return POLA_TOKEN.findall(hasil)


def preprocess(teks: str) -> list[str]:
    """Fungsi tunggal yang dipakai query dan passage oleh anggota 3."""
    return [token for token in tokenisasi(teks) if token not in STOPWORDS]


def teks_index(passage: dict) -> str:
    """Gabungkan field sesuai SPEK_PASSAGE, tanpa mengubah passage asli."""
    return " ".join(
        passage.get(kolom, "")
        for kolom in ("judul_subbab", "konteks", "teks")
        if passage.get(kolom, "")
    )


def preprocess_passage(passage: dict) -> list[str]:
    return preprocess(teks_index(passage))
