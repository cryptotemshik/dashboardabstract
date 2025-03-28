import time
import requests
import pandas as pd
import streamlit as st
import plotly.express as px

# === 💪 ДАННЫЕ О ПОРТФЕЛЕ (обновлено) === #
portfolio = {
    "$CHENGU": {"address": "0xd045e0686a784e272e651fc2c08324edabe7403a", "amount": 721740, "entry_price": 0.0011},
    "$POLLY": {"address": "0x987cf44f3f5d854ec0703123d7fd003a8b56ebb4", "amount": 1860000, "entry_price": 0.00008},
    "$ABSTER": {"address": "0xc325b7e2736a5202bd860f5974d0aa375e57ede5", "amount": 90000, "entry_price": 0.00927},
    "$NUTZ": {"address": "0x440b408ec70c5755bcdea0c902df2757ef0d875f", "amount": 211480, "entry_price": 0.00079}
}

# === 🔮 ФУНКЦИЯ ДЛЯ ПОЛУЧЕНИЯ ЦЕНЫ ТОКЕНА === #
def get_token_data(token_address):
    url = f"https://api.dexscreener.com/latest/dex/tokens/{token_address}"
    response = requests.get(url).json()
    
    if "pairs" in response and response["pairs"]:
        pair = response["pairs"][0]
        return {
            "price": float(pair["priceUsd"]),
            "change_24h": float(pair["priceChange"]["h24"])
        }
    return {"price": 0, "change_24h": 0}

# === 📊 Streamlit UI === #
st.set_page_config(page_title="Crypto Portfolio Tracker", layout="wide")
st.title("📊 Crypto Portfolio Tracker")

prices, values, changes, initial_values, profit_losses = {}, {}, {}, {}, {}

for token, data in portfolio.items():
    token_data = get_token_data(data["address"])
    price = token_data["price"]
    change_24h = token_data["change_24h"]
    
    value = price * data["amount"]
    initial_value = data["entry_price"] * data["amount"]
    profit_loss = value - initial_value
    
    prices[token] = price
    values[token] = value
    changes[token] = change_24h
    initial_values[token] = initial_value
    profit_losses[token] = profit_loss

# === Вычисляем % от портфеля === #
total_portfolio_value = sum(values.values())
percentages = {token: (val / total_portfolio_value) * 100 for token, val in values.items()}

# === Создаем DataFrame === #
df = pd.DataFrame({
    "Token": [f'<a href="https://www.dexscreener.com/abstract/{data["address"]}" target="_blank">{token}</a>' for token, data in portfolio.items()],
    "Price ($)": [f"{price:.6f}" for price in prices.values()],
    "Amount": [portfolio[t]["amount"] for t in portfolio],
    "Value ($)": [f"{value:.2f}" for value in values.values()],
    "Entry Price ($)": [f"{portfolio[t]['entry_price']:.6f}" for t in portfolio],
    "Invested ($)": [f"{initial_value:.2f}" for initial_value in initial_values.values()],
    "Change 24h (%)": [f"{change:.2f}" for change in changes.values()],
    "Profit/Loss ($)": [f"{profit_loss:.2f}" for profit_loss in profit_losses.values()],
    "% of Portfolio": [f"{percentage:.2f}" for percentage in percentages.values()]
})

# === Добавляем строку Итого === #
total_value = sum(values.values())
total_invested = sum(initial_values.values())
total_profit_loss = sum(profit_losses.values())

# Для изменения портфеля 24h
total_change_24h = ((total_value - total_invested) / total_invested) * 100 if total_invested > 0 else 0

# Строка Итого
total_row = pd.DataFrame([{
    "Token": "Итого",
    "Price ($)": "---",
    "Amount": "---",
    "Value ($)": f"{total_value:.2f}",
    "Entry Price ($)": "---",
    "Invested ($)": f"{total_invested:.2f}",
    "Change 24h (%)": f"{total_change_24h:.2f}",
    "Profit/Loss ($)": f"{total_profit_loss:.2f}",
    "% of Portfolio": "100.00"
}])

# Объединяем основную таблицу с итоговой строкой
df_with_total = pd.concat([df, total_row], ignore_index=True)

# === Функция для стилизации === #
def style_positive_negative(val):
    """Функция для окрашивания ячеек в зависимости от значений"""
    if isinstance(val, (int, float)):
        if val > 0:
            return "background-color: green; color: white;"
        elif val < 0:
            return "background-color: red; color: white;"
    return ""

# === Применяем стили для столбцов Change 24h (%) и Profit/Loss ($) === #
df_styled = df_with_total.style.applymap(style_positive_negative, subset=["Change 24h (%)", "Profit/Loss ($)"])

# Убираем строку Итого из данных для графика
df_for_graph = df_with_total[df_with_total["Token"] != "Итого"]

# === Отображаем таблицу с гиперссылками и без индекса (сортировка по столбцам доступна) === #
st.markdown(f'<style>table {{overflow-x: auto;}}</style>', unsafe_allow_html=True)

# Используем метод to_html() для отображения таблицы с гиперссылками и без индексов
df_html = df_styled.to_html(escape=False, index=False)
st.markdown(df_html, unsafe_allow_html=True)

# === ГРАФИК 1 — Pie Chart (Распределение портфеля) === #
fig_pie = px.pie(df_for_graph, names="Token", values="Value ($)", title="Portfolio Distribution")
st.plotly_chart(fig_pie)

# === Таймер для автоматического обновления === #
st.text("Автообновление каждые 10 секунд.")

# Добавляем проверку на обновление данных через стейт (перезапуск)
if "last_update" not in st.session_state:
    st.session_state.last_update = time.time()

# Проверяем, если прошло больше 10 секунд, обновляем
if time.time() - st.session_state.last_update > 10:
    st.session_state.last_update = time.time()
    st.experimental_rerun()  # Принудительный перезапуск

