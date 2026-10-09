import os
import sys
import time
import json
import argparse
from curl_cffi import requests
from bs4 import BeautifulSoup

# 確保在 Windows 控制台下正常輸出 UTF-8 中文字元
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

# ==================== 🛠️ 設定區 🛠️ ====================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HISTORY_FILE = os.path.join(BASE_DIR, "nexon_history.json")
CONFIG_FILE = os.path.join(BASE_DIR, "config_nexon.json")

# 優先讀取環境變數 (供 GitHub Actions 雲端 24H 執行)，其次讀取本機 config_nexon.json
DEFAULT_WEBHOOK = "https://discord.com/api/webhooks/1556595913479159951/KWE_HACS-fjdee1XnOnpbfxU2ba00xk-uXwp9KWk1x4LLqsFWQHAVKrdpfkV93IYpD4m"

def get_webhook_url():
    env_url = os.environ.get("DISCORD_WEBHOOK_URL_NEXON") or os.environ.get("DISCORD_WEBHOOK_URL")
    if env_url:
        return env_url.strip()
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("discord_webhook_url", "").strip() or DEFAULT_WEBHOOK
        except Exception:
            pass
    return DEFAULT_WEBHOOK

# 目標監測網址
URL = "https://nexon.com"
# =====================================================

def load_history():
    if not os.path.exists(HISTORY_FILE):
        return {}
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️ 讀取歷史記錄失敗: {e}")
        return {}

def save_history(history):
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️ 保存歷史記錄失敗: {e}")

def send_to_discord(message):
    """將消息發送到 Discord 頻道的函數"""
    webhook_url = get_webhook_url()
    if "請把你的" in webhook_url or not webhook_url.startswith("https"):
        print("⚠️ 未設定正確的 Discord Webhook URL，跳過發送。")
        return
        
    payload = {
        "content": message
    }
    try:
        response = requests.post(webhook_url, json=payload, timeout=10)
        if response.status_code in (200, 204):
            print("🚀 [Discord] 通知發送成功！")
        else:
            print(f"❌ [Discord] 發送失敗，狀態碼: {response.status_code}")
    except Exception as e:
        print(f"❌ [Discord] 連線異常: {e}")

def check_latest_news():
    """解析網頁並回傳最新訊息"""
    try:
        response = requests.get(URL, impersonate="chrome", timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        valid_links = []
        garbage_keywords = ["terms", "privacy", "使用條款", "隱私權", "nexon", "facebook", "fb", "登入", "登出"]
        
        for a_tag in soup.find_all('a'):
            text = " ".join(a_tag.get_text().split()).strip()
            href = a_tag.get('href', '').strip()
            
            if len(text) > 2 and not any(g in text.lower() for g in garbage_keywords):
                if href and not href.startswith("http"):
                    if href.startswith("/"):
                        href = f"https://nexon.com{href}"
                    else:
                        href = f"https://nexon.com/{href}"
                
                link_info = f"**📢 公告標題**: {text}\n**🔗 傳送門**: {href}"
                if link_info not in valid_links:
                    valid_links.append(link_info)
                    
        if valid_links:
            return valid_links[0]
            
        return "網頁讀取成功，但找不到任何有效的公告超連結。"
            
    except Exception as e:
        return f"【連線異常】: {e}"

def run_once(record_only=False):
    """單次檢查模式 (適合 GitHub Actions 定時執行或工作排程器)"""
    history = load_history()
    last_news = history.get("last_news")
    current_news = check_latest_news()
    
    if current_news and "連線異常" not in current_news:
        if last_news is None or record_only:
            history["last_news"] = current_news
            history["updated_at"] = time.strftime('%Y-%m-%d %H:%M:%S')
            save_history(history)
            print(f"[{time.strftime('%H:%M:%S')}] 初始記錄 Nexon 最新消息成功。")
            if not record_only:
                send_to_discord(f"🤖 **Nexon 官網最新消息監測器已上線！**\n\n當前最新消息：\n{current_news}")
        elif current_news != last_news:
            print("🔥 【📢 偵測到 Nexon 官網內容更新！】 🔥")
            dc_message = f"🔥 【📢 **偵測到全新消息發布！**】 🔥\n\n{current_news}\n\n更新時間: {time.strftime('%Y-%m-%d %H:%M:%S')}"
            send_to_discord(dc_message)
            history["last_news"] = current_news
            history["updated_at"] = time.strftime('%Y-%m-%d %H:%M:%S')
            save_history(history)
        else:
            print(f"[{time.strftime('%H:%M:%S')}] 檢查完畢：Nexon 內容無異動。")
    else:
        print(f"[{time.strftime('%H:%M:%S')}] 檢查時遇到異常，跳過此輪。內容: {current_news}")

def monitor():
    print("====================================")
    print(" 🚀 Discord 連動模式已啟用！開始監測最新消息...")
    print("====================================")
    
    while True:
        run_once()
        # 每 5 分鐘自動檢查一次
        time.sleep(300)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Nexon 官網公告監控腳本")
    parser.add_argument("--once", action="store_true", help="執行單次檢查後立即退出 (適合 GitHub Actions / 排程器)")
    parser.add_argument("--record-only", action="store_true", help="僅登記當前最新消息，不推播通知 (避免首次重複洗版)")
    args = parser.parse_args()

    if args.once:
        run_once(record_only=args.record_only)
    else:
        monitor()
