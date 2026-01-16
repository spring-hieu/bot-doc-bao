import requests
from bs4 import BeautifulSoup
import datetime

# --- THAY THÔNG TIN CỦA ÔNG VÀO 2 DÒNG DƯỚI ---
TOKEN = "8102540158:AAEwx9ncov_fdECCtBb5tsUhlrWQgsGu-WM" 
CHAT_ID = "7360846401" 
# Ví dụ: CHAT_ID = "123456789" (Nhớ để trong dấu ngoặc kép)

def gui_tin_nhan(noi_dung):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": noi_dung, "parse_mode": "Markdown"}
    requests.post(url, json=data)

def lay_tin_vnexpress():
    try:
        # Lấy tin từ VnExpress
        r = requests.get("https://vnexpress.net/tin-tuc-24h")
        soup = BeautifulSoup(r.text, 'html.parser')
        
        # Lấy 5 tin đầu tiên
        list_news = []
        articles = soup.find_all('h3', class_='title-news', limit=5)
        
        for art in articles:
            a_tag = art.find('a')
            title = a_tag.text.strip()
            link = a_tag['href']
            list_news.append(f"🔹 [{title}]({link})")
            
        return "\n".join(list_news)
    except:
        return "Lỗi lấy tin VnExpress rồi!"

def main():
    ngay_hom_nay = datetime.datetime.now().strftime("%d/%m/%Y")
    
    # Lấy nội dung
    tin_tuc = lay_tin_vnexpress()
    
    # Soạn tin nhắn
    noi_dung_gui = f"📅 **Bản tin ngày {ngay_hom_nay}**\n\n{tin_tuc}\n\nChúc ngày mới vui vẻ!"
    
    # Gửi
    gui_tin_nhan(noi_dung_gui)
    print("Đã gửi tin nhắn xong!")

if __name__ == "__main__":
    main()
