"""Question processing berbasis aturan; tidak mencari atau menjawab passage."""

import json
import re
import sys

try:  # Impor dari folder Tugas Akhir sebagai namespace package.
    from .preprocess import VERSI_PREPROCESS, normalisasi_teks, preprocess, tokenisasi
except ImportError:  # Impor langsung dari notebook atau pemanggilan CLI.
    from preprocess import VERSI_PREPROCESS, normalisasi_teks, preprocess, tokenisasi


POLA_TANYA = re.compile(
    r"\b(?:berapa(?:kah)?|siapa(?:kah)?|kapan(?:kah)?|"
    r"(?:di|ke|dari)\s*mana|bagaimana(?:kah)?|mengapa|kenapa|"
    r"apakah|apa|mana(?:kah)?)\b"
)


def jenis_pertanyaan(teks: str) -> tuple[str, str, list[str]]:
    """Kenali penanda tanya pertama; lebih dari satu penanda perlu dipecah."""
    penanda = [m.group() for m in POLA_TANYA.finditer(teks)]
    if not penanda:
        return "TIDAK_DIKENALI", "", []
    pertama = penanda[0]
    if re.fullmatch(r"(?:di|ke|dari)\s*mana", pertama):
        jenis = "DI_MANA"
    elif pertama in {"mengapa", "kenapa"}:
        jenis = "MENGAPA"
    elif pertama == "apakah":
        jenis = "YA_TIDAK"
    else:
        jenis = pertama.removesuffix("kah").upper()
    return jenis, pertama, penanda


def tipe_jawaban(teks: str, jenis: str, penanda: str) -> tuple[str, str]:
    """Aturan berurutan: bentuk tanya utama lebih kuat daripada kata topik."""
    if jenis == "YA_TIDAK":
        return "YA_TIDAK", "pertanyaan konfirmasi"
    # ponytail: heuristik domain; gunakan classifier jika variasi pertanyaan meluas.
    if jenis == "SIAPA":
        if re.search(r"\bnama(?:nya)?\b", teks):
            return "ORANG", "siapa disertai permintaan nama"
        return "JABATAN", "siapa tanpa permintaan nama; asumsi domain akademik"
    if jenis == "KAPAN":
        return "WAKTU", "kapan: tanggal, tahun, atau peristiwa awal/akhir"
    if jenis == "DI_MANA":
        return "LOKASI", "penanda lokasi"
    if jenis == "MENGAPA":
        return "ALASAN", "penanda sebab"
    if jenis in {"TIDAK_DIKENALI", "MANA"}:
        return "TIDAK_DIKENALI", "bentuk belum dicakup aturan"

    # Untuk BERAPA, utamakan objek hitungan setelah penanda tanya.
    if jenis == "BERAPA":
        setelah = teks.split(penanda, 1)[1].strip()
        if re.search(r"\b(?:persen|persentase)\b|%", setelah):
            return "PERSENTASE", "berapa disertai satuan persen"
        kepala = re.sub(r"^(?:(?:jumlah|total|minimal|maksimal|minimum|maksimum)\s+)+", "", setelah)
        if re.match(r"(?:sks|satuan kredit|nilai|ipk|ip|indeks prestasi|bobot|skor|orang|kali)\b", kepala):
            return "ANGKA", "objek hitungan numerik"
        if re.match(r"(?:lama|durasi|waktu|menit|jam|hari|minggu|bulan|tahun|semester)\b", kepala):
            return "DURASI", "objek hitungan berupa lama waktu"
        return "ANGKA", "berapa: jumlah numerik sebagai default"

    if re.search(r"\b(?:rumus|menghitung|hitung|perhitungan)\b", teks):
        return "RUMUS", "permintaan rumus atau cara menghitung"
    if re.search(r"\b(?:syarat|syarat-syarat|persyaratan)\b", teks):
        return "SYARAT", "permintaan persyaratan"
    if re.search(r"\b(?:prosedur|mekanisme|langkah|cara)\b", teks) or jenis == "BAGAIMANA":
        return "PROSEDUR", "permintaan cara atau tahapan"
    if re.search(r"\b(?:apa itu|apa yang dimaksud|pengertian|definisi|arti|kepanjangan)\b", teks):
        return "DEFINISI", "permintaan makna istilah"
    if re.search(r"\b(?:persen|persentase)\b|%", teks):
        return "PERSENTASE", "permintaan persentase"
    if re.search(r"\b(?:bobot|rentang|skor|ipk|indeks prestasi kumulatif)\b", teks):
        return "ANGKA", "target besaran numerik"
    if re.search(r"\b(?:nilai huruf|huruf mutu)\b", teks):
        return "NILAI_HURUF", "target konversi ke huruf"
    if re.search(r"\b(?:durasi|lama|batas waktu)\b", teks):
        return "DURASI", "target lama waktu"
    if re.search(r"\bapa saja\b", teks):
        return "DAFTAR", "permintaan daftar"
    if jenis == "APA":
        return "DEFINISI", "apa tanpa target khusus; asumsi definisi"
    return "TIDAK_DIKENALI", "target belum dicakup aturan"


def proses_pertanyaan(pertanyaan: str) -> dict:
    """Keluaran JSON-serializable untuk anggota 3 (query) dan 4 (tipe)."""
    normal = normalisasi_teks(pertanyaan)
    if not normal:
        raise ValueError("Pertanyaan tidak boleh kosong.")
    jenis, penanda, semua_penanda = jenis_pertanyaan(normal)
    tipe, aturan = tipe_jawaban(normal, jenis, penanda)
    tokens = preprocess(pertanyaan)
    kata_kunci = list(dict.fromkeys(tokens))
    catatan = []
    perlu_klarifikasi = tipe == "TIDAK_DIKENALI" or not kata_kunci
    if len(semua_penanda) > 1:
        perlu_klarifikasi = True
        catatan.append("Terdapat beberapa penanda tanya; pecah menjadi satu pertanyaan per masukan.")
    if jenis == "SIAPA":
        catatan.append("Korpus terutama memuat jabatan. Pemetaan SIAPA ke JABATAN adalah heuristik, bukan NER.")
    if tipe == "ORANG":
        catatan.append("Nama orang sangat terbatas; keberadaan jawaban harus diperiksa saat retrieval.")
    if tipe == "WAKTU":
        catatan.append("Kalender akademik tidak tersedia; fakta tahun atau peristiwa mungkin tersedia.")
    if tipe in {"ALASAN", "PROSEDUR", "DAFTAR", "SYARAT", "YA_TIDAK"}:
        catatan.append("Tipe ini memerlukan penanganan anggota 4 dan dapat melampaui jawaban factoid singkat.")
    if re.search(r"\b(?:terbaru|sekarang|saat ini)\b", normal):
        catatan.append("Korpus historis (FILKOM 2020, tata tertib 2016, penilaian 2015); bukan aturan terkini.")
    if perlu_klarifikasi and len(semua_penanda) <= 1:
        catatan.append("Gunakan kata tanya dan sebutkan objek akademik yang ingin ditanyakan.")
    return {
        "pertanyaan": pertanyaan,
        "normalisasi": normal,
        "token": tokenisasi(pertanyaan),
        "token_pencarian": tokens,
        "kata_kunci": kata_kunci,
        # Query memakai urutan dan frekuensi token yang sama dengan passage.
        "query": " ".join(tokens),
        "jenis_pertanyaan": jenis,
        "penanda_tanya": penanda,
        "tipe_jawaban": tipe,
        "aturan_tipe": aturan,
        "status": "PERLU_KLARIFIKASI" if perlu_klarifikasi else "SIAP_RETRIEVAL",
        "catatan": catatan,
        "versi_preprocess": VERSI_PREPROCESS,
    }


if __name__ == "__main__":
    masukan = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else input("Pertanyaan: ")
    print(json.dumps(proses_pertanyaan(masukan), ensure_ascii=False, indent=2))
