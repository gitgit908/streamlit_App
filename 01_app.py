import streamlit as st
import random
import base64
from openai import OpenAI

# -------------------------
# 페이지 설정
# -------------------------
st.set_page_config(
    page_title="🐱 내 고양이 만들기",
    page_icon="🐾",
    layout="centered"
)

# -------------------------
# CSS
# -------------------------
st.markdown("""
<style>

.stApp{
background:linear-gradient(180deg,#FFF8FB,#FFFDF7);
}

.title{
text-align:center;
font-size:48px;
font-weight:bold;
color:#ff66aa;
}

.subtitle{
text-align:center;
color:#888;
font-size:18px;
margin-bottom:25px;
}

.box{
background:white;
padding:25px;
border-radius:25px;
box-shadow:0px 6px 18px rgba(0,0,0,.08);
}

.result{
background:#fff0f8;
padding:20px;
border-radius:20px;
margin-top:20px;
}

.stButton>button{
width:100%;
height:55px;
border-radius:18px;
background:#ff7eb6;
color:white;
font-size:22px;
font-weight:bold;
border:none;
}

.stButton>button:hover{
background:#ff5aa0;
}

</style>
""", unsafe_allow_html=True)

# -------------------------
# OpenAI
# -------------------------
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# -------------------------
# 데이터
# -------------------------

personalities = [
"애교가 넘쳐나요 😻",
"호기심이 엄청 많아요 🔍",
"낮잠을 가장 좋아해요 😴",
"새벽마다 우다다를 해요 💨",
"집사만 졸졸 따라다녀요 🥰",
"도도하지만 속은 따뜻해요 🤍",
"장난치는 걸 가장 좋아해요 😆",
"창밖 새 구경을 하루 종일 해요 🐦"
]

toys = [
"깃털 낚싯대",
"레이저 포인터",
"캣닢 인형",
"종이상자",
"터널",
"장난감 쥐",
"고양이 볼",
"스크래처"
]

snacks = [
"츄르",
"닭가슴살",
"연어 트릿",
"참치 큐브",
"북어",
"동결건조 간식",
"오리 트릿",
"치킨 스틱"
]

colors = [
"치즈",
"삼색",
"고등어",
"턱시도",
"러시안블루",
"검은색",
"새하얀",
"브라운 태비"
]

eyes = [
"초록색 눈",
"파란 눈",
"호박색 눈",
"금빛 눈"
]

mbti = [
"INFP","INFJ","ENFP","ENFJ",
"ISTP","ISFP","INTP","INTJ",
"ESTP","ESFP","ENTP","ENTJ",
"ISTJ","ISFJ","ESTJ","ESFJ"
]

# -------------------------
# 화면
# -------------------------

st.markdown('<div class="title">🐱 이름으로 내 고양이 만들기</div>', unsafe_allow_html=True)

st.markdown(
'<div class="subtitle">이름만 입력하면 AI가 성격과 취향, MBTI, 그림까지 만들어줘요!</div>',
unsafe_allow_html=True
)

cat_name = st.text_input("🐾 고양이 이름")

if st.button("✨ 내 고양이 만들기"):

    if cat_name.strip()=="":
        st.warning("고양이 이름을 입력해주세요.")
        st.stop()

    random.seed(cat_name)

    personality=random.choice(personalities)
    toy=random.choice(toys)
    snack=random.choice(snacks)
    color=random.choice(colors)
    eye=random.choice(eyes)
    cat_mbti=random.choice(mbti)

    st.markdown('<div class="result">',unsafe_allow_html=True)

    st.subheader(f"🐱 {cat_name}")

    st.write(f"💖 **성격** : {personality}")
    st.write(f"🧶 **좋아하는 놀잇감** : {toy}")
    st.write(f"🍗 **좋아하는 간식** : {snack}")
    st.write(f"🧠 **MBTI** : {cat_mbti}")

    st.markdown("</div>",unsafe_allow_html=True)

    prompt=f"""
A super cute kawaii illustration of a {color} cat named {cat_name}.

The cat has {eye}.

Personality:
{personality}

Favorite toy:
{toy}

Favorite snack:
{snack}

MBTI:
{cat_mbti}

Pastel colors.

Pink background.

Children's storybook illustration.

Soft lighting.

Extremely adorable.

High quality digital art.
"""

    with st.spinner("🐾 AI가 고양이를 그리고 있어요..."):

        image=client.images.generate(
            model="gpt-image-1",
            prompt=prompt,
            size="1024x1024"
        )

        img=image.data[0].b64_json

        st.image(
            base64.b64decode(img),
            caption=f"{cat_name}의 AI 초상화 🩷",
            use_container_width=True
        )
