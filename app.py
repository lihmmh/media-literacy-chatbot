import os
import streamlit as st
import google.generativeai as genai

# ================================
# API KEY (환경변수에서 불러오기)
# ================================
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    st.error("🚨 API 키가 설정되지 않았습니다. Streamlit Cloud에서 환경변수 GEMINI_API_KEY를 지정하세요.")
    st.stop()

genai.configure(api_key=API_KEY)
model = genai.GenerativeModel("gemma-3-12b-it")


# ================================
# 1) 뉴스 생성
# ================================
def generate_random_news():
    prompt = """
    아래 조건을 만족하는 초등학생용 뉴스 기사를 웹에서 찾아와줘.
    - 5~7문장
    - 무섭지 않음
    - 진짜일 수도 있고 가짜일 수도 있음
    - 가볍고 귀여운 느낌
    - 어린이가 보기 편한 톤
    
    출력 형식:
    [기사]
    내용...
    """
    return model.generate_content(prompt).text


# ================================
# 2) 1단계 피드백 + 질문
# ================================
def chat_feedback_step1(news, first_impression, real_or_fake, reason):
    prompt = f"""
    너는 초등학생과 자연스럽게 이야기하는 친구 같은 챗봇이야.

    말투 스타일:
    - 귀엽고 부드러움
    - 너무 교사 같지 않게
    - "오!", "오호~" 등 리액션 1개 포함
    - 친구처럼 따뜻하게 정리해주기

    미디어 리터러시 역할:
    - 첫 단계에서는 '사실/의견 구분'을 가볍게 생각하도록 유도
    - 설명하지 말고, 학생이 스스로 생각하도록 질문 1개로 끝내기

    출력 규칙:
    - 전체 3~4문장
    - 마지막 문장은 반드시 학생에게 묻는 '꼬리질문 1개'

    [기사]
    {news}

    학생 첫 느낌: {first_impression}
    학생 판단: {real_or_fake}
    학생 이유: {reason}
    """
    return model.generate_content(prompt).text


# ================================
# 3) 후속 단계
# ================================
def chat_followup(step, student_answer):
    step_goal = {
        2: "기사 속 감정적이거나 과장된 표현을 떠올리게 하기",
        3: "기사에서 빠진 정보나 출처 부족을 생각하게 하기",
        4: "전체 판단을 따뜻하게 마무리하도록 돕기"
    }

    final_line_rule = (
        "마지막은 자연스럽게 이어지는 질문 1개로 끝내"
        if step < 4 else
        "마지막은 질문 없이 이 기사가 진짜일 가능성이 높은지 가짜일 가능성이 높은지 학생에게 알려주고, 학생이 어디서 잘 생각했는지, 그리고 어디서 잘못 생각했는지 제시해. 마지막 문장은 따뜻한 마무리 문장으로 끝내"
    )

    prompt = f"""
    너는 초등학생과 티키타카하는 친구 같은 챗봇이야.

    말투 스타일:
    - 가볍고 귀엽고 부드러움
    - "오!", "오호!", "그렇구나~" 같은 리액션 1개
    - 학생 말을 부드럽게 다시 정리
    - 너무 교사 말투 금지

    미디어 리터러시 목적:
    - 이번 단계 목표: {step_goal[step]}
    - 학생이 직접 생각하도록 ‘힌트 느낌’만 내기

    출력 규칙:
    - 전체 2~3문장
    - {final_line_rule}
    - 단계 번호 언급 금지

    학생의 말:
    "{student_answer}"
    """
    return model.generate_content(prompt).text


# ================================
# Streamlit UI
# ================================
st.set_page_config(page_title="미디어 리터러시 챗봇", layout="wide")

st.title("📚 미디어 리터러시 티키타카 챗봇")
st.markdown("초등학생을 위한 ‘사실/의견 구분’ 사고력 훈련 챗봇입니다 ✨")

if "news" not in st.session_state:
    st.session_state.news = None
if "step" not in st.session_state:
    st.session_state.step = 0


# ===============  뉴스 생성 버튼 ===============
if st.button("📰 새로운 뉴스 보기"):
    st.session_state.news = generate_random_news()
    st.session_state.step = 0

# ===============  뉴스 출력  ===============
if st.session_state.news:
    st.subheader("📰 오늘의 뉴스")
    st.write(st.session_state.news)

    # ======================================================
    # 1단계
    # ======================================================
    if st.session_state.step == 0:
        st.subheader("1단계: 너의 첫 느낌은 어땠어?")
        first = st.text_input("😮 처음 느낌", key="first")
        fake = st.selectbox("✨ 진짜일까 가짜일까?", ["진짜", "가짜"], key="fake")
        reason = st.text_input("🤔 왜 그렇게 생각했어?", key="reason")

        if st.button("다음 단계 ➡️"):
            reply = chat_feedback_step1(st.session_state.news, first, fake, reason)
            st.session_state.reply1 = reply
            st.session_state.step = 1

    # ======================================================
    # 1단계 답변 출력
    if st.session_state.step >= 1:
        st.subheader("💬 챗봇의 이야기")
        st.write(st.session_state.reply1)

        # 2단계
        if st.session_state.step == 1:
            ans1 = st.text_input("🙋 내 생각", key="ans1")
            if st.button("다음 단계 ➡️", key="next2"):
                st.session_state.reply2 = chat_followup(2, ans1)
                st.session_state.step = 2

    # ======================================================
    # 2단계 출력
    if st.session_state.step >= 2:
        st.write(st.session_state.reply2)

        # 3단계
        if st.session_state.step == 2:
            ans2 = st.text_input("🙋 내 생각", key="ans2")
            if st.button("다음 단계 ➡️", key="next3"):
                st.session_state.reply3 = chat_followup(3, ans2)
                st.session_state.step = 3

    # ======================================================
    # 3단계 출력
    if st.session_state.step >= 3:
        st.write(st.session_state.reply3)

        # 4단계
        if st.session_state.step == 3:
            ans3 = st.text_input("🙋 내 생각", key="ans3")
            if st.button("최종 단계 ➡️", key="next4"):
                st.session_state.reply4 = chat_followup(4, ans3)
                st.session_state.step = 4

    # ======================================================
    # 4단계 출력 (마무리)
    if st.session_state.step == 4:
        st.write("🎉 **최종 결과**")
        st.write(st.session_state.reply4)
