from __future__ import annotations

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from src.chunking import compute_similarity
from src.embeddings import _mock_embed

try:
    from src.embeddings import LocalEmbedder
    embedder = LocalEmbedder()
    print("Using LocalEmbedder for realistic semantic scores...\n")
except Exception:
    print("LocalEmbedder not available. Using _mock_embed (scores will be arbitrary).")
    print("Hint: Run 'pip install sentence-transformers' to see real semantic similarity.\n")
    embedder = _mock_embed

PAIRS = [
    (
        "Mince the garlic and chili, then fry them in cooking oil until fragrant.",
        "Crush the garlic and chili, put them in a hot oil pan, and stir well to release the aroma."
    ),
    (
        "Simmer over low heat for 30 minutes so the meat absorbs the spices.",
        "Cook at a low temperature for about half an hour to make the dish flavorful."
    ),
    (
        "Braised Tofu with Quail Eggs is a delicious dish for the family.",
        "Gold prices surged sharply on the international market today."
    ),
    (
        "Add a little sugar to give the dish a mild sweet flavor.",
        "Absolutely do not add sugar to this dish because it will ruin the taste."
    ),
    (
        "Clean the duck carefully with salt and ginger to remove the bad odor.",
        "Wash the snails with chili water so they release all the mud and dirt."
    )
]

if __name__ == "__main__":
    for i, (sent_a, sent_b) in enumerate(PAIRS, 1):
        vec_a = embedder(sent_a)
        vec_b = embedder(sent_b)
        score = compute_similarity(vec_a, vec_b)
        print(f"Pair {i}:")
        print(f"  Score: {score:.4f}")