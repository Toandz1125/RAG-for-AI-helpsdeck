class Chunker:
    def __init__(self, chunk_size: int = 800, chunk_overlap: int = 120):
        """
        Args:
            chunk_size: Độ dài tối đa của mỗi đoạn văn bản (ký tự).
            chunk_overlap: Số ký tự lặp lại giữa 2 đoạn liền kề (giúp giữ ngữ cảnh).
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split_text(self, text: str) -> list[str]:
        if not text:
            return []

        # Nếu người dùng cung cấp nhiều dòng, tách mỗi dòng thành một chunk
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        if lines:
            return lines

        # Fallback: cắt theo ký tự (ít dùng khi đã có dòng)
        chunks = []
        start = 0
        text_length = len(text)

        while start < text_length:
            end = start + self.chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            if end >= text_length:
                break
            start += self.chunk_size - self.chunk_overlap

        return chunks