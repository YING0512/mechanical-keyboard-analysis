"""
week1_crawler_bahamut.py
從巴哈姆特論壇爬取鍵盤相關討論標題，儲存成 CSV。
"""

import requests
from bs4 import BeautifulSoup
import csv
import time
from datetime import date
import os

# ── 設定常數 ────────────────────────────────────────────────────────────────

# 目標版面（電競周邊版 bsn=60645；若失敗備用電腦硬體板 bsn=60030）
BASE_URLS = [
    "https://forum.gamer.com.tw/B.php?bsn=60645",
    "https://forum.gamer.com.tw/B.php?bsn=60030",
]

# 爬取頁數
MAX_PAGES = 3

# 鍵盤相關關鍵字（篩選用，不分大小寫）
KEYBOARD_KEYWORDS = ["鍵盤", "keyboard", "keycap", "switch", "軸", "熱插拔", "三模", "雙模", "機械"]

# 品牌名單（比對標題）
BRAND_LIST = [
    "Leopold", "Varmilo", "Ducky", "FILCO", "Keychron", "Logitech", "羅技",
    "Razer", "SteelSeries", "HHKB", "Cherry", "Corsair", "ASUS", "華碩",
    "MSI", "微星", "Cooler Master", "Redragon", "Akko", "狼途",
]

# 負面關鍵字
NEGATIVE_KEYWORDS = ["雙擊", "斷線", "延遲", "故障", "瑕疵", "退貨", "壞", "爛", "差評", "有問題"]

# 輸出路徑
OUTPUT_PATH = os.path.join("data", "raw", "bahamut_posts.csv")

# 請求標頭（模擬瀏覽器）
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

# ── 工具函式 ─────────────────────────────────────────────────────────────────

def detect_brand(title):
    """比對品牌名單，傳回第一個符合的品牌名；找不到傳回空字串"""
    for brand in BRAND_LIST:
        if brand.lower() in title.lower():
            return brand
    return ""


def detect_negative(title):
    """偵測標題是否含負面關鍵字；含有傳回 1，否則傳回 0"""
    for word in NEGATIVE_KEYWORDS:
        if word in title:
            return 1
    return 0


def contains_keyboard_keyword(title):
    """判斷標題是否含鍵盤相關關鍵字"""
    lower_title = title.lower()
    for kw in KEYBOARD_KEYWORDS:
        if kw.lower() in lower_title:
            return True
    return False


def make_fake_data(today_str):
    """網站無法存取時，產生 5 筆假資料供後續流程測試"""
    fake_rows = []
    for i in range(1, 6):
        fake_rows.append({
            "title": f"【鍵盤】假資料測試文章 {i}",
            "post_date": today_str,
            "gp_count": 0,
            "reply_count": 0,
            "brand": "",
            "is_negative": 0,
            "source": "bahamut",
            "crawl_date": today_str,
        })
    return fake_rows


# ── 爬取單頁 ──────────────────────────────────────────────────────────────────

def fetch_page(base_url, page_num):
    """
    爬取指定版面的第 page_num 頁，傳回文章列表（list of dict）。
    bsn 版面分頁參數為 &p=N（N 從 1 開始）。
    """
    url = f"{base_url}&p={page_num}"
    try:
        # 發送 GET 請求，附帶 User-Agent 與 timeout
        resp = requests.get(url, headers=HEADERS, timeout=10)
        if resp.status_code != 200:
            print(f"[錯誤] 頁面回傳狀態碼 {resp.status_code}，URL: {url}")
            return None
        return resp.text
    except requests.exceptions.RequestException as e:
        print(f"[錯誤] 連線失敗：{e}")
        return None


def parse_posts(html):
    """
    解析列表頁 HTML，抽取文章標題、日期、推薦數、回應數。
    巴哈論壇列表頁結構：每篇文章在 <tr class="b-list__row"> 內。
    傳回 list of dict。
    """
    posts = []
    soup = BeautifulSoup(html, "html.parser")

    # 嘗試找到文章列表列（巴哈姆特論壇 B 板列表結構）
    rows = soup.select("tr.b-list__row")

    # 若主要選擇器找不到，嘗試備用選擇器
    if not rows:
        rows = soup.select("div.b-list-item")

    if not rows:
        # 再嘗試抓所有 <a class="b-list__main__title"> 的父元素
        title_links = soup.select("a.b-list__main__title")
        if title_links:
            for link in title_links:
                title = link.get_text(strip=True)
                # 無法精確取得其他欄位時用預設值
                posts.append({
                    "title": title,
                    "post_date": "",
                    "gp_count": 0,
                    "reply_count": 0,
                })
            return posts
        # 完全解析失敗
        return posts

    for row in rows:
        try:
            # 取得標題
            title_tag = row.select_one("a.b-list__main__title")
            if not title_tag:
                # 嘗試 fallback 標題選擇器
                title_tag = row.select_one("a[class*='title']")
            if not title_tag:
                continue
            title = title_tag.get_text(strip=True)
            if not title:
                continue

            # 取得發文日期
            date_tag = row.select_one("div.b-list__row__date")
            if not date_tag:
                date_tag = row.select_one("span.b-list__row__date")
            post_date = date_tag.get_text(strip=True) if date_tag else ""

            # 取得推薦數（gp）
            gp_tag = row.select_one("span.b-list__count__like")
            if not gp_tag:
                gp_tag = row.select_one("div.b-list__count__like")
            gp_text = gp_tag.get_text(strip=True) if gp_tag else "0"
            try:
                gp_count = int(gp_text.replace(",", ""))
            except ValueError:
                gp_count = 0

            # 取得回應數
            reply_tag = row.select_one("span.b-list__count__reply")
            if not reply_tag:
                reply_tag = row.select_one("div.b-list__count__reply")
            reply_text = reply_tag.get_text(strip=True) if reply_tag else "0"
            try:
                reply_count = int(reply_text.replace(",", ""))
            except ValueError:
                reply_count = 0

            posts.append({
                "title": title,
                "post_date": post_date,
                "gp_count": gp_count,
                "reply_count": reply_count,
            })

        except Exception as e:
            # 單筆解析失敗不中斷整體流程
            print(f"[警告] 單筆文章解析失敗：{e}")
            continue

    return posts


# ── 主流程 ────────────────────────────────────────────────────────────────────

def main():
    today_str = str(date.today())
    all_posts = []
    success = False

    # 依序嘗試兩個版面 URL，取得資料後即停止
    for base_url in BASE_URLS:
        print(f"[資訊] 嘗試爬取版面：{base_url}")
        board_posts = []

        for page in range(1, MAX_PAGES + 1):
            print(f"  → 爬取第 {page} 頁...")
            html = fetch_page(base_url, page)
            if html is None:
                print(f"  [跳過] 第 {page} 頁取得失敗")
                continue

            # 解析該頁文章
            page_posts = parse_posts(html)
            if page_posts:
                board_posts.extend(page_posts)
                print(f"  → 本頁取得 {len(page_posts)} 筆")
            else:
                print(f"  [警告] 第 {page} 頁解析結果為空，可能是結構變動")

            # 每次請求間隔 3 秒，避免過度請求
            if page < MAX_PAGES:
                time.sleep(3)

        if board_posts:
            all_posts = board_posts
            success = True
            print(f"[資訊] 版面 {base_url} 共取得 {len(all_posts)} 筆，停止嘗試其他版面")
            break

        print(f"[資訊] 版面 {base_url} 無資料，嘗試下一個版面...")
        time.sleep(3)

    # 若完全失敗，改用假資料
    if not success or not all_posts:
        print("[錯誤] 所有版面皆無法取得資料，將使用 5 筆假資料繼續流程")
        rows_to_save = make_fake_data(today_str)
    else:
        # 關鍵字篩選：只保留含鍵盤相關關鍵字的文章
        filtered = [p for p in all_posts if contains_keyboard_keyword(p["title"])]
        if len(filtered) < 10:
            print(f"[說明] 篩選後僅 {len(filtered)} 筆，不足 10 筆，改保留所有 {len(all_posts)} 筆文章（未篩選）")
            filtered = all_posts

        # 加入分析欄位與 metadata
        rows_to_save = []
        for p in filtered:
            rows_to_save.append({
                "title": p["title"],
                "post_date": p["post_date"],
                "gp_count": p["gp_count"],
                "reply_count": p["reply_count"],
                "brand": detect_brand(p["title"]),
                "is_negative": detect_negative(p["title"]),
                "source": "bahamut",
                "crawl_date": today_str,
            })

    # 確保輸出目錄存在
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

    # 寫入 CSV 檔案
    fieldnames = ["title", "post_date", "gp_count", "reply_count", "brand", "is_negative", "source", "crawl_date"]
    with open(OUTPUT_PATH, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows_to_save)

    # 統計負面關鍵字數量並印出結果
    negative_count = sum(1 for r in rows_to_save if r["is_negative"] == 1)
    print(f"\n已爬取 {len(rows_to_save)} 筆文章標題，其中 {negative_count} 筆含負面關鍵字")
    print(f"資料已儲存至：{OUTPUT_PATH}")


if __name__ == "__main__":
    main()
