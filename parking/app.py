import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(
    page_title="서울시 공영주차장 안내",
    page_icon="🅿️",
    layout="wide"
)

st.title("🅿️ 서울시 공영주차장 정보")

st.markdown(
"""
공영주차장을 검색하고

가장 저렴한 주차장을 추천받을 수 있습니다.
"""
)

# -------------------------
# CSV 업로드
# -------------------------

uploaded = st.file_uploader(
    "CSV 업로드",
    type="csv"
)

if uploaded is None:
    st.info("서울시 공영주차장 CSV를 업로드하세요.")
    st.stop()

# -------------------------
# CSV 읽기
# -------------------------

try:
    df = pd.read_csv(uploaded, encoding="cp949")
except:
    try:
        df = pd.read_csv(uploaded, encoding="utf-8")
    except:
        df = pd.read_csv(uploaded)

df.columns = df.columns.str.strip()

# -------------------------
# 컬럼 자동 찾기
# -------------------------

def find_col(words):

    for col in df.columns:

        for word in words:

            if word in col:

                return col

    return None

NAME = find_col(["주차장명"])

ADDR = find_col(["주소"])

DIST = find_col(["자치구"])

LAT = find_col(["위도"])

LON = find_col(["경도"])

FREE = find_col(["유무료"])

NIGHT = find_col(["야간무료"])

BASE = find_col(["기본 주차 요금","기본주차요금"])

UNIT = find_col(["추가 단위 요금"])

DAYMAX = find_col(["일 최대"])

WK_START = find_col(["평일 운영 시작"])

WK_END = find_col(["평일 운영 종료"])

SAT_START = find_col(["토요일 운영 시작"])

SAT_END = find_col(["토요일 운영 종료"])

HOL_START = find_col(["공휴일 운영 시작"])

HOL_END = find_col(["공휴일 운영 종료"])

# -------------------------
# 전처리
# -------------------------

df = df.dropna(subset=[LAT,LON])

df[LAT] = pd.to_numeric(df[LAT])

df[LON] = pd.to_numeric(df[LON])

if BASE:

    df[BASE] = (
        df[BASE]
        .astype(str)
        .str.replace(",","")
        .str.extract("(\d+)")
        .fillna(0)
        .astype(int)
    )

if UNIT:

    df[UNIT] = (
        df[UNIT]
        .astype(str)
        .str.replace(",","")
        .str.extract("(\d+)")
        .fillna(0)
        .astype(int)
    )

if DAYMAX:

    df[DAYMAX] = (
        df[DAYMAX]
        .astype(str)
        .str.replace(",","")
        .str.extract("(\d+)")
        .fillna(0)
        .astype(int)
    )

# -------------------------
# 사이드바
# -------------------------

st.sidebar.title("검색")

keyword = st.sidebar.text_input(
    "주차장 이름"
)

if DIST:

    gu_list = sorted(df[DIST].dropna().unique())

    gu = st.sidebar.selectbox(
        "자치구",
        ["전체"] + gu_list
    )

else:

    gu = "전체"

free_only = st.sidebar.checkbox(
    "무료 주차장"
)

night_only = st.sidebar.checkbox(
    "야간 무료 개방"
)

weekend_only = st.sidebar.checkbox(
    "주말 운영"
)

if BASE:

    fee = st.sidebar.slider(

        "기본요금",

        int(df[BASE].min()),

        int(df[BASE].max()),

        (
            int(df[BASE].min()),
            int(df[BASE].max())
        )
    )

# -------------------------
# 검색
# -------------------------

parking = df.copy()

if keyword:

    parking = parking[
        parking[NAME].astype(str)
        .str.contains(keyword)
    ]

if gu != "전체":

    parking = parking[
        parking[DIST] == gu
    ]

if BASE:

    parking = parking[
        (parking[BASE] >= fee[0]) &
        (parking[BASE] <= fee[1])
    ]

if free_only and FREE:

    parking = parking[
        parking[FREE]
        .astype(str)
        .str.contains("무료")
    ]

if night_only and NIGHT:

    parking = parking[
        parking[NIGHT]
        .astype(str)
        .str.contains("가능|무료|Y")
    ]

if weekend_only:

    if SAT_START:

        parking = parking[
            parking[SAT_START].notna()
        ]

st.sidebar.success(
    f"{len(parking)}개의 주차장이 검색되었습니다."
)

# -------------------------
# 요약 카드
# -------------------------

c1,c2,c3,c4 = st.columns(4)

c1.metric(
    "검색 결과",
    len(parking)
)

if FREE:

    c2.metric(
        "무료",
        parking[FREE]
        .astype(str)
        .str.contains("무료")
        .sum()
    )

if BASE:

    c3.metric(
        "평균요금",
        f"{int(parking[BASE].mean())}원"
    )

if DAYMAX:

    c4.metric(
        "평균 일최대",
        f"{int(parking[DAYMAX].mean())}원"
    )

st.markdown("---")
# =====================================================
# 2편 : 지도(Folium)
# 아래 코드를 1편 맨 아래에 이어서 붙여 넣으세요.
# =====================================================

import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium

st.header("🗺️ 공영주차장 지도")

# -------------------------
# 지도 중심
# -------------------------

if len(parking) > 0:

    center = [
        parking[LAT].mean(),
        parking[LON].mean()
    ]

else:

    center = [
        df[LAT].mean(),
        df[LON].mean()
    ]

m = folium.Map(
    location=center,
    zoom_start=12,
    control_scale=True
)

cluster = MarkerCluster().add_to(m)

# -------------------------
# 마커 생성
# -------------------------

for _, row in parking.iterrows():

    # 마커 색상
    color = "blue"

    if FREE:
        if "무료" in str(row[FREE]):
            color = "green"

    elif NIGHT:
        if "가능" in str(row[NIGHT]):
            color = "purple"

    popup_html = f"""
    <div style="width:260px">
        <h4>{row.get(NAME,"")}</h4>

        <b>📍 주소</b><br>
        {row.get(ADDR,"-")}<br><br>

        <b>💰 기본요금</b><br>
        {row.get(BASE,"-")} 원<br><br>

        <b>🆓 무료 여부</b><br>
        {row.get(FREE,"-")}<br><br>

        <b>🌙 야간 무료</b><br>
        {row.get(NIGHT,"-")}<br><br>

        <b>⏰ 평일</b><br>
        {row.get(WK_START,"-")} ~
        {row.get(WK_END,"-")}<br><br>

        <b>📅 토요일</b><br>
        {row.get(SAT_START,"-")} ~
        {row.get(SAT_END,"-")}<br><br>

        <b>🎉 공휴일</b><br>
        {row.get(HOL_START,"-")} ~
        {row.get(HOL_END,"-")}
    </div>
    """

    tooltip = f"""
    {row.get(NAME,"")}

    기본요금 : {row.get(BASE,"-")}원
    """

    folium.Marker(
        location=[
            row[LAT],
            row[LON]
        ],
        tooltip=tooltip,
        popup=folium.Popup(
            popup_html,
            max_width=350
        ),
        icon=folium.Icon(
            color=color,
            icon="info-sign"
        )
    ).add_to(cluster)

# -------------------------
# 지도 출력
# -------------------------

map_data = st_folium(
    m,
    width=None,
    height=700
)

# -------------------------
# 선택한 마커 정보
# -------------------------

if map_data["last_object_clicked"]:

    lat = map_data["last_object_clicked"]["lat"]
    lon = map_data["last_object_clicked"]["lng"]

    selected = parking[
        (parking[LAT].round(6) == round(lat,6)) &
        (parking[LON].round(6) == round(lon,6))
    ]

    if len(selected):

        st.markdown("---")

        st.subheader("📍 선택한 주차장")

        row = selected.iloc[0]

        col1, col2 = st.columns(2)

        with col1:

            st.write("### 기본정보")

            st.write("**주차장명**")
            st.write(row[NAME])

            st.write("**주소**")
            st.write(row[ADDR])

            if DIST:
                st.write("**자치구**")
                st.write(row[DIST])

        with col2:

            st.write("### 이용정보")

            if BASE:
                st.write(f"**기본요금 :** {row[BASE]}원")

            if DAYMAX:
                st.write(f"**일 최대요금 :** {row[DAYMAX]}원")

            if FREE:
                st.write(f"**무료 :** {row[FREE]}")

            if NIGHT:
                st.write(f"**야간 무료 :** {row[NIGHT]}")

st.markdown("---")
# =====================================================
# 3편 : 추천 알고리즘 + TOP10 + 예상 주차요금 계산기
# =====================================================

st.header("🏆 추천 주차장")

recommend = parking.copy()

if len(recommend):

    recommend["추천점수"] = 0

    # -------------------------
    # 가격 점수
    # -------------------------

    if BASE:

        max_fee = recommend[BASE].max()

        recommend["추천점수"] += (
            max_fee - recommend[BASE]
        )

    # -------------------------
    # 무료 점수
    # -------------------------

    if FREE:

        recommend.loc[
            recommend[FREE]
            .astype(str)
            .str.contains("무료"),
            "추천점수"
        ] += 1000

    # -------------------------
    # 야간무료 점수
    # -------------------------

    if NIGHT:

        recommend.loc[
            recommend[NIGHT]
            .astype(str)
            .str.contains("가능|무료|Y"),
            "추천점수"
        ] += 300

    # -------------------------
    # 주말 운영 점수
    # -------------------------

    if SAT_START:

        recommend.loc[
            recommend[SAT_START].notna(),
            "추천점수"
        ] += 200

    recommend = recommend.sort_values(
        "추천점수",
        ascending=False
    )

    best = recommend.iloc[0]

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "추천 주차장",
        best[NAME]
    )

    if BASE:

        c2.metric(
            "기본요금",
            f"{best[BASE]}원"
        )

    if DAYMAX:

        c3.metric(
            "일 최대",
            f"{best[DAYMAX]}원"
        )

    with st.expander("추천 상세 정보", expanded=True):

        st.write("### 📍 주소")
        st.write(best[ADDR])

        if FREE:
            st.write(f"🆓 무료 : {best[FREE]}")

        if NIGHT:
            st.write(f"🌙 야간 무료 : {best[NIGHT]}")

        if WK_START:
            st.write(
                f"⏰ 평일 : {best[WK_START]} ~ {best[WK_END]}"
            )

        if SAT_START:
            st.write(
                f"📅 토요일 : {best[SAT_START]} ~ {best[SAT_END]}"
            )

# =====================================================
# TOP10
# =====================================================

st.markdown("---")

st.subheader("💰 기본요금이 저렴한 TOP10")

if BASE:

    top10 = parking.sort_values(BASE).head(10)

    top10 = top10[
        [
            NAME,
            ADDR,
            BASE,
            DAYMAX
        ]
    ]

    top10.index = range(1, len(top10)+1)

    st.dataframe(
        top10,
        use_container_width=True,
        height=390
    )

# =====================================================
# 예상 주차요금 계산기
# =====================================================

st.markdown("---")

st.subheader("🧮 예상 주차요금 계산")

if BASE and UNIT:

    place = st.selectbox(
        "주차장 선택",
        parking[NAME]
    )

    minute = st.slider(
        "주차 시간(분)",
        30,
        720,
        120,
        step=30
    )

    row = parking[
        parking[NAME] == place
    ].iloc[0]

    try:

        base_fee = int(row[BASE])

        unit_fee = int(row[UNIT])

        base_time = 30

        if minute <= base_time:

            price = base_fee

        else:

            extra = minute - base_time

            unit = extra // 10

            price = base_fee + unit * unit_fee

        if DAYMAX:

            daymax = int(row[DAYMAX])

            if daymax > 0:

                price = min(price, daymax)

        st.success(
            f"예상 주차요금 : {price:,} 원"
        )

    except:

        st.warning("요금 계산이 불가능한 데이터입니다.")

# =====================================================
# 추천 순위
# =====================================================

st.markdown("---")

st.subheader("⭐ 추천 순위 TOP20")

ranking = recommend[
    [
        NAME,
        ADDR,
        BASE,
        "추천점수"
    ]
].head(20)

ranking.index = range(1, len(ranking)+1)

st.dataframe(
    ranking,
    use_container_width=True,
    height=500
)

st.markdown("---")
# =====================================================
# 4편 : 통계 + 그래프 + 다운로드 + 상세정보
# =====================================================

import plotly.express as px

st.header("📊 통계")

# =====================================================
# Metric
# =====================================================

m1, m2, m3, m4 = st.columns(4)

m1.metric(
    "검색 결과",
    len(parking)
)

if FREE:

    free_count = parking[FREE].astype(str).str.contains("무료").sum()

    m2.metric(
        "무료 주차장",
        free_count
    )

if NIGHT:

    night_count = parking[NIGHT].astype(str).str.contains("가능|무료|Y").sum()

    m3.metric(
        "야간 무료",
        night_count
    )

if BASE:

    avg_fee = int(parking[BASE].mean())

    m4.metric(
        "평균 기본요금",
        f"{avg_fee:,}원"
    )

# =====================================================
# 자치구 평균요금
# =====================================================

if DIST and BASE:

    st.subheader("🏙️ 자치구 평균 기본요금")

    gu_fee = (
        parking
        .groupby(DIST)[BASE]
        .mean()
        .sort_values()
        .reset_index()
    )

    fig = px.bar(
        gu_fee,
        x=DIST,
        y=BASE,
        text_auto=".0f",
        color=BASE
    )

    fig.update_layout(
        height=500,
        xaxis_title="자치구",
        yaxis_title="평균 기본요금(원)"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

# =====================================================
# 무료 / 유료 비율
# =====================================================

if FREE:

    st.subheader("🆓 무료 / 유료 비율")

    pie = (
        parking[FREE]
        .value_counts()
        .reset_index()
    )

    pie.columns = [
        "구분",
        "개수"
    ]

    fig = px.pie(
        pie,
        names="구분",
        values="개수",
        hole=0.4
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

# =====================================================
# TOP10 그래프
# =====================================================

if BASE:

    st.subheader("💰 가장 저렴한 TOP10")

    graph = (
        parking
        .sort_values(BASE)
        .head(10)
    )

    fig = px.bar(
        graph,
        x=BASE,
        y=NAME,
        orientation="h",
        text=BASE
    )

    fig.update_layout(
        height=550,
        yaxis_title=""
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

# =====================================================
# 상세 데이터
# =====================================================

st.markdown("---")

st.subheader("📋 상세 데이터")

show_cols = st.multiselect(

    "표시할 컬럼",

    list(parking.columns),

    default=[
        NAME,
        ADDR,
        BASE
    ]
)

if len(show_cols):

    st.dataframe(

        parking[show_cols],

        use_container_width=True,

        height=500
    )

# =====================================================
# CSV 다운로드
# =====================================================

csv = parking.to_csv(

    index=False,

    encoding="utf-8-sig"

).encode("utf-8-sig")

st.download_button(

    "📥 검색 결과 다운로드",

    data=csv,

    file_name="parking_result.csv",

    mime="text/csv"

)

# =====================================================
# 지도 데이터 다운로드
# =====================================================

map_csv = parking[

    [
        NAME,
        ADDR,
        LAT,
        LON
    ]

].to_csv(

    index=False,

    encoding="utf-8-sig"

).encode("utf-8-sig")

st.download_button(

    "🗺️ 지도 좌표 다운로드",

    map_csv,

    file_name="parking_map.csv",

    mime="text/csv"

)

# =====================================================
# 데이터 미리보기
# =====================================================

with st.expander("원본 데이터 보기"):

    st.dataframe(

        df,

        use_container_width=True,

        height=400

    )

# =====================================================
# Footer
# =====================================================

st.markdown("---")

st.caption(
    "서울시 공영주차장 정보 서비스 | Streamlit + Folium + Plotly"
)
