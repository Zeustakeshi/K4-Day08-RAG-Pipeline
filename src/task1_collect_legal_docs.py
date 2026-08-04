"""
Task 1 — Thu thập văn bản chính sách thương mại điện tử / hỗ trợ khách hàng.

Hướng dẫn:
    1. Tìm tối thiểu 3 văn bản chính sách (PDF/DOCX) từ trang chính thức của một sàn TMĐT.
    2. Tải về và lưu vào data/landing/legal/
    3. Đặt tên file rõ ràng, không dấu, mô tả đúng nội dung.

Gợi ý nguồn (ví dụ trang công khai Shopee Vietnam — help.shopee.vn):
    - https://help.shopee.vn/portal/4/article/77251 (Chính sách trả hàng và hoàn tiền)
    - https://help.shopee.vn/portal/4/article/79198 (Phương thức thanh toán)
    - https://help.shopee.vn/portal/4/article/77244 (Chính sách bảo mật)

Gợi ý văn bản (chủ đề chính sách thương mại điện tử):
    - Chính sách đổi trả/hoàn tiền (Returns/Refund Policy)
    - Phương thức thanh toán (Payment Methods)
    - Chính sách bảo mật (Privacy Policy)
    - Quy định đăng bán sản phẩm cho người bán (Seller Listing Regulations)

Nhớ gắn metadata `customer_role` (`buyer`/`seller`/`both`) cho từng tài liệu — yêu cầu riêng
của K4 Variant (kế thừa từ Lab 07), cần thiết để viết benchmark query dùng metadata_filter.

Lưu ý: một số trang help center dùng JavaScript render nội dung (SPA) — crawl về chỉ thấy
tiêu đề mà không có nội dung thật. Đổi sang bài viết khác cùng domain thay vì cố xử lý,
và chỉ dùng nguồn công khai/được phép chia sẻ.
"""

import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

DATA_DIR = Path(__file__).parent.parent / "data" / "landing" / "legal"

async def download_shopee_policy(url: str, filename: str, role: str):
    async with async_playwright() as p:
        # Mở trình duyệt Chromium ẩn
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        print(f"Đang tải dữ liệu thực tế từ: {url}")
        
        # Truy cập và chờ mạng tĩnh lặng để đảm bảo JS đã render xong nội dung
        await page.goto(url, wait_until="networkidle")
        await page.wait_for_timeout(3000) # Đợi thêm 3 giây cho chắc chắn
        
        # Chèn metadata vào đầu trang HTML trước khi xuất PDF
        js_code = f"() => {{ const el = document.createElement('p'); el.innerText = 'Metadata: customer_role={role}'; document.body.prepend(el); }}"
        await page.evaluate(js_code)
        
        # Xuất trang web ra file PDF
        filepath = DATA_DIR / filename
        await page.pdf(path=str(filepath), format="A4", print_background=True)
        print(f"✓ Đã lưu file PDF: {filepath}")
        
        await browser.close()

async def main():
    # Tạo thư mục nếu chưa có
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    print(f"✓ Thư mục lưu trữ: {DATA_DIR}")

    # Danh sách URL công khai của Shopee
    policies = [
        {
            "url": "https://help.shopee.vn/portal/4/article/77251",
            "filename": "returns-refund-policy.pdf",
            "role": "buyer"
        },
        {
            "url": "https://help.shopee.vn/portal/4/article/79198",
            "filename": "payment-methods.pdf",
            "role": "buyer"
        },
        {
            "url": "https://help.shopee.vn/portal/4/article/77244",
            "filename": "privacy-policy.pdf",
            "role": "both"
        }
    ]

    for doc in policies:
        await download_shopee_policy(doc["url"], doc["filename"], doc["role"])

if __name__ == "__main__":
    asyncio.run(main())