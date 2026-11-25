"""Ekstraksi jawaban Hybrid (Simbolik + Dependency Parsing UDPipe + Proximity)."""

import re

import spacy_udpipe

from .simbolik import ekstrak_rumus, evaluasi_tabel, normalisasi_bilangan

_UNIT_DURASI = frozenset({"menit", "jam", "hari", "minggu", "bulan", "tahun", "semester"})
_UNIT_ANGKA = frozenset({
    "sks", "ipk", "ip", "bobot", "skor", "poin", "kali", "orang", "publikasi", "jenis",
})
_BULAN_ID = frozenset({
    "januari", "februari", "maret", "april", "mei", "juni",
    "juli", "agustus", "september", "oktober", "november", "desember",
})

_NLP = None


def load_udpipe():
    """Muat model UDPipe bahasa Indonesia sekali saja (lazy singleton)."""
    global _NLP
    if _NLP is not None:
        return _NLP
    try:
        _NLP = spacy_udpipe.load("id")
    except (AssertionError, OSError):
        spacy_udpipe.download("id")
        _NLP = spacy_udpipe.load("id")
    return _NLP


def _akar_sederhana(kata: str) -> str:
    """Normalisasi imbuhan umum bahasa Indonesia agar verba/nomina berelasi cocok."""
    w = re.sub(r"[^a-z0-9+]", "", kata.casefold())
    if len(w) <= 4:
        return w
    if w.startswith(("meny", "peny")):
        w = "s" + w[4:]
    elif w.startswith(("men", "pen")) and len(w) > 5 and w[3] in "aeiou":
        w = "t" + w[3:]
    elif w.startswith(("mem", "pem")) and len(w) > 5 and w[3] in "aeiou":
        w = "p" + w[3:]
    elif w.startswith(("meng", "peng")) and len(w) > 6 and w[4] in "aeiou":
        w = w[4:]
    else:
        w = re.sub(r"^(?:meng|peng|mem|pem|men|pen|me|pe|di|ber|ter|ke)", "", w)
    if len(w) > 5:
        w = re.sub(r"(?:kan|an)$", "", w)
    return w


def _akar_kunci(hasil_pertanyaan: dict) -> set[str]:
    kata = hasil_pertanyaan.get("kata_kunci") or []
    return {_akar_sederhana(k) for k in kata if len(k) >= 2}


def _bersihkan_butir(teks: str) -> str:
    """Buang penanda butir di awal teks (mis. '7. ', '10. ', 'a. ')."""
    return re.sub(r"^\s*(?:\d+|[a-z]{1,2}|[ivx]+)\.\s+", "", teks.strip(), flags=re.IGNORECASE)


def _format_sumber(passage: dict, dokumen: dict | None = None) -> str:
    sumber = passage.get("sumber")
    if not sumber and dokumen and passage.get("dok_id") in dokumen:
        sumber = dokumen[passage["dok_id"]]
    if not sumber:
        return f"{passage.get('passage_id', '')}, hlm. {passage.get('halaman', '-')}"
    bab = passage.get("bab", "")
    subbab = passage.get("subbab", "")
    lokasi = f"BAB {bab} {subbab}".strip() if bab else passage.get("judul_subbab", "")
    bagian = f", {lokasi}" if lokasi else ""
    return f"{sumber['judul']} ({sumber['tahun']}){bagian}, hlm. {passage.get('halaman', '-')}"


def _jarak_terdekat(
    idx_token: int,
    doc,
    akar_kunci: set[str],
    kecualikan: range | None = None,
) -> int:
    cocok = [
        abs(idx_token - t.i)
        for t in doc
        if (kecualikan is None or t.i not in kecualikan)
        and _akar_sederhana(t.text) in akar_kunci
    ]
    return min(cocok) if cocok else 999


def _bonus_dependensi(token, akar_kunci: set[str]) -> float:
    """Beri bonus jika head sintaksis atau induk berjarak 2 langkah cocok dengan kata kunci."""
    node = token.head
    for langkah in range(2):
        if _akar_sederhana(node.text) in akar_kunci:
            return 1.2 if langkah == 0 else 0.6
        if node.head == node:
            break
        node = node.head
    return 0.0


def _overlap_kalimat(span_or_token, akar_kunci: set[str]) -> int:
    akar_sent = {_akar_sederhana(tok.text) for tok in span_or_token.sent}
    return len(akar_sent & akar_kunci)


def _ekstrak_kuantitatif(doc, tipe: str, akar_kunci: set[str], rank: int) -> tuple[str, float] | None:
    kandidat = []
    for t in doc:
        if t.pos_ != "NUM" or not re.search(r"\d", t.text):
            continue
        # Abaikan angka penomoran sub-poin seperti "9." atau "a.".
        if t.i + 1 < len(doc) and doc[t.i + 1].text == ".":
            continue

        teks_num = t.text
        idx_akhir = t.i
        # Gabungkan angka desimal yang terpecah oleh tokenizer (mis. "4," + "0").
        if teks_num.endswith(",") and t.i + 1 < len(doc) and doc[t.i + 1].pos_ == "NUM":
            teks_num = f"{teks_num}{doc[t.i + 1].text}"
            idx_akhir = t.i + 1

        teks_next = doc[idx_akhir + 1].text.casefold() if idx_akhir + 1 < len(doc) else ""
        teks_prev = doc[t.i - 1].text if t.i > 0 else ""

        if tipe == "PERSENTASE":
            if teks_next not in {"%", "persen"}:
                continue
            jawaban = f"{teks_num}%" if teks_next == "%" else f"{teks_num} {doc[idx_akhir + 1].text}"
        elif tipe == "DURASI":
            if teks_next not in _UNIT_DURASI:
                continue
            jawaban = f"{teks_num} {doc[idx_akhir + 1].text}"
        else:  # ANGKA
            if teks_next in _UNIT_DURASI and teks_next not in akar_kunci:
                continue
            if teks_next in _UNIT_ANGKA:
                jawaban = f"{teks_num} {doc[idx_akhir + 1].text}"
            elif teks_prev in {"≥", "≤", ">", "<"}:
                jawaban = f"{teks_prev} {teks_num}"
            else:
                jawaban = teks_num

        jarak = _jarak_terdekat(t.i, doc, akar_kunci)
        overlap = _overlap_kalimat(t, akar_kunci)
        skor = (0.8 * overlap) + (2.0 / (jarak + 1.0)) + _bonus_dependensi(t, akar_kunci) + (1.0 / rank)
        kandidat.append((skor, jawaban))

    if not kandidat:
        return None
    kandidat.sort(key=lambda x: -x[0])
    return kandidat[0][1], kandidat[0][0]


def _ekstrak_definisi(doc, akar_kunci: set[str], rank: int) -> tuple[str, float] | None:
    for t in doc:
        if t.dep_ != "cop" or t.text.casefold() not in {"adalah", "merupakan", "ialah", "yaitu"}:
            continue
        subjek = [c for c in t.head.children if "subj" in c.dep_]
        teks_subjek = " ".join(tok.text for s in subjek for tok in s.subtree)
        akar_subjek = {_akar_sederhana(w) for w in teks_subjek.split()}
        overlap = len(akar_subjek & akar_kunci)
        if not overlap and akar_kunci:
            continue
        sent_end = t.sent.end
        potongan = doc[t.i + 1 : sent_end].text.strip()
        if not potongan:
            continue
        jawaban = potongan[0].upper() + potongan[1:]
        skor = overlap + (1.0 / rank)
        return jawaban, skor
    return None


def _ekstrak_jabatan(doc, akar_kunci: set[str], rank: int) -> tuple[str, float] | None:
    kandidat = []
    i = 0
    while i < len(doc):
        t = doc[i]
        if t.text[0].isupper() and t.pos_ in {"PROPN", "NOUN"} and t.dep_ != "punct":
            j = i + 1
            while j < len(doc) and doc[j].text[0].isupper() and doc[j].pos_ in {"PROPN", "NOUN"}:
                j += 1
            span = doc[i:j]
            akar_span = {_akar_sederhana(tok.text) for tok in span}
            # Hindari memilih ulang entitas topik pertanyaan (mis. "Dosen Pembimbing").
            if not akar_span.issubset(akar_kunci):
                rentang = range(i, j)
                jarak = min(_jarak_terdekat(k, doc, akar_kunci, rentang) for k in rentang)
                dep_bonus = max(_bonus_dependensi(doc[k], akar_kunci) for k in rentang)
                overlap = _overlap_kalimat(span, akar_kunci)
                skor = (0.8 * overlap) + (2.0 / (jarak + 1.0)) + (1.5 * dep_bonus) + (1.0 / rank)
                kandidat.append((skor, span.text))
            i = j
        else:
            i += 1
    if not kandidat:
        return None
    kandidat.sort(key=lambda x: -x[0])
    return kandidat[0][1], kandidat[0][0]


def _ekstrak_waktu(doc, akar_kunci: set[str], rank: int) -> tuple[str, float] | None:
    for t in doc:
        if t.pos_ != "NUM" or not re.search(r"\d", t.text):
            continue
        next_w = doc[t.i + 1].text.casefold() if t.i + 1 < len(doc) else ""
        if next_w not in _UNIT_DURASI and next_w not in _BULAN_ID:
            continue
        awal = t.i
        if awal >= 2 and doc[awal - 2 : awal].text.casefold() in {"paling lambat", "paling lama", "paling cepat"}:
            awal -= 2
        akhir = t.i + 2
        while akhir < t.sent.end and doc[akhir].text.casefold() not in {"dan", "serta", ",", ";", "."}:
            akhir += 1
        frasa = doc[awal:akhir].text.strip()
        if frasa:
            jawaban = frasa[0].upper() + frasa[1:] + "."
            skor = (2.0 / (_jarak_terdekat(t.i, doc, akar_kunci) + 1.0)) + (1.0 / rank)
            return jawaban, skor
    return None


def _kalimat_terbaik(teks: str, akar_kunci: set[str], rank: int) -> tuple[str, float] | None:
    kalimat_list = [k.strip() for k in re.split(r"(?<=[.!?])\s+", teks) if k.strip()]
    if not kalimat_list:
        return None
    terbaik = max(
        kalimat_list,
        key=lambda k: len({_akar_sederhana(w) for w in k.split()} & akar_kunci),
    )
    overlap = len({_akar_sederhana(w) for w in terbaik.split()} & akar_kunci)
    return terbaik, overlap + (1.0 / rank)


class EkstraktorJawaban:
    """Ekstraktor jawaban Hybrid (Simbolik + Dependency Parsing UDPipe + Proximity)."""

    def __init__(self, dokumen: dict | None = None, nlp=None):
        self.dokumen = dokumen or {}
        self._nlp = nlp

    @property
    def nlp(self):
        if self._nlp is None:
            self._nlp = load_udpipe()
        return self._nlp

    def ekstrak(self, hasil_pertanyaan: dict, kandidat_passages: list[dict]) -> dict:
        pertanyaan = hasil_pertanyaan.get("pertanyaan", "")
        tipe = hasil_pertanyaan.get("tipe_jawaban", "TIDAK_DIKENALI")

        if hasil_pertanyaan.get("status") != "SIAP_RETRIEVAL" or not kandidat_passages:
            return {
                "pertanyaan": pertanyaan,
                "tipe_jawaban": tipe,
                "jawaban": "",
                "metode": "tidak_tersedia",
                "skor": 0.0,
                "passage_id": "",
                "kutipan": "",
                "sumber": "",
                "status": "TIDAK_DITEMUKAN",
            }

        akar_kunci = _akar_kunci(hasil_pertanyaan)

        # 1. Jalur Simbolik untuk tabel dan rumus.
        for rank_idx, p in enumerate(kandidat_passages, start=1):
            rank = p.get("rank", rank_idx)
            teks = p.get("teks", "")
            if tipe == "RUMUS":
                rumus = ekstrak_rumus(teks)
                if rumus:
                    return self._bangun_hasil(pertanyaan, tipe, rumus, "simbolik", 1.0 / rank, p)
            if p.get("jenis") == "tabel" or tipe == "NILAI_HURUF":
                nilai_tabel = evaluasi_tabel(teks, pertanyaan, tipe)
                if nilai_tabel:
                    return self._bangun_hasil(pertanyaan, tipe, nilai_tabel, "simbolik", 1.0 / rank, p)

        # 2. Jalur Linguistik (Dependency Parsing UDPipe + Lexical Proximity).
        kandidat_linguistik = []
        for rank_idx, p in enumerate(kandidat_passages, start=1):
            rank = p.get("rank", rank_idx)
            teks_bersih = normalisasi_bilangan(_bersihkan_butir(p.get("teks", "")))
            doc = self.nlp(teks_bersih)

            hasil_ling = None
            if tipe in {"ANGKA", "DURASI", "PERSENTASE"}:
                hasil_ling = _ekstrak_kuantitatif(doc, tipe, akar_kunci, rank)
            elif tipe == "DEFINISI":
                hasil_ling = _ekstrak_definisi(doc, akar_kunci, rank)
            elif tipe in {"JABATAN", "ORANG"}:
                hasil_ling = _ekstrak_jabatan(doc, akar_kunci, rank)
            elif tipe == "WAKTU":
                hasil_ling = _ekstrak_waktu(doc, akar_kunci, rank)

            if hasil_ling:
                jawaban, skor = hasil_ling
                kandidat_linguistik.append((skor, jawaban, p))

        if kandidat_linguistik:
            kandidat_linguistik.sort(key=lambda x: -x[0])
            skor_terbaik, jawaban_terbaik, passage_terbaik = kandidat_linguistik[0]
            return self._bangun_hasil(
                pertanyaan, tipe, jawaban_terbaik, "linguistik_udpipe", skor_terbaik, passage_terbaik,
            )

        # 3. Jalur Fallback: pilih kalimat dengan overlap kata kunci tertinggi.
        top_p = kandidat_passages[0]
        fallback = _kalimat_terbaik(_bersihkan_butir(top_p.get("teks", "")), akar_kunci, top_p.get("rank", 1))
        if fallback:
            jawaban_fb, skor_fb = fallback
            return self._bangun_hasil(pertanyaan, tipe, jawaban_fb, "fallback_kalimat", skor_fb, top_p)

        return self._bangun_hasil(pertanyaan, tipe, "", "tidak_tersedia", 0.0, top_p, ditemukan=False)

    def _bangun_hasil(
        self,
        pertanyaan: str,
        tipe: str,
        jawaban: str,
        metode: str,
        skor: float,
        passage: dict,
        ditemukan: bool = True,
    ) -> dict:
        return {
            "pertanyaan": pertanyaan,
            "tipe_jawaban": tipe,
            "jawaban": jawaban,
            "metode": metode,
            "skor": round(float(skor), 4),
            "passage_id": passage.get("passage_id") or passage.get("id", ""),
            "kutipan": passage.get("teks", ""),
            "sumber": _format_sumber(passage, self.dokumen),
            "status": "DITEMUKAN" if ditemukan else "TIDAK_DITEMUKAN",
        }


def ekstrak_jawaban(hasil_pertanyaan: dict, kandidat_passages: list[dict], dokumen: dict | None = None) -> dict:
    """Fungsi pembantu ringkas tanpa perlu inisialisasi kelas berulang."""
    return EkstraktorJawaban(dokumen=dokumen).ekstrak(hasil_pertanyaan, kandidat_passages)
