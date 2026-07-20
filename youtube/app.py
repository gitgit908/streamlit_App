import re
from collections import Counter

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from googleapiclient.discovery import build
from konlpy.tag import Okt
from PIL import Image
from wordcloud import WordCloud

########################################
# 설정
########################################

st.set_page_config(
    page_title="유튜브 댓글 분석기",
    layout="wide"
)

API_KEY = st.secrets["YOUTUBE_API_KEY"]

FONT_PATH = "fonts/NanumGothic.ttf"

youtube = build(
    "youtube",
    "v3",
    developerKey=API_KEY
)

########################################
# 함수
########################################

def get_video_id(url):

    patterns = [
        r"v=([A-Za-z0-9_-]+)",
        r"youtu\.be/([A-Za-z0-9_-]+)",
        r"shorts/([A-Za-z0-9_-]+)"
    ]

    for p in patterns:
        m = re.search(p, url)
        if m:
            return m.group(1)

    return None


def get_comments(video_id, max_comments):

    comments = []

    request = youtube.commentThreads().list(
        part="snippet",
        videoId=video_id,
        maxResults=100,
        textFormat="plainText"
    )

    while request and len(comments) < max_comments:

        response = request.execute()

        for item in response["items"]:

            s = item["snippet"]["topLevelComment"]["snippet"]

            comments.append({
                "text": s["textDisplay"],
                "like": s["likeCount"],
                "time": s["publishedAt"]
            })

            if len(comments) >= max_comments:
                break

        request = youtube.commentThreads().list_next(
            request,
            response
        )

    return pd.DataFrame(comments)


########################################
# 화면
########################################

st.title("🎬 유튜브 댓글 분석기")

url = st.text_input("유튜브 링크")

count = st.slider(
    "댓글 수",
    100,
    2000,
    500,
    100
)

########################################

if st.button("분석 시작"):

    video_id = get_video_id(url)

    if video_id is None:
        st.error("영상 주소를 확인하세요.")
        st.stop()

    st.video(url)

    with st.spinner("댓글 수집 중..."):

        df = get_comments(video_id, count)

    st.success(f"{len(df)}개의 댓글 수집 완료")

    ####################################################
    # 시간대별
    ####################################################

    df["time"] = pd.to_datetime(df["time"])

    df["hour"] = df["time"].dt.hour

    hour_df = (
        df.groupby("hour")
        .size()
        .reset_index(name="댓글수")
    )

    fig = px.bar(
        hour_df,
        x="hour",
        y="댓글수",
        title="시간대별 댓글 작성 추이"
    )

    st.plotly_chart(fig, use_container_width=True)

    ####################################################
    # 좋아요
    ####################################################

    st.subheader("댓글 반응")

    st.metric(
        "평균 좋아요",
        round(df["like"].mean(), 2)
    )

    top = df.sort_values(
        "like",
        ascending=False
    ).head(10)

    st.subheader("좋아요 많은 댓글")

    st.dataframe(
        top[["like","text"]],
        use_container_width=True
    )

    ####################################################
    # 워드클라우드
    ####################################################

    okt = Okt()

    nouns = []

    for txt in df["text"]:

        nouns.extend(okt.nouns(txt))

    nouns = [
        n
        for n in nouns
        if len(n) >= 2
    ]

    freq = Counter(nouns)

    wc = WordCloud(
        width=900,
        height=500,
        background_color="white",
        font_path=FONT_PATH
    ).generate_from_frequencies(freq)

    fig2, ax = plt.subplots(figsize=(12,6))

    ax.imshow(wc)

    ax.axis("off")

    st.subheader("한글 워드클라우드")

    st.pyplot(fig2)

    ####################################################
    # 빈도표
    ####################################################

    word_df = pd.DataFrame(
        freq.most_common(30),
        columns=["단어","빈도"]
    )

    st.subheader("상위 단어")

    st.dataframe(word_df)
