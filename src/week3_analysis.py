"""
Week 3 資料分析與圖表模組
分析機械鍵盤規格與售價關係、品牌討論傾向，並用 matplotlib 繪製圖表。
"""

import os
import sys
import pandas as pd
import matplotlib

# 若無互動式 GUI（非互動環境），使用 Agg 後端避免阻塞
if not sys.stdout.isatty():
    matplotlib.use('Agg')
import matplotlib.pyplot as plt

# 設定中文字體（Windows 下使用微軟正黑體）
matplotlib.rcParams['font.family'] = 'Microsoft JhengHei'
matplotlib.rcParams['axes.unicode_minus'] = False


def _show_or_close():
    """若在 GUI 環境則顯示圖表，若在無 GUI 環境則直接關閉。"""
    is_interactive = matplotlib.get_backend().lower() not in ['agg', 'pdf', 'ps', 'svg']
    if is_interactive and sys.stdout.isatty():
        try:
            plt.show()
        except Exception:
            pass
    plt.close()


# ──────────────────────────────────────────
# 讀取資料
# ──────────────────────────────────────────

def load_data():
    """
    讀取 products_cleaned.csv 與 bahamut_posts.csv。
    若檔案不存在或缺少有效欄位，自動建立含 20 筆假資料的 DataFrame。
    """
    products_path = os.path.join('data', 'processed', 'products_cleaned.csv')
    bahamut_path  = os.path.join('data', 'raw', 'bahamut_posts.csv')

    # ── 1. 讀取商品資料 ──
    df_products = None
    if os.path.exists(products_path):
        print(f'[INFO] 讀取商品資料：{products_path}')
        try:
            df_products = pd.read_csv(products_path)
        except Exception as e:
            print(f'[WARN] 讀取商品檔案失敗（{e}），改用假資料')
            df_products = None

    # 若檔案不存在或為空，建立 20 筆假資料（含不同 connect_mode、switch_type、price_twd）
    if df_products is None or df_products.empty:
        print('[INFO] 商品資料不存在或為空，建立假資料（20 筆）')
        connect_modes = [
            '有線', '藍牙', '2.4G無線', '有線', '藍牙',
            '2.4G無線', '有線', '有線', '藍牙', '2.4G無線',
            '有線', '藍牙', '有線', '2.4G無線', '藍牙',
            '有線', '有線', '2.4G無線', '藍牙', '有線'
        ]
        switch_types = [
            '青軸', '茶軸', '紅軸', '青軸', '茶軸',
            '紅軸', '青軸', '茶軸', '紅軸', '靜音紅軸',
            '茶軸', '青軸', '靜音紅軸', '茶軸', '紅軸',
            '靜音紅軸', '青軸', '茶軸', '紅軸', '青軸'
        ]
        prices = [
            1290, 2490, 3290, 1590, 2890,
            3690, 1890, 2190, 4290, 3490,
            2290, 1190, 3190, 2690, 4590,
            3390, 1490, 2790, 3890, 990
        ]
        df_products = pd.DataFrame({
            'product_name': [f'機械鍵盤型號_{i+1}' for i in range(20)],
            'connect_mode': connect_modes,
            'switch_type':  switch_types,
            'price_twd':    prices,
            'source':       ['假資料'] * 20
        })

    # ── 2. 讀取巴哈姆特論壇資料 ──
    df_bahamut = None
    if os.path.exists(bahamut_path):
        print(f'[INFO] 讀取論壇資料：{bahamut_path}')
        try:
            df_bahamut = pd.read_csv(bahamut_path)
        except Exception as e:
            print(f'[WARN] 讀取論壇檔案失敗（{e}），改用假資料')
            df_bahamut = None

    # 若檔案不存在、為空或 brand 欄位全為空/NaN，建立 20 筆標準假資料
    need_fake_bahamut = False
    if df_bahamut is None or df_bahamut.empty:
        need_fake_bahamut = True
    elif 'brand' not in df_bahamut.columns or df_bahamut['brand'].fillna('').astype(str).str.strip().eq('').all():
        print('[INFO] 論壇資料缺少有效品牌，補入 20 筆測試假資料進行分析')
        need_fake_bahamut = True

    if need_fake_bahamut:
        print('[INFO] 建立論壇假資料（20 筆，包含多品牌與負面標記）')
        brands = [
            'CORSAIR', 'Ducky', 'Keychron', 'Leopold', 'CORSAIR',
            'Ducky', 'Keychron', 'Leopold', 'CORSAIR', 'Ducky',
            'Keychron', 'Leopold', 'CORSAIR', 'Ducky', 'Keychron',
            'CORSAIR', 'Razer', 'Razer', 'ROG', ''
        ]
        is_neg = [
            1, 0, 1, 0, 0,
            1, 0, 0, 1, 0,
            1, 0, 0, 0, 0,
            0, 1, 0, 0, 0
        ]
        titles = [
            '【問題】CORSAIR 鍵盤雙擊問題請益',
            '【心得】Ducky One 3 開箱與手感分享',
            '【災情】Keychron 藍牙經常斷線問題',
            '【推薦】Leopold 大鍵手感真的沒話說',
            '【開箱】CORSAIR K70 RGB 使用心得',
            '【問題】Ducky 鍵盤按鍵沒反應故障',
            '【討論】Keychron 適合辦公室打字嗎？',
            '【心得】Leopold FC900R 辦公首選',
            '【抱怨】CORSAIR iCUE 軟體更新後當機',
            '【心得】Ducky 機械鍵盤耐用度推薦',
            '【問題】Keychron 無線延遲嚴重怎麼解',
            '【心得】Leopold 靜音紅軸安靜好打',
            '【分享】CORSAIR 光軸鍵盤開箱',
            '【分享】Ducky 經典鍵盤收藏',
            '【討論】Keychron 換軸教學分享',
            '【心得】CORSAIR 旗艦鍵盤使用半年',
            '【抱怨】Razer 綠軸用一年出現雙擊壞掉',
            '【開箱】Razer 獵魂光蛛體驗',
            '【心得】ROG 夜魔鍵盤開箱心得',
            '【閒聊】大家第一把機械鍵盤買哪牌？'
        ]
        df_bahamut = pd.DataFrame({
            'title':       titles,
            'brand':       brands,
            'is_negative': is_neg,
            'source':      ['假資料'] * 20
        })

    return df_products, df_bahamut


# ──────────────────────────────────────────
# 分析一：規格與售價比較
# ──────────────────────────────────────────

def analyze_price_by_spec(df, col):
    """
    以指定欄位（connect_mode 或 switch_type）分組，
    計算各組的商品數量、平均價、中位數、最低價、最高價。
    """
    # 步驟 1：檢查欄位是否存在
    if 'price_twd' not in df.columns or col not in df.columns:
        print(f'[WARN] 缺少必要欄位（price_twd 或 {col}），跳過分析')
        return pd.DataFrame()

    # 步驟 2：移除價格或分組欄位為空值的資料列
    df_clean = df.dropna(subset=['price_twd', col])

    # 步驟 3：用 pandas groupby 計算各組統計量
    grouped = df_clean.groupby(col)['price_twd'].agg(
        商品數量='count',
        平均價='mean',
        中位數='median',
        最低價='min',
        最高價='max'
    ).reset_index()

    grouped['平均價'] = grouped['平均價'].round(0).astype(int)
    grouped['中位數'] = grouped['中位數'].astype(int)

    # 步驟 4：印出結果表格
    print(f'\n【依 {col} 分組的價格統計】')
    print(grouped.to_string(index=False))
    return grouped


def plot_price_boxplot(df):
    """
    繪製圖表 1：連線方式 vs 價格分布（箱形圖）。
    若某組資料少於 2 筆，跳過該組並印出提示。
    儲存到 output/figures/fig1_price_by_connect.png。
    """
    # 步驟 1：建立輸出目錄
    os.makedirs(os.path.join('output', 'figures'), exist_ok=True)

    if 'connect_mode' not in df.columns or 'price_twd' not in df.columns:
        print('[WARN] 缺少 connect_mode 或 price_twd 欄位，跳過圖表 1')
        return

    # 步驟 2：按 connect_mode 收集價格，過濾少於 2 筆的組別
    groups = {}
    for mode, grp in df.groupby('connect_mode'):
        # 排除空值與空白
        if pd.isna(mode) or str(mode).strip() == '':
            continue
        prices = grp['price_twd'].dropna().tolist()
        if len(prices) < 2:
            print(f'[提示] connect_mode="{mode}" 資料不足 2 筆（共 {len(prices)} 筆），圖表中跳過此組')
        else:
            groups[mode] = prices

    if not groups:
        print('[WARN] 無足夠資料繪製箱形圖，跳過圖表 1')
        return

    labels = list(groups.keys())
    data   = [groups[k] for k in labels]

    # 步驟 3：繪製箱形圖並設定標題與座標軸
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.boxplot(data, tick_labels=labels)
    ax.set_title('不同連線方式的鍵盤價格分布')
    ax.set_xlabel('連線方式')
    ax.set_ylabel('價格（新台幣）')
    plt.tight_layout()

    # 步驟 4：儲存圖表檔案並適當關閉
    save_path = os.path.join('output', 'figures', 'fig1_price_by_connect.png')
    plt.savefig(save_path, dpi=150)
    print(f'[INFO] 圖表 1 已儲存：{save_path}')
    _show_or_close()


def plot_price_bar(df):
    """
    繪製圖表 2：軸體類型 vs 平均價（長條圖）。
    若某組資料少於 2 筆，跳過該組並印出提示。
    儲存到 output/figures/fig2_price_by_switch.png。
    """
    # 步驟 1：建立輸出目錄
    os.makedirs(os.path.join('output', 'figures'), exist_ok=True)

    if 'switch_type' not in df.columns or 'price_twd' not in df.columns:
        print('[WARN] 缺少 switch_type 或 price_twd 欄位，跳過圖表 2')
        return

    # 步驟 2：計算各軸體平均售價，過濾少於 2 筆的組別
    avg_prices = {}
    for stype, grp in df.groupby('switch_type'):
        if pd.isna(stype) or str(stype).strip() == '':
            continue
        prices = grp['price_twd'].dropna().tolist()
        if len(prices) < 2:
            print(f'[提示] switch_type="{stype}" 資料不足 2 筆（共 {len(prices)} 筆），圖表中跳過此組')
        else:
            avg_prices[stype] = sum(prices) / len(prices)

    if not avg_prices:
        print('[WARN] 無足夠資料繪製長條圖，跳過圖表 2')
        return

    labels = list(avg_prices.keys())
    values = [avg_prices[k] for k in labels]

    # 步驟 3：繪製長條圖並設定標題與座標軸
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(labels, values, color='steelblue')
    ax.set_title('不同軸體類型的平均售價')
    ax.set_xlabel('軸體類型')
    ax.set_ylabel('平均價格（新台幣）')
    plt.tight_layout()

    # 步驟 4：儲存圖表檔案並適當關閉
    save_path = os.path.join('output', 'figures', 'fig2_price_by_switch.png')
    plt.savefig(save_path, dpi=150)
    print(f'[INFO] 圖表 2 已儲存：{save_path}')
    _show_or_close()


# ──────────────────────────────────────────
# 分析二：品牌討論傾向
# ──────────────────────────────────────────

def analyze_brand_mentions(df):
    """
    統計各品牌討論次數，並計算出現 >= 3 次品牌的負面標題比例。
    """
    # 步驟 1：檢查欄位是否存在
    if 'brand' not in df.columns or 'is_negative' not in df.columns:
        print('[WARN] 缺少 brand 或 is_negative 欄位，跳過品牌分析')
        return pd.Series(dtype=int), pd.Series(dtype=float)

    # 步驟 2：只統計 brand != "" 的列
    df_valid = df[df['brand'].fillna('').astype(str).str.strip() != '']

    # 步驟 3：計算品牌出現次數排行（出現次數 >= 1）
    brand_counts = df_valid['brand'].value_counts()
    brand_counts = brand_counts[brand_counts >= 1]

    print('\n【品牌討論次數排行（出現 >= 1 次）】')
    for brand, cnt in brand_counts.items():
        print(f'  {brand}: {cnt} 次')

    # 步驟 4：計算各品牌負面標題比例（僅計算出現次數 >= 3 的品牌）
    print('\n【品牌負面討論比例（出現 >= 3 次才計算）】')
    neg_ratios = {}
    for brand, cnt in brand_counts.items():
        if cnt < 3:
            print(f'  [提示] 品牌「{brand}」僅出現 {cnt} 次，樣本太少不可靠，不計算負面比例（至少需 3 筆）')
        else:
            brand_df  = df_valid[df_valid['brand'] == brand]
            neg_count = (brand_df['is_negative'] == 1).sum()
            ratio     = neg_count / len(brand_df)
            neg_ratios[brand] = ratio
            print(f'  {brand}: 負面比例 {ratio:.1%}（負面 {neg_count} / 總計 {len(brand_df)}）')

    return brand_counts, pd.Series(neg_ratios)


def plot_brand_mentions(df):
    """
    繪製圖表 3：各品牌討論次數（長條圖，依次數降序排列）。
    儲存到 output/figures/fig3_brand_mentions.png。
    """
    # 步驟 1：建立輸出目錄
    os.makedirs(os.path.join('output', 'figures'), exist_ok=True)

    if 'brand' not in df.columns:
        print('[WARN] 缺少 brand 欄位，跳過圖表 3')
        return

    # 步驟 2：只統計品牌不為空的列，並依次數降序排列
    df_valid = df[df['brand'].fillna('').astype(str).str.strip() != '']
    brand_counts = df_valid['brand'].value_counts()
    brand_counts = brand_counts[brand_counts >= 1].sort_values(ascending=False)

    if brand_counts.empty:
        print('[WARN] 無品牌資料，跳過圖表 3')
        return

    labels = brand_counts.index.tolist()
    values = brand_counts.values.tolist()

    # 步驟 3：繪製長條圖並設定標題與座標軸
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(labels, values, color='coral')
    ax.set_title('各品牌論壇討論次數')
    ax.set_xlabel('品牌')
    ax.set_ylabel('討論次數')
    plt.tight_layout()

    # 步驟 4：儲存圖表檔案並適當關閉
    save_path = os.path.join('output', 'figures', 'fig3_brand_mentions.png')
    plt.savefig(save_path, dpi=150)
    print(f'[INFO] 圖表 3 已儲存：{save_path}')
    _show_or_close()


# ──────────────────────────────────────────
# 主程式
# ──────────────────────────────────────────

def main():
    """主程式：依序執行資料讀取、分析與圖表繪製。"""
    print('=' * 55)
    print('  Week 3 分析開始')
    print('=' * 55)

    # 步驟 1：讀取資料
    df_products, df_bahamut = load_data()

    # 步驟 2：分析一 - 連線方式與售價比較
    analyze_price_by_spec(df_products, 'connect_mode')

    # 步驟 3：分析一 - 軸體類型與售價比較
    analyze_price_by_spec(df_products, 'switch_type')

    # 步驟 4：繪製圖表 1 - 連線方式 vs 價格分布（箱形圖）
    plot_price_boxplot(df_products)

    # 步驟 5：繪製圖表 2 - 軸體類型 vs 平均價（長條圖）
    plot_price_bar(df_products)

    # 步驟 6：分析二 - 品牌討論傾向與負面標題比例
    analyze_brand_mentions(df_bahamut)

    # 步驟 7：繪製圖表 3 - 各品牌討論次數（長條圖）
    plot_brand_mentions(df_bahamut)

    print('\n' + '=' * 55)
    print('  Week 3 分析完成')
    print('=' * 55)


if __name__ == '__main__':
    main()
