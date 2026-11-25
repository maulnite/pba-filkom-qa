"""Jalankan ulang evaluasi retrieval Anggota 1–3 dari data di repositori."""

import json
from pathlib import Path
from statistics import mean

from Anggota2_Pertanyaan.question_processing import proses_pertanyaan
from Anggota3_Retrieval.retrieval import Retrieval

ROOT = Path(__file__).resolve().parents[1]
DATA_KORPUS = ROOT / "Anggota1_Korpus" / "data"
BERKAS_UJI = (
    ROOT / "Anggota2_Pertanyaan" / "data" / "pertanyaan_anggota2.json",
    ROOT / "Anggota3_Retrieval" / "data" / "pertanyaan_anggota3.json",
)


def main() -> None:
    metadata = json.loads((DATA_KORPUS / "dokumen.json").read_text(encoding="utf-8"))
    with (DATA_KORPUS / "passages.jsonl").open(encoding="utf-8") as berkas:
        passages = [json.loads(baris) for baris in berkas if baris.strip()]

    retrieval = Retrieval(passages, metadata)
    peringkat_bukti = []
    for path in BERKAS_UJI:
        pertanyaan = json.loads(path.read_text(encoding="utf-8"))
        for item in pertanyaan:
            hasil = proses_pertanyaan(item["pertanyaan"])
            kandidat = retrieval.cari_passage(hasil, top_k=len(passages))
            peringkat = next(
                (p["rank"] for p in kandidat if p["passage_id"] in item["passage_id"]),
                None,
            )
            peringkat_bukti.append(peringkat)
            label = str(peringkat) if peringkat is not None else "tidak ditemukan"
            print(f'{item["penanya"]} · {item["pertanyaan"]} → {label}')

    jumlah = len(peringkat_bukti)
    masuk_lima_besar = sum(p is not None and p <= 5 for p in peringkat_bukti)
    mrr = mean(1 / p if p is not None else 0 for p in peringkat_bukti)
    print(f"\nKorpus: {len(passages)} passage")
    print(f"Hit@5: {masuk_lima_besar}/{jumlah} ({masuk_lima_besar / jumlah:.1%})")
    print(f"MRR: {mrr:.3f}")


if __name__ == "__main__":
    main()
