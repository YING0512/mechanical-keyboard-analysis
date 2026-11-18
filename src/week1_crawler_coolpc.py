"""
week1_crawler_coolpc.py
爬取原價屋 evaluate.php 中鍵盤類商品的品名與價格，存入 CSV。
"""

import requests
from bs4 import BeautifulSoup
import csv
import re
import os
from datetime import date

# ── 設定常數 ──────────────────────────────────────────────
TARGET_URL = "https://www.coolpc.com.tw/evaluate.php"
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "coolpc_keyboards.csv")
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}
TODAY = date.today().strftime("%Y-%m-%d")


# ── 步驟 1：取得頁面 HTML ─────────────────────────────────
def fetch_html(url):
    """發送 GET 請求並回傳原始 HTML 文字；失敗時回傳 None。"""
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.encoding = "utf-8"
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"[錯誤] 無法連線至 {url}：{e}")
        return None


# ── 步驟 2：從 HTML 解析鍵盤 option 清單 ─────────────────
def parse_keyboards(html):
    """
    解析 HTML，尋找 label 含「鍵盤」的 <optgroup>，
    取出其下所有 <option> 的文字與 value。
    若找不到 optgroup，改用關鍵字搜尋備案。
    """
    soup = BeautifulSoup(html, "html.parser")
    items = []

    # 優先策略：找含「鍵盤」的 optgroup
    keyboard_group = None
    for og in soup.find_all("optgroup"):
        label = og.get("label", "")
        if "鍵盤" in label or "keyboard" in label.lower():
            keyboard_group = og
            break

    if keyboard_group:
        # 取出該 optgroup 下每一個 option
        for opt in keyboard_group.find_all("option"):
            text = opt.get_text(strip=True)
            value = opt.get("value", "")
            items.append((text, value))
    else:
        # 備案策略：在所有 option 中搜尋含鍵盤關鍵字的項目
        print("[提示] 找不到鍵盤 optgroup，改用關鍵字備案策略")
        for opt in soup.find_all("option"):
            text = opt.get_text(strip=True)
            if "鍵盤" in text or "keyboard" in text.lower():
                value = opt.get("value", "")
                items.append((text, value))

    return items


# ── 步驟 3：從商品文字中解析價格 ─────────────────────────
def extract_price(text, value=""):
    """
    優先從 value 屬性找 3-5 位數字，
    若無則從商品名稱 text 找；有多個取最後一個。
    找不到則回傳 None。
    """
    # 先嘗試從 value 欄位抓（原價屋 value 通常直接就是整數價格）
    if value.strip().lstrip("-").isdigit():
        v = int(value.strip())
        if v > 0:
            return v

    # 再從名稱文字中用正規表示式抓 3~5 位數字
    matches = re.findall(r"\d{3,5}", text)
    if matches:
        return int(matches[-1])

    return None


# ── 步驟 4：將資料存成 CSV ───────────────────────────────
def save_to_csv(records, filepath):
    """將 records（list of dict）寫入 CSV 檔案。"""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["product_name", "price_twd", "source", "crawl_date"])
        writer.writeheader()
        writer.writerows(records)


# ── 步驟 5：備案 — 若無法取得頁面則使用假資料測試 ────────
def load_sample_html():
    """
    若網路不通或網站結構變更，讀取本地 sample_coolpc.html 作為備案。
    若備案 HTML 也不存在，建立一份最小化的假資料供測試。
    """
    sample_path = os.path.join(os.path.dirname(__file__), "..", "sample_coolpc.html")

    if os.path.exists(sample_path):
        print("[備案] 使用本地 sample_coolpc.html")
        with open(sample_path, encoding="utf-8") as f:
            return f.read()

    # 建立最小化假資料
    print("[備案] 找不到 sample_coolpc.html，產生內建假資料供測試")
    sample_html = """
    <html><body>
    <select>
      <optgroup label="鍵盤 Keyboard">
        <option value="1290">Cherry MX Board 3.0S TKL 青軸 1,290元</option>
        <option value="2490">Corsair K70 RGB MK.2 銀軸 2,490元</option>
        <option value="1890">Ducky One 3 SF 茶軸 1,890元</option>
        <option value="3290">Leopold FC900R PD 靜音紅軸 3,290元</option>
        <option value="990">Akko 3068B Plus 青軸 990元</option>
        <option value="-1">── 以下缺貨 ──</option>
        <option value="2190">Filco Majestouch 2 TKL 茶軸 2,190元</option>
      </optgroup>
    </select>
    </body></html>
    """
    # 同時寫入磁碟以便下次直接讀取
    with open(sample_path, "w", encoding="utf-8") as f:
        f.write(sample_html)
    return sample_html


# ── 主程式 ───────────────────────────────────────────────
def main():
    # 嘗試爬取原價屋頁面
    print(f"[開始] 爬取 {TARGET_URL}")
    html = fetch_html(TARGET_URL)

    # 若取得失敗，改用備案 HTML
    if html is None:
        print("[警告] 無法取得線上頁面，切換備案模式")
        html = load_sample_html()

    # 解析鍵盤品項
    raw_items = parse_keyboards(html)

    if not raw_items:
        print("[警告] 解析結果為空，請檢查網站結構是否變更")
        html = load_sample_html()
        raw_items = parse_keyboards(html)

    # 組裝最終紀錄，過濾掉分隔行（value 為負數或文字為 ──）
    records = []
    for text, value in raw_items:
        # 跳過分隔用的假選項
        if text.startswith("──") or text.startswith("--") or not text:
            continue
        price = extract_price(text, value)
        records.append({
            "product_name": text,
            "price_twd": price,
            "source": "coolpc",
            "crawl_date": TODAY,
        })

    # 儲存 CSV
    abs_output = os.path.abspath(OUTPUT_FILE)
    save_to_csv(records, abs_output)

    # 印出結果摘要
    print(f"已成功爬取 {len(records)} 筆資料，已存入 data/raw/coolpc_keyboards.csv")


if __name__ == "__main__":
    main()
