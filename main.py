import feedparser
import requests
import os
import datetime
from time import mktime
from bs4 import BeautifulSoup

# --- CẤU HÌNH ---
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# Số lượng tin nhắn muốn quét ngược về quá khứ để xóa
# 100 là đủ sạch cho cả ngày hôm trước. Nếu nhiều hơn thì tăng lên.
DELETE_LIMIT = 100 
LIMIT_PER_CAT = 15

DANH_MUC = [
    {
        "ten": "🌍 TÀI CHÍNH & KINH TẾ TG",
        "urls": ["https://cafef.vn/tai-chinh-quoc-te.rss", "https://vnexpress.net/rss/the-gioi.rss"],
        "keywords": ["kinh tế", "tài chính", "fed", "lãi suất", "lạm phát", "usd", "tỷ giá", "trung quốc", "mỹ", "eu"]
    },
    {
        "ten": "🔥 ĐỊA CHÍNH TRỊ & XUNG ĐỘT",
        "urls": ["https://vnexpress.net/rss/the-gioi.rss", "https://thanhnien.vn/rss/the-gioi.rss"],
        "keywords": ["xung đột", "chiến tranh", "quân sự", "biểu tình", "bầu cử", "tổng thống", "vũ khí", "nato", "biển đông", "israel", "nga", "ukraine"]
    },
    {
        "ten": "📈 CHỨNG KHOÁN & TÀI CHÍNH VN",
        "urls": ["https://cafef.vn/tai-chinh-chung-khoan.rss", "https://vietstock.vn/rss/chung-khoan.rss"],
        "keywords": ["cổ phiếu", "vn-index", "chứng khoán", "ngân hàng", "lợi nhuận", "thua lỗ", "trái phiếu"]
    },
    {
        "ten": "⚖️ THUẾ & CHÍNH SÁCH MỚI",
        "urls": ["https://thuvienphapluat.vn/rss/van-ban-moi.xml", "https://vnexpress.net/rss/phap-luat.rss"],
        "keywords": ["thuế", "nghị định", "thông tư", "luật", "chính phủ", "đề xuất", "ban hành"]
    },
    {
        "ten": "🛒 THƯƠNG MẠI ĐIỆN TỬ (E-COM)",
        "urls": ["https://cafebiz.vn/cong-nghe.rss"],
        "keywords": ["shopee", "lazada", "tiki", "tiktok", "thương mại điện tử", "online", "bán lẻ"]
    },
    {
        "ten": "✈️ DU LỊCH & XU HƯỚNG",
        "urls": ["https://vnexpress.net/rss/du-lich.rss"],
        "keywords": [] 
    }
]

def clean_html(raw_html):
    try:
        soup = BeautifulSoup(raw_html, "html.parser")
        return soup.get_text(separator=" ").strip()
    except:
        return raw_html

def convert_time(entry):
    try:
        if hasattr(entry, 'published_parsed'):
            dt_utc = datetime.datetime.fromtimestamp(mktime(entry.published_parsed))
            dt_vn = dt_utc + datetime.timedelta(hours=7)
            return dt_vn.strftime("%H:%M")
    except: pass
    return "Mới"

def don_dep_chat():
    print("🧹 Bắt đầu dọn dẹp tin nhắn cũ...")
    
    # 1. Gửi một tin nhắn mồi để lấy ID hiện tại
    url_send = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        resp = requests.post(url_send, json={"chat_id": TELEGRAM_CHAT_ID, "text": "⏳ Đang làm sạch màn hình..."}).json()
        
        if not resp.get("ok"):
            print("Lỗi không gửi được tin mồi:", resp)
            return

        current_id = resp['result']['message_id']
        
        # 2. Vòng lặp xóa ngược từ ID hiện tại về quá khứ
        # Xóa ID tin mồi + 99 tin trước đó
        for i in range(current_id, current_id - DELETE_LIMIT, -1):
            url_del = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/deleteMessage"
            requests.post(url_del, json={"chat_id": TELEGRAM_CHAT_ID, "message_id": i})
            
    except Exception as e:
        print(f"Lỗi dọn dẹp: {e}")

def gui_tin_nhan(ds_tin_nhan):
    for msg in ds_tin_nhan:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {
            "chat_id": TELEGRAM_CHAT_ID, 
            "text": msg, 
            "disable_web_page_preview": True,
            "parse_mode": "Markdown"
        }
        requests.post(url, json=data)

def xu_ly_tin_tuc():
    ngay = datetime.datetime.now().strftime("%d/%m/%Y")
    messages_queue = [f"📅 **BẢN TIN NGÀY {ngay}**"]
    current_msg = ""
    
    for muc in DANH_MUC:
        header = f"\n➖➖➖➖➖➖➖➖➖➖\n**{muc['ten']}**\n"
        
        if len(current_msg) + len(header) > 3500:
            messages_queue.append(current_msg)
            current_msg = header
        else:
            current_msg += header
            
        count = 0
        collected_links = set()
        
        for url in muc['urls']:
            if count >= LIMIT_PER_CAT: break
            try:
                feed = feedparser.parse(url)
                for entry in feed.entries:
                    if count >= LIMIT_PER_CAT: break
                    link = entry.link
                    if link in collected_links: continue
                    
                    keywords = muc.get('keywords', [])
                    desc_raw = getattr(entry, 'summary', '') or getattr(entry, 'description', '')
                    desc_clean = clean_html(desc_raw)
                    
                    if keywords:
                        text_check = (entry.title + " " + desc_clean).lower()
                        if not any(k in text_check for k in keywords): continue
                    
                    time_str = convert_time(entry)
                    news_item = f"\n🕒 `{time_str}` | [{entry.title}]({link})\n"
                    
                    if len(current_msg) + len(news_item) > 3800:
                        messages_queue.append(current_msg)
                        current_msg = news_item
                    else:
                        current_msg += news_item
                    
                    collected_links.add(link)
                    count += 1
            except: pass
            
        if count == 0:
            current_msg += "\n_(Không có tin mới)_\n"

    if current_msg:
        messages_queue.append(current_msg)
        
    return messages_queue

def main():
    if not TELEGRAM_TOKEN:
        print("Chưa cấu hình Token!")
        return
    
    # Bước 1: Quét sạch tin nhắn cũ trước
    don_dep_chat()
    
    # Bước 2: Gom tin mới
    ds_tin = xu_ly_tin_tuc()
    
    # Bước 3: Gửi tin mới
    gui_tin_nhan(ds_tin)

if __name__ == "__main__":
    main()
