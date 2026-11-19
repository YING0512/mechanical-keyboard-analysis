"""
week4_filter.py
Week 4 - 機械鍵盤篩選工具
功能：依預算、連線模式、軸體種類、熱插拔條件篩選商品
"""

import pandas as pd
import os
from datetime import date

# ── 假資料定義（當 CSV 不存在時使用）────────────────────────────────
FAKE_DATA = {
    "product_name": [
        "羅技 G913 TKL 無線機械鍵盤",
        "海盜船 K70 RGB Pro 機械鍵盤",
        "FILCO MAJESTOUCH 2 機械鍵盤",
        "Royal Kludge RK84 三模機械鍵盤",
        "Keychron K8 Pro 三模熱插拔鍵盤",
        "Ducky One 3 SF 機械鍵盤",
        "Leopold FC900R 機械鍵盤",
        "HHKB Professional HYBRID Type-S",
        "NuPhy Air75 V2 三模無線鍵盤",
        "Akko 3068B Plus 三模熱插拔鍵盤",
    ],
    "price_twd": [5490, 3990, 3200, 1890, 3490, 2890, 3600, 8900, 3290, 1680],
    "switch_type": [
        "GL Linear", "Cherry MX Red", "Cherry MX Brown",
        "青軸", "Gateron G Pro Red", "Cherry MX Blue",
        "Cherry MX Red", "靜電容", "Gateron Low Profile Red", "Akko CS Jelly Pink",
    ],
    "connect_mode": [
        "無線", "有線", "有線",
        "三模", "三模", "有線",
        "有線", "三模", "三模", "三模",
    ],
    "hot_swap": [False, False, False, True, True, False, False, False, True, True],
}


def load_data():
    """讀取清理後的商品 CSV；若不存在則建立 10 筆假資料並回傳 DataFrame。"""
    csv_path = os.path.join("data", "processed", "products_cleaned.csv")

    # 嘗試讀取 CSV 檔案
    if os.path.exists(csv_path):
        try:
            df = pd.read_csv(csv_path, encoding="utf-8-sig")
            print(f"已載入資料：{csv_path}（共 {len(df)} 筆）")
            return df
        except Exception as e:
            print(f"讀取 CSV 失敗：{e}，改用假資料。")

    # 若檔案不存在，建立假資料
    print(f"找不到 {csv_path}，改用 10 筆假資料進行示範。")
    df = pd.DataFrame(FAKE_DATA)
    return df


def filter_keyboards(budget_min, budget_max, connect_mode=None, switch_type=None, hot_swap=None):
    """
    依條件篩選機械鍵盤商品。

    參數：
        budget_min  (int/float)：最低預算（含）
        budget_max  (int/float)：最高預算（含）
        connect_mode (str|None)：連線模式（None 表示不限）
        switch_type  (str|None)：軸體種類（None 表示不限）
        hot_swap     (bool|None)：是否要熱插拔（None 表示不限）

    回傳：
        符合條件的 pandas DataFrame
    """
    # 步驟 1：載入資料
    df = load_data()

    # 步驟 2：確保 price_twd 為數值型態，並移除無效資料
    df["price_twd"] = pd.to_numeric(df["price_twd"], errors="coerce")
    df = df.dropna(subset=["price_twd"])

    # 步驟 3：篩選預算範圍
    result = df[(df["price_twd"] >= budget_min) & (df["price_twd"] <= budget_max)].copy()

    # 步驟 4：若指定 connect_mode，篩選連線模式
    if connect_mode is not None:
        result = result[result["connect_mode"] == connect_mode]

    # 步驟 5：若指定 switch_type，篩選軸體種類
    if switch_type is not None:
        result = result[result["switch_type"] == switch_type]

    # 步驟 6：若指定 hot_swap，篩選熱插拔條件
    if hot_swap is not None:
        # 確保 hot_swap 欄位為布林型態
        result["hot_swap"] = result["hot_swap"].apply(
            lambda x: str(x).strip().lower() in ("true", "1", "yes", "是")
            if not isinstance(x, bool) else x
        )
        result = result[result["hot_swap"] == hot_swap]

    # 步驟 7：重置索引後回傳
    result = result.reset_index(drop=True)
    return result


def show_filter_results(df):
    """
    印出篩選結果。
    - 若無結果，提示使用者放寬條件。
    - 否則顯示前 20 筆指定欄位，並印出總筆數。
    """
    # 步驟 1：檢查結果是否為空
    if df.empty:
        print("找不到符合條件的商品，建議放寬篩選條件")
        return

    # 步驟 2：準備顯示欄位（允許欄位不存在時仍能顯示）
    display_cols = ["product_name", "price_twd", "switch_type", "connect_mode", "hot_swap"]
    available_cols = [col for col in display_cols if col in df.columns]

    # 步驟 3：只取前 20 筆
    top20 = df[available_cols].head(20)

    # 步驟 4：格式化印出（使用 to_string 避免截斷）
    print(top20.to_string(index=False))

    # 步驟 5：印出總筆數統計
    print(f"\n共找到 {len(df)} 筆商品")


# ── 主程式示範 ─────────────────────────────────────────────────────
if __name__ == "__main__":
    # 示範篩選 1：預算 1500～3000 元、三模連線
    print("=" * 60)
    print("篩選條件：預算 1500～3000 元、三模連線")
    print("=" * 60)
    result1 = filter_keyboards(budget_min=1500, budget_max=3000, connect_mode="三模")
    show_filter_results(result1)

    print()

    # 示範篩選 2：預算 2000～5000 元、熱插拔
    print("=" * 60)
    print("篩選條件：預算 2000～5000 元、熱插拔")
    print("=" * 60)
    result2 = filter_keyboards(budget_min=2000, budget_max=5000, hot_swap=True)
    show_filter_results(result2)
