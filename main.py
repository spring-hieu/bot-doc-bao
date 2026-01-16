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

# Số lượng tin mỗi mục
LIMIT_PER_CAT = 30 
DELETE_LIMIT = 200 

DANH_MUC = [
    {
        "ten": "🌍 TÀI CHÍNH & KINH TẾ THẾ GIỚI",
        "urls": [
            "https://cafef.vn/tai-chinh-quoc-te.rss",
            "https://vnexpress.net/rss/the-gioi.rss",
            "https://vneconomy.vn/timeline/9920/the-gioi.htm",
            "https://bnews.vn/rss/the-gioi.rss"
        ],
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
        "keywords": [
            "vn-index", "vnindex", "hnx", "upcom", "cổ phiếu", "chứng khoán", "thanh khoản",
            "khối ngoại", "tự doanh", "lợi nhuận", "thua lỗ", "báo cáo tài chính", "cổ tức",
            "ngân hàng", "bất động sản", "trái phiếu", "đáo hạn", "vốn hóa", "ipo",
            "nhận định", "phân tích", "khuyến nghị", "bắt đáy", "chốt lời", "margin",
            "hpg", "vcb", "ssi", "vic", "vhm", "fpt", "mwg"
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
        "keywords": [
            "số liệu", "thống kê", "báo cáo", "doanh thu", "lượt khách", "khách quốc tế",
            "khách nội địa", "lữ hành", "hàng không", "vé máy bay", "cục du lịch", "visa",
            "thị thực", "miễn visa", "xu hướng", "công suất phòng", "khách sạn", "resort",
            "du lịch bền vững", "mice", "tăng trưởng", "sụt giảm", "un tourism"
        ]
    }
]

def clean_html(raw_html):
    # --- CẢI TIẾN MỚI ---
    try:
        # Dùng html.parser (có sẵn) để tránh lỗi kén thư viện
        soup = BeautifulSoup(raw_html, "html.parser")
        
        # 1. Hủy diệt các thẻ không mong muốn (Ảnh, Script, Style, Iframe)
        for tag in soup(['script', 'style', 'img', 'iframe', 'video']):
            tag.decompose()
            
        # 2. Lấy text thuần túy
        text = soup.get_text(separator=" ")
        
        # 3. Xử lý khoảng trắng thừa (biến "   abc   " thành "abc")
        text = " ".join(text.split())
        
        # 4. Xóa các cụm từ rác thường gặp ở đầu tin
        garbage_phrases = ["TTO -", "(Dân trí)", "VTV.vn -", "Báo Đầu tư -"]
        for phrase in garbage_phrases:
            text = text.replace(phrase, "")
            
        return text.strip()
    except:
        return "" # Nếu lỗi quá thì trả về rỗng để đỡ rác màn hình

def convert_time(entry):
    try:
        if hasattr(entry, 'published_parsed'):
            dt_utc = datetime.datetime.fromtimestamp(mktime(entry.published_parsed))
            dt_vn = dt_utc + datetime.timedelta(hours=7)
            return dt_vn.strftime("%H:%M")
    except: pass
    return "Mới"

def don_dep_chat():
    print("🧹 Bắt đầu dọn dẹp...")
    url_send = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        resp = requests.post(url_send, json={"chat_id": TELEGRAM_CHAT_ID, "text": "⏳ Đang xử lý dữ liệu..."}).json()
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
        
        # Chia nhỏ nếu quá dài
        if len(msg) > 4000:
            parts = [msg[i:i+4000] for i in range(0, len(msg), 4000)]
            for part in parts:
                requests.post(url, json={
                    "chat_id": TELEGRAM_CHAT_ID, 
                    "text": part, 
                    "disable_web_page_preview": True,
                    "parse_mode": "Markdown"
                })
                time.sleep(1)
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
    messages_queue.append(f"📅 **BẢN TIN NGÀY {ngay}**")
    
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
                    
                    # --- GỌI HÀM LÀM SẠCH MỚI ---
                    desc_clean = clean_html(desc_raw)
                    
                    # Kiểm tra từ khóa
                    if keywords:
                        text_check = (entry.title + " " + desc_clean).lower()
                        if not any(k in text_check for k in keywords): continue
                    
                    time_str = convert_time(entry)
                    
                    # Format tin nhắn gọn gàng: Tiêu đề đậm, Mô tả nghiêng
                    news_item = f"\n🕒 `{time_str}` | **{entry.title}**\n_{desc_clean}_\n👉 [Xem chi tiết]({link})\n"
                    
                    if len(current_msg) + len(news_item) > 3500:
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
    if not TELEGRAM_TOKEN: return
    don_dep_chat()
    ds_tin = xu_ly_tin_tuc()
    gui_theo_lo(ds_tin)

if __name__ == "__main__":
    main()
