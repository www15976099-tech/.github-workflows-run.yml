import os
import json
import time
import requests

TG_TOKEN = os.environ.get("TG_TOKEN")
TG_CHAT_ID = os.environ.get("TG_CHAT_ID")
TARGET_URL = "https://lastchancetoy.com"
DB_FILE = "checked_toys_with_img.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def check_env():
    """檢查 GitHub Secrets 保險箱有沒有順利把鑰匙交給 Python"""
    print("=== 正在檢查 GitHub Secrets 環境變數 ===")
    if not TG_TOKEN:
        print("❌ 錯誤：找不到 TG_TOKEN！請檢查 GitHub 倉庫的 Settings -> Secrets 中有沒有拼錯字。")
        exit(2)
    else:
        print(f"✅ 成功找到 TG_TOKEN (前4碼為: {TG_TOKEN[:4]}...)")
        
    if not TG_CHAT_ID:
        print("❌ 錯誤：找不到 TG_CHAT_ID！請檢查 GitHub 倉庫的 Settings -> Secrets 中有沒有拼錯字。")
        exit(2)
    else:
        print(f"✅ 成功找到 TG_CHAT_ID (內容為: {TG_CHAT_ID})")
    print("=======================================\n")

def send_telegram_with_photo(photo_url, caption):
    url = f"https://telegram.org{TG_TOKEN}/sendPhoto"
    payload = {"chat_id": TG_CHAT_ID, "photo": photo_url, "caption": caption, "parse_mode": "Markdown"}
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code != 200:
            print(f"⚠️ 圖片通知發送失敗，原因: {response.text}")
            send_telegram_text(caption)
    except Exception as e:
        print(f"❌ 發送圖文通知時發生崩潰: {e}")

def send_telegram_text(text):
    url = f"https://telegram.org{TG_TOKEN}/sendMessage"
    payload = {"chat_id": TG_CHAT_ID, "text": text, "parse_mode": "Markdown"}
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code != 200:
            print(f"❌ 純文字通知也發送失敗，原因: {response.text}")
    except Exception as e:
        print(f"❌ 發送純文字通知時發生崩潰: {e}")

def load_history():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except:
                return []
    return []

def save_history(history):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=4)

def check_new_goods():
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 開始掃描玩具店網頁...")
    try:
        response = requests.get(f"{TARGET_URL}?limit=15", headers=HEADERS, timeout=15)
        if response.status_code != 200:
            print(f"❌ 網頁請求失敗，目標網站返回了狀態碼: {response.status_code}")
            exit(2)
            
        data = response.json()
        products = data.get("products", [])
        if not products:
            print("❌ 網頁請求成功，但 Shopify 沒有回傳任何商品數據。")
            return

        history = load_history()
        is_first_run = (len(history) == 0)
        new_items_found = False

        for prod in products:
            title = prod.get("title")
            handle = prod.get("handle")
            prod_id = str(prod.get("id"))
            link = f"https://lastchancetoy.com{handle}"
            
            variants = prod.get("variants", [])
            price = variants[0].get("price") if variants else "未提供"
            
            images = prod.get("images", [])
            photo_url = images[0].get("src") if images else None

            if prod_id not in history:
                history.append(prod_id)
                new_items_found = True
                
                if not is_first_run:
                    msg = f"🚨 *【孤注一扭】發現全新商品上架！*\n\n" \
                          f"【品名】: {title}\n" \
                          f"【價格】: ${price}\n\n" \
                          f"🔗 [點擊立刻前往預購/購買]({link})"
                    
                    if photo_url:
                        send_telegram_with_photo(photo_url, msg)
                    else:
                        send_telegram_text(msg)

        if new_items_found:
            save_history(history)
            print("🎉 掃描完成：發現新商品並成功更新歷史紀錄！")
        else:
            print("☕ 掃描完成：目前網站沒有任何新商品上架。")

    except Exception as e:
        print(f"❌ 爬蟲核心邏輯發生崩潰，詳細錯誤訊息: {e}")
        exit(2)

if __name__ == "__main__":
    check_env()      # 先檢查保險箱密碼
    check_new_goods() # 再開始爬蟲
