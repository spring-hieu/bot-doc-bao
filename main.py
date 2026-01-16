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

# SỐ LƯỢNG TIN: 30 tin mỗi mục
LIMIT_PER_CAT = 30 
DELETE_LIMIT = 200 # Tăng số lượng tin xóa cũ lên để đảm bảo sạch sẽ

# CẤU HÌNH DANH MỤC & TỪ KHÓA CHUYÊN SÂU
DANH_MUC = [
    {
        "ten": "🌍 TÀI CHÍNH & KINH TẾ THẾ GIỚI",
        "urls": [
            "https://cafef.vn/tai-chinh-quoc-te.rss",
            "https://vnexpress.net/rss/the-gioi.rss",
            "https://vneconomy.vn/timeline/9920/the-gioi.htm",
            "https://bnews.vn/rss/the-gioi.rss"
        ],
        # Từ khóa bao trùm FED, Vàng, Dầu, Crypto, Tỷ giá...
        "keywords": [
            "fed", "cục dự trữ liên bang", "lãi suất", "lạm phát", "gdp", "cpi", "pmi",
            "usd", "tỷ giá", "yên nhật", "nhân dân tệ", "eur", "vàng", "dầu", "năng lượng",
            "world bank", "imf", "ecb", "suy thoái", "khủng hoảng", "bitcoin", "crypto",
            "chứng khoán mỹ", "wall street", "dow jones", "nasdaq", "s&p 500",
            "trung quốc", "kinh tế mỹ", "xuất khẩu", "chuỗi cung ứng"
        ]
    },
    {
        "ten": "🔥 ĐỊA CHÍNH TRỊ & BẤT ỔN TOÀN CẦU",
        "urls": [
            "https://vnexpress.net/rss/the-gioi.rss",
            "https://thanhnien.vn/rss/the-gioi.rss",
            "https://tuoitre.vn/rss/the-gioi.rss"
        ],
        # Từ khóa về xung đột, quân sự, bầu cử
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
        "urls": [
            "https://cafef.vn/tai-chinh-chung-khoan.rss",
            "https://vietstock.vn/rss/chung-khoan.rss",
            "https://tinnhanhchungkhoan.vn/rss/chung-khoan.rss",
            "https://vneconomy.vn/timeline/6/chung-khoan.htm"
        ],
        # Từ khóa phân tích, mã cổ phiếu, báo cáo
        "keywords": [
            "vn-index", "vnindex", "hnx", "upcom", "cổ phiếu", "chứng khoán", "thanh khoản",
            "khối ngoại", "tự doanh", "lợi nhuận", "thua lỗ", "báo cáo tài chính", "cổ tức",
            "ngân hàng", "bất động sản", "trái phiếu", "đáo hạn", "vốn hóa", "ipo",
            "nhận định", "phân tích", "khuyến nghị", "bắt đáy", "chốt lời", "margin",
            "hpg", "vcb", "ssi", "vic", "vhm", "fpt", "mwg" # Các mã bluechip ví dụ
        ]
    },
    {
        "ten": "⚖️ CHÍNH SÁCH THUẾ & LUẬT",
        "urls": [
            "https://thuvienphapluat.vn/rss/van-ban-moi.xml",
            "https://vnexpress.net/rss/phap-luat.rss",
            "https://cafef.vn/vi-mo-dau-tu.rss",
            "https://tapchitaichinh.vn/co-che-chinh-sach.rss"
        ],
        # Từ khóa chuyên về Thuế
        "keywords": [
            "thuế", "vat", "thuế thu nhập", "thuế tndn", "thuế tncn", "hoàn thuế",
            "tổng cục thuế", "bộ tài chính", "hải quan", "nghị định", "thông tư", "luật",
            "chính phủ", "quốc hội", "dự thảo", "ban hành", "quy định mới", "xử phạt",
            "hóa đơn điện tử", "chính sách tài khóa", "giảm thuế", "miễn thuế"
        ]
    },
    {
        "ten": "🛒 THƯƠNG MẠI ĐIỆN TỬ (E-COM)",
        "urls": [
            "https://cafebiz.vn/cong-nghe.rss",
            "https://vnexpress.net/rss/kinh-doanh.rss",
            "https://vneconomy.vn/timeline/99/tieu-dung.htm"
        ],
        # Từ khóa về E-com, Logistics, Bán lẻ online
        "keywords": [
            "thương mại điện tử", "e-commerce", "mua sắm trực tuyến", "online", "bán lẻ",
            "shopee", "lazada", "tiki", "tiktok shop", "amazon", "alibaba", "temu",
            "giao hàng", "logistic", "kho bãi", "thanh toán", "ví điện tử", "momo", "zalopay",
            "livestream", "chốt đơn", "doanh thu online", "chuyển đổi số"
        ]
    },
    {
        "ten": "📊 SỐ LIỆU & XU HƯỚNG DU LỊCH",
        "urls": [
            "https://vnexpress.net/rss/du-lich.rss",
            "https://tcdulichphat.com/rss/home", 
            "https://baodautu.vn/du-lich.rss"
        ],
        # Từ khóa tập trung vào BÁO CÁO, SỐ LIỆU (Loại bỏ tin review ăn chơi)
        "keywords": [
            "số liệu", "thống kê", "báo cáo", "doanh thu", "lượt khách", "khách quốc tế",
            "khách nội địa", "lữ hành", "hàng không", "vé máy bay", "cục du lịch", "visa",
            "thị thực", "miễn visa", "xu hướng", "công suất phòng", "khách sạn", "resort",
            "du lịch bền vững", "mice", "tăng trưởng", "sụt giảm", "un tourism"
        ]
    }
]

def clean_html(raw_html):
    # Làm sạch thẻ HTML nhưng giữ lại text dài
    try:
        soup = BeautifulSoup(raw_html, "lxml")
        text = soup.get_text(separator=" ").strip()
        # Xóa các cụm từ thừa thường gặp trong RSS
        text = text.replace("TTO -", "").replace("(Dân trí)", "").strip()
        return text
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
    print("🧹 Đang dọn dẹp sạch sẽ tin cũ...")
    url_send = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        # Gửi tin mồi
        resp = requests.post(url_send, json={"chat_id": TELEGRAM_CHAT_ID, "text": "⏳ Đang tổng hợp 180 tin tức..."}).json()
        if not resp.get("ok"): return

        current_id = resp['result']['message_id']
        # Xóa ngược về quá khứ
        for i in range(current_id, current_id - DELETE_LIMIT, -1):
            url_del = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/deleteMessage"
            requests.post(url_del, json={"chat_id": TELEGRAM_CHAT_ID, "message_id": i})
            
    except Exception as e:
        print(f"Lỗi dọn dẹp: {e}")

def gui_theo_lo(ds_msg):
    # Hàm gửi tin nhắn, tự động chia nhỏ nếu quá dài
    for msg in ds_msg:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        
        # Nếu tin nhắn quá dài (Telegram giới hạn 4096 ký tự), cắt đôi ra
        if len(msg) > 4000:
            parts = [msg[i:i+4000] for i in range(0, len(msg), 4000)]
            for part in parts:
                requests.post(url, json={
                    "chat_id": TELEGRAM_CHAT_ID, 
                    "text": part, 
                    "disable_web_page_preview": True,
                    "parse_mode": "Markdown"
                })
                time.sleep(1) # Nghỉ xíu tránh bị spam
        else:
            requests.post(url, json={
                "chat_id": TELEGRAM_CHAT_ID, 
                "text": msg, 
                "disable_web_page_preview": True,
                "parse_mode": "Markdown"
            })
            time.sleep(1)

def xu_ly_tin_tuc():
    ngay = datetime.datetime.now().strftime("%d/%m/%Y")
    messages_queue = []
    
    # Header đầu tiên
    messages_queue.append(f"📅 **BÁO CÁO TOÀN CẢNH NGÀY {ngay}**\n_Chế độ: 30 tin/mục - Mô tả chi tiết_")
    
    current_msg = ""
    
    for muc in DANH_MUC:
        header = f"\n➖➖➖➖➖➖➖➖➖➖\n**{muc['ten']}**\n"
        
        # Nếu đang gom dở mà thêm header bị dài quá thì ngắt luôn
        if len(current_msg) + len(header) > 3000:
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
                    
                    # Lọc từ khóa
                    keywords = muc.get('keywords', [])
                    desc_raw = getattr(entry, 'summary', '') or getattr(entry, 'description', '')
                    desc_clean = clean_html(desc_raw) # Lấy toàn bộ mô tả
                    
                    # Kiểm tra từ khóa
                    if keywords:
                        text_check = (entry.title + " " + desc_clean).lower()
                        if not any(k in text_check for k in keywords): continue
                    
                    time_str = convert_time(entry)
                    
                    # Nội dung tin (Title in đậm, Mô tả để thường cho dễ đọc)
                    news_item = f"\n🕒 `{time_str}` | **{entry.title}**\n{desc_clean}\n👉 [Xem chi tiết]({link})\n"
                    
                    # Kiểm tra độ dài an toàn (3500 ký tự để trừ hao)
                    if len(current_msg) + len(news_item) > 3500:
                        messages_queue.append(current_msg)
                        current_msg = news_item # Bắt đầu tin mới
                    else:
                        current_msg += news_item
                    
                    collected_links.add(link)
                    count += 1
            except: pass
            
        if count == 0:
            current_msg += "\n_(Không có dữ liệu phù hợp)_\n"

    # Đẩy nốt phần còn dư
    if current_msg:
        messages_queue.append(current_msg)
        
    return messages_queue

def main():
    if not TELEGRAM_TOKEN:
        print("Chưa cấu hình Token!")
        return
    
    # 1. Dọn dẹp
    don_dep_chat()
    
    # 2. Xử lý
    ds_tin = xu_ly_tin_tuc()
    
    # 3. Gửi
    gui_theo_lo(ds_tin)

if __name__ == "__main__":
    main()
