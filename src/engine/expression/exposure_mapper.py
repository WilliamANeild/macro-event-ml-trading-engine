from __future__ import annotations

import numpy as np

from src.engine.universe.schemas import Instrument


class ExposureMapper:
    def build_exposure_matrix(
        self,
        universe: list[Instrument],
        themes: list[str],
    ) -> dict[str, dict[str, float]]:
        # Build document corpus from instrument metadata
        docs: dict[str, str] = {}
        for inst in universe:
            text = f"{inst.name} {inst.theme} {inst.subtheme} {' '.join(inst.tags)}"
            docs[inst.symbol] = text.lower()

        # Build vocabulary
        all_words: set[str] = set()
        for text in docs.values():
            all_words.update(text.split())
        vocab = sorted(all_words)
        word_to_idx = {w: i for i, w in enumerate(vocab)}

        # TF vectors for each instrument
        n_vocab = len(vocab)
        symbols = list(docs.keys())
        tf_matrix = np.zeros((len(symbols), n_vocab))
        for i, sym in enumerate(symbols):
            words = docs[sym].split()
            for w in words:
                if w in word_to_idx:
                    tf_matrix[i, word_to_idx[w]] += 1
            # Normalize
            norm = np.linalg.norm(tf_matrix[i])
            if norm > 0:
                tf_matrix[i] /= norm

        # IDF weights
        doc_freq = (tf_matrix > 0).sum(axis=0) + 1
        idf = np.log(len(symbols) / doc_freq) + 1
        tfidf_matrix = tf_matrix * idf

        # Normalize rows
        for i in range(len(symbols)):
            norm = np.linalg.norm(tfidf_matrix[i])
            if norm > 0:
                tfidf_matrix[i] /= norm

        # For each theme, compute cosine similarity
        exposure: dict[str, dict[str, float]] = {}
        for theme in themes:
            theme_words = theme.lower().split("_")
            theme_vec = np.zeros(n_vocab)
            for w in theme_words:
                if w in word_to_idx:
                    theme_vec[word_to_idx[w]] = 1.0
            norm = np.linalg.norm(theme_vec)
            if norm > 0:
                theme_vec /= norm
                theme_vec *= idf  # Apply IDF
                norm2 = np.linalg.norm(theme_vec)
                if norm2 > 0:
                    theme_vec /= norm2

            scores: dict[str, float] = {}
            for i, sym in enumerate(symbols):
                sim = float(np.dot(tfidf_matrix[i], theme_vec))
                scores[sym] = max(sim, 0.0)

            # Normalize per theme
            total = sum(scores.values())
            if total > 0:
                scores = {k: v / total for k, v in scores.items()}
            exposure[theme] = scores

        return exposure
