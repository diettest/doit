import os, sqlite3, calendar
from datetime import date
from pathlib import Path
import pandas as pd
import streamlit as st
from openai import OpenAI

st.set_page_config(page_title="AI 건강 습관 플래너", page_icon="🌿", layout="wide")
st.markdown("""
<style>
.block-container{max-width:1100px;padding-top:2rem}
div[data-testid="stForm"]{background:white;padding:20px;border:1px solid #e7ebf0;border-radius:14px}
div.stButton>button{border-radius:10px;min-height:42px}
</style>
""", unsafe_allow_html=True)
st.title("AI 건강 습관 플래너")
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
    page = st.radio("화면 선택", ["AI 계획 만들기", "하루 기록하기", "달력 및 그래프", "설정 및 사용법"], label_visibility="collapsed")

if page == "AI 계획 만들기":
    st.header("나에게 맞는 계획 만들기")
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
        submit = st.form_submit_button("AI 계획 생성하기", type="primary", use_container_width=True)
    if submit:
        key = os.getenv("OPENAI_API_KEY","").strip()
        try:
            if not key: key = str(st.secrets["OPENAI_API_KEY"]).strip()
        except Exception: pass
        if not key:
            st.error("OpenAI API 키가 설정되지 않았습니다. 설정 및 사용법을 확인하세요.")
        else:
            profile = f"나이: {age}\n활동량: {activity}\n운동 난이도: {intensity}\n식사 선호: {food}\n활동 가능 시간: {time}\n중요한 목표: {goal}\n알레르기: {allergies}\n운동 선호: {likes}"
            rules = """한국어로 답하는 청소년 건강 습관 코치다. 사용자의 정보를 바탕으로 실천 가능한 계획을 작성한다.
체중 감량, 목표 체중, 체지방 감소, 외모 평가, BMI/BMR/TDEE, 칼로리 계산이나 제한, 단식, 끼니 거르기, 보상 운동을 절대 제안하지 않는다.
균형 잡힌 일반 식사 메뉴를 아침·점심·저녁으로 제안하고 식사량을 줄이라고 하지 않는다.
알레르기를 반영한다. 운동은 안전하고 즐거운 활동으로 구성하며 높은 난이도라도 무리하게 시키지 않는다.
통증·어지럼·과도한 피로 시 중단하고 쉬도록 안내한다. 휴식과 수면도 포함한다.
다음 순서로 작성한다: 1 오늘의 생활 습관 목표 2 아침·점심·저녁 메뉴 3 운동 종류와 수행 방법 4 난이도 조절 5 휴식·수면 6 안전 주의사항."""
            try:
                with st.spinner("AI가 계획을 작성하고 있습니다..."):
                    client = OpenAI(api_key=key)
                    result = client.responses.create(
                        model=os.getenv("OPENAI_MODEL","gpt-5.5"),
                        instructions=rules, input=profile, max_output_tokens=1800, store=False)
                st.session_state["plan"] = result.output_text
            except Exception as e:
                st.error(f"AI 요청 오류: {e}")
    if st.session_state.get("plan"):
        st.divider()
        st.subheader("나의 AI 맞춤 계획")
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
1. AI 계획 만들기에서 목록과 버튼으로 정보를 선택합니다.
2. AI 계획 생성하기를 누르면 한국어 계획표가 만들어집니다.
3. 하루 기록하기에서 실천한 습관을 체크하고 저장합니다.
4. 달력 및 그래프에서 기록을 확인합니다.

**OpenAI API 연결**
Streamlit Cloud의 앱 Settings > Secrets에 다음 내용을 입력합니다.

```toml
OPENAI_API_KEY = "발급받은_API_키"
```

API 키는 Python 코드나 공개 GitHub 저장소에 직접 입력하지 마세요. ChatGPT 구독과 API 사용 요금은 별개일 수 있습니다.

**실행**
```bash
pip install -r requirements.txt
streamlit run app.py
```

기록은 `health_habit_log.db`에 저장됩니다. 배포 환경에 따라 재배포 시 기록이 초기화될 수 있으므로 장기 운영에는 별도 데이터베이스가 필요합니다.
""")
st.sidebar.divider()
st.sidebar.caption("AI 건강 습관 플래너 · 한국어 GUI")
