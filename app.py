import os
import streamlit as st
import google.generativeai as genai

# ================================
# 0. API KEY 설정
# ================================
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    st.error("🚨 API 키가 설정되지 않았습니다. Streamlit Cloud에서 환경변수 GEMINI_API_KEY를 지정하세요.")
    st.stop()

genai.configure(api_key=API_KEY)
model = genai.GenerativeModel("gemma-3-12b-it")


# ================================
# 1. 공통: 히스토리 기반 호출 함수
# ================================
def run_model_with_history(history, system_instruction: str) -> str:
    """
    history: [{"role": "user"/"assistant", "content": "..."}]
    system_instruction: 이번 단계에서 모델이 해야 할 일 설명 (한국어)
    """
    history_text = ""
    for turn in history:
        role = "학생" if turn["role"] == "user" else "챗봇"
        history_text += f"[{role}] {turn['content']}\n"

    prompt = f"""
다음은 초등학생과 챗봇이 나눈 전체 대화야.  
이 대화의 흐름을 모두 고려해서, 아래 지시를 따라 답변해 줘.

[지금까지의 대화]
{history_text}

[이번 단계에서 너의 역할과 지시]
{system_instruction}
"""

    response = model.generate_content(prompt)
    return response.text


# ================================
# 2. 뉴스 생성 함수 (난이도 반영)
# ================================
def generate_news(level: str) -> str:
    """
    level: '쉬움', '보통', '어려움'
    """
    if level == "쉬움":
        level_desc = """
        - 초등 저학년(1~3학년)이 이해할 수 있을 정도의 쉬운 단어 사용
        - 일상적인 소재 (동물, 친구, 학교, 간단한 발명 등)
        - 문장 수 4~6문장
        """
    elif level == "어려움":
        level_desc = """
        - 초등 고학년(5~6학년)을 대상으로 약간 복잡한 구조 사용
        - 뉴스처럼 보이지만, 사실/의견이 섞여 있거나 정보가 조금 모자라도록 구성
        - 수치, 전문가 인용, '아무래도', '많은 사람들은' 같은 표현을 적절히 섞기
        - 문장 수 6~8문장
        """
    else:  # 보통
        level_desc = """
        - 초등 중학년(3~5학년)을 대상으로 한 중간 난이도
        - 재미있지만 너무 유치하지 않은 내용
        - 사실 같은 정보와 의견/감정 표현이 적당히 섞이도록 구성
        - 문장 수 5~7문장
        """

    prompt = f"""
너는 초등학생을 위한 미디어 리터러시 수업에서 사용할 '가벼운 뉴스 기사'를 만드는 역할이야.

[공통 조건]
- 무섭지 않은 내용
- 진짜일 수도 있고, 가짜일 수도 있음 (판단이 애매하면 더 좋음)
- 귀엽고 유쾌한 분위기
- 어린이가 읽었을 때 부담 없는 톤
- 마지막에 사진 설명 한 줄 추가 (예: 사진: ...)

[난이도 조건]
{level_desc}

[출력 형식 예시]
<뉴스>
...(본문)...

사진: ...

반드시 위와 비슷한 형식을 지켜 줘.
"""
    return model.generate_content(prompt).text


# ================================
# 3. Streamlit 기본 설정
# ================================
st.set_page_config(page_title="미디어 리터러시 챗봇", layout="wide")
st.title("📚 미디어 리터러시 티키타카 챗봇")

st.markdown(
    "초등학생이 기사를 읽고 **사실/의견 구분, 빠진 정보 찾기, 출처 생각하기**를 연습할 수 있는 챗봇이야."
)

# 세션 상태 초기화
if "step" not in st.session_state:
    st.session_state.step = 0
if "news" not in st.session_state:
    st.session_state.news = None
if "history" not in st.session_state:
    st.session_state.history = []
if "level" not in st.session_state:
    st.session_state.level = "보통"


# ================================
# 4. 사이드바 (난이도 + 새 뉴스)
# ================================
with st.sidebar:
    st.header("⚙️ 설정")

    level = st.selectbox(
        "뉴스 난이도",
        ["쉬움", "보통", "어려움"],
        index=["쉬움", "보통", "어려움"].index(st.session_state.level),
    )
    st.session_state.level = level

    if st.button("📰 새 뉴스 불러오기"):
        st.session_state.news = generate_news(level)
        st.session_state.history = []
        st.session_state.step = 0
        st.experimental_rerun()


# ================================
# 5. 뉴스 출력
# ================================
if st.session_state.news:
    st.subheader("📰 오늘의 뉴스")
    st.write(st.session_state.news)
else:
    st.info("왼쪽 사이드바에서 **📰 새 뉴스 불러오기** 버튼을 눌러 시작해 주세요.")
    st.stop()


# ================================
# 6. 단계별 상호작용
# ================================

# ---------- STEP 0 → 1: 첫 느낌, 진짜/가짜, 이유 ----------
if st.session_state.step == 0:
    st.markdown("### 1단계: 첫 느낌을 말해볼까?")

    col1, col2 = st.columns(2)
    with col1:
        first_impression = st.text_input("😮 기사 읽고 가장 먼저 떠오른 느낌은?", key="first")
    with col2:
        real_or_fake = st.selectbox("✨ 진짜일까, 가짜일까?", ["진짜 같아", "가짜 같아", "잘 모르겠어"], key="rf")

    reason = st.text_input("🤔 왜 그렇게 생각했는지 말해줘!", key="reason")

    if st.button("챗봇에게 내 생각 보내기 ➡️"):
        if not first_impression or not reason:
            st.warning("모든 칸을 채워준 뒤 버튼을 눌러줘!")
        else:
            # 히스토리에 학생 발언 기록
            user_msg = (
                f"처음 느낌: {first_impression}, "
                f"진짜/가짜 판단: {real_or_fake}, "
                f"이유: {reason}"
            )
            st.session_state.history.append({"role": "user", "content": user_msg})

            system_instruction = f"""
너는 초등학생에게 미디어 리터러시를 가르치는 '친구 같은 챗봇'이야.

[이번 단계 목표]
- 학생의 느낌과 판단을 잘 들어주고, 요약해서 되돌려 줘.
- '사실'과 '의견'이 섞여 있을 수 있다는 것을 가볍게 떠올리게 해 줘.
- 바로 정답을 말하지 말고, 학생이 스스로 생각해 보도록 유도해.
- 아직은 자세한 설명보다 '생각해 보게 만드는 질문'이 중요해.

[말투]
- 귀엽고 따뜻하게
- "오!", "오호~", "그렇구나~" 같은 리액션 1개 포함
- 너무 교사 같지 않고, 친구처럼 편안하게

[형식]
- 3~4문장
- 마지막 문장은 항상 학생에게 묻는 **질문 1개**로 끝내기
"""

            reply = run_model_with_history(st.session_state.history, system_instruction)
            st.session_state.history.append({"role": "assistant", "content": reply})
            st.session_state.step = 1
            st.experimental_rerun()


# ---------- STEP 1 → 2: 감정적/과장 표현 찾기 ----------
if st.session_state.step >= 1:
    st.markdown("### 💬 챗봇의 이야기")
    st.write(st.session_state.history[-1]["content"])

if st.session_state.step == 1:
    st.markdown("### 2단계: 감정이 많이 담긴 표현 찾아보기")

    ans1 = st.text_input(
        "기사에서 **신나 보이거나, 무서울 것 같거나, 이상하게 과장된 느낌이 나는 문장이나 표현**이 있었어?",
        key="ans1",
    )

    if st.button("내 생각 보내기 ➡️", key="btn_step2"):
        if not ans1:
            st.warning("한 줄이라도 괜찮으니까 적어줘!")
        else:
            st.session_state.history.append({"role": "user", "content": ans1})

            system_instruction = """
[이번 단계 목표]
- 학생이 감정적/과장된 표현을 떠올리도록 돕기
- 그런 표현이 왜 사실과 의견을 섞이게 만들 수 있는지 '힌트' 정도만 알려주기
- 학생이 잘 관찰한 부분은 꼭 칭찬하기

[오해 교정]
- 학생이 '사실인데 감정적' / '완전한 오해'를 말하면,
  ▷ "이 부분은 사실이지만, 이렇게 느껴질 수 있어"  
  ▷ "여긴 실제로는 이렇게 되어 있어"  
  이런 식으로 부드럽게 바로잡아 줘.

[형식]
- 2~3문장
- 마지막 문장은 다시 한 번 생각을 이어가도록 질문 1개로 끝내기
"""

            reply = run_model_with_history(st.session_state.history, system_instruction)
            st.session_state.history.append({"role": "assistant", "content": reply})
            st.session_state.step = 2
            st.experimental_rerun()


# ---------- STEP 2 → 3: 빠진 정보/출처 생각하기 ----------
if st.session_state.step == 2:
    st.markdown("### 3단계: 빠진 정보나 궁금한 점 떠올리기")

    ans2 = st.text_input(
        "이 기사를 읽으면서 **'이런 건 안 나와 있네?'**, "
        "**'누가 말한 거지?'**, **'언제 일인지 모르겠는데?'**처럼 "
        '빠져 있는 정보나 궁금했던 점이 있었어?',
        key="ans2",
    )

    if st.button("내 생각 보내기 ➡️", key="btn_step3"):
        if not ans2:
            st.warning("생각이 잘 안 나면 '잘 모르겠어'라고 적어도 괜찮아!")
        else:
            st.session_state.history.append({"role": "user", "content": ans2})

            system_instruction = """
[이번 단계 목표]
- 기사에서 빠져 있을 수 있는 정보(언제, 어디서, 누가, 얼마나, 출처 등)를 함께 떠올리게 하기
- '출처가 없으면 왜 조심해야 하는지'를 너무 어렵지 않게 설명하기
- 학생이 이미 잘 짚은 부분이 있다면 꼭 칭찬하기

[형식]
- 2~3문장
- 마지막 문장은 다시 한 번 생각을 정리해 보도록 하는 질문 1개로 끝내기
"""

            reply = run_model_with_history(st.session_state.history, system_instruction)
            st.session_state.history.append({"role": "assistant", "content": reply})
            st.session_state.step = 3
            st.experimental_rerun()


# ---------- STEP 3 → 4: 최종 판단 + 학습 정리 ----------
if st.session_state.step == 3:
    st.markdown("### 4단계: 다시 생각해 본 최종 판단")

    ans3 = st.text_input(
        "여기까지 생각해보니, **이 기사는 진짜일 가능성이 더 커? 가짜일 가능성이 더 커?** "
        "그리고 가장 중요한 이유 1~2가지만 적어줘!",
        key="ans3",
    )

    if st.button("최종 정리 보기 🎉", key="btn_step4"):
        if not ans3:
            st.warning("간단히 한 줄만 적어줘도 괜찮아!")
        else:
            st.session_state.history.append({"role": "user", "content": ans3})

            system_instruction = """
너는 지금까지의 대화를 바탕으로 학생의 생각을 함께 정리해 주는 역할이야.

[이번 단계 목표]
1) 이 기사가 **진짜일 가능성이 높은지 / 가짜일 가능성이 높은지**에 대해,
   - 단정이 아니라 '가능성이 더 커 보이는 쪽'을 부드럽게 말해줘.
2) 학생이 잘 생각한 부분을 구체적으로 2~3개 칭찬해 줘.
3) 학생의 판단 중에서 '사실과 다른 부분'이나 '더 살펴보면 좋을 부분'이 있다면,
   - "이 부분은 사실은 ~~야" 처럼 부드럽게 바로잡아 주고 이유를 설명해 줘.

[오늘의 정리(명시적 기준)]
마지막에는 **<오늘의 정리>** 라는 제목 아래,
- 3~5줄 정도로 '사실/의견을 구분하는 기준'과
- '기사를 볼 때 꼭 확인해야 할 정보(언제, 어디, 누가, 얼마나, 출처 등)'
을 bullet(-) 형식으로 정리해 줘.

[형식]
1) 먼저 학생에게 말해주는 글 4~6문장
2) 빈 줄 한 줄
3) "<오늘의 정리>"라는 제목
4) 그 아래에 - 로 시작하는 bullet 정리 3~5개
질문으로 끝내지 말고, 따뜻한 응원 문장으로 마무리해.
"""

            reply = run_model_with_history(st.session_state.history, system_instruction)
            st.session_state.history.append({"role": "assistant", "content": reply})
            st.session_state.step = 4
            st.experimental_rerun()


# ---------- STEP 4: 최종 출력 ----------
if st.session_state.step == 4:
    st.markdown("### 🎉 최종 결과 & 오늘의 정리")
    st.write(st.session_state.history[-1]["content"])

    st.markdown("---")
    if st.button("다른 뉴스로 다시 해보기 🔁"):
        # 히스토리와 단계만 초기화하고, 뉴스는 유지할지 여부 선택 가능
        st.session_state.history = []
        st.session_state.step = 0
        st.experimental_rerun()
