import pandas as pd
import streamlit as st
import datetime
from datetime import date, timedelta
import matplotlib.pyplot as plt
import plotly.graph_objs as go
import yfinance as yf
import mplfinance as mpf
import streamlit.components.v1 as components

# CSVファイルからデータを読み込む
df = pd.read_csv("data_j.csv",encoding='utf-8')
# 企業名の一覧を取得する
company_names = df["銘柄名"].unique()
# 日付を取得する
today = datetime.date.today()
df_rank = pd.DataFrame({
    'name': ['Alice', 'Bob', 'Charlie', 'David', 'Ella', 'Frank', 'Grace', 'Henry', 'Isaac', 'Judy'],
    'score': [80, 90, 70, 60, 85, 75, 95, 80, 75, 85]
})

# ボタンが押されたかどうかを判定するフラグ
button_clicked = False
chart_slot = None
stockcode = None

st.set_option('deprecation.showPyplotGlobalUse', False)

@st.cache_data
def get_hist(stockcode):
    df = yf.download(tickers=stockcode, start=today - datetime.timedelta(days=731), end=today - datetime.timedelta(days=1))
    # チャートの表示に必要なカラムだけにDataframeを整形（カラムが少なくても多くてもだめ）
    hist = df[['Open', 'High', 'Low', 'Close', 'Volume']]
    return hist

def get_tomorrow():
    hist = get_hist(stockcode)
    # 現在のend_dateで指定された日付の次の日の日付を取得
    next_date = hist.index[hist.index.get_loc(datetime.datetime.combine(st.session_state["end_date"], datetime.time())) + 1].date()
    st.session_state["end_date"] = next_date
    return next_date

def get_prices():
    hist = get_hist(stockcode)
    end_date = st.session_state["end_date"]
    filtered_hist = hist[hist.index.date == end_date]
    if len(filtered_hist) == 0:
        st.warning(f"No data available for {end_date}")
        return None, None
    open_price = filtered_hist["Open"].iloc[0]
    close_price = filtered_hist["Close"].iloc[0]
    st.session_state["open_price"] = open_price
    st.session_state["close_price"] = close_price
    return open_price, close_price

def get_chart():
    global chart_slot
    if chart_slot is None or chart_slot._type != "chart":
        chart_slot = st.empty()
    # Streamlitのsession stateを初期化
    if 'end_date' not in st.session_state:
        st.session_state["end_date"] = today - datetime.timedelta(days=366)
    hist = get_hist(stockcode)
    # シミュレーションに使う期間を算出するための定義（session_stateにためた値を使って算出する）
    st.session_state["chart_end"] = st.session_state["end_date"]
    start_date = st.session_state["chart_end"] - datetime.timedelta(days=60) # 減算を行う
    fig = mpf.plot(hist.loc[start_date:st.session_state.chart_end], type='candle',
                    volume=True, figratio=(20, 8), mav=(5, 25))
    if chart_slot is None or chart_slot._type != "chart":
        chart_slot = st.empty()
    chart_slot.pyplot(fig)

with st.container():
    st.title("株価シミュレーションアプリ")
    with st.container():
        col5,col6,col7 = st.columns(3)
        with col5:
            # 名前の入力
            st.session_state["name"] = st.text_input("名前を入力してください","")
        with col6:
            # 部分検索するためのテキストボックスを設置
            search_term = st.text_input("検索", "")
            # 部分検索でマッチする銘柄名を抽出
            matched_company_names = df["銘柄名"].str.contains(search_term, na=False)
        with col7:
            # 選択された銘柄名をダウンリストから選択する
            options = [None] + df["銘柄名"][matched_company_names].tolist()
            selected_company_name = st.selectbox("銘柄を選択してください", options)
    st.session_state['company'] = selected_company_name
    result_company = st.session_state.get('company',None)
    selected_row = df.loc[matched_company_names & (df['銘柄名']==result_company)]
    if not selected_row.empty:
        code = selected_row['コード'].iloc[-1]
        stockcode = str(code) + '.T'
    if st.button("銘柄決定"):
        button_clicked = True
        if chart_slot is None:
            chart_slot = st.empty()
        get_chart()
        get_prices()

    # counter = st.session_state.get('counter',0)
    challenger = st.session_state.get("name","挑戦者求む")
    result_date = st.session_state.get('end_date', today - datetime.timedelta(days=366))
    result_cash = st.session_state.get('remaining_cash',100000)
    result_num = st.session_state.get('num_shares',10)
    result_open_price = st.session_state.get("open_price",500)
    result_close_price = st.session_state.get("close_price",500)
    st.sidebar.write(f"挑戦者：{challenger}")
    st.sidebar.write(f"選択銘柄：{result_company}")
    st.sidebar.write(f"銘柄コード：{stockcode}")
    st.sidebar.write(f"決定日：{result_date}")
    st.sidebar.write(f"現金残高：{result_cash}")
    st.sidebar.write(f"保有株数：{result_num}")
    with st.sidebar.container():
        col3,col4 = st.columns(2)
        with col3:
            st.write(f"本日の始値：{result_open_price}")
        with col4:
            st.write(f"本日の終値：{result_close_price}")
with st.container():
    chart_slot = st.empty()



# シミュレーション用関数（counterの値を元に計算して各st.session_stateに代入）
def simulate_trade():
    open_price, close_price = get_prices()
    input_buy = st.session_state.input_buy
    input_sell = st.session_state.input_sell
    if input_buy == '' and input_sell == '':
        pass
    elif input_sell != '':
        input_sell = int(input_sell)
        if input_sell > result_num:
            st.write(f"株数が不足しています! 保有株数: {result_num}")
        else:
            sell_price = open_price * input_sell
            st.session_state['remaining_cash'] = result_cash + sell_price
            st.session_state['num_shares'] = result_num - input_sell
            st.session_state["input_sell"] = "" # 入力欄をクリア
    else:
        input_buy = int(input_buy)
        if input_buy * open_price > result_cash:
            st.write("現金残高が不足しています!")
        else:
            buy_price = input_buy * open_price
            st.session_state['remaining_cash'] = result_cash - buy_price
            st.session_state['num_shares'] = result_num + input_buy
            st.session_state["input_buy"] = "" # 入力欄をクリア

def get_done():
    get_tomorrow()
    get_prices()
    get_chart()
    simulate_trade()

def main():
    # ボタンを配置する
    with st.sidebar.container():
        col1,col2 = st.columns(2)
        with col1:
            st.text_input("購入数を入力してください", key="input_buy")
        with col2:
            st.text_input("売却数を入力してください", key="input_sell")
        st.sidebar.text_input("取引メモ",key="comment")
        st.button(label='売買実行', on_click=get_done)
        st.sidebar.write(f"{result_company}の実行ランキング")

    top5 = df_rank.sort_values('score', ascending=False).head(5)
    st.sidebar.table(top5.reset_index(drop=True))

if __name__ == '__main__':
    main()


