from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from rank_bm25 import BM25Okapi

from .scanner import build_visible_tree, load_documents


TOKEN_PATTERN = re.compile(r"[a-zA-Z0-9]+")


def tokenize(text: str) -> list[str]:
    return TOKEN_PATTERN.findall(text.lower())


@dataclass
class SearchIndex:
    tree: dict
    documents: list[dict[str, str]]
    bm25: BM25Okapi


class IndexManager:
    def __init__(self, root_dir: Path):
        self.root_dir = root_dir
        self._index: SearchIndex | None = None

    def build(self) -> SearchIndex:
        tree = build_visible_tree(self.root_dir)
        documents = load_documents(self.root_dir)

        if not documents:
            raise ValueError("No readable JSON content was found under file_system.")

        tokenized_corpus = [tokenize(item["content"]) for item in documents]
        bm25 = BM25Okapi(tokenized_corpus)
        self._index = SearchIndex(tree=tree, documents=documents, bm25=bm25)
        return self._index

    def get_or_build(self) -> SearchIndex:
        if self._index is None:
            return self.build()
        return self._index

    def refresh(self) -> SearchIndex:
        return self.build()

    def search_top_k(self, query: str, top_k: int = 3) -> list[dict[str, str]]:
        index = self.get_or_build()
        query_tokens = tokenize(query)
        if not query_tokens:
            return []

        scores = index.bm25.get_scores(query_tokens)
        if len(scores) == 0:
            return []

        ranked_indices = sorted(
            range(len(scores)),
            key=lambda i: scores[i],
            reverse=True,
        )

        matches: list[dict[str, str]] = []
        for idx in ranked_indices:
            if scores[idx] <= 0:
                continue
            matches.append(index.documents[idx])
            if len(matches) >= top_k:
                break

        return matches
