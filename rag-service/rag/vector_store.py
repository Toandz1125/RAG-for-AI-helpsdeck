import os
import pickle
import numpy as np
from rag.config import VECTOR_DB_PATH

class VectorStore:
    def __init__(self):
        self.db_path = VECTOR_DB_PATH
        # Lưu thêm bản sao dạng .txt để người dùng tiện kiểm tra
        self.txt_path = os.path.join(os.path.dirname(VECTOR_DB_PATH), "vector_store.txt")
        self.data = {
            "chunks": [],
            "vectors": []
        }
        self.load_db()

    def load_db(self):
        if os.path.exists(self.db_path):
            with open(self.db_path, 'rb') as f:
                loaded = pickle.load(f)
                # Chuẩn hoá dữ liệu để tránh lỗi KeyError 'chunks'
                if isinstance(loaded, dict):
                    chunks = loaded.get("chunks", [])
                    vectors = loaded.get("vectors", [])
                    # Nếu file cũ lưu dạng list các bản ghi {chunk, vector}
                    if not chunks and not vectors and isinstance(loaded.get("items"), list):
                        items = loaded.get("items", [])
                        chunks = [it.get("chunk", "") for it in items]
                        vectors = [it.get("vector", []) for it in items]
                    # Gán về cấu trúc chuẩn
                    self.data = {"chunks": list(chunks), "vectors": list(vectors)}
                elif isinstance(loaded, list):
                    # Danh sách các tuple/list (chunk, vector)
                    chunks, vectors = [], []
                    for it in loaded:
                        if isinstance(it, (list, tuple)) and len(it) == 2:
                            chunks.append(it[0])
                            vectors.append(it[1])
                    self.data = {"chunks": chunks, "vectors": vectors}
                else:
                    # Không rõ định dạng, giữ nguyên mặc định rỗng
                    self.data = {"chunks": [], "vectors": []}

    def save_db(self):
        # Tạo thư mục data nếu chưa có
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        with open(self.db_path, 'wb') as f:
            pickle.dump(self.data, f)
        # Ghi thêm file .txt để dễ xem nội dung
        try:
            with open(self.txt_path, 'w', encoding='utf-8') as f:
                for i, (chunk, vector) in enumerate(zip(self.data["chunks"], self.data["vectors"])):
                    f.write(f"# Item {i+1}\n")
                    f.write("CHUNK:\n")
                    f.write(chunk.replace('\r', '') + "\n")
                    f.write("VECTOR:\n")
                    f.write(",".join(str(v) for v in vector) + "\n\n")
        except Exception:
            # Không để việc ghi .txt làm hỏng quá trình lưu DB nhị phân
            pass

    def reset(self):
        """Xóa toàn bộ DB (dùng khi muốn nạp lại từ đầu)."""
        self.data = {"chunks": [], "vectors": []}
        # Xóa file trên đĩa nếu có
        for path in [self.db_path, self.txt_path]:
            try:
                if os.path.exists(path):
                    os.remove(path)
            except Exception:
                pass

    def add_documents(self, chunks: list[str], vectors: list[list[float]]):
        """Lưu thêm văn bản và vector tương ứng vào DB."""
        # Đảm bảo khoá tồn tại
        if "chunks" not in self.data or not isinstance(self.data.get("chunks"), list):
            self.data["chunks"] = []
        if "vectors" not in self.data or not isinstance(self.data.get("vectors"), list):
            self.data["vectors"] = []
        # Dedup theo nội dung chunk để tránh lặp khi ingest trùng file
        existing = set(self.data["chunks"])
        for chunk, vec in zip(chunks or [], vectors or []):
            if chunk in existing:
                continue
            self.data["chunks"].append(chunk)
            self.data["vectors"].append(vec)
            existing.add(chunk)
        self.save_db()

    def search(self, query_vector: list[float], top_k: int = 3):
        """Tìm top_k đoạn văn bản giống nhất với query_vector."""
        if not self.data["vectors"]:
            return []

        # Chuyển list về numpy array để tính toán nhanh
        db_vectors = np.array(self.data["vectors"])
        query_vector = np.array(query_vector)

        # Tính Cosine Similarity: (A . B) / (|A| * |B|)
        # Vì model sentence-transformers thường đã chuẩn hóa vector (norm=1),
        # nên chỉ cần tính dot product.
        scores = np.dot(db_vectors, query_vector)
        
        # Lấy index của top_k điểm cao nhất
        top_indices = np.argsort(scores)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            results.append({
                "chunk": self.data["chunks"][idx],
                "score": float(scores[idx])
            })
            
        return results