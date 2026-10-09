#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
跑跑卡丁車官方網站 (https://popkart.tiancity.com/homepage/v3/)
新聞公告抓取與 Discord Webhook 即時通知腳本
"""

import sys
import os
import time
import json
import logging
import argparse
import requests
from datetime import datetime, timezone
from bs4 import BeautifulSoup

# 確保在 Windows 控制台下正常輸出 UTF-8 中文字元
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("notifier.log", encoding="utf-8")
    ]
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")
HISTORY_FILE = os.path.join(BASE_DIR, "history.json")

# 官網新聞資料 API (首頁 v3 動態引用的來源)
NEWS_API_URL = "https://evt06.tiancity.com/portal/news/home/index.php?game=kart"
DEFAULT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://popkart.tiancity.com/'
}

# 各公告分類在 Discord Embed 顯示的邊框顏色
CATEGORY_COLORS = {
    "系统公告": 0xE74C3C,  # 紅色
    "游戏新闻": 0x3498DB,  # 藍色
    "活动公告": 0xF39C12,  # 橙黃色
    "赛事专题": 0x9B59B6,  # 紫色
}
DEFAULT_COLOR = 0x1ABC9C     # 預設青綠色


def load_config():
    """載入本機設定，並以環境變數覆蓋部署設定。"""
    default_config = {
        "discord_webhook_url": "", "check_interval_seconds": 300,
        "fetch_article_preview": True, "first_run_behavior": "record_only",
        "mention_role_id": "",
        "notify_categories": ["系统公告", "游戏新闻", "活动公告", "赛事专题"]
    }
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(default_config, f, ensure_ascii=False, indent=2)
        config = default_config
    else:
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
        except Exception as e:
            logging.error(f"讀取設定檔失敗: {e}")
            config = default_config.copy()
    for env_name, config_name in (
        ("DISCORD_WEBHOOK_URL", "discord_webhook_url"),
        ("DISCORD_MENTION_ROLE_ID", "mention_role_id"),
    ):
        if env_name in os.environ:
            config[config_name] = os.environ[env_name]
    return config


def load_history():
    """載入已通知過的新聞歷史記錄"""
    if not os.path.exists(HISTORY_FILE):
        return {}
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logging.warning(f"讀取歷史記錄失敗或檔案毀損，將重新建立: {e}")
        return {}


def save_history(history):
    """保存已通知過的新聞歷史記錄"""
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logging.error(f"保存歷史記錄失敗: {e}")
        return False


def fetch_latest_news():
    """
    抓取官網首頁的新聞公告資料。
    該接口返回包含最新公告 (qb)、系統 (xt)、新聞 (yx)、活動 (gg)、賽事 (ss) 的資料。
    """
    try:
        resp = requests.get(NEWS_API_URL, headers=DEFAULT_HEADERS, timeout=15)
        resp.raise_for_status()
        text = resp.text

        # 世紀天成此接口在 PHP 環境下可能會先輸出報錯文本，最後才附加 ({"qb":[...]})
        # 我們定位最後出現的 {"qb": 並解析 JSON
        idx = text.rfind('{"qb":')
        if idx == -1:
            logging.error("未在回應中找到 {\"qb\": 開頭的 JSON 資料")
            return None

        end_idx = text.rfind('}')
        if end_idx == -1 or end_idx < idx:
            logging.error("JSON 結尾括號格式不正確")
            return None

        json_str = text[idx:end_idx + 1]
        data = json.loads(json_str)

        # qb 包含所有最新新聞公告綜合列表
        items = data.get("qb", [])
        return items

    except Exception as e:
        logging.error(f"抓取最新新聞失敗: {e}")
        return None


def fetch_article_preview(article_url):
    """抓取單篇公告的內容預覽（前 250 字左右）"""
    if not article_url or not article_url.startswith("http"):
        return ""
    try:
        resp = requests.get(article_url, headers=DEFAULT_HEADERS, timeout=10)
        resp.raise_for_status()
        # 網頁編碼可能為 utf-8 或 gbk
        soup = BeautifulSoup(resp.content, "html.parser")
        article_div = soup.find("div", class_="article")
        if article_div:
            text = article_div.get_text(separator=" ", strip=True)
            text = " ".join(text.split())
            if len(text) > 250:
                return text[:250] + "..."
            return text
    except Exception as e:
        logging.debug(f"抓取文章預覽失敗 [{article_url}]: {e}")
    return ""


def send_discord_webhook(webhook_url, item, preview_text="", mention_role_id=""):
    """
    發送 Discord Webhook 通知
    使用 Rich Embed 呈現標題、連結、分類、發布時間與內文摘要
    """
    if not webhook_url or not webhook_url.startswith("https://discord.com/api/webhooks/"):
        logging.warning("尚未設定有效的 Discord Webhook URL，跳過發送。")
        return False

    title = item.get("title", "無標題")
    href = item.get("tit_href", "https://popkart.tiancity.com/homepage/v3/")
    cat = item.get("cat", "新聞公告")
    dat = item.get("dat", datetime.now().strftime("%Y-%m-%d"))

    color = CATEGORY_COLORS.get(cat, DEFAULT_COLOR)

    embed = {
        "title": f"📢 【{cat}】{title}",
        "url": href,
        "color": color,
        "fields": [
            {
                "name": "📌 發布日期",
                "value": dat,
                "inline": True
            },
            {
                "name": "🏷️ 分類",
                "value": cat,
                "inline": True
            }
        ],
        "footer": {
            "text": "跑跑卡丁車官方網站公告監控 • 世紀天成",
            "icon_url": "https://popkart.tiancity.com/homepage/v3/favicon.ico"
        },
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    if preview_text:
        embed["description"] = preview_text

    content = ""
    if mention_role_id:
        if mention_role_id.lower() == "everyone":
            content = "@everyone"
        elif mention_role_id.lower() == "here":
            content = "@here"
        else:
            content = f"<@&{mention_role_id}>"

    payload = {
        "username": "跑跑卡丁車官網公告",
        "avatar_url": "https://popkart.tiancity.com/homepage/v3/favicon.ico",
        "embeds": [embed]
    }
    if content:
        payload["content"] = content
        if mention_role_id.lower() in ("everyone", "here"):
            payload["allowed_mentions"] = {"parse": ["everyone"]}
        else:
            payload["allowed_mentions"] = {
                "parse": ["roles"], "roles": [mention_role_id]
            }

    for attempt in range(3):
        try:
            resp = requests.post(webhook_url, json=payload, timeout=10)
            if resp.status_code == 204:
                logging.info(f"✅ Discord 通知發送成功: [{cat}] {title}")
                return True
            elif resp.status_code == 429:
                retry_after = resp.json().get("retry_after", 2)
                logging.warning(f"Discord 速率限制，等待 {retry_after} 秒後重試...")
                time.sleep(retry_after)
            else:
                logging.error(f"Discord Webhook 發送失敗 (HTTP {resp.status_code}): {resp.text}")
                return False
        except Exception as e:
            logging.error(f"發送 Discord Webhook 連線失敗 (嘗試 {attempt + 1}/3): {e}")
            time.sleep(2)

    return False


def send_test_message(webhook_url):
    """發送測試訊息以確認 Discord Webhook 連線狀態"""
    logging.info("發送測試訊息至 Discord...")
    test_item = {
        "title": "測試通知：跑跑卡丁車官網公告監控已就緒",
        "tit_href": "https://popkart.tiancity.com/homepage/v3/",
        "cat": "系統公告",
        "dat": datetime.now().strftime("%Y-%m-%d")
    }
    preview = "這是一則測試訊息，當跑跑卡丁車官方網站有發布任何新公告或新聞時，機器人將會自動在此頻道推播通知！"
    return send_discord_webhook(webhook_url, test_item, preview_text=preview)


def check_and_notify(config, history, record_only=False):
    """執行一次新聞檢查與通知"""
    webhook_url = config.get("discord_webhook_url", "").strip()
    fetch_preview = config.get("fetch_article_preview", True)
    allowed_categories = set(config.get("notify_categories", ["系统公告", "游戏新闻", "活动公告", "赛事专题"]))
    mention_role_id = config.get("mention_role_id", "").strip()
    first_run_behavior = config.get("first_run_behavior", "record_only")

    news_list = fetch_latest_news()
    if news_list is None:
        logging.error("本次檢查未取得有效公告資料。")
        return False
    if not news_list:
        logging.info("本次檢查沒有最新公告。")
        return True

    is_first_run = (len(history) == 0)
    new_items = []

    # 按照時間由舊到新排序（讓 Discord 通知按順序發送）
    for item in reversed(news_list):
        href = item.get("tit_href", "").strip()
        cat = item.get("cat", "").strip()
        title = item.get("title", "").strip()

        if not href:
            continue

        # 類別過濾
        if cat and cat not in allowed_categories:
            continue

        if href not in history:
            new_items.append(item)

    if record_only:
        logging.info("首次雲端執行：只登記目前公告，不推播。")
        for item in news_list:
            href = item.get("tit_href", "").strip()
            if href:
                history[href] = {
                    "title": item.get("title"),
                    "cat": item.get("cat"),
                    "dat": item.get("dat"),
                    "recorded_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
        if not save_history(history):
            return False
        logging.info(f"現有 {len(history)} 篇公告記錄完成。")
        return True

    if is_first_run:
        logging.info(f"第一次啟動程式，偵測到 {len(news_list)} 篇現有公告。")
        if first_run_behavior == "record_only":
            logging.info("依設定（record_only），將現有公告存入紀錄庫，不重複推播歷史訊息。")
            for item in news_list:
                href = item.get("tit_href", "").strip()
                if href:
                    history[href] = {
                        "title": item.get("title"),
                        "cat": item.get("cat"),
                        "dat": item.get("dat"),
                        "recorded_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
            if not save_history(history):
                return False
            logging.info(f"現有 {len(history)} 篇公告記錄完成，後續發布新文章時將會推播通知。")
            return True

    if not new_items:
        logging.info("檢查完成：暫無新的公告發布。")
        return True

    logging.info(f"發現 {len(new_items)} 篇新公告！開始發送 Discord 通知...")

    for item in new_items:
        href = item.get("tit_href", "")
        preview = ""
        if fetch_preview:
            preview = fetch_article_preview(href)

        success = send_discord_webhook(webhook_url, item, preview_text=preview, mention_role_id=mention_role_id)
        if not success:
            logging.error(f"通知失敗，保留公告以便下次重試：{href}")
            return False
        if success:
            history[href] = {
                "title": item.get("title"),
                "cat": item.get("cat"),
                "dat": item.get("dat"),
                "recorded_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            if not save_history(history):
                return False

        # 適度間隔，避免觸發 Discord 限制
        time.sleep(1.5)

    return True


def main():
    parser = argparse.ArgumentParser(description="跑跑卡丁車官網公告監控與 Discord 通知機器人")
    parser.add_argument("--once", action="store_true", help="只執行一次檢查後退出（適用於定時排程工作）")
    parser.add_argument("--record-only", action="store_true", help="只登記目前公告，不發送通知")
    parser.add_argument("--test", action="store_true", help="發送一則測試通知到 Discord 驗證 Webhook 設定")
    parser.add_argument("--reset", action="store_true", help="清空歷史記錄檔 (history.json)")
    args = parser.parse_args()

    config = load_config()
    history = load_history()

    if args.reset:
        if os.path.exists(HISTORY_FILE):
            os.remove(HISTORY_FILE)
            logging.info("已清空歷史記錄 (history.json)。")
        return

    webhook_url = config.get("discord_webhook_url", "").strip()

    if args.test:
        if not webhook_url:
            logging.error("請先在 config.json 中的 'discord_webhook_url' 填入您的 Discord Webhook 網址！")
            return
        success = send_test_message(webhook_url)
        if success:
            logging.info("🎉 測試通知發送成功！請查看您的 Discord 頻道。")
        else:
            logging.error("❌ 測試通知發送失敗，請確認 Webhook 網址是否正確。")
        return

    if not webhook_url:
        logging.warning("⚠️  尚未在 config.json 設定 'discord_webhook_url'！")
        logging.warning("請編輯 config.json 填入您的 Webhook 網址後重啟，目前將僅執行抓取而不發送通知。")

    if args.once:
        if not webhook_url.startswith("https://discord.com/api/webhooks/"):
            logging.error("單次監控需要有效 Webhook，請設定 DISCORD_WEBHOOK_URL。")
            return 1
        logging.info("執行單次公告檢查...")
        return 0 if check_and_notify(config, history, record_only=args.record_only) else 1

    interval = config.get("check_interval_seconds", 300)
    logging.info(f"🚀 跑跑卡丁車官網公告監控已啟動！")
    logging.info(f"每 {interval} 秒（約 {interval // 60} 分鐘）檢查一次最新公告...")
    logging.info("按 Ctrl+C 可停止程式運行。\n")

    try:
        while True:
            logging.info("🔍 開始檢查官網公告...")
            check_and_notify(config, history)
            logging.info(f"⏳ 等待 {interval} 秒後進行下一次檢查...\n")
            time.sleep(interval)
    except KeyboardInterrupt:
        logging.info("使用者中斷，程式安全停止。")


if __name__ == "__main__":
    sys.exit(main())
