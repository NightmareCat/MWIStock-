import matplotlib.pyplot as plt
import streamlit as st
import matplotlib

# 设置全局字体（如 SimHei 黑体）
matplotlib.rcParams['font.family'] = 'SimHei'
matplotlib.rcParams['axes.unicode_minus'] = False  # 正确显示负号

def plot_price_history(df):
    # 过滤掉 bid==0 或 NaN 的行
    df_filtered = df.copy()
    df_filtered = df_filtered[df_filtered["bid"].notnull() & (df_filtered["bid"] > 0)]

    if df_filtered.empty:
        st.warning("⚠️ 所有 bid 值为 0 或缺失，无法绘图")
        return

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(df_filtered["datetime"], df_filtered["ask"], label="Ask", color="red", alpha=0.6)
    ax.plot(df_filtered["datetime"], df_filtered["bid"], label="Bid", color="blue")
    ax.set_title("价格走势")
    ax.set_xlabel("时间")
    ax.set_ylabel("价格")
    ax.grid(True)
    ax.legend()
    st.pyplot(fig)