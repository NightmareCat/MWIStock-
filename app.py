import streamlit as st
import pandas as pd
import numpy as np
from config_manager import (
    load_config, save_config,
    load_name_map, get_item_id_by_chinese_name
)
from data_loader import get_price_data
from plot_utils import plot_price_history
from analysis import (
    analyze_trend,
    analyze_moving_averages,
    analyze_support_resistance,
    analyze_bollinger_bands,
    analyze_correlation_matrix,
    forecast_price_by_correlation
)

def main():
    st.set_page_config(page_title="MWI 市场分析", layout="wide")
    st.title("🌌 MWI 市场价格分析工具")

    # 加载配置
    config = load_config()
    name_map = load_name_map("config/name_map_spaces.json")
    monitored_items = config.get("items", [])
    n_days = config.get("n_days", 7)
    price_dict = {}  # 初始化避免作用域错误

    # ====== 侧栏操作 ======
    st.sidebar.header("🧰 配置监控物品")
    item_input = st.sidebar.text_input("输入物品名（中文或英文 ID）")
    if st.sidebar.button("➕ 添加物品") and item_input.strip():
        item_id = get_item_id_by_chinese_name(name_map, item_input.strip())
        if item_id not in monitored_items:
            monitored_items.append(item_id)
            save_config({"items": monitored_items, "n_days": n_days})
            st.experimental_rerun()

    if st.sidebar.button("🧹 清空监控列表"):
        monitored_items.clear()
        save_config({"items": monitored_items, "n_days": n_days})
        st.experimental_rerun()

    n_days = st.sidebar.slider("📅 显示近 N 天数据", 1, 90, n_days)
    save_config({"items": monitored_items, "n_days": n_days})

    page_mode = st.sidebar.radio("📄 页面模式", [
        "🔍 单物品分析",
        "📊 总监控视图",
        "📈 商品相关性分析"
    ])

    if not monitored_items:
        st.info("请在左侧添加至少一个监控物品。")
        return

    # 📈 商品相关性分析
    if page_mode == "📈 商品相关性分析":
        st.header("📈 商品相关性分析与预测")

        for item_id in monitored_items:
            try:
                df = get_price_data(item_id, n_days=n_days)
                df["bid"] = pd.to_numeric(df["bid"], errors="coerce").replace(0, np.nan).interpolate(limit_direction="both")
                df["ask"] = pd.to_numeric(df["ask"], errors="coerce").replace(0, np.nan).interpolate(limit_direction="both")
                price_dict[item_id] = df
            except Exception as e:
                st.warning(f"{item_id} 数据加载失败：{e}")

        if len(price_dict) >= 2:
            merged_df, corr_matrix = analyze_correlation_matrix(price_dict)
            target_item = st.selectbox("🎯 选择目标商品进行预测", monitored_items)
            forecast_price_by_correlation(merged_df, corr_matrix, target_item)
        else:
            st.warning("请至少添加两个商品以进行相关性分析。")
        return

    # 📊 总监控视图
    if page_mode == "📊 总监控视图":
        st.header("📊 所有监控商品趋势总览")
        cols = st.columns(2)
        for idx, item_id in enumerate(monitored_items):
            try:
                df = get_price_data(item_id, n_days=n_days)
                df["bid"] = pd.to_numeric(df["bid"], errors="coerce").replace(0, np.nan).interpolate(limit_direction="both")
                df["ask"] = pd.to_numeric(df["ask"], errors="coerce").replace(0, np.nan).interpolate(limit_direction="both")
                with cols[idx % 2]:
                    st.markdown(f"**{name_map.get(item_id, item_id)}**")
                    plot_price_history(df)
            except Exception as e:
                st.warning(f"{item_id} 加载失败：{e}")
        return

    # 🔍 单物品分析页
    tab_titles = [name_map.get(item, item) for item in monitored_items]
    tabs = st.tabs(tab_titles)
    item_to_delete = None

    for i, item_id in enumerate(monitored_items):
        with tabs[i]:
            item_name_display = name_map.get(item_id, item_id)
            st.subheader(f"📈 {item_name_display}：{n_days} 日价格趋势")

            if st.button(f"❌ 删除 {item_name_display}", key=f"del_{item_id}"):
                item_to_delete = item_id

            try:
                df = get_price_data(item_id, n_days=n_days)
                df["bid"] = pd.to_numeric(df["bid"], errors="coerce").replace(0, np.nan).interpolate(limit_direction="both")
                df["ask"] = pd.to_numeric(df["ask"], errors="coerce").replace(0, np.nan).interpolate(limit_direction="both")

                plot_price_history(df)
                analyze_trend(df)
                analyze_moving_averages(df)
                analyze_support_resistance(df)
                analyze_bollinger_bands(df)
            except Exception as e:
                st.error(f"读取数据出错：{e}")

    if item_to_delete:
        monitored_items.remove(item_to_delete)
        save_config({"items": monitored_items, "n_days": n_days})
        st.experimental_rerun()

if __name__ == "__main__":
    main()
