import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib import rc

import requests
import re
import io
from datetime import datetime
from collections import Counter

from wordcloud import WordCloud

from konlpy.tag import Okt

from textblob import TextBlob

st.set_page_config(
    page_title="유튜브 댓글 분석기",
    page_icon="📺",
    layout="wide"
)

####################################################
# FONT
####################################################

FONT_PATH = "youtube/NanumGothic.ttf"

fontprop = fm.FontProperties(fname=FONT_PATH)

rc("font", family=fontprop.get_name())

plt.rcParams["axes.unicode_minus"] = False

####################################################
# API
####################################################

API_KEY = st.secrets["YOUTUBE_API_KEY"]

####################################################
# FUNCTIONS
####################################################

def extract_video_id(url):

    patterns = [
        r"v=([A-Za-z0-9_-]{11})",
        r"youtu\.be\/([A-Za-z0-9_-]{11})",
        r"shorts\/([A-Za-z0-9_-]{11})"
    ]

    for p in patterns:

        m = re.search(p, url)

        if m:
            return m.group(1)

    return None


def get_video_info(video_id):

    url = "https://www.googleapis.com/youtube/v3/videos"

    params = {

        "part":"snippet,statistics",

        "id":video_id,

        "key":API_KEY

    }

    res = requests.get(url,params=params)

    data = res.json()

    if len(data["items"]) == 0:

        return None

    item = data["items"][0]

    return {

        "title":item["snippet"]["title"],

        "channel":item["snippet"]["channelTitle"],

        "published":item["snippet"]["publishedAt"],

        "viewCount":int(item["statistics"].get("viewCount",0)),

        "likeCount":int(item["statistics"].get("likeCount",0))

    }


def get_comments(video_id,max_comments):

    comments=[]

    next_page=""

    while len(comments)<max_comments:

        url="https://www.googleapis.com/youtube/v3/commentThreads"

        params={

            "part":"snippet",

            "videoId":video_id,

            "maxResults":100,

            "textFormat":"plainText",

            "key":API_KEY

        }

        if next_page!="":

            params["pageToken"]=next_page

        res=requests.get(url,params=params)

        data=res.json()

        if "items" not in data:

            break

        for item in data["items"]:

            s=item["snippet"]["topLevelComment"]["snippet"]

            comments.append({

                "작성자":s["authorDisplayName"],

                "댓글":s["textDisplay"],

                "좋아요":s["likeCount"],

                "작성시간":s["publishedAt"]

            })

            if len(comments)>=max_comments:

                break

        if "nextPageToken" not in data:

            break

        next_page=data["nextPageToken"]

    return pd.DataFrame(comments)


def preprocess_dataframe(df):

    df["작성시간"]=pd.to_datetime(df["작성시간"])

    df["날짜"]=df["작성시간"].dt.date

    df["시간"]=df["작성시간"].dt.hour

    return df


####################################################
# TITLE
####################################################

st.title("📺 유튜브 댓글 분석기")

####################################################
# URL
####################################################

youtube_url=st.text_input(
    "유튜브 링크 입력"
)

####################################################
# COUNT
####################################################

comment_count=st.number_input(

    "댓글 개수",

    min_value=100,

    max_value=5000,

    value=1000,

    step=100

)

####################################################
# START
####################################################

if st.button("댓글 수집 시작"):

    video_id=extract_video_id(youtube_url)

    if video_id is None:

        st.error("올바른 유튜브 주소가 아닙니다.")

        st.stop()

    info=get_video_info(video_id)

    if info is None:

        st.error("영상 정보를 가져올 수 없습니다.")

        st.stop()

    st.subheader(info["title"])

    st.write("채널 :",info["channel"])

    st.write("조회수 :",format(info["viewCount"],","))

    st.write("좋아요 :",format(info["likeCount"],","))

    st.video(youtube_url)

    progress=st.progress(0)

    status=st.empty()

    status.write("댓글 수집중...")

    df=get_comments(video_id,comment_count)

    progress.progress(40)

    df=preprocess_dataframe(df)

    progress.progress(100)

    status.success(f"{len(df)}개의 댓글 수집 완료")
####################################################
# ANALYSIS
####################################################

if "comment_df" in st.session_state:

    df = st.session_state["comment_df"]

    ####################################################
    # BASIC
    ####################################################

    st.divider()

    st.header("📊 기본 통계")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "댓글 수",
        len(df)
    )

    col2.metric(
        "평균 좋아요",
        round(df["좋아요"].mean(), 2)
    )

    col3.metric(
        "최대 좋아요",
        int(df["좋아요"].max())
    )

    col4.metric(
        "좋아요 총합",
        int(df["좋아요"].sum())
    )

    ####################################################
    # HOUR
    ####################################################

    st.divider()

    st.header("🕒 시간대별 댓글 작성 추이")

    hour_df = (
        df.groupby("시간")
        .size()
        .reset_index(name="댓글수")
        .sort_values("시간")
    )

    fig, ax = plt.subplots(figsize=(10, 4))

    ax.plot(
        hour_df["시간"],
        hour_df["댓글수"],
        marker="o"
    )

    ax.set_xlabel("시간")

    ax.set_ylabel("댓글 수")

    ax.set_title("시간대별 댓글 작성 추이")

    ax.grid(True)

    st.pyplot(fig)

    ####################################################
    # DATE
    ####################################################

    st.divider()

    st.header("📅 날짜별 댓글 작성 추이")

    date_df = (
        df.groupby("날짜")
        .size()
        .reset_index(name="댓글수")
    )

    date_df = date_df.sort_values("날짜")

    fig, ax = plt.subplots(figsize=(12, 5))

    ax.plot(
        date_df["날짜"].astype(str),
        date_df["댓글수"],
        marker="o"
    )

    ax.tick_params(
        axis="x",
        rotation=45
    )

    ax.set_xlabel("날짜")

    ax.set_ylabel("댓글 수")

    ax.set_title("날짜별 댓글 작성 추이")

    ax.grid(True)

    st.pyplot(fig)

    ####################################################
    # LIKE
    ####################################################

    st.divider()

    st.header("👍 좋아요 통계")

    like_col1, like_col2, like_col3 = st.columns(3)

    like_col1.metric(
        "평균",
        round(df["좋아요"].mean(), 2)
    )

    like_col2.metric(
        "중앙값",
        int(df["좋아요"].median())
    )

    like_col3.metric(
        "최대",
        int(df["좋아요"].max())
    )

    st.write("좋아요 분포")

    fig, ax = plt.subplots(figsize=(9, 4))

    ax.hist(
        df["좋아요"],
        bins=30
    )

    ax.set_xlabel("좋아요")

    ax.set_ylabel("댓글 수")

    st.pyplot(fig)

    ####################################################
    # TOP20
    ####################################################

    st.divider()

    st.header("🏆 좋아요 TOP20")

    top20 = (
        df.sort_values(
            "좋아요",
            ascending=False
        )
        .head(20)
        .reset_index(drop=True)
    )

    top20.index = top20.index + 1

    st.dataframe(
        top20,
        use_container_width=True
    )

    ####################################################
    # BAR
    ####################################################

    fig, ax = plt.subplots(figsize=(10, 8))

    y = np.arange(len(top20))

    ax.barh(
        y,
        top20["좋아요"]
    )

    ax.set_yticks(y)

    ax.set_yticklabels(
        [str(i) for i in range(1, len(top20) + 1)]
    )

    ax.invert_yaxis()

    ax.set_xlabel("좋아요")

    ax.set_title("좋아요 TOP20")

    st.pyplot(fig)

    ####################################################
    # SEARCH
    ####################################################

    st.divider()

    st.header("🔍 댓글 검색")

    keyword = st.text_input(
        "검색어 입력"
    )

    if keyword:

        result_df = df[
            df["댓글"].str.contains(
                keyword,
                case=False,
                na=False
            )
        ]

        st.write(
            f"검색 결과 : {len(result_df)}개"
        )

        st.dataframe(
            result_df,
            use_container_width=True
        )
          ####################################################
    # TEXT ANALYSIS
    ####################################################

    st.divider()

    st.header("📝 텍스트 분석")

    okt = Okt()

    stopwords = {

        "것","수","등","더","좀","진짜","정말","너무","그냥","그리고",
        "입니다","있다","있는","합니다","하면","해서","에서","으로",
        "에게","까지","처럼","대한","하는","했다","하는데","하는게",
        "영상","유튜브","댓글","오늘","이번","저는","나는","우리",
        "입니다","ㅋㅋ","ㅎㅎ","ㅠㅠ","ㅜㅜ","ㅋㅋㅋ","ㅎㅎㅎ","ㄷㄷ",
        "진심","완전","진짜로","입니다","있어요","하세요","됩니다"
    }

    text_list = []

    for text in df["댓글"]:

        if pd.isna(text):
            continue

        text = str(text)

        text = re.sub(r"http\S+", " ", text)
        text = re.sub(r"www\S+", " ", text)
        text = re.sub(r"[^가-힣A-Za-z0-9 ]", " ", text)
        text = re.sub(r"\s+", " ", text)

        nouns = okt.nouns(text)

        for word in nouns:

            word = word.strip()

            if len(word) < 2:
                continue

            if word in stopwords:
                continue

            text_list.append(word)

    ####################################################
    # WORD COUNT
    ####################################################

    counter = Counter(text_list)

    word_df = pd.DataFrame(

        counter.items(),

        columns=["단어","빈도"]

    )

    word_df = word_df.sort_values(

        "빈도",

        ascending=False

    ).reset_index(drop=True)

    ####################################################
    # WORDCLOUD
    ####################################################

    st.divider()

    st.header("☁️ 한글 워드클라우드")

    if len(counter) == 0:

        st.warning("워드클라우드를 생성할 단어가 없습니다.")

    else:

        wc = WordCloud(

            font_path=FONT_PATH,

            width=1200,

            height=700,

            background_color="white",

            max_words=300,

            collocations=False

        )

        wc.generate_from_frequencies(counter)

        fig, ax = plt.subplots(figsize=(14, 8))

        ax.imshow(wc)

        ax.axis("off")

        st.pyplot(fig)

    ####################################################
    # TOP30 WORD
    ####################################################

    st.divider()

    st.header("📈 단어 TOP30")

    top30 = word_df.head(30)

    st.dataframe(

        top30,

        use_container_width=True

    )

    fig, ax = plt.subplots(figsize=(12, 10))

    ax.barh(

        top30["단어"],

        top30["빈도"]

    )

    ax.invert_yaxis()

    ax.set_xlabel("빈도")

    ax.set_ylabel("단어")

    ax.set_title("단어 TOP30")

    st.pyplot(fig)

    ####################################################
    # WORD SEARCH
    ####################################################

    st.divider()

    st.header("🔎 단어 검색")

    search_word = st.text_input(

        "단어 검색"

    )

    if search_word != "":

        if search_word in counter:

            st.success(

                f"'{search_word}' 등장 횟수 : {counter[search_word]}회"

            )

        else:

            st.warning("등장하지 않은 단어입니다.")

    ####################################################
    # FREQUENCY TABLE
    ####################################################

    st.divider()

    st.header("📋 전체 단어 빈도")

    st.dataframe(

        word_df,

        use_container_width=True,

        height=500

    )
      ####################################################
    # SENTIMENT ANALYSIS
    ####################################################

    st.divider()

    st.header("😊 감성분석")

    def analyze_sentiment(text):

        if pd.isna(text):
            return "중립"

        try:

            polarity = TextBlob(str(text)).sentiment.polarity

        except Exception:

            return "중립"

        if polarity > 0.1:
            return "긍정"

        elif polarity < -0.1:
            return "부정"

        else:
            return "중립"

    sentiment_df = df.copy()

    sentiment_df["감성"] = sentiment_df["댓글"].apply(analyze_sentiment)

    sentiment_count = (
        sentiment_df["감성"]
        .value_counts()
        .reindex(["긍정", "중립", "부정"], fill_value=0)
    )

    col1, col2, col3 = st.columns(3)

    col1.metric("긍정", int(sentiment_count["긍정"]))
    col2.metric("중립", int(sentiment_count["중립"]))
    col3.metric("부정", int(sentiment_count["부정"]))

    fig, ax = plt.subplots(figsize=(6, 6))

    ax.pie(
        sentiment_count.values,
        labels=sentiment_count.index,
        autopct="%1.1f%%",
        startangle=90
    )

    ax.set_title("감성 분포")

    st.pyplot(fig)

    ####################################################
    # SUMMARY
    ####################################################

    st.divider()

    st.header("📌 분석 요약")

    if len(word_df) > 0:
        top_keyword = word_df.iloc[0]["단어"]
        top_keyword_count = int(word_df.iloc[0]["빈도"])
    else:
        top_keyword = "-"
        top_keyword_count = 0

    st.write(f"• 총 댓글 수 : **{len(df):,}개**")
    st.write(f"• 총 좋아요 수 : **{int(df['좋아요'].sum()):,}개**")
    st.write(f"• 평균 좋아요 : **{df['좋아요'].mean():.2f}개**")
    st.write(f"• 가장 많이 등장한 단어 : **{top_keyword} ({top_keyword_count}회)**")
    st.write(f"• 긍정 댓글 : **{int(sentiment_count['긍정']):,}개**")
    st.write(f"• 중립 댓글 : **{int(sentiment_count['중립']):,}개**")
    st.write(f"• 부정 댓글 : **{int(sentiment_count['부정']):,}개**")

    ####################################################
    # CSV DOWNLOAD
    ####################################################

    st.divider()

    st.header("💾 CSV 다운로드")

    download_df = sentiment_df.copy()

    download_df["작성시간"] = (
        download_df["작성시간"]
        .astype(str)
    )

    csv = download_df.to_csv(
        index=False,
        encoding="utf-8-sig"
    )

    st.download_button(
        label="📥 댓글 분석 CSV 다운로드",
        data=csv,
        file_name="youtube_comment_analysis.csv",
        mime="text/csv"
    )

    ####################################################
    # RAW DATA
    ####################################################

    st.divider()

    with st.expander("원본 댓글 데이터 보기"):

        st.dataframe(
            sentiment_df,
            use_container_width=True,
            height=500
        )

    ####################################################
    # FINISH
    ####################################################

    st.success("모든 분석이 완료되었습니다.")
    st.session_state["comment_df"]=df
