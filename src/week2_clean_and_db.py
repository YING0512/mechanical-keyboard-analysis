"""
Week 2 — 資料清理與 SQLite 資料庫模組
負責：讀取原始 CSV → 清理 → 擷取規格 → 存 CSV → 建 DB → 匯入資料 → 驗證查詢
"""

import os
import re
import sqlite3
import pandas as pd
from datetime import date

# ─── 路徑設定 ───────────────────────────────────────────────────────────────
BASE_DIR      = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_CSV       = os.path.join(BASE_DIR, "data", "raw",       "coolpc_keyboards.csv")
POSTS_CSV     = os.path.join(BASE_DIR, "data", "raw",       "bahamut_posts.csv")
CLEANED_CSV   = os.path.join(BASE_DIR, "data", "processed", "products_cleaned.csv")
DB_PATH       = os.path.join(BASE_DIR, "data", "keyboards.db")


# ─── 假資料（當原始 CSV 不存在時使用）───────────────────────────────────────
SAMPLE_DATA = [
    {"product_name": "Keychron K3 Pro 75% 三模熱插拔 RGB 光軸 NT$2,990",  "price_twd": 2990, "source": "sample", "crawl_date": str(date.today())},
    {"product_name": "Keychron K2 Pro 75% 三模熱插拔 茶軸 NT$2,490",       "price_twd": 2490, "source": "sample", "crawl_date": str(date.today())},
    {"product_name": "Ducky One 3 TKL 青軸 RGB 有線 NT$3,200",            "price_twd": 3200, "source": "sample", "crawl_date": str(date.today())},
    {"product_name": "Leopold FC660M 65% 靜音紅軸 有線 NT$2,800",         "price_twd": 2800, "source": "sample", "crawl_date": str(date.today())},
    {"product_name": "Akko 3068B Plus 60% 雙模熱插拔 RGB 磁軸 NT$1,290", "price_twd": 1290, "source": "sample", "crawl_date": str(date.today())},
    {"product_name": "Cherry MX Board 3.0S TKL 黑軸 NT$2,100",           "price_twd": 2100, "source": "sample", "crawl_date": str(date.today())},
    {"product_name": "Filco Majestouch 2 100% 茶軸 有線 NT$3,500",        "price_twd": 3500, "source": "sample", "crawl_date": str(date.today())},
    {"product_name": "HHKB Professional HYBRID 60% 無線 NT$5,800",        "price_twd": 5800, "source": "sample", "crawl_date": str(date.today())},
    {"product_name": "Corsair K70 RGB Pro 100% 紅軸 熱插拔 有線 NT$4,200", "price_twd": 4200, "source": "sample", "crawl_date": str(date.today())},
    {"product_name": "Razer BlackWidow V3 TKL 青軸 RGB 有線 NT$3,800",   "price_twd": 3800, "source": "sample", "crawl_date": str(date.today())},
]


# ════════════════════════════════════════════════════════════════════════════
# 第一部分：清理產品資料
# ════════════════════════════════════════════════════════════════════════════

def extract_features(product_name: str) -> dict:
    """從單一 product_name 字串擷取規格欄位，回傳 dict。"""

    # --- switch_type：判斷軸體類型 ---
    switch_map = ["磁軸", "光軸", "青軸", "紅軸", "茶軸", "黑軸"]
    switch_type = None
    for sw in switch_map:
        if sw in product_name:
            switch_type = sw
            break
    if switch_type is None and "軸" in product_name:
        switch_type = "其他機械軸"

    # --- connect_mode：判斷連線方式 ---
    if "三模" in product_name:
        connect_mode = "三模"
    elif "雙模" in product_name:
        connect_mode = "雙模"
    elif "無線" in product_name:
        connect_mode = "無線"
    elif "有線" in product_name:
        connect_mode = "有線"
    else:
        # 不含任何無線/三模/雙模關鍵字，預設有線
        connect_mode = "有線"

    # --- hot_swap：是否熱插拔 ---
    hot_swap = 1 if "熱插拔" in product_name else 0

    # --- rgb：是否有 RGB（不分大小寫）---
    rgb = 1 if re.search(r"rgb", product_name, re.IGNORECASE) else 0

    # --- layout：配列（正規表示式比對百分比或 TKL）---
    layout_pattern = r"(100%|96%|80%|75%|65%|60%|TKL)"
    layout_match = re.search(layout_pattern, product_name, re.IGNORECASE)
    layout = layout_match.group(1).upper() if layout_match else None

    return {
        "switch_type":  switch_type,
        "connect_mode": connect_mode,
        "hot_swap":     hot_swap,
        "rgb":          rgb,
        "layout":       layout,
    }


def clean_product_data() -> pd.DataFrame:
    """讀取原始 CSV，清理資料，擷取規格欄位，回傳清理後 DataFrame。"""

    # 讀取原始 CSV；若不存在則使用假資料
    if os.path.exists(RAW_CSV):
        print(f"[Week2] 讀取原始資料：{RAW_CSV}")
        df = pd.read_csv(RAW_CSV)
    else:
        print("[Week2] 原始 CSV 不存在，使用假資料進行測試")
        df = pd.DataFrame(SAMPLE_DATA)

    # 刪除 product_name 為空值的列
    df = df.dropna(subset=["product_name"])

    # 去除 product_name 前後空白
    df["product_name"] = df["product_name"].str.strip()

    # price_twd 轉為整數，無法轉換的填 0
    def to_int(val):
        try:
            return int(val)
        except (ValueError, TypeError):
            return 0

    df["price_twd"] = df["price_twd"].apply(to_int)

    # 擷取規格欄位（逐列呼叫 extract_features）
    features_list = []
    for name in df["product_name"]:
        features_list.append(extract_features(name))
    features_df = pd.DataFrame(features_list, index=df.index)

    # 合併規格欄位到主 DataFrame
    for col in ["switch_type", "connect_mode", "hot_swap", "rgb", "layout"]:
        df[col] = features_df[col]

    # 確保必要欄位存在（若原始 CSV 缺欄）
    if "source" not in df.columns:
        df["source"] = "coolpc"
    if "crawl_date" not in df.columns:
        df["crawl_date"] = str(date.today())

    # 只保留指定欄位，依序排列
    output_cols = ["product_name", "price_twd", "switch_type", "connect_mode",
                   "hot_swap", "rgb", "layout", "source", "crawl_date"]
    df = df[output_cols].reset_index(drop=True)

    # 儲存清理後資料到 data/processed/products_cleaned.csv
    os.makedirs(os.path.dirname(CLEANED_CSV), exist_ok=True)
    df.to_csv(CLEANED_CSV, index=False, encoding="utf-8-sig")
    print(f"[Week2] 清理後資料已存入：{CLEANED_CSV}（共 {len(df)} 筆）")

    return df


# ════════════════════════════════════════════════════════════════════════════
# 第二部分：建立 SQLite 資料庫
# ════════════════════════════════════════════════════════════════════════════

def setup_database(conn: sqlite3.Connection) -> None:
    """建立三張資料表（若已存在則跳過）。"""

    cursor = conn.cursor()

    # 建立 products 主表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            product_id  INTEGER PRIMARY KEY AUTOINCREMENT,
            brand       TEXT,
            model       TEXT,
            product_name TEXT,
            price_twd   INTEGER,
            source      TEXT,
            crawl_date  TEXT
        )
    """)

    # 建立 product_features 規格表（與 products 一對一，外鍵關聯）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS product_features (
            product_id   INTEGER PRIMARY KEY,
            switch_type  TEXT,
            layout       TEXT,
            connect_mode TEXT,
            hot_swap     INTEGER,
            rgb          INTEGER,
            FOREIGN KEY (product_id) REFERENCES products(product_id)
        )
    """)

    # 建立 posts 論壇標題表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            post_id      INTEGER PRIMARY KEY AUTOINCREMENT,
            title        TEXT,
            post_date    TEXT,
            gp_count     INTEGER,
            reply_count  INTEGER,
            brand        TEXT,
            is_negative  INTEGER
        )
    """)

    conn.commit()
    print("[Week2] 資料庫資料表建立完成（products / product_features / posts）")


def import_data(conn: sqlite3.Connection, df: pd.DataFrame) -> None:
    """將清理後 DataFrame 匯入 products 與 product_features 資料表。"""

    cursor = conn.cursor()

    # 匯入前先清空舊資料（避免重複執行時重複插入）
    cursor.execute("DELETE FROM product_features")
    cursor.execute("DELETE FROM products")
    conn.commit()

    # 逐列插入 products 與 product_features
    for _, row in df.iterrows():
        # 插入 products 主表（brand 與 model 先填空字串）
        cursor.execute("""
            INSERT INTO products (brand, model, product_name, price_twd, source, crawl_date)
            VALUES (?, ?, ?, ?, ?, ?)
        """, ("", "", row["product_name"], int(row["price_twd"]),
              str(row.get("source", "")), str(row.get("crawl_date", ""))))

        # 取得剛插入的 product_id
        product_id = cursor.lastrowid

        # 插入 product_features 規格表
        cursor.execute("""
            INSERT INTO product_features (product_id, switch_type, layout, connect_mode, hot_swap, rgb)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (product_id,
              row["switch_type"] if pd.notna(row["switch_type"]) else None,
              row["layout"]      if pd.notna(row["layout"])      else None,
              row["connect_mode"] if pd.notna(row["connect_mode"]) else None,
              int(row["hot_swap"]),
              int(row["rgb"])))

    conn.commit()
    print(f"[Week2] 已匯入 {len(df)} 筆產品資料到 products & product_features")

    # 若 bahamut_posts.csv 存在，匯入 posts 資料表
    if os.path.exists(POSTS_CSV):
        try:
            posts_df = pd.read_csv(POSTS_CSV)
            cursor.execute("DELETE FROM posts")
            for _, row in posts_df.iterrows():
                cursor.execute("""
                    INSERT INTO posts (title, post_date, gp_count, reply_count, brand, is_negative)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (str(row.get("title", "")),
                      str(row.get("post_date", "")),
                      int(row.get("gp_count", 0)),
                      int(row.get("reply_count", 0)),
                      str(row.get("brand", "")),
                      int(row.get("is_negative", 0))))
            conn.commit()
            print(f"[Week2] 已匯入 {len(posts_df)} 筆論壇標題到 posts")
        except Exception as e:
            print(f"[Week2] 匯入 posts 資料時發生錯誤：{e}")
    else:
        print(f"[Week2] 找不到 {POSTS_CSV}，跳過 posts 匯入")


# ════════════════════════════════════════════════════════════════════════════
# 驗證查詢
# ════════════════════════════════════════════════════════════════════════════

def run_verification_queries(conn: sqlite3.Connection) -> None:
    """執行驗證查詢並印出結果。"""

    cursor = conn.cursor()

    # 查詢 products 總筆數
    cursor.execute("SELECT COUNT(*) FROM products")
    count = cursor.fetchone()[0]
    print(f"\n[驗證] products 總筆數：{count}")

    # 依連線方式分群計數（JOIN product_features）
    print("\n[驗證] 各連線方式的產品數量：")
    cursor.execute("""
        SELECT connect_mode, COUNT(*)
        FROM products
        JOIN product_features USING(product_id)
        GROUP BY connect_mode
    """)
    for row in cursor.fetchall():
        print(f"  connect_mode={row[0]}：{row[1]} 筆")

    # 依 is_negative 分群計數（posts 表）
    print("\n[驗證] posts 正負面標題分布：")
    try:
        cursor.execute("SELECT is_negative, COUNT(*) FROM posts GROUP BY is_negative")
        rows = cursor.fetchall()
        if rows:
            for row in rows:
                label = "負面" if row[0] == 1 else "非負面"
                print(f"  is_negative={row[0]}（{label}）：{row[1]} 筆")
        else:
            print("  posts 資料表為空")
    except sqlite3.OperationalError as e:
        print(f"  posts 查詢失敗：{e}")


# ════════════════════════════════════════════════════════════════════════════
# 主程式入口
# ════════════════════════════════════════════════════════════════════════════

def main():
    print("=" * 60)
    print("Week 2：資料清理與 SQLite 資料庫建立")
    print("=" * 60)

    # 第一部分：清理資料並擷取規格
    cleaned_df = clean_product_data()

    # 第二部分：建立資料庫並匯入資料
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        # 建立資料表
        setup_database(conn)
        # 匯入清理後資料
        import_data(conn, cleaned_df)
        # 執行驗證查詢
        run_verification_queries(conn)

    print(f"\n[Week2] 完成！資料庫路徑：{DB_PATH}")


if __name__ == "__main__":
    main()
