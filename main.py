import feedparser
import google.generativeai as genai
import requests
import os
import datetime

# --- CẤU HÌNH LẤY TỪ GITHUB SECRETS ---
# (Code sẽ tự lấy từ mục Settings ông đã cài, không cần sửa ở đây)
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# --- DANH SÁCH NGUỒN TIN (RSS) ---
# Tôi đã chọn lọc các nguồn RSS chất lượng cho từng mục ông cần
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
        "https://thuvienphapluat.vn/rss/van-ban-moi.xml", # Nguồn chuyên về luật
        "https://vnexpress.net/rss/phap-luat.rss"
    ]
}

def gui_telegram(noi_dung):
    if not noi_dung: return
    # Telegram giới hạn 4096 ký tự, nếu dài quá phải cắt nhỏ
    max_len = 4000
    for i in range(0, len(noi_dung), max_len):
        chunk = noi_dung[i:i+max_len]
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {"chat_id": TELEGRAM_CHAT_ID, "text": chunk, "parse_mode": "Markdown"}
        requests.post(url, json=data)

def lay_du_lieu_rss():
    tong_hop_tin = ""
    print("Đang đi gom tin tức...")
    
    for danh_muc, urls in NGUON_TIN.items():
        tong_hop_tin += f"\n--- DANH MỤC: {danh_muc} ---\n"
        count = 0
        for url in urls:
            try:
                feed = feedparser.parse(url)
                # Lấy 5 tin mới nhất mỗi nguồn để tránh quá tải AI
                for entry in feed.entries[:5]:
                    title = entry.title
                    link = entry.link
                    tong_hop_tin += f"- {title} ({link})\n"
                    count += 1
            except Exception as e:
                print(f"Lỗi link {url}: {e}")
    
    return tong_hop_tin

def xu_ly_bang_gemini(data_raw):
    print("Đang gửi cho Gemini xử lý (đợi xíu)...")
    
    genai.configure(api_key=GEMINI_API_KEY)
    # Dùng model flash cho nhanh và rẻ
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    ngay = datetime.datetime.now().strftime("%d/%m/%Y")
    
    # Câu lệnh ra lệnh cho AI (Prompt)
    prompt = f"""
    Bạn là trợ lý phân tích tin tức tài chính chuyên nghiệp.
    Hôm nay là {ngay}.
    Dưới đây là danh sách các tiêu đề báo mới nhất từ nhiều nguồn:
    
    {data_raw}
    
    NHIỆM VỤ CỦA BẠN:
    1. Đọc lướt và lọc bỏ tin rác, tin trùng lặp, tin giải trí không liên quan.
    2. Tổng hợp lại thành một bản tin vắn tắt (Morning Briefing).
    3. Phân chia rõ ràng theo các mục: 
       - 📈 **Tài chính - Chứng khoán** (Tập trung VNIndex, mã cổ phiếu hot, biến động lớn)
       - 🌍 **Kinh doanh & Thế giới** (Vàng, Dầu, Fed, tin vĩ mô)
       - 🛒 **TMĐT & Xu hướng**
       - ⚖️ **Chính sách & Thuế mới** (Cực kỳ quan trọng, nếu có nghị định mới phải highlight)
    4. Giọng văn: Ngắn gọn, súc tích, chuyên gia, đi thẳng vào vấn đề.
    5. Định dạng: Dùng Markdown của Telegram (in đậm **text**, dùng icon đầu dòng).
    6. Cuối mỗi tin quan trọng, hãy để link gốc để người đọc bấm vào xem.
    
    Hãy viết bản tin ngay dưới đây:
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Lỗi AI: {e}"

def main():
    if not GEMINI_API_KEY or not TELEGRAM_TOKEN:
        print("Chưa cài đặt Key/Token trong Settings!")
        return

    # 1. Gom tin
    raw_data = lay_du_lieu_rss()
    
    # 2. Nhờ AI viết bài
    ban_tin_cuoi = xu_ly_bang_gemini(raw_data)
    
    # 3. Gửi Telegram
    gui_telegram(ban_tin_cuoi)
    print("Xong!")

if __name__ == "__main__":
    main()
