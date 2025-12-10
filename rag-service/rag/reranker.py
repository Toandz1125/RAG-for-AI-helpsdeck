from typing import List, Dict

class Reranker:
    def __init__(self):
        # Có thể load model CrossEncoder ở đây nếu cần độ chính xác cao
        pass

    def rerank(self, query: str, results: List[Dict]) -> List[Dict]:
        """
        Hiện tại trả về nguyên bản. 
        Mở rộng: Sử dụng CrossEncoder để tính lại score.
        """
        # Sắp xếp theo score (khoảng cách L2 càng nhỏ càng tốt với FAISS FlatL2)
        # Nếu dùng Cosine Similarity thì logic sort sẽ ngược lại
        return sorted(results, key=lambda x: x.get('score', 0))