import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import os
import time

# --- CẤU HÌNH ---
BASE_URL = "https://vju.vnu.edu.vn/"
MAX_PAGES = 100  # Tăng lên 100 trang để lấy nhiều dữ liệu hơn
OUTPUT_FILE = "data1.txt"

visited_urls = set()
queue_urls = [BASE_URL]

def get_soup(url):
    try:
        # Thêm header để giả lập trình duyệt, tránh bị chặn
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            return BeautifulSoup(resp.content, 'html.parser')
    except: pass
    return None

def crawl():
    print(f"--- BẮT ĐẦU QUÉT SÂU (Max: {MAX_PAGES} trang) ---")
    
    content_list = []
    count = 0
    
    # Tạo thư mục nếu chưa có
    if not os.path.exists("data"): os.makedirs("data")

    while queue_urls and count < MAX_PAGES:
        current_url = queue_urls.pop(0)
        
        if current_url in visited_urls: continue
        visited_urls.add(current_url)

        print(f"[{count+1}/{MAX_PAGES}] Đang đọc: {current_url}")
        
        soup = get_soup(current_url)
        if not soup: continue

        # 1. Lấy nội dung text
        # Mẹo: Chỉ lấy thẻ <p> và <div> chính để bớt rác menu/footer
        body_text = ""
        for tag in soup.find_all(['p', 'h1', 'h2', 'h3', 'li']):
            text = tag.get_text(strip=True)
            if len(text) > 20: # Chỉ lấy câu dài hơn 20 ký tự
                body_text += text + "\n"
        
        if len(body_text) > 500: # Chỉ lưu trang có nội dung đáng kể
            content_list.append(f"SOURCE: {current_url}\n{body_text}\n{'='*20}\n")
            count += 1
        
        # 2. Tìm link mới để cho vào hàng đợi
        for a in soup.find_all('a', href=True):
            full_url = urljoin(BASE_URL, a['href'])
            parsed = urlparse(full_url)
            # Chỉ lấy link nội bộ vju.vnu.edu.vn
            if "vju.vnu.edu.vn" in parsed.netloc and full_url not in visited_urls:
                queue_urls.append(full_url)
        
        # Nghỉ 0.5 giây để không làm sập web trường
        time.sleep(0.5)

    print(f"\n-> Đang lưu dữ liệu vào {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write("".join(content_list))
    print("-> HOÀN TẤT! Hãy chạy file console để hỏi.")

if __name__ == "__main__":
    crawl()