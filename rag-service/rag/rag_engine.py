import os
from rag.loader import DocumentLoader
from rag.chunker import Chunker
from rag.embedder import Embedder
from rag.vector_store import VectorStore
from rag.config import VECTOR_DB_PATH

class RagEngine:
    def __init__(self):
        self.embedder = Embedder()
        self.vector_store = VectorStore()
        # Loader và Chunker khởi tạo khi cần dùng
        self.loader = DocumentLoader()
        self.chunker = Chunker(chunk_size=500, chunk_overlap=50)

    def ingest(self, file_path: str):
        """
        Quy trình nạp dữ liệu: Đọc -> Cắt -> Vector hóa -> Lưu DB
        """
        print(f"--- Bắt đầu nạp dữ liệu từ {file_path} ---")
        # Kiểm tra tồn tại và đúng định dạng .txt
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Không tìm thấy file: {file_path}")
        if not file_path.lower().endswith('.txt'):
            print("[CẢNH BÁO] File không phải .txt, vẫn tiếp tục nạp.")
        
        # 1. Đọc file
        text = self.loader.load(file_path)
        print(f"[1] Đọc xong: {len(text)} ký tự")

        # 2. Cắt nhỏ
        chunks = self.chunker.split_text(text)
        print(f"[2] Cắt xong: {len(chunks)} đoạn")

        # 3. Tạo vector (Bước này lâu nhất)
        print(f"[3] Đang tạo vector (vui lòng chờ)...")
        vectors = []
        for chunk in chunks:
            vec = self.embedder.get_embedding(chunk)
            vectors.append(vec)
            
        # 4. Lưu vào DB
        self.vector_store.add_documents(chunks, vectors)
        print(f"[4] Đã lưu vào Database thành công.")
        # Thông báo vị trí file text export để người dùng dễ kiểm tra
        txt_path = os.path.join(os.path.dirname(VECTOR_DB_PATH), "vector_store.txt")
        print(f"[INFO] Đã ghi nội dung đọc/vec vào: {txt_path}")

    def retrieve(self, query: str, top_k: int = 3):
        """
        Tìm kiếm thông tin liên quan từ DB
        """
        query_vector = self.embedder.get_embedding(query)
        results = self.vector_store.search(query_vector, top_k)
        return results

    def generate_prompt(self, query: str, context_results: list):
        """
        Ghép câu hỏi và thông tin tìm được thành một Prompt hoàn chỉnh
        để gửi cho LLM.
        """
        # Nối các đoạn văn tìm được thành một chuỗi
        context_text = "\n\n".join([r['chunk'] for r in context_results])
        
        prompt = f"""
        Dựa vào thông tin dưới đây, hãy trả lời câu hỏi bằng tiếng Việt.
        Nếu thông tin không đủ để trả lời, hãy nói "Tôi không biết".
        
        --- THÔNG TIN NỀN (CONTEXT) ---
        {context_text}
        
        --- CÂU HỎI ---
        {query}
        """
        return prompt.strip()