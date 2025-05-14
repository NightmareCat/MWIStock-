import pandas as pd
import numpy as np
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.linear_model import LinearRegression

def analyze_trend(df):
    df = df.dropna(subset=["ask", "bid"])
    if df.empty:
        st.write("无足够数据分析")
        return

    # 简单线性回归斜率（趋势）
    y = (df["ask"] + df["bid"]) / 2
    x = np.arange(len(y))
    slope, _ = np.polyfit(x, y, 1)
    
    st.write(f"趋势斜率：{slope:.3f}")
    st.write(f"最近价格：{y.iloc[-1]:.2f}")
    st.line_chart(y.rolling(5).mean(), use_container_width=True)

def analyze_moving_averages(df, short_window=5, long_window=20):
    df = df.copy()
    df["price"] = (df["ask"] + df["bid"]) / 2
    df["short_ma"] = df["price"].rolling(window=short_window).mean()
    df["long_ma"] = df["price"].rolling(window=long_window).mean()

    # 交易信号
    latest_cross = None
    if len(df.dropna()) > 0:
        last_row = df.dropna().iloc[-1]
        if last_row["short_ma"] > last_row["long_ma"]:
            latest_cross = "📈 买入信号：短期均线上穿长期均线"
        elif last_row["short_ma"] < last_row["long_ma"]:
            latest_cross = "📉 卖出信号：短期均线下穿长期均线"

    # 图示
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(df["datetime"], df["price"], label="价格", alpha=0.3)
    ax.plot(df["datetime"], df["short_ma"], label=f"短期 MA({short_window})", color="green")
    ax.plot(df["datetime"], df["long_ma"], label=f"长期 MA({long_window})", color="orange")
    ax.set_title("移动平均线分析")
    ax.legend()
    ax.grid(True)
    st.pyplot(fig)

    # 建议输出
    if latest_cross:
        st.success(latest_cross)
    else:
        st.info("尚未形成明显交叉信号。")
        
def analyze_support_resistance(df, window=20):
    df = df.copy()
    df["price"] = (df["ask"] + df["bid"]) / 2
    recent = df.dropna().tail(window)["price"]

    if recent.empty:
        st.warning("数据不足以分析支撑/阻力位")
        return

    support = recent.min()
    resistance = recent.max()
    current = recent.iloc[-1]

    st.write(f"🔹 近期支撑位：{support:.2f}")
    st.write(f"🔺 近期阻力位：{resistance:.2f}")
    if current <= support * 1.01:
        st.success("📉 靠近支撑位，可能反弹，考虑买入")
    elif current >= resistance * 0.99:
        st.warning("📈 接近阻力位，可能回调，谨慎买入")
    else:
        st.info("价格位于区间中间，趋势尚不明确")

def analyze_bollinger_bands(df, window=20, num_std=2):
    df = df.copy()
    df["price"] = (df["ask"] + df["bid"]) / 2
    df["ma"] = df["price"].rolling(window).mean()
    df["std"] = df["price"].rolling(window).std()
    df["upper"] = df["ma"] + num_std * df["std"]
    df["lower"] = df["ma"] - num_std * df["std"]

    latest = df.dropna().iloc[-1]
    status = None
    if latest["price"] > latest["upper"]:
        status = "价格高于布林带上轨，可能超买 → ⚠️ 注意回调风险"
    elif latest["price"] < latest["lower"]:
        status = "价格低于布林带下轨，可能超卖 → ✅ 有反弹可能"
    else:
        status = "价格处于布林带区间内，趋势正常"

    # 绘图
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(df["datetime"], df["price"], label="价格", color="gray")
    ax.plot(df["datetime"], df["ma"], label="中线", color="blue")
    ax.plot(df["datetime"], df["upper"], label="上轨", color="green", linestyle="--")
    ax.plot(df["datetime"], df["lower"], label="下轨", color="red", linestyle="--")
    ax.set_title("布林带分析")
    ax.legend()
    ax.grid(True)
    st.pyplot(fig)

    st.info(f"📊 当前状态：{status}")
    

def analyze_correlation_matrix(price_dict: dict):
    """
    输入一个字典：{ item_name: df }
    每个 df 含 datetime 和 price（平均价）
    输出相关性热图
    """
    st.subheader("🔗 商品价格相关性分析")
    
    # 构建汇总 DataFrame
    merged = pd.DataFrame()
    for item, df in price_dict.items():
        temp = df.copy()
        temp["price"] = (temp["ask"] + temp["bid"]) / 2
        temp = temp[["datetime", "price"]].rename(columns={"price": item})
        merged = pd.merge(merged, temp, on="datetime", how="outer") if not merged.empty else temp

    merged.set_index("datetime", inplace=True)
    merged = merged.interpolate(method="linear", limit_direction="both").dropna()

    if merged.empty:
        st.warning("⚠️ 无法生成相关性矩阵，数据不足")
        return

    corr_matrix = merged.corr()
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.heatmap(corr_matrix, annot=True, cmap="coolwarm", ax=ax)
    st.pyplot(fig)

    return merged, corr_matrix

def forecast_price_by_correlation(merged_df: pd.DataFrame, corr_matrix: pd.DataFrame, target_item: str, top_n=2, days=3):
    """
    使用与 target_item 高相关的 top_n 项进行线性回归预测未来价格
    """
    st.subheader(f"🔮 基于相关性的价格预测：{target_item}")

    top_corr = corr_matrix[target_item].drop(target_item).abs().sort_values(ascending=False).head(top_n)
    predictors = top_corr.index.tolist()

    st.write(f"使用以下商品作为预测因子：{', '.join(predictors)}")

    df = merged_df[[target_item] + predictors].dropna()
    X = df[predictors]
    y = df[target_item]

    model = LinearRegression()
    model.fit(X, y)

    # 使用最近几天作为预测输入
    future_X = X.tail(days)
    pred = model.predict(future_X)

    st.line_chart(pd.Series(list(y.tail(days)) + list(pred), index=range(len(y.tail(days)) + days)))

    for i, val in enumerate(pred):
        st.write(f"📍 第 {i+1} 天预测：{val:.2f}")
