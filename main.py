import feedparser
import requests
import os
import datetime
import json
from bs4 import BeautifulSoup
from time import mktime

# --- CẤU HÌNH ---
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
HISTORY_FILE = "history.json" # Cuốn sổ tay ghi nhớ

LIMIT_PER_CAT = 15 # Số tin mỗi mục

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
    # Hàm chuyển đổi giờ RSS sang giờ Việt Nam (UTC+7)
    try:
        if hasattr(entry, 'published_parsed'):
            # Lấy giờ gốc (UTC)
            dt_utc = datetime.datetime.fromtimestamp(mktime(entry.published_parsed))
            # Cộng thêm 7 tiếng
            dt_vn = dt_utc + datetime.timedelta(hours=7)
            return dt_vn.strftime("%H:%M") # Trả về dạng 14:30
    except:
        pass
    return "Mới"

def xoa_tin_nhan_cu():
    # Đọc file lịch sử để xóa tin hôm qua
    if not os.path.exists(HISTORY_FILE):
        return
    
    try:
        with open(HISTORY_FILE, 'r') as f:
            old_ids = json.load(f)
            
        print(f"Đang xóa {len(old_ids)} tin nhắn cũ...")
        for msg_id in old_ids:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/deleteMessage"
            requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "message_id": msg_id})
            
    except Exception as e:
        print(f"Lỗi khi đọc/xóa lịch sử: {e}")

def gui_va_luu_id(ds_tin_nhan):
    # Gửi tin mới và lưu lại ID của chúng
    sent_ids = []
    
    for msg in ds_tin_nhan:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {
            "chat_id": TELEGRAM_CHAT_ID, 
            "text": msg, 
            "disable_web_page_preview": True,
            "parse_mode": "Markdown" # Để hiển thị in đậm
        }
        try:
            response = requests.post(url, json=data)
            resp_data = response.json()
            if resp_data.get("ok"):
                # Lưu lại ID của tin nhắn vừa gửi
                sent_ids.append(resp_data["result"]["message_id"])
        except Exception as e:
            print(f"Lỗi gửi tin: {e}")

    # Ghi đè vào file history.json cho ngày mai dùng
    with open(HISTORY_FILE, 'w') as f:
        json.dump(sent_ids, f)
    print(f"Đã lưu {len(sent_ids)} ID tin nhắn vào sổ tay.")

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
                    
                    title = entry.title
                    link = entry.link
                    
                    if link in collected_links: continue
                    
                    # Lọc từ khóa
                    keywords = muc.get('keywords', [])
                    desc_raw = getattr(entry, 'summary', '') or getattr(entry, 'description', '')
                    desc_clean = clean_html(desc_raw)
                    
                    if keywords:
                        text_check = (title + " " + desc_clean).lower()
                        if not any(k in text_check for k in keywords):
                            continue
                    
                    # Lấy giờ
                    time_str = convert_time(entry)
                    
                    # Tạo tin nhắn có Giờ
                    news_item = f"\n🕒 `{time_str}` | [{title}]({link})\n"
                    
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
    
    # 1. Xóa tin cũ của ngày hôm qua
    xoa_tin_nhan_cu()
    
    # 2. Tạo tin mới
    ds_tin = xu_ly_tin_tuc()
    
    # 3. Gửi và lưu ID mới vào sổ
    gui_va_luu_id(ds_tin)

if __name__ == "__main__":
    main()
