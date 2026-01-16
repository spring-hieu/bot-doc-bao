from google import genai
from google.genai import types
import feedparser
import requests
import os
import datetime

# --- CẤU HÌNH ---
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# --- DANH SÁCH NGUỒN TIN (RSS) ---
NGUON_TIN = {
    "Tài chính & Chứng khoán VN": [
        "https://cafef.vn/tai-chinh-chung-khoan.rss",
        "https://vietstock.vn/rss/chung-khoan.rss"
    ],
    "Kinh doanh & Thế giới": [
        "https://vnexpress.net/rss/kinh-doanh.rss",
        "https://vnexpress.net/rss/the-gioi.rss",
        "https://cafef.vn/tai-chinh-quoc-te.rss"
    ],
    "Thương mại điện tử & StartUp": [
        "https://cafebiz.vn/cong-nghe.rss",
        "https://vnexpress.net/rss/khoi-nghiep.rss"
    ],
    "Chính sách - Thuế - Luật mới": [
        "https://thuvienphapluat.vn/rss/van-ban-moi.xml",
        "https://vnexpress.net/rss/phap-luat.rss"
    ]
}

def gui_telegram(noi_dung):
    if not noi_dung: 
        print("Không có nội dung để gửi!")
        return
    
    max_len = 4000
    for i in range(0, len(noi_dung), max_len):
        chunk = noi_dung[i:i+max_len]
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {"chat_id": TELEGRAM_CHAT_ID, "text": chunk, "parse_mode": "Markdown"}
        try:
            requests.post(url, json=data)
        except Exception as e:
            print(f"Lỗi gửi Telegram: {e}")

def lay_du_lieu_rss():
    tong_hop_tin = ""
    print("Đang đi gom tin tức...")
    
    for danh_muc, urls in NGUON_TIN.items():
        tong_hop_tin += f"\n--- DANH MỤC: {danh_muc} ---\n"
        for url in urls:
            try:
                feed = feedparser.parse(url)
                # Lấy 3 tin mới nhất mỗi nguồn cho nhanh
                for entry in feed.entries[:3]:
                    title = entry.title
                    link = entry.link
                    tong_hop_tin += f"- {title} ({link})\n"
            except Exception as e:
                print(f"Lỗi link {url}: {e}")
    
    return tong_hop_tin

def xu_ly_bang_gemini(data_raw):
    print("Đang gửi cho Gemini 2.5 Flash Lite xử lý...")
    
    try:
        # Khởi tạo Client theo chuẩn mới 2026
        client = genai.Client(api_key=GEMINI_API_KEY)
        
        ngay = datetime.datetime.now().strftime("%d/%m/%Y")
        
        prompt = f"""
        Bạn là trợ lý phân tích tài chính. Hôm nay là {ngay}.
        Dữ liệu tin tức thô:
        {data_raw}
        
        YÊU CẦU:
        1. Tổng hợp thành bản tin Morning Briefing chuyên nghiệp.
        2. Phân chia theo mục: 
           - 📈 Chứng khoán & Tài chính
           - 🌍 Vĩ mô & Thế giới
           - 🛒 Kinh doanh & Xu hướng
           - ⚖️ Chính sách & Luật (Rất quan trọng)
        3. Văn phong súc tích, tóm tắt ý chính, loại bỏ tin rác.
        4. Bắt buộc dẫn link gốc cuối mỗi tin quan trọng.
        5. Dùng Markdown Telegram.
        """
        
        # Gọi model gemini-2.5-flash-lite
        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=prompt
        )
        
        return response.text
    except Exception as e:
        return f"Lỗi AI (Check lại tên Model hoặc Key): {e}"

def main():
    if not GEMINI_API_KEY:
        print("Chưa có Key Gemini!")
        return

    raw_data = lay_du_lieu_rss()
    if not raw_data:
        print("Không lấy được tin RSS nào!")
        return

    ban_tin_cuoi = xu_ly_bang_gemini(raw_data)
    gui_telegram(ban_tin_cuoi)
    print("Hoàn tất!")

if __name__ == "__main__":
    main()
