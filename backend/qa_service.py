from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai

from .indexer import IndexManager


PROMPT_TEMPLATE = """Answer the question based only on the content below.
If the answer is not in the content, say you cannot find it in the scanned files.

Question: {query}

Content:
{content}
"""


class QAService:
    def __init__(self, file_system_root: Path):
        load_dotenv()
        self.model_name = "gemini-2.5-flash-lite"
        api_key = os.getenv("GEMINI_API_KEY")
        self.client = genai.Client(api_key=api_key) if api_key else None
        self.index = IndexManager(file_system_root)

    def scan(self) -> dict:
        index = self.index.get_or_build()
        return {
            "tree": index.tree,
            "indexed_documents": len(index.documents),
        }

    def answer(self, query: str) -> dict:
        if self.client is None:
            raise RuntimeError("GEMINI_API_KEY is missing. Please set it in your environment or .env file.")

        documents = self.index.search_top_k(query, top_k=3)
        if not documents:
            return {
                "answer": "I could not find a relevant file in the scanned data.",
                "source": {
                    "file_path": "",
                    "file_name": "",
                    "file_type": "",
                },
                "matched_preview": "",
            }

        context_blocks: list[str] = []
        for i, doc in enumerate(documents, start=1):
            content = doc["content"]
            if len(content) > 8000:
                content = content[:8000]

            context_blocks.append(
                f"[Document {i}]\n"
                f"File path: {doc['file_path']}\n"
                f"File type: {doc['file_type']}\n"
                f"Content:\n{content}"
            )

        combined_content = "\n\n".join(context_blocks)

        prompt = PROMPT_TEMPLATE.format(query=query.strip(), content=combined_content)

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
        )

        answer_text = getattr(response, "text", "") or "No response generated."
        primary = documents[0]

        return {
            "answer": answer_text.strip(),
            "source": {
                "file_path": primary["file_path"],
                "file_name": primary["file_name"],
                "file_type": primary["file_type"],
            },
            "matched_preview": primary["content"][:500],
        }
