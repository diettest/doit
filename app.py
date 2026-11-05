import sqlite3, calendar
from datetime import date
from pathlib import Path
import pandas as pd
import streamlit as st

st.set_page_config(page_title="건강 습관 플래너", page_icon="🌿", layout="wide")
st.markdown("""
<style>
:root { color-scheme: dark; }
html, body, .stApp, [data-testid="stAppViewContainer"],
[data-testid="stMain"], [data-testid="stMainBlockContainer"] {
    background: #101722 !important;
    color: #ffffff !important;
}
/* 모든 일반 텍스트를 흰색으로 강제 */
.stApp p, .stApp span, .stApp label, .stApp li,
.stApp h1, .stApp h2, .stApp h3, .stApp h4,
.stApp [data-testid="stMarkdownContainer"],
.stApp [data-testid="stCaptionContainer"],
.stApp [data-testid="stWidgetLabel"],
.stApp [data-testid="stHeader"],
.stApp [data-testid="stMetricLabel"],
.stApp [data-testid="stMetricValue"],
.stApp [data-testid="stAlert"] *,
[data-testid="stSidebar"] *,
[data-testid="stRadio"] *,
[data-testid="stSelectbox"] *,
[data-testid="stSelectSlider"] *,
[data-testid="stNumberInput"] *,
[data-testid="stDateInput"] *,
[data-testid="stDataFrame"] * {
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    opacity: 1 !important;
}
.block-container { max-width: 1100px; padding-top: 2rem; }
[data-testid="stSidebar"], [data-testid="stSidebar"] > div {
    background: #172131 !important;
}
div[data-testid="stForm"], [data-testid="stVerticalBlockBorderWrapper"] {
    background: #1b2636 !important;
    border: 1px solid #46556b !important;
    border-radius: 14px !important;
}
/* 선택 상자와 입력칸은 어두운 바탕 */
[data-baseweb="select"] > div,
[data-baseweb="select"] input,
[data-baseweb="input"] > div,
[data-baseweb="textarea"] > div,
.stApp input, .stApp textarea {
    background: #111a27 !important;
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    border-color: #718096 !important;
    opacity: 1 !important;
}
[data-baseweb="select"] *, [data-baseweb="popover"] *,
[data-baseweb="menu"] *, [role="listbox"] *, [role="option"] * {
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    background-color: #1b2636 !important;
}
.stApp input::placeholder, .stApp textarea::placeholder {
    color: #d1d5db !important;
    -webkit-text-fill-color: #d1d5db !important;
    opacity: 1 !important;
}
[data-testid="stAlert"] {
    background: #1b304b !important;
    border: 1px solid #4b83bd !important;
}
[data-testid="stDataFrame"], [data-testid="stTable"] {
    background: #1b2636 !important;
}
div.stButton > button, div[data-testid="stFormSubmitButton"] button {
    background: #2563eb !important;
    color: #ffffff !important;
    border: 1px solid #60a5fa !important;
    border-radius: 10px !important;
    min-height: 42px;
}
div.stButton > button *, div[data-testid="stFormSubmitButton"] button * {
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
}
</style>
""", unsafe_allow_html=True)
st.title("건강 습관 플래너")
st.caption("한국어로 제공되는 맞춤형 식사·신체활동 계획과 생활 습관 기록")
st.info("성장기 사용자를 고려해 체중 감량 처방, 칼로리 제한, BMI/BMR/TDEE 기반 감량 계산 및 체중 도달일 예측은 제공하지 않습니다. 건강한 식사·활동·휴식 습관을 관리합니다.")

DB = Path(__file__).parent / "health_habit_log.db"
def db_init():
    with sqlite3.connect(DB) as c:
        c.execute("""CREATE TABLE IF NOT EXISTS logs(
        day TEXT PRIMARY KEY, breakfast INTEGER, lunch INTEGER, dinner INTEGER,
        activity INTEGER, rest INTEGER, water INTEGER, memo TEXT)""")
def get_logs():
    with sqlite3.connect(DB) as c:
        return pd.read_sql_query("SELECT * FROM logs ORDER BY day", c)
def save_log(day, vals, memo):
    with sqlite3.connect(DB) as c:
        c.execute("""INSERT INTO logs VALUES(?,?,?,?,?,?,?,?)
        ON CONFLICT(day) DO UPDATE SET breakfast=excluded.breakfast,lunch=excluded.lunch,
        dinner=excluded.dinner,activity=excluded.activity,rest=excluded.rest,
        water=excluded.water,memo=excluded.memo""",
        (day.isoformat(), *[int(v) for v in vals], memo))
db_init()

with st.sidebar:
    st.header("메뉴")
    page = st.radio("화면 선택", ["맞춤 계획 만들기", "하루 기록하기", "달력 및 그래프", "설정 및 사용법"], label_visibility="collapsed")

if page == "맞춤 계획 만들기":
    st.header("나에게 맞는 건강 습관 계획 만들기")
    with st.form("profile"):
        a,b = st.columns(2)
        with a:
            age = st.selectbox("나이", ["13~15세","16~17세","18~19세","20세 이상"])
            activity = st.radio("평소 활동량", ["낮음","보통","높음"], horizontal=True)
            intensity = st.radio("원하는 운동 난이도", ["낮음","보통","높음"], horizontal=True)
        with b:
            food = st.selectbox("식사 선호", ["한식 위주","간단한 음식","채식 위주","특별한 선호 없음"])
            time = st.select_slider("하루 활동 가능 시간", ["10~15분","20~30분","30~45분","상황에 따라 다름"], value="20~30분")
            goal = st.selectbox("중요한 목표", ["규칙적인 식사","체력 기르기","유연성 향상","일상 활동 늘리기","건강한 생활 습관 만들기"])
        allergies = st.text_input("알레르기 또는 피해야 하는 음식", placeholder="없으면 없음")
        likes = st.text_input("좋아하거나 피하고 싶은 운동 (선택)")
        submit = st.form_submit_button("맞춤 계획 생성하기", type="primary", use_container_width=True)
    if submit:
        def make_plan(age, activity, intensity, food, time, goal, allergies, likes):
            # 사용자가 적은 알레르기·회피 음식은 메뉴명에 포함된 경우 제외한다.
            avoid = [x.strip().lower() for x in allergies.replace("，", ",").split(",") if x.strip() and x.strip() != "없음"]

            meal_sets = {
                "한식 위주": [
                    ("밥, 달걀찜, 김, 과일", "밥, 두부조림, 나물, 국", "밥, 생선구이 또는 두부구이, 채소"),
                    ("밥, 맑은 국, 달걀, 과일", "밥, 닭고기 또는 콩 반찬, 채소", "밥, 된장국, 버섯볶음"),
                ],
                "간단한 음식": [
                    ("통밀빵 또는 식빵, 우유나 두유, 과일", "주먹밥, 달걀 또는 두부, 채소", "샌드위치와 수프"),
                    ("오트밀과 과일, 우유나 두유", "밥과 단백질 반찬, 채소", "감자와 달걀 또는 콩 요리, 채소"),
                ],
                "채식 위주": [
                    ("두유와 오트밀, 과일", "콩·두부 반찬과 밥, 채소", "채소볶음밥과 두부"),
                    ("통밀빵, 견과류 대신 씨앗류 선택 가능, 과일", "렌틸콩 또는 두부 덮밥", "채소카레와 밥"),
                ],
                "특별한 선호 없음": [
                    ("밥 또는 빵, 달걀이나 두부, 과일", "밥, 고기·생선·콩 중 한 가지, 채소", "밥, 단백질 반찬, 채소"),
                    ("요거트 또는 두유, 곡류, 과일", "국·밥·반찬을 골고루", "면이나 밥 요리와 단백질·채소 곁들이기"),
                ],
            }
            seed = sum(ord(ch) for ch in (age + activity + intensity + food + time + goal))
            meals = meal_sets[food][seed % len(meal_sets[food])]
            meal_labels = ["아침", "점심", "저녁"]
            meal_lines = []
            for label, meal in zip(meal_labels, meals):
                if any(term in meal.lower() for term in avoid):
                    meal = "알레르기 유발 식품이 들어가지 않는 익숙하고 균형 잡힌 식사로 선택하세요. 식품 표시와 조리 재료를 확인하세요."
                meal_lines.append(f"- {label}: {meal}")
                if label == "저녁":
                    meal_lines.append("  - 식사 안내: 식사량을 줄이거나 끼니를 거르지 말고, 평소 식사에서 여러 식품을 골고루 선택하세요.")

            activity_options = {
                "체력 기르기": ["편안한 속도로 걷기", "좋아하는 음악에 맞춰 춤추기", "가벼운 맨몸 체조", "공놀이 또는 배드민턴처럼 즐거운 놀이 활동", "실내 자전거 타기"],
                "유연성 향상": ["목·어깨·등·다리의 부드러운 스트레칭", "통증이 없는 범위에서 하는 가벼운 관절 움직임", "천천히 호흡하며 전신 스트레칭", "초보자용 요가 동작 따라 하기"],
                "일상 활동 늘리기": ["가까운 거리는 걷기", "집안 정리나 가벼운 청소하기", "좋아하는 음악에 맞춰 움직이기", "쉬는 시간마다 자리에서 일어나 몸 풀기", "가족이나 친구와 가벼운 공놀이 하기"],
                "규칙적인 식사": ["식사 시간을 정하고 알림 설정하기", "식사 전후로 가볍게 걷기", "식사 준비를 돕거나 식탁 정리하기", "식사 사이에 가볍게 스트레칭하기"],
                "건강한 생활 습관 만들기": ["산책하기", "가벼운 스트레칭이나 요가하기", "좋아하는 음악에 맞춰 춤추기", "실내에서 가볍게 체조하기", "친구나 가족과 즐거운 놀이 활동하기"],
            }
            movements = activity_options[goal]
            first = seed % len(movements)
            selected_movements = [movements[first], movements[(first + 1) % len(movements)]]
            if likes.strip():
                selected_movements.append(f"선호하는 활동: {likes.strip()}")
            movement_text = "\n".join(f"- {item}" for item in selected_movements)

            duration = {
                "10~15분": "10~15분 정도부터 편안하게 시작하세요.",
                "20~30분": "20~30분 안에서 컨디션에 맞게 나누어 해도 됩니다.",
                "30~45분": "30~45분을 한 번에 할 필요는 없으며 중간에 쉬어도 됩니다.",
                "상황에 따라 다름": "가능한 시간에 짧게 나누어 실천하세요.",
            }[time]
            level = {
                "낮음": "대화가 가능한 편안한 강도로 진행하세요.",
                "보통": "몸 상태를 살피며 편안함과 약간의 도전 사이에서 조절하세요.",
                "높음": "난이도를 높이기보다 자세와 안전을 우선하고 충분히 쉬세요.",
            }[intensity]
            activity_note = {
                "낮음": "평소 활동량이 적다면 짧고 편안한 움직임부터 시작하세요.",
                "보통": "현재 생활 리듬을 유지하면서 활동을 조금씩 다양하게 해보세요.",
                "높음": "활동량이 많더라도 회복 시간과 휴식일을 챙기세요.",
            }[activity]

            return f"""## 1. 오늘의 생활 습관 목표
{goal}에 초점을 맞추고, 할 수 있는 만큼 꾸준히 실천합니다.

## 2. 균형 잡힌 식사 예시
{chr(10).join(meal_lines)}

## 3. 신체활동
추천 활동 예시:
{movement_text}
- 시간: {duration}
- 조절: {level}
- 참고: {activity_note}

## 4. 휴식과 수면
- 잠자리에 드는 시간을 일정하게 유지해 보세요.
- 활동 사이에 쉬는 시간을 두고, 피곤하면 충분히 휴식하세요.

## 5. 안전 주의사항
- 통증, 어지럼, 숨이 많이 차는 느낌 또는 과도한 피로가 있으면 활동을 멈추고 쉬세요.
- 알레르기나 식품 제한이 있다면 제품 표시와 조리 재료를 반드시 확인하고, 불확실하면 보호자나 전문가에게 확인하세요.
- 이 계획은 일반적인 생활 습관 예시이며 개인별 의료·영양 상담을 대신하지 않습니다.
"""

        st.session_state["plan"] = make_plan(age, activity, intensity, food, time, goal, allergies, likes)
        st.success("맞춤 계획을 만들었습니다. 입력한 조건을 바탕으로 기본 계획을 조합했습니다.")
    if st.session_state.get("plan"):
        st.divider()
        st.subheader("나의 맞춤 건강 습관 계획")
        st.markdown(st.session_state["plan"])
        st.download_button("계획표 다운로드", st.session_state["plan"], "건강_습관_계획.txt", "text/plain")

elif page == "하루 기록하기":
    st.header("하루 건강 습관 기록")
    st.write("체중 대신 매일의 건강 습관을 체크합니다.")
    with st.form("daily"):
        day = st.date_input("기록 날짜", date.today())
        x,y = st.columns(2)
        with x:
            breakfast = st.checkbox("아침 식사를 챙겼어요")
            lunch = st.checkbox("점심 식사를 챙겼어요")
            dinner = st.checkbox("저녁 식사를 챙겼어요")
        with y:
            activity = st.checkbox("즐거운 신체활동을 했어요")
            rest = st.checkbox("충분히 쉬고 잠을 잤어요")
            water = st.checkbox("물을 자주 마셨어요")
        memo = st.text_area("오늘의 메모 (선택)")
        save = st.form_submit_button("기록 저장하기", type="primary", use_container_width=True)
    if save:
        save_log(day,[breakfast,lunch,dinner,activity,rest,water],memo)
        st.success("기록을 저장했습니다.")
    logs = get_logs()
    if not logs.empty:
        st.subheader("최근 기록")
        recent=logs.tail(7).copy()
        recent["실천 항목 수"]=recent[["breakfast","lunch","dinner","activity","rest","water"]].sum(axis=1)
        st.dataframe(recent[["day","실천 항목 수","memo"]].rename(columns={"day":"날짜","memo":"메모"}),hide_index=True,use_container_width=True)

elif page == "달력 및 그래프":
    st.header("기록 달력 및 그래프")
    today=date.today()
    c1,c2=st.columns(2)
    year=c1.number_input("연도",2020,2100,today.year)
    month=c2.selectbox("월",range(1,13),index=today.month-1)
    logs=get_logs()
    dates=set(logs["day"].tolist()) if not logs.empty else set()
    rows=[]
    for week in calendar.Calendar(firstweekday=6).monthdayscalendar(int(year),int(month)):
        row=[]
        for n in week:
            if not n: row.append("")
            else:
                key=date(int(year),int(month),n).isoformat()
                row.append(f"{n} ●" if key in dates else str(n))
        rows.append(row)
    st.dataframe(pd.DataFrame(rows,columns=["일","월","화","수","목","금","토"]),hide_index=True,use_container_width=True)
    st.caption("● 표시가 있는 날짜에는 기록이 저장되어 있습니다.")
    if not logs.empty:
        logs["날짜"]=pd.to_datetime(logs["day"])
        logs["실천 항목 수"]=logs[["breakfast","lunch","dinner","activity","rest","water"]].sum(axis=1)
        st.subheader("생활 습관 실천 그래프")
        st.line_chart(logs.set_index("날짜")[["실천 항목 수"]])
        st.dataframe(logs[["day","실천 항목 수","memo"]].rename(columns={"day":"날짜","memo":"메모"}).sort_values("날짜",ascending=False),hide_index=True,use_container_width=True)
    else: st.info("아직 기록이 없습니다. 하루 기록하기에서 첫 기록을 저장하세요.")

else:
    st.header("설정 및 사용 방법")
    st.markdown("""
**사용 순서**
1. 맞춤 계획 만들기에서 목록과 버튼으로 정보를 선택합니다.
2. 맞춤 계획 생성하기를 누르면 입력 조건에 맞춘 계획표가 만들어집니다.
3. 하루 기록하기에서 실천한 습관을 체크하고 저장합니다.
4. 달력 및 그래프에서 기록을 확인합니다.

**계획 생성 방식**
별도의 API 키나 결제 없이 프로그램 안의 예시와 규칙을 조합해 계획을 만듭니다. 생성형 AI가 직접 답변하는 기능은 포함되어 있지 않습니다.

**실행**
```bash
pip install -r requirements.txt
streamlit run app.py
```

기록은 `health_habit_log.db`에 저장됩니다. 배포 환경에 따라 재배포 시 기록이 초기화될 수 있으므로 장기 운영에는 별도 데이터베이스가 필요합니다.
""")
st.sidebar.divider()
st.sidebar.caption("건강 습관 플래너 · 한국어 GUI")
