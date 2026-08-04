"""
Task 3 — Convert toàn bộ file trong data/landing/ thành Markdown.
- Chạy được trên mọi máy tính nhờ đường dẫn tương đối.
- Bắt lỗi MissingDependencyException nếu máy khác chưa cài extra [pdf].
"""

import json
from pathlib import Path
import sys

# Thử import MarkItDown
try:
    from markitdown import MarkItDown
except ImportError:
    print("Lỗi: Chưa cài đặt MarkItDown.")
    print("Vui lòng chạy: pip install \"markitdown[pdf]\"")
    sys.exit(1)

# ĐƯỜNG DẪN ĐỘNG: Chạy được trên mọi máy tính.
# Giả định file code này nằm trong thư mục src/ (vd: src/task3_convert.py)
# Path(__file__).resolve().parent.parent sẽ lùi 2 cấp để trỏ về thư mục gốc của Project.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
LANDING_DIR = PROJECT_ROOT / "data" / "landing"
OUTPUT_DIR = PROJECT_ROOT / "data" / "standardized"

def convert_legal_docs():
    """Convert PDF/DOCX files trong data/landing/legal/ sang markdown."""
    legal_dir = LANDING_DIR / "legal"
    output_dir = OUTPUT_DIR / "legal"
    
    # Tạo thư mục đầu ra nếu chưa có
    output_dir.mkdir(parents=True, exist_ok=True)

    if not legal_dir.exists():
        print(f"Thư mục không tồn tại: {legal_dir}")
        return

    md = MarkItDown()

    print(f"\n--- Quét thư mục Legal: {legal_dir.name} ---")
    for filepath in legal_dir.iterdir():
        if filepath.suffix.lower() in (".pdf", ".docx", ".doc"):
            print(f"Đang convert: {filepath.name} ...")
            try:
                # Chuyển đổi file
                result = md.convert(str(filepath))
                output_path = output_dir / f"{filepath.stem}.md"
                output_path.write_text(result.text_content, encoding="utf-8")
                print(f"  ✓ Saved: {output_path.name}")
                
            except Exception as e:
                error_msg = str(e)
                print(f"  ✗ Lỗi khi convert {filepath.name}: {error_msg}")
                # Bắt lỗi đặc thù MissingDependencyException cho PDF
                if "MissingDependencyException" in error_msg or "pdf" in error_msg.lower():
                    print("    -> ⚡ LƯU Ý: Lỗi này thường do thiếu công cụ xử lý PDF.")
                    print("    -> Hãy đảm bảo bạn đã cài extra [pdf] bằng lệnh: pip install \"markitdown[pdf]\"")


def convert_news_articles():
    """Convert JSON crawled articles trong data/landing/news/ sang markdown."""
    news_dir = LANDING_DIR / "news"
    output_dir = OUTPUT_DIR / "news"
    
    output_dir.mkdir(parents=True, exist_ok=True)

    if not news_dir.exists():
        print(f"Thư mục không tồn tại: {news_dir}")
        return

    print(f"\n--- Quét thư mục News: {news_dir.name} ---")
    for filepath in news_dir.iterdir():
        if filepath.suffix.lower() == ".json":
            print(f"Đang convert: {filepath.name} ...")
            try:
                # Đọc dữ liệu JSON
                data = json.loads(filepath.read_text(encoding="utf-8"))
                output_path = output_dir / f"{filepath.stem}.md"
                
                # Trích xuất dữ liệu
                title = data.get('title', 'Unknown')
                url = data.get('url', 'N/A')
                crawled_date = data.get('date_crawled') or data.get('crawl_date', 'N/A')
                
                # Format Markdown
                header = f"# {title}\n\n**Source:** {url}\n**Crawled:** {crawled_date}\n\n---\n\n"
                md_content = data.get("content_markdown") or data.get("content", "")
                
                content = header + md_content
                output_path.write_text(content, encoding="utf-8")
                print(f"  ✓ Saved: {output_path.name}")
                
            except json.JSONDecodeError:
                print(f"  ✗ Lỗi: File {filepath.name} không đúng định dạng JSON.")
            except Exception as e:
                print(f"  ✗ Lỗi khi xử lý {filepath.name}: {e}")


def convert_all():
    """Chạy toàn bộ pipeline convert."""
    print("=" * 50)
    print("Task 3: Convert to Markdown (MarkItDown)")
    print(f"Project Root: {PROJECT_ROOT}")
    print("=" * 50)

    convert_legal_docs()
    convert_news_articles()

    print("\n✓ Hoàn tất! Hãy kiểm tra trong:", OUTPUT_DIR)


if __name__ == "__main__":
    convert_all()