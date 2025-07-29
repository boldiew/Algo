import os
import json
from typing import Any, Dict, List
import numpy as np
import faiss


class MemoryStore:
    """Simple FAISS-backed memory for agent predictions."""

    def __init__(self, path: str = "memory.index", dim: int = 10):
        self.path = path
        self.meta_path = path + ".meta"
        self.dim = dim
        if os.path.exists(self.path):
            self.index = faiss.read_index(self.path)
        else:
            self.index = faiss.IndexFlatL2(dim)
        self.metadata: List[Dict[str, Any]] = []
        if os.path.exists(self.meta_path):
            with open(self.meta_path) as f:
                self.metadata = [json.loads(line) for line in f]

    def add(self, vector: List[float], meta: Dict[str, Any]):
        vec = np.array([vector], dtype="float32")
        self.index.add(vec)
        self.metadata.append(meta)
        faiss.write_index(self.index, self.path)
        with open(self.meta_path, "a") as f:
            f.write(json.dumps(meta) + "\n")

    def search(self, vector: List[float], k: int = 5) -> List[Dict[str, Any]]:
        if self.index.ntotal == 0:
            return []
        vec = np.array([vector], dtype="float32")
        distances, idxs = self.index.search(vec, k)
        return [self.metadata[i] for i in idxs[0] if i < len(self.metadata)]
