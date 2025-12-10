import os
import uvicorn
import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# ==========================================
# 1. CẤU HÌNH & KHỞI TẠO
# ==========================================
DATA_FILE = "data1.txt"  # File dữ liệu gốc
MIN_SCORE = 0.1          # Ngưỡng điểm thấp nhất (0.0 - 1.0) để chấp nhận kết quả

app = FastAPI(title="Offline Search Engine (No AI)")

class LocalSearchEngine:
    def __init__(self):
        self.chunks = []       # Lưu nội dung văn bản
        self.vectorizer = None # Bộ biến đổi toán học
        self.tfidf_matrix = None # Ma trận số hóa của dữ liệu

    def load_and_train(self):
        """Đọc file và tính toán chỉ số thống kê (TF-IDF)"""
        print(f"--- Đang tải dữ liệu từ {DATA_FILE} ---")
        
        if not os.path.exists(DATA_FILE):
            print(f"LỖI: Không tìm thấy file '{DATA_FILE}'. Hãy tạo file này trước.")
            self.chunks = []
            return

        # 1. Đọc file text
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            text = f.read()

        # 2. Cắt văn bản thành từng dòng (Chunking)
        # Loại bỏ các dòng trống
        self.chunks = [line.strip() for line in text.split('\n') if line.strip()]
        
        if not self.chunks:
            print("Cảnh báo: File dữ liệu rỗng!")
            return

        print(f"-> Đã đọc được {len(self.chunks)} dòng dữ liệu.")

        # 3. Tạo Vector hóa (Biến chữ thành số dựa trên tần suất từ)
        # TfidfVectorizer sẽ học bộ từ vựng từ data1.txt của bạn
        print("-> Đang tính toán ma trận thống kê...")
        self.vectorizer = TfidfVectorizer()
        self.tfidf_matrix = self.vectorizer.fit_transform(self.chunks)
        print("-> Hệ thống đã sẵn sàng! (Offline 100%)")

    def search(self, query):
        """Tìm kiếm dựa trên độ tương đồng Cosine"""
        if not self.vectorizer or self.tfidf_matrix is None:
            return "Hệ thống chưa có dữ liệu.", 0.0

        # 1. Biến câu hỏi người dùng thành vector số (theo quy luật đã học ở trên)
        query_vec = self.vectorizer.transform([query])

        # 2. Tính toán độ giống nhau giữa Câu hỏi và Tất cả các dòng trong Data
        # Kết quả là một danh sách điểm số (từ 0 đến 1)
        similarities = cosine_similarity(query_vec, self.tfidf_matrix).flatten()

        # 3. Tìm vị trí có điểm cao nhất
        best_idx = np.argmax(similarities)
        best_score = similarities[best_idx]

        # 4. Kiểm tra ngưỡng
        if best_score < MIN_SCORE:
            return None, float(best_score)
        
        return self.chunks[best_idx], float(best_score)

# Khởi tạo công cụ tìm kiếm
engine = LocalSearchEngine()
engine.load_and_train()

# ==========================================
# 2. API ENDPOINT
# ==========================================

class UserQuery(BaseModel):
    message: str

@app.post("/chat")
def chat_offline(req: UserQuery):
    # Tìm kiếm
    result_text, score = engine.search(req.message)

    print(f"Query: '{req.message}' | Best match score: {score:.4f}")

    if result_text:
        return {
            "reply": result_text,  # Trả về nguyên văn đoạn tìm thấy
            "score": score,
            "method": "TF-IDF (Statistical Math)"
        }
    else:
        return {
            "reply": "Không tìm thấy thông tin phù hợp trong tài liệu.",
            "score": score,
            "method": "TF-IDF (Statistical Math)"
        }

if __name__ == "__main__":
    # Chạy server
    uvicorn.run(app, host="127.0.0.1", port=8000)