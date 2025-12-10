import google.generativeai as genai

def run_console():
    # Key của bạn
    api_key = "AIzaSyAn4GwPtsQ6ExlrnVfk9j84kW90zefmdxg"

    try:
        genai.configure(api_key=api_key)
        
        # ĐÃ SỬA: Dùng model gemini-2.5-flash có trong danh sách của bạn
        model = genai.GenerativeModel(
    'gemini-2.5-flash',
    # Thêm chỉ thị hệ thống (System Instruction) để ép khuôn mô hình
    system_instruction="""
    Bạn là một trợ lý RAG chuyên biệt. Nhiệm vụ của bạn là trả lời câu hỏi CHỈ DỰA TRÊN thông tin được cung cấp trong ngữ cảnh (Context).
    
    Quy tắc bắt buộc:
    1. Tuyệt đối KHÔNG sử dụng kiến thức bên ngoài hoặc kiến thức được huấn luyện trước đó để trả lời.
    2. Nếu thông tin không có trong ngữ cảnh được cung cấp, hãy trả lời chính xác: "Thông tin này không có trong tài liệu của bạn."
    3. Không được tự suy diễn hay bịa đặt thông tin.
    """
)
        
        chat = model.start_chat(history=[])
        
        print("--- Đã kết nối thành công (Model: 2.5-flash) ---")
        print("--- Gõ 'exit' để thoát ---")

        while True:
            text = input("\nBạn: ")
            if text.lower() in ['exit', 'quit']:
                break
            
            if not text.strip():
                continue

            try:
                response = chat.send_message(text)
                print(f"Trả lời: {response.text}")
            except Exception as e:
                print(f"Lỗi API: {e}")

    except Exception as e:
        print(f"Lỗi cấu hình: {e}")

if __name__ == "__main__":
    run_console()