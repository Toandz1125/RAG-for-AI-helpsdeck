import os

class DocumentLoader:
    def __init__(self):
        pass

    def load(self, file_path: str) -> str:
        # Kiểm tra file có tồn tại không
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Không tìm thấy file tại đường dẫn: {file_path}")

        try:
            # Mở file với encoding utf-8 để đọc đúng tiếng Việt
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            if not content:
                print(f"Cảnh báo: File {file_path} rỗng.")
                return ""
                
            return content

        except Exception as e:
            raise RuntimeError(f"Lỗi khi đọc file {file_path}: {str(e)}")
        
        