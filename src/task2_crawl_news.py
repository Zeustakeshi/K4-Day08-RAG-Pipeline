"""
Task 2 — Crawl bài viết về phong tục tập quán, lễ hội lớn và trang phục truyền thống Việt Nam.

Hướng dẫn:
    1. Crawl tối thiểu 5 bài viết về lễ hội, phong tục, trang phục truyền thống.
    2. Sử dụng requests / BeautifulSoup.
    3. Lưu output vào data/landing/news/
    4. Mỗi bài lưu 1 file JSON chứa metadata (url, title, crawl_date, date_crawled, content, content_markdown).
"""

import json
import re
from datetime import datetime
from pathlib import Path
import requests

DATA_DIR = Path(__file__).parent.parent / "data" / "landing" / "news"

# Danh sách URL bài viết phong tục & lễ hội Việt Nam
TARGET_ARTICLES = [
    {
        "id": 1,
        "title_default": "Tết Nguyên Đán - Phong tục & Lễ hội",
        "url": "https://vi.wikipedia.org/wiki/T%E1%BA%BFt_Nguy%C3%AAn_%C4%90%C3%A1n"
    },
    {
        "id": 2,
        "title_default": "Giỗ Tổ Hùng Vương - Lễ hội truyền thống",
        "url": "https://vi.wikipedia.org/wiki/Gi%E1%BB%97_T%E1%BB%95_H%C3%B9ng_V%C6%B0%C6%A1ng"
    },
    {
        "id": 3,
        "title_default": "Tết Trung Thu - Phong tục cổ truyền",
        "url": "https://vi.wikipedia.org/wiki/T%E1%BA%BFt_Trung_thu"
    },
    {
        "id": 4,
        "title_default": "Áo dài - Trang phục truyền thống Việt Nam",
        "url": "https://vi.wikipedia.org/wiki/%C3%81o_d%C3%A0i"
    },
    {
        "id": 5,
        "title_default": "Tết Đoan Ngọ - Phong tục cổ truyền",
        "url": "https://vi.wikipedia.org/wiki/T%E1%BA%BFt_%C4%90oan_Ng%E1%BB%8D"
    },
    {
        "id": 6,
        "title_default": "Lễ hội Chùa Hương - Phong tục hành hương",
        "url": "https://vi.wikipedia.org/wiki/Ch%C3%B9a_H%C6%B0%C6%A1ng"
    }
]


def setup_directory():
    """Tạo thư mục data/landing/news/ nếu chưa có."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def extract_title_and_content(html: str, fallback_title: str) -> tuple[str, str]:
    """Trích xuất title và nội dung văn bản từ HTML bài viết."""
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        
        # Tiêu đề
        title_tag = soup.find("h1", id="firstHeading") or soup.find("h1") or soup.find("title")
        title = title_tag.get_text(strip=True) if title_tag else fallback_title

        # Nội dung chính
        content_div = soup.find("div", id="mw-content-text") or soup.find("body") or soup
        # Loại bỏ các thẻ không cần thiết
        for element in content_div(["script", "style", "table", "nav", "footer", "form"]):
            element.decompose()

        paragraphs = [p.get_text(strip=True) for p in content_div.find_all("p") if p.get_text(strip=True)]
        content_text = "\n\n".join(paragraphs)
        if not content_text or len(content_text) < 100:
            content_text = content_div.get_text(separator="\n", strip=True)

        return title, content_text
    except Exception:
        # Fallback
        title_match = re.search(r"<title>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
        title = title_match.group(1).strip() if title_match else fallback_title

        text = re.sub(r"<script.*?>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<style.*?>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<.*?>", " ", text)
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        content_text = "\n".join(lines)
        return title, content_text


def fetch_url(session: requests.Session, url: str) -> str:
    """Tải nội dung trang web bằng requests."""
    response = session.get(url, timeout=10)
    response.raise_for_status()
    response.encoding = "utf-8"
    return response.text


def crawl_news():
    """Crawl bài viết về phong tục & lễ hội và lưu thành các file JSON."""
    setup_directory()
    print("=" * 60)
    print("Task 2: Crawl bài viết về phong tục & lễ hội Việt Nam")
    print("=" * 60)

    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    })

    for item in TARGET_ARTICLES:
        file_index = item["id"]
        url = item["url"]
        fallback_title = item["title_default"]
        filename = f"article_{file_index:02d}.json"
        filepath = DATA_DIR / filename

        print(f"Crawling bài [{file_index:02d}]: {url}")

        try:
            html = fetch_url(session, url)
            title, content = extract_title_and_content(html, fallback_title)
            crawled_time = datetime.now().isoformat()

            article_data = {
                "url": url,
                "title": title,
                "crawl_date": crawled_time,
                "date_crawled": crawled_time,
                "content": content,
                "content_markdown": f"# {title}\n\n{content}"
            }

            filepath.write_text(json.dumps(article_data, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"  ✓ Đã lưu: {filepath.name} ({len(content)} ký tự)")
        except Exception as e:
            print(f"  ✗ Lỗi khi crawl {url}: {e}")

    print("\n✓ Hoàn tất Task 2! Dữ liệu đã lưu tại:", DATA_DIR)


if __name__ == "__main__":
    crawl_news()