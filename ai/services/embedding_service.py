"""
Embedding service for text representation and similarity calculations.
Provides simple TF-IDF / character-n-gram tokenization and feature vector generation
without requiring external heavy neural models or remote API calls.
"""

import math
import re
from typing import List, Dict, Set

def tokenize(text: str) -> List[str]:
    """Tokenize and normalize text into clean lowercase words."""
    cleaned = re.sub(r"[^\w\s]", " ", text.lower())
    return [w for w in cleaned.split() if len(w) > 1]

def get_character_ngrams(text: str, n: int = 3) -> Set[str]:
    """Extract character n-grams for fuzzy duplicate matching."""
    cleaned = re.sub(r"\s+", " ", text.lower().strip())
    if len(cleaned) < n:
        return {cleaned}
    return {cleaned[i:i+n] for i in range(len(cleaned) - n + 1)}

class LocalEmbeddingService:
    """Lightweight, standalone local text vectorizer for similarity comparisons."""
    
    @staticmethod
    def get_token_freq(text: str) -> Dict[str, int]:
        tokens = tokenize(text)
        freq: Dict[str, int] = {}
        for token in tokens:
            freq[token] = freq.get(token, 0) + 1
        return freq

    @staticmethod
    def cosine_similarity(text1: str, text2: str) -> float:
        """Computes Cosine similarity between term frequency vectors of two texts."""
        vec1 = LocalEmbeddingService.get_token_freq(text1)
        vec2 = LocalEmbeddingService.get_token_freq(text2)
        
        if not vec1 or not vec2:
            return 0.0
            
        intersection = set(vec1.keys()) & set(vec2.keys())
        numerator = sum(vec1[x] * vec2[x] for x in intersection)
        
        sum1 = sum(val ** 2 for val in vec1.values())
        sum2 = sum(val ** 2 for val in vec2.values())
        denominator = math.sqrt(sum1) * math.sqrt(sum2)
        
        if denominator == 0:
            return 0.0
            
        return float(numerator / denominator)

    @staticmethod
    def jaccard_similarity(text1: str, text2: str) -> float:
        """Computes Jaccard similarity based on 3-gram character overlapping."""
        ngrams1 = get_character_ngrams(text1, n=3)
        ngrams2 = get_character_ngrams(text2, n=3)
        
        if not ngrams1 or not ngrams2:
            return 0.0
            
        intersection = ngrams1 & ngrams2
        union = ngrams1 | ngrams2
        
        return float(len(intersection) / len(union))
