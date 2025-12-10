# rag/embedder.py
from sentence_transformers import SentenceTransformer
from rag.config import EMBEDDING_MODEL_NAME

class Embedder:
    def __init__(self):
        # Tải model từ HuggingFace (sẽ lưu vào cache máy tính)
        self.model = SentenceTransformer(EMBEDDING_MODEL_NAME)

    def get_embedding(self, text: str) -> list[float]:
        """
        Chuyển đổi text thành vector (list các số thực).
        """
        if not text:
            return []
        # Hàm encode trả về numpy array, cần chuyển về list chuẩn của Python
        return self.model.encode(text).tolist()
