"""
Task 1 — Tải file thứ 3 (Chủ đề: Tết Nguyên Đán - Nguồn: Wikipedia API).
"""

import requests
from pathlib import Path
from urllib.parse import quote

DATA_DIR = Path(__file__).parent.parent / "data" / "landing" / "legal"

def setup_directory():
    DATA_DIR.mkdir(parents=True, exist_ok=True)

def download_pdf(url: str, filename: str):
    filepath = DATA_DIR / filename
    print(f"Đang tải: {filename}...")
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, stream=True, timeout=30)
        response.raise_for_status()
        
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"  ✓ Đã lưu thành công file: {filepath}")
    except Exception as e:
        print(f"  × Lỗi khi tải {filename}: {e}")

def main():
    setup_directory()
    
    # Dùng Wikipedia API để lấy nội dung tĩnh chuẩn PDF
    base_api = "https://vi.wikipedia.org/api/rest_v1/page/pdf/"
    url_thay_the = base_api + quote("Tết_Nguyên_Đán")
    
    download_pdf(url_thay_the, "tet-nguyen-dan.pdf")

if __name__ == "__main__":
    main()