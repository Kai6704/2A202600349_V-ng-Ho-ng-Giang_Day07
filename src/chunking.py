from __future__ import annotations

import math
import re


class FixedSizeChunker:
    """
    Split text into fixed-size chunks with optional overlap.

    Rules:
        - Each chunk is at most chunk_size characters long.
        - Consecutive chunks share overlap characters.
        - The last chunk contains whatever remains.
        - If text is shorter than chunk_size, return [text].
    """

    def __init__(self, chunk_size: int = 500, overlap: int = 50) -> None:
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        if len(text) <= self.chunk_size:
            return [text]

        step = self.chunk_size - self.overlap
        chunks: list[str] = []
        for start in range(0, len(text), step):
            chunk = text[start : start + self.chunk_size]
            chunks.append(chunk)
            if start + self.chunk_size >= len(text):
                break
        return chunks


class SentenceChunker:
    """
    Split text into chunks of at most max_sentences_per_chunk sentences.

    Sentence detection: split on ". ", "! ", "? " or ".\n".
    Strip extra whitespace from each chunk.
    """

    def __init__(self, max_sentences_per_chunk: int = 3) -> None:
        self.max_sentences_per_chunk = max(1, max_sentences_per_chunk)

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
            
        # Sử dụng lookbehind regex để tách câu nhưng vẫn giữ lại dấu câu (. ! ?)
        raw_sentences = re.split(r'(?<=[.!?])\s+', text)
        sentences = [s.strip() for s in raw_sentences if s.strip()]
        
        chunks = []
        for i in range(0, len(sentences), self.max_sentences_per_chunk):
            chunks.append(" ".join(sentences[i : i + self.max_sentences_per_chunk]))
            
        return chunks


class RecursiveChunker:
    """
    Recursively split text using separators in priority order.

    Default separator priority:
        ["\n\n", "\n", ". ", " ", ""]
    """

    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def __init__(self, separators: list[str] | None = None, chunk_size: int = 500) -> None:
        self.separators = self.DEFAULT_SEPARATORS if separators is None else list(separators)
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        return self._split(text, self.separators)

    def _split(self, current_text: str, remaining_separators: list[str]) -> list[str]:
        if not current_text:
            return []
            
        if len(current_text) <= self.chunk_size:
            return [current_text]
            
        if not remaining_separators:
            # Không còn separator nào thì buộc phải chia nhỏ theo kích thước cố định
            return [current_text[i:i+self.chunk_size] for i in range(0, len(current_text), self.chunk_size)]
            
        sep = remaining_separators[0]
        next_seps = remaining_separators[1:]
        
        parts = list(current_text) if sep == "" else current_text.split(sep)
            
        chunks = []
        current_chunk = ""
        
        for part in parts:
            if not part:
                continue
                
            if len(part) > self.chunk_size:
                if current_chunk:
                    chunks.append(current_chunk)
                    current_chunk = ""
                chunks.extend(self._split(part, next_seps))
            else:
                separator_len = len(sep) if current_chunk else 0
                if len(current_chunk) + separator_len + len(part) > self.chunk_size:
                    chunks.append(current_chunk)
                    current_chunk = part
                else:
                    if current_chunk:
                        current_chunk += sep + part
                    else:
                        current_chunk = part
                        
        if current_chunk:
            chunks.append(current_chunk)
            
        return chunks


class CustomRecipeChunker:
    """Custom strategy for Vietnamese Cooking Recipes based on headers."""
    def chunk(self, text: str) -> list[str]:
        pattern = r'(Introduce:|Ingredients:|Process:|Finally:|Step \d+:)'
        parts = re.split(pattern, text)
        
        chunks = []
        for i in range(1, len(parts)-1, 2):
            header = parts[i].strip()
            content = parts[i+1].strip()
            if content:
                chunks.append(f"{header}\n{content}")
        return chunks


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def compute_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Compute cosine similarity between two vectors.

    cosine_similarity = dot(a, b) / (||a|| * ||b||)

    Returns 0.0 if either vector has zero magnitude.
    """
    if not vec_a or not vec_b:
        return 0.0
        
    dot_product = _dot(vec_a, vec_b)
    mag_a = math.sqrt(sum(a * a for a in vec_a))
    mag_b = math.sqrt(sum(b * b for b in vec_b))
    
    if mag_a == 0 or mag_b == 0:
        return 0.0
        
    return dot_product / (mag_a * mag_b)


class ChunkingStrategyComparator:
    """Run all built-in chunking strategies and compare their results."""

    def compare(self, text: str, chunk_size: int = 500, overlap: int = 50) -> dict:
        strategies = {
            "fixed_size": FixedSizeChunker(chunk_size=chunk_size, overlap=overlap),
            "by_sentences": SentenceChunker(),
            "recursive": RecursiveChunker(chunk_size=chunk_size),
            "custom_recipe": CustomRecipeChunker()
        }
        
        results = {}
        for name, chunker in strategies.items():
            chunks = chunker.chunk(text)
            results[name] = {
                "count": len(chunks),
                "avg_length": sum(len(c) for c in chunks) / len(chunks) if chunks else 0.0,
                "chunks": chunks
            }
        return results
