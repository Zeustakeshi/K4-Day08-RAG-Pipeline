"""
Task 2 — Crawl bài viết về phong tục tập quán, lễ hội lớn và trang phục truyền thống Việt Nam
          từ nhiều nguồn trang web (domain) khác nhau.

Hướng dẫn:
    1. Crawl tối thiểu 5 bài viết về phong tục, lễ hội lớn, trang phục truyền thống Việt Nam.
    2. Mỗi bài lưu thành 1 file JSON chứa metadata (url, domain, title, crawl_date, date_crawled, content, content_markdown).
    3. Lưu file vào data/landing/news/ (article_01.json -> article_06.json).
"""

import json
from datetime import datetime
from pathlib import Path
import requests
from bs4 import BeautifulSoup

DATA_DIR = Path(__file__).parent.parent / "data" / "landing" / "news"

# 6 Bài viết chất lượng cao về Phong tục, Lễ hội lớn và Trang phục truyền thống Việt Nam từ nhiều trang web
TARGET_ARTICLES = [
    {
        "id": 1,
        "domain": "vi.wikipedia.org",
        "title": "Tết Nguyên Đán - Phong tục tập quán & Lễ hội truyền thống Việt Nam",
        "url": "https://vi.wikipedia.org/wiki/Tết_Nguyên_Đán"
    },
    {
        "id": 2,
        "domain": "suckhoedoisong.vn",
        "title": "Lễ hội Áo dài Du lịch Hà Nội - Tôn vinh trang phục truyền thống Việt Nam",
        "url": "https://suckhoedoisong.vn/le-hoi-ao-dai-du-lich-ha-noi-2023-169231027150000000.htm"
    },
    {
        "id": 3,
        "domain": "thethaovanhoa.vn",
        "title": "Văn hóa, Lễ hội truyền thống và Di sản phong tục Việt Nam",
        "url": "https://thethaovanhoa.vn/van-hoa.htm"
    },
    {
        "id": 4,
        "domain": "vi.wikisource.org",
        "title": "Việt Nam Phong Tục - Tập quán & Lễ nghi cổ truyền (Phan Kế Bính)",
        "url": "https://vi.wikisource.org/wiki/Vi%E1%BB%87t_Nam_phong_t%E1%BB%A5c"
    },
    {
        "id": 5,
        "domain": "vi.wikipedia.org",
        "title": "Giỗ Tổ Hùng Vương - Lễ hội Đền Hùng",
        "url": "https://vi.wikipedia.org/wiki/Giỗ_Tổ_Hùng_Vương"
    },
    {
        "id": 6,
        "domain": "vi.wikipedia.org",
        "title": "Áo dài - Trang phục truyền thống Việt Nam",
        "url": "https://vi.wikipedia.org/wiki/Áo_dài"
    }
]


def setup_directory():
    """Tạo thư mục data/landing/news/ nếu chưa có."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def extract_clean_content(html: str, fallback_title: str) -> tuple[str, str]:
    """Trích xuất tiêu đề và nội dung văn bản sạch từ HTML."""
    soup = BeautifulSoup(html, "html.parser")

    # Loại bỏ các phần không chứa nội dung chính
    for tag in soup(["script", "style", "header", "footer", "nav", "form", "iframe", "aside", "noscript"]):
        tag.decompose()

    # Thử lấy tiêu đề từ H1
    h1_tag = soup.find("h1")
    if h1_tag and len(h1_tag.get_text(strip=True)) > 2:
        title = h1_tag.get_text(strip=True)
    else:
        title = fallback_title

    # Lấy văn bản sạch phân chia theo dòng
    lines = [line.strip() for line in soup.get_text(separator="\n", strip=True).splitlines() if len(line.strip()) > 3]
    
    # Loại bỏ dòng trùng lặp liên tiếp
    cleaned_lines = []
    for line in lines:
        if not cleaned_lines or cleaned_lines[-1] != line:
            cleaned_lines.append(line)

    content_text = "\n\n".join(cleaned_lines)
    return title, content_text


def fetch_url(session: requests.Session, url: str) -> str:
    """Tải nội dung trang web với header browser chuẩn."""
    response = session.get(url, timeout=12)
    response.raise_for_status()
    response.encoding = "utf-8"
    return response.text


def crawl_news():
    """Crawl 6 bài viết về phong tục, lễ hội, trang phục truyền thống từ nhiều website và lưu JSON."""
    setup_directory()
    print("=" * 75)
    print("Task 2: Crawl bài viết Phong tục, Lễ hội lớn & Trang phục truyền thống Việt Nam")
    print("=" * 75)

    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7"
    })

    for item in TARGET_ARTICLES:
        file_index = item["id"]
        domain = item["domain"]
        url = item["url"]
        fallback_title = item["title"]
        filename = f"article_{file_index:02d}.json"
        filepath = DATA_DIR / filename

        print(f"Crawling bài [{file_index:02d}] từ Domain [{domain}]: {url}")

        try:
            html = fetch_url(session, url)
            title, content = extract_clean_content(html, fallback_title)
            crawled_time = datetime.now().isoformat()

            article_data = {
                "url": url,
                "domain": domain,
                "title": title,
                "crawl_date": crawled_time,
                "date_crawled": crawled_time,
                "content": content,
                "content_markdown": f"# {title}\n\n**Nguồn / Domain:** {domain}\n**URL:** {url}\n\n---\n\n{content}"
            }

            filepath.write_text(json.dumps(article_data, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"  ✓ Đã lưu: {filepath.name} | Title: {title[:40]} | Độ dài: {len(content)} ký tự")
        except Exception as e:
            print(f"  ✗ Lỗi khi crawl {url}: {e}")

    print("\n✓ Hoàn tất Task 2! Dữ liệu đã lưu tại:", DATA_DIR)


if __name__ == "__main__":
    crawl_news()