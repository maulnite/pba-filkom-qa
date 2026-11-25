"""Pencarian passage dengan TF-IDF dan cosine similarity."""

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from Anggota2_Pertanyaan.preprocess import preprocess_passage


def pakai_token_langsung(tokens):
    return tokens


class Retrieval:
    def __init__(self, passages, dokumen):
        self.passages = list(passages)
        self.dokumen = dokumen
        self.vectorizer = TfidfVectorizer(analyzer=pakai_token_langsung)
        token_korpus = [preprocess_passage(p) for p in self.passages]
        self.matriks_passage = self.vectorizer.fit_transform(token_korpus)

    def cari_passage(self, hasil_pertanyaan, top_k=5):
        """Terima keluaran Rio dan kembalikan kandidat dengan skor positif."""
        token_query = hasil_pertanyaan.get("token_pencarian", [])
        if (
            hasil_pertanyaan.get("status") != "SIAP_RETRIEVAL"
            or not token_query
            or top_k <= 0
        ):
            return []

        vektor_query = self.vectorizer.transform([token_query])
        skor = cosine_similarity(vektor_query, self.matriks_passage)[0]
        urutan = sorted(
            (i for i, nilai in enumerate(skor) if nilai > 0),
            key=lambda i: (-skor[i], self.passages[i]["id"]),
        )

        hasil = []
        for rank, i in enumerate(urutan[:top_k], start=1):
            passage = self.passages[i]
            hasil.append({
                **passage,
                "passage_id": passage["id"],
                "rank": rank,
                "score": float(skor[i]),
                "sumber": dict(self.dokumen[passage["dok_id"]]),
            })
        return hasil
