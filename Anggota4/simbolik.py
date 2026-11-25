"""Pemrosesan simbolik untuk angka kata, tabel interval, dan rumus matematika."""

import operator
import re

_UNIT_BILANGAN = (
    "sks|semester|menit|jam|hari|minggu|bulan|tahun|kali|orang|publikasi|jenis"
)

_DASAR = {
    "nol": 0, "satu": 1, "dua": 2, "tiga": 3, "empat": 4,
    "lima": 5, "enam": 6, "tujuh": 7, "delapan": 8, "sembilan": 9,
}

_KOMPARATOR = {
    "<": operator.lt,
    "≤": operator.le,
    "<=": operator.le,
    ">": operator.gt,
    "≥": operator.ge,
    ">=": operator.ge,
}

_POLA_KURUNG_ANGKA = re.compile(r"\b(\d+(?:,\d+)?)\s*\([a-z\s-]+\)", re.IGNORECASE)
_POLA_KATA_BILANGAN = re.compile(
    rf"\b(?!(?:salah\s+)?satu\b(?!\s+(?:{_UNIT_BILANGAN})\b))"
    r"(?:(?:seratus|(?:" + "|".join(_DASAR) + r")\s+ratus)\s+)?"
    r"(?:(?:sepuluh|sebelas|(?:" + "|".join(_DASAR) + r")\s+belas)|"
    r"(?:(?:" + "|".join(_DASAR) + r")\s+puluh(?:\s+(?:" + "|".join(_DASAR) + r"))?)|"
    r"(?:" + "|".join(_DASAR) + r"))"
    rf"(?=\s+(?:{_UNIT_BILANGAN})\b|\b)",
    re.IGNORECASE,
)


def _parse_frasa_bilangan(frasa: str) -> int | None:
    """Konversi frasa bilangan bahasa Indonesia (0-999) ke integer."""
    tokens = frasa.casefold().split()
    total = 0
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        if tok == "seratus":
            total += 100
        elif tok == "sepuluh":
            total += 10
        elif tok == "sebelas":
            total += 11
        elif tok in _DASAR:
            val = _DASAR[tok]
            if i + 1 < len(tokens) and tokens[i + 1] in {"belas", "puluh", "ratus"}:
                pengali = tokens[i + 1]
                if pengali == "belas":
                    total += 10 + val
                elif pengali == "puluh":
                    total += val * 10
                else:
                    total += val * 100
                i += 1
            else:
                total += val
        else:
            return None
        i += 1
    return total


def normalisasi_bilangan(teks: str) -> str:
    """Hapus duplikasi angka dalam kurung dan konversi kata bilangan ke digit."""
    hasil = _POLA_KURUNG_ANGKA.sub(r"\1", teks)

    def _ganti(match: re.Match) -> str:
        frasa = match.group(0)
        tokens = frasa.casefold().split()
        # Biarkan kata tunggal tanpa satuan jika ambigu ("satu hal", "dua sisi").
        if len(tokens) == 1:
            sisa = hasil[match.end():].lstrip()
            if not re.match(rf"^(?:{_UNIT_BILANGAN})\b", sisa, re.IGNORECASE):
                return frasa
        angka = _parse_frasa_bilangan(frasa)
        return str(angka) if angka is not None else frasa

    return _POLA_KATA_BILANGAN.sub(_ganti, hasil)


def _ke_float(teks_angka: str) -> float:
    return float(teks_angka.replace(",", "."))


def _cek_rentang(teks: str, nilai: float) -> bool | None:
    """Evaluasi ekspresi interval pada baris tabel terhadap nilai numerik query."""
    dua_sisi = re.search(
        r"(\d+(?:,\d+)?)\s*([<≤]|<=)\s*[A-Za-z]+\s*([<≤]|<=)\s*(\d+(?:,\d+)?)",
        teks,
    )
    if dua_sisi:
        bawah, op1, op2, atas = dua_sisi.groups()
        return _KOMPARATOR[op1](_ke_float(bawah), nilai) and _KOMPARATOR[op2](nilai, _ke_float(atas))

    satu_sisi = re.search(r"\b[A-Za-z]+\s*([≥≤<>]|>=|<=)\s*(\d+(?:,\d+)?)", teks)
    if satu_sisi:
        op, batas = satu_sisi.groups()
        return _KOMPARATOR[op](nilai, _ke_float(batas))
    return None


def evaluasi_tabel(teks: str, pertanyaan: str, tipe_jawaban: str) -> str | None:
    """Cocokkan nilai angka atau huruf pada passage bertipe tabel."""
    angka_query = re.findall(r"\d+(?:,\d+|\.\d+)?", pertanyaan)
    if angka_query:
        nilai = _ke_float(angka_query[-1].replace(".", ","))
        cocok = _cek_rentang(teks, nilai)
        if cocok is False:
            return None
        if cocok is True:
            if tipe_jawaban == "NILAI_HURUF":
                m = re.search(r"nilai huruf\s+([A-E]\+?)", teks)
                if m:
                    return m.group(1)
            m_adalah = re.search(r"\badalah\s+([^.(]+)", teks)
            if m_adalah:
                return m_adalah.group(1).strip()

    # Lookup tabel bobot / angka mutu berdasarkan huruf mutu pada pertanyaan.
    m_huruf_q = re.findall(r"(?<![A-Za-z])([A-E]\+?)(?![A-Za-z0-9+])", pertanyaan)
    if m_huruf_q:
        huruf_target = m_huruf_q[-1]
        pola_baris = re.search(
            rf"(?:Huruf Mutu \(HM\)|nilai huruf)\s+{re.escape(huruf_target)}(?![A-Za-z0-9+])",
            teks,
        )
        if pola_baris:
            m_nilai = re.search(r"(?:Angka Mutu \(AM\)|bobot)\s+(\d+(?:,\d+)?)", teks)
            if m_nilai:
                return m_nilai.group(1)
    return None


def ekstrak_rumus(teks: str) -> str | None:
    """Ekstrak ekspresi persamaan rumus dari passage."""
    m = re.search(r"\b([A-Z]{1,4}\s*=\s*[^.]+)", teks)
    if not m:
        return None
    rumus = re.split(r",\s*dengan\b", m.group(1), maxsplit=1)[0].strip()
    return f"{rumus}."
