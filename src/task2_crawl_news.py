"""
Task 2 — Crawl bài viết/hướng dẫn hỗ trợ khách hàng về thương mại điện tử.

Hướng dẫn:
    1. Crawl tối thiểu 5 bài viết từ trung tâm trợ giúp công khai của một sàn TMĐT.
    2. Sử dụng Crawl4AI hoặc thư viện crawling tương tự.
    3. Lưu output vào data/landing/news/
    4. Mỗi bài lưu 1 file JSON với metadata (url, title, date_crawled, content).

Cài đặt:
    pip install crawl4ai
    playwright install chromium   # bắt buộc — pip install crawl4ai KHÔNG tự tải browser binary,
                                   # thiếu bước này sẽ báo lỗi
                                   # "BrowserType.launch: Executable doesn't exist"

Gợi ý chủ đề: theo dõi đơn hàng, đổi phương thức thanh toán, bằng chứng hoàn tiền,
mua hàng xuyên biên giới.

Lưu ý: một số trang help center dùng JavaScript render (SPA) — nếu crawl về chỉ thấy
tiêu đề mà không có nội dung, đổi sang bài viết khác cùng domain thay vì cố xử lý.
"""

"""
Task 2 — Crawl bài viết/hướng dẫn hỗ trợ khách hàng về thương mại điện tử.
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data" / "landing" / "news"


def setup_directory():
    """Tạo thư mục data/landing/news/ nếu chưa có."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)


async def crawl_article(url: str) -> dict:
    """
    Crawl một bài viết và trả về dict chứa metadata + content.
    """
    from crawl4ai import AsyncWebCrawler

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=url)
        
        # Xử lý tiêu đề an toàn từ metadata
        title = "Unknown"
        if result.metadata and isinstance(result.metadata, dict):
            title = result.metadata.get("title", "Unknown")
            
        return {
            "url": url,
            "title": title,
            "date_crawled": datetime.now().isoformat(),
            "content_markdown": result.markdown,
        }


async def crawl_all():
    """Crawl chọn lọc các bài viết bị lỗi."""
    setup_directory()

    # Chỉ crawl lại những file bị lỗi (2, 4, 5) để tránh spam các link đã thành công (1, 3)
    # Mapping định dạng: số thứ tự file -> link mới cần thay thế
    urls_to_fix = {
        2: "https://help.shopee.vn/portal/4/article/79213", # Thay cho file 2 bị rỗng
        4: "https://help.shopee.vn/portal/4/article/79198", # Thay cho file 4 bị block
        5: "https://help.shopee.vn/portal/4/article/77244"  # Thay cho file 5 bị block
    }

    # Chuyển dict thành list để dễ xử lý vòng lặp và delay
    items = list(urls_to_fix.items())
    
    for i, (file_index, url) in enumerate(items):
        print(f"Crawling link bổ sung cho bài {file_index:02d}: {url}")
        article = await crawl_article(url)

        # Ghi đè trực tiếp vào file tương ứng (article_02.json, article_04.json, article_05.json)
        filename = f"article_{file_index:02d}.json"
        filepath = DATA_DIR / filename
        filepath.write_text(json.dumps(article, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  ✓ Saved: {filepath}")
        
        # Thêm độ trễ 5 giây để tránh bị Shopee block giữa các lần tải
        if i < len(items) - 1:
            print("  ⏳ Đang nghỉ 5s để tránh bị block...")
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(crawl_all())