import feedparser
import requests
import os
import datetime
from bs4 import BeautifulSoup

# --- CẤU HÌNH ---
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# Số lượng tin tối đa cho mỗi danh mục
LIMIT_PER_CAT = 20 

# CẤU HÌNH NGUỒN TIN VÀ TỪ KHÓA LỌC
# Code sẽ quét RSS, nếu tiêu đề hoặc mô tả chứa keyword thì mới lấy.
# Nếu keywords để rỗng [] thì lấy hết.
DANH_MUC = [
    {
        "ten": "🌍 TÀI CHÍNH & KINH TẾ THẾ GIỚI",
        "urls": [
            "https://cafef.vn/tai-chinh-quoc-te.rss",
            "https://vnexpress.net/rss/the-gioi.rss",
            "https://vneconomy.vn/timeline/9920/the-gioi.htm" # RSS giả lập
        ],
        "keywords": ["kinh tế", "tài chính", "fed", "lãi suất", "lạm phát", "gdp", "usd", "tỷ giá", "trung quốc", "mỹ", "eu"]
    },
    {
        "ten": "🔥 ĐỊA CHÍNH TRỊ & XUNG ĐỘT",
        "urls": [
            "https://vnexpress.net/rss/the-gioi.rss",
            "https://thanhnien.vn/rss/the-gioi.rss"
        ],
        "keywords": ["xung đột", "chiến tranh", "quân sự", "biểu tình", "bầu cử", "tổng thống", "vũ khí", "nato", "biển đông", "israel", "nga", "ukraine"]
    },
    {
        "ten": "📈 CHỨNG KHOÁN & TÀI CHÍNH VN",
        "urls": [
            "https://cafef.vn/tai-chinh-chung-khoan.rss",
            "https://vietstock.vn/rss/chung-khoan.rss",
            "https://vnexpress.net/rss/kinh-doanh.rss"
        ],
        "keywords": ["cổ phiếu", "vn-index", "chứng khoán", "ngân hàng", "lợi nhuận", "thua lỗ", "trái phiếu", "sàn hose", "hnx", "báo cáo"]
    },
    {
        "ten": "⚖️ THUẾ & CHÍNH SÁCH MỚI",
        "urls": [
            "https://thuvienphapluat.vn/rss/van-ban-moi.xml",
            "https://vnexpress.net/rss/phap-luat.rss",
            "https://cafef.vn/vi-mo-dau-tu.rss"
        ],
        "keywords": ["thuế", "nghị định", "thông tư", "luật", "chính phủ", "đề xuất", "ban hành", "quy định", "phạt", "bảo hiểm"]
    },
    {
        "ten": "🛒 THƯƠNG MẠI ĐIỆN TỬ (E-COM)",
        "urls": [
            "https://cafebiz.vn/cong-nghe.rss",
            "https://vnexpress.net/rss/kinh-doanh.rss"
        ],
        "keywords": ["shopee", "lazada", "tiki", "tiktok", "thương mại điện tử", "online", "bán lẻ", "livestream", "logistic", "giao hàng"]
    },
    {
        "ten": "✈️ DU LỊCH & XU HƯỚNG",
        "urls": [
            "https://vnexpress.net/rss/du-lich.rss",
            "https://thanhnien.vn/rss/du-lich.rss"
        ],
        "keywords": [] # Lấy hết tin du lịch, không cần lọc
    }
]

def clean_html(raw_html):
    # Hàm làm sạch thẻ HTML trong mô tả
    try:
        soup = BeautifulSoup(raw_html, "html.parser")
        text = soup.get_text(separator=" ")
        return text.strip()
    except:
        return raw_html

def rut_gon_van_ban(text, max_words=50):
    # Cắt văn bản xuống còn khoảng 50 từ
    words = text.split()
    if len(words) > max_words:
        return " ".join(words[:max_words]) + "..."
    return text

def gui_telegram(ds_tin_nhan):
    for msg in ds_tin_nhan:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        # Tắt chế độ Markdown để tránh lỗi ký tự đặc biệt, dùng HTML đơn giản hoặc text thường
        data = {
            "chat_id": TELEGRAM_CHAT_ID, 
            "text": msg, 
            "disable_web_page_preview": True
        }
        requests.post(url, json=data)

def xu_ly_tin_tuc():
    ngay = datetime.datetime.now().strftime("%d/%m/%Y")
    # Tin nhắn mở đầu
    messages_queue = [f"📅 **TỔNG HỢP TIN NGÀY {ngay}**\n(Tool tự động tổng hợp - Không dùng AI)"]
    
    current_msg = ""
    
    for muc in DANH_MUC:
        header = f"\n➖➖➖➖➖➖➖➖➖➖\n**{muc['ten']}**\n"
        
        # Nếu thêm header vào mà quá dài thì ngắt tin nhắn cũ, tạo tin mới
        if len(current_msg) + len(header) > 3500:
            messages_queue.append(current_msg)
            current_msg = header
        else:
            current_msg += header
            
        count = 0
        collected_links = set() # Để lọc tin trùng nhau
        
        for url in muc['urls']:
            if count >= LIMIT_PER_CAT: break
            
            try:
                feed = feedparser.parse(url)
                for entry in feed.entries:
                    if count >= LIMIT_PER_CAT: break
                    
                    title = entry.title
                    link = entry.link
                    
                    # Lọc trùng lặp
                    if link in collected_links: continue
                    
                    # Lấy mô tả (summary)
                    desc_raw = getattr(entry, 'summary', '') or getattr(entry, 'description', '')
                    desc_clean = clean_html(desc_raw)
                    desc_short = rut_gon_van_ban(desc_clean, 50)
                    
                    # LOGIC LỌC TỪ KHÓA
                    # Nếu danh mục có keywords, phải check xem bài viết có chứa từ khóa đó không
                    keywords = muc.get('keywords', [])
                    if keywords:
                        text_to_check = (title + " " + desc_clean).lower()
                        # Nếu KHÔNG chứa từ khóa nào trong list thì bỏ qua
                        if not any(k in text_to_check for k in keywords):
                            continue
                    
                    # Tạo nội dung tin
                    news_item = f"\n🔹 {title}\n_{desc_short}_\n👉 {link}\n"
                    
                    # Kiểm tra độ dài tin nhắn
                    if len(current_msg) + len(news_item) > 3800: # Giới hạn an toàn của Tele là 4096
                        messages_queue.append(current_msg)
                        current_msg = news_item # Bắt đầu tin mới với nội dung bài báo này
                    else:
                        current_msg += news_item
                    
                    collected_links.add(link)
                    count += 1
            except Exception as e:
                print(f"Lỗi đọc RSS {url}: {e}")
                
        if count == 0:
            current_msg += "\n(Không có tin mới phù hợp keyword hôm nay)\n"

    # Đẩy nốt phần còn dư vào hàng đợi
    if current_msg:
        messages_queue.append(current_msg)
        
    return messages_queue

def main():
    if not TELEGRAM_TOKEN:
        print("Chưa cấu hình Token!")
        return
        
    ds_tin = xu_ly_tin_tuc()
    gui_telegram(ds_tin)
    print("Đã gửi tin xong!")

if __name__ == "__main__":
    main()
