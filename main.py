Hiểu rồi. Đây là yêu cầu hợp lý để cân bằng giữa việc không bỏ sót tin ở các ngành ít tin (Thuế, Du lịch) và không bị spam tin cũ ở các ngành nóng (Tài chính, Chiến sự).

Tôi đã sửa lại code với cơ chế "Tiêu chuẩn kép":

Nhóm 1 (Tài chính, Thế giới, Chứng khoán): Chế độ Strict Mode -> Chỉ lấy tin ĐÚNG NGÀY HÔM NAY.

Nhóm 2 (Thuế, E-com, Du lịch): Chế độ Extended Mode -> Lấy tin trong vòng 3 NGÀY (Hôm nay + 2 ngày trước).

Ông copy đè code này vào main.py là chuẩn chỉ:

code
Python
download
content_copy
expand_less
import feedparser
import requests
import os
import datetime
import time
from time import mktime
from bs4 import BeautifulSoup

# --- CẤU HÌNH ---
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

LIMIT_PER_CAT = 30 
DELETE_LIMIT = 200 

# --- CẤU HÌNH DANH MỤC (Thêm tham số 'days_old') ---
# days_old = 0: Chỉ lấy tin hôm nay
# days_old = 2: Lấy tin hôm nay + 2 ngày trước
DANH_MUC = [
    {
        "ten": "🌍 TÀI CHÍNH & KINH TẾ THẾ GIỚI",
        "days_old": 0, # CHỈ LẤY HÔM NAY
        "urls": [
            "https://vietstock.vn/773/the-gioi/chung-khoan-the-gioi.rss",
            "https://vietstock.vn/772/the-gioi/tai-chinh-quoc-te.rss",
            "https://vnexpress.net/rss/the-gioi.rss"
        ],
        "keywords": [
            "fed", "cục dự trữ", "lãi suất", "lạm phát", "gdp", "cpi", "pmi",
            "usd", "tỷ giá", "yên nhật", "nhân dân tệ", "eur", "vàng", "dầu", "năng lượng",
            "world bank", "imf", "ecb", "suy thoái", "khủng hoảng", "bitcoin", "crypto",
            "chứng khoán mỹ", "wall street", "dow jones", "nasdaq", "s&p 500",
            "trung quốc", "kinh tế mỹ", "xuất khẩu", "chuỗi cung ứng"
        ]
    },
    {
        "ten": "🔥 ĐỊA CHÍNH TRỊ & BẤT ỔN TOÀN CẦU",
        "days_old": 0, # CHỈ LẤY HÔM NAY
        "urls": [
            "https://vnexpress.net/rss/the-gioi.rss",
            "https://tuoitre.vn/rss/the-gioi.rss",
            "https://thanhnien.vn/rss/the-gioi.rss"
        ],
        "keywords": [
            "xung đột", "chiến tranh", "quân sự", "giao tranh", "tấn công", "khủng bố",
            "biểu tình", "bạo loạn", "đảo chính", "bầu cử", "tổng thống", "thủ tướng",
            "nato", "liên hợp quốc", "biển đông", "trung đông", "gaza", "israel", "hamas",
            "ukraine", "nga", "triều tiên", "hạt nhân", "tên lửa", "vũ khí", "biên giới",
            "trừng phạt", "cấm vận", "ngoại giao", "houthi", "biển đỏ"
        ]
    },
    {
        "ten": "📈 CHỨNG KHOÁN & TÀI CHÍNH VIỆT NAM",
        "days_old": 0, # CHỈ LẤY HÔM NAY
        "urls": [
            "https://cafef.vn/rss/thi-truong-chung-khoan.rss",
            "https://vietstock.vn/830/chung-khoan/co-phieu.rss",
            "https://vietstock.vn/3358/chung-khoan/etf-va-cac-quy.rss",
            "https://vietstock.vn/761/kinh-te/vi-mo.rss",
            "https://vietstock.vn/757/tai-chinh/ngan-hang.rss",
            "https://vietstock.vn/737/doanh-nghiep/hoat-dong-kinh-doanh.rss",
            "https://vietstock.vn/759/hang-hoa/vang-va-kim-loai-quy.rss",
            "https://vietstock.vn/1636/nhan-dinh-phan-tich/nhan-dinh-thi-truong.rss",
            "https://vietstock.vn/582/nhan-dinh-phan-tich/phan-tich-co-ban.rss",
            "https://vietstock.vn/585/nhan-dinh-phan-tich/phan-tich-ky-thuat.rss"
        ],
        "keywords": [
            "vn-index", "vnindex", "hnx", "upcom", "cổ phiếu", "chứng khoán", "thanh khoản",
            "khối ngoại", "tự doanh", "lợi nhuận", "thua lỗ", "báo cáo tài chính", "cổ tức",
            "ngân hàng", "bất động sản", "trái phiếu", "đáo hạn", "vốn hóa", "ipo",
            "nhận định", "phân tích", "khuyến nghị", "bắt đáy", "chốt lời", "margin",
            "kỹ thuật", "cơ bản", "etf", "quỹ", "vàng", "sjc"
        ]
    },
    {
        "ten": "⚖️ CHÍNH SÁCH THUẾ & LUẬT",
        "days_old": 2, # LẤY CẢ TIN CŨ (3 ngày)
        "urls": [
            "https://thuvienphapluat.vn/rss.xml", 
            "https://vnexpress.net/rss/phap-luat.rss",
            "https://dantri.com.vn/rss/phap-luat.rss"
        ],
        "keywords": [
            "thuế", "vat", "thuế thu nhập", "thuế tndn", "thuế tncn", "hoàn thuế",
            "tổng cục thuế", "bộ tài chính", "hải quan", "nghị định", "thông tư", "luật",
            "chính phủ", "quốc hội", "dự thảo", "ban hành", "quy định mới", "xử phạt",
            "hóa đơn điện tử", "chính sách tài khóa", "giảm thuế", "miễn thuế"
        ]
    },
    {
        "ten": "🛒 THƯƠNG MẠI & KINH DOANH ONLINE",
        "days_old": 2, # LẤY CẢ TIN CŨ (3 ngày)
        "urls": [
            "https://vnexpress.net/rss/kinh-doanh.rss",
            "https://tinhte.vn/rss"
        ],
        "keywords": [
            "thương mại điện tử", "e-commerce", "mua sắm trực tuyến", "online", "bán lẻ",
            "shopee", "lazada", "tiki", "tiktok shop", "amazon", "alibaba", "temu",
            "giao hàng", "logistic", "kho bãi", "thanh toán", "ví điện tử", "momo", "zalopay",
            "livestream", "chốt đơn", "doanh thu online", "chuyển đổi số"
        ]
    },
    {
        "ten": "📊 SỐ LIỆU & XU HƯỚNG DU LỊCH",
        "days_old": 2, # LẤY CẢ TIN CŨ (3 ngày)
        "urls": [
            "https://thanhnien.vn/rss/du-lich.rss", 
            "https://dantri.com.vn/rss/du-lich.rss", 
            "https://tuoitre.vn/rss/du-lich.rss"
        ],
        "keywords": [
            "số liệu", "thống kê", "báo cáo", "doanh thu", "lượt khách", "khách quốc tế",
            "khách nội địa", "lữ hành", "hàng không", "vé máy bay", "cục du lịch", "visa",
            "thị thực", "miễn visa", "xu hướng", "công suất phòng", "khách sạn", "resort",
            "du lịch bền vững", "mice", "tăng trưởng", "sụt giảm", "un tourism"
        ]
    }
]

def clean_html(raw_html):
    try:
        soup = BeautifulSoup(raw_html, "html.parser")
        for tag in soup(['script', 'style', 'img', 'iframe', 'video', 'a']):
            tag.decompose()
        
        text = soup.get_text(separator=" ")
        text = " ".join(text.split())
        
        garbage_phrases = ["TTO -", "(Dân trí)", "VTV.vn -", "Báo Đầu tư -", "ANTD.VN -"]
        for phrase in garbage_phrases:
            text = text.replace(phrase, "")
            
        return text.strip()
    except:
        return ""

def get_vietnam_time():
    utc_now = datetime.datetime.utcnow()
    vn_now = utc_now + datetime.timedelta(hours=7)
    return vn_now

def check_thoi_gian_hop_le(entry, allowed_days):
    # allowed_days: Số ngày cũ cho phép (0 là chỉ hôm nay, >0 là cho phép tin cũ)
    try:
        if hasattr(entry, 'published_parsed') and entry.published_parsed:
            dt_utc = datetime.datetime(*entry.published_parsed[:6])
            dt_vn = dt_utc + datetime.timedelta(hours=7)
            vn_now = get_vietnam_time()
            
            # Nếu allowed_days = 0 (Chỉ lấy hôm nay)
            if allowed_days == 0:
                if dt_vn.date() == vn_now.date():
                    return True, dt_vn.strftime("%H:%M") # Chỉ hiện giờ
                else:
                    return False, None
            
            # Nếu allowed_days > 0 (Cho phép tin cũ)
            else:
                delta = vn_now - dt_vn
                if delta.days <= allowed_days:
                    # Nếu là hôm nay thì hiện giờ
                    if dt_vn.date() == vn_now.date():
                        return True, dt_vn.strftime("%H:%M")
                    # Nếu tin cũ thì hiện Ngày + Giờ
                    else:
                        return True, dt_vn.strftime("%d/%m %H:%M")
                else:
                    return False, None
    except:
        # Nếu không có ngày tháng, mặc định lấy (để đỡ sót)
        return True, "Mới"
    return False, None

def don_dep_chat():
    print("🧹 Bắt đầu dọn dẹp...")
    url_send = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        resp = requests.post(url_send, json={"chat_id": TELEGRAM_CHAT_ID, "text": "⏳ Đang lọc dữ liệu theo từng danh mục..."}).json()
        if not resp.get("ok"): return

        current_id = resp['result']['message_id']
        for i in range(current_id, current_id - DELETE_LIMIT, -1):
            url_del = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/deleteMessage"
            requests.post(url_del, json={"chat_id": TELEGRAM_CHAT_ID, "message_id": i})
    except Exception as e:
        print(f"Lỗi dọn dẹp: {e}")

def gui_theo_lo(ds_msg):
    for msg in ds_msg:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        if len(msg) > 4000:
            parts = [msg[i:i+4000] for i in range(0, len(msg), 4000)]
            for part in parts:
                requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": part, "disable_web_page_preview": True, "parse_mode": "Markdown"})
                time.sleep(1)
        else:
            requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "disable_web_page_preview": True, "parse_mode": "Markdown"})
            time.sleep(1)

def xu_ly_tin_tuc():
    vn_now = get_vietnam_time()
    ngay_str = vn_now.strftime("%d/%m/%Y")
    
    messages_queue = []
    messages_queue.append(f"📅 **BẢN TIN NGÀY {ngay_str}**")
    
    current_msg = ""
    
    for muc in DANH_MUC:
        header = f"\n➖➖➖➖➖➖➖➖➖➖\n**{muc['ten']}**\n"
        if len(current_msg) + len(header) > 3000:
            messages_queue.append(current_msg)
            current_msg = header
        else:
            current_msg += header
            
        count = 0
        collected_links = set()
        # Lấy giới hạn ngày của danh mục hiện tại (mặc định là 0 nếu không khai báo)
        days_limit = muc.get("days_old", 0)
        
        for url in muc['urls']:
            if count >= LIMIT_PER_CAT: break
            try:
                feed = feedparser.parse(url)
                if not feed.entries: continue 

                for entry in feed.entries:
                    if count >= LIMIT_PER_CAT: break
                    link = entry.link
                    if link in collected_links: continue
                    
                    # --- CHECK NGÀY THEO TỪNG DANH MỤC ---
                    hop_le, time_str = check_thoi_gian_hop_le(entry, days_limit)
                    if not hop_le: continue 
                    
                    keywords = muc.get('keywords', [])
                    desc_raw = getattr(entry, 'summary', '') or getattr(entry, 'description', '')
                    desc_clean = clean_html(desc_raw)
                    
                    if keywords:
                        text_check = (entry.title + " " + desc_clean).lower()
                        if not any(k in text_check for k in keywords): continue
                    
                    # Nội dung tin
                    news_item = f"\n🕒 `{time_str}` | **{entry.title}**\n_{desc_clean}_\n👉 [Xem chi tiết]({link})\n"
                    
                    if len(current_msg) + len(news_item) > 3500:
                        messages_queue.append(current_msg)
                        current_msg = news_item 
                    else:
                        current_msg += news_item
                    
                    collected_links.add(link)
                    count += 1
            except Exception as e:
                print(f"Lỗi đọc RSS {url}: {e}")
            
        if count == 0:
            # Thông báo khác nhau tùy theo chế độ
            if days_limit == 0:
                current_msg += "\n_(Chưa có tin mới hôm nay)_\n"
            else:
                current_msg += "\n_(Không có tin trong 3 ngày qua)_\n"

    if current_msg:
        messages_queue.append(current_msg)
        
    return messages_queue

def main():
    if not TELEGRAM_TOKEN: return
    don_dep_chat()
    ds_tin = xu_ly_tin_tuc()
    gui_theo_lo(ds_tin)

if __name__ == "__main__":
    main()
