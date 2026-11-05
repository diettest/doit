import os
import sqlite3
import calendar
from datetime import date, datetime
from pathlib import Path

import pandas as pd
import streamlit as st
from openai import OpenAI

APP_DIR = Path(__file__).parent
DB_PATH = APP_DIR / "routine_log.db"

st.set_page_config(page_title="AI 건강 루틴 플래너", page_icon="🌿", layout="wide")

st.title("AI 건강 루틴 플래너")
st.caption("균형 잡힌 식사, 즐거운 신체활동, 충분한 휴식을 계획하고 기록하는 프로그램")

st.info(
    "이 앱은 청소년도 사용할 수 있는 건강 습관 관리용 예시입니다. "
    "체중 감량 목표, 칼로리 제한, 체중 도달일 예측은 제공하지 않습니다. "
    "성장기에는 체중이나 BMI만으로 건강 상태를 판단하지 말고, 필요한 경우 보호자와 의료 전문가에게 상담하세요."
)

def get_api_key():
    key = os.getenv("OPENAI_API_KEY", "").strip()
    try:
        if not key and "OPENAI_API_KEY" in st.secrets:
            key = str(st.secrets["OPENAI_API_KEY"]).strip()
    except Exception:
        pass
    return key

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS daily_logs (
                log_date TEXT PRIMARY KEY,
                breakfast INTEGER NOT NULL,
                lunch INTEGER NOT NULL,
                dinner INTEGER NOT NULL,
                movement INTEGER NOT NULL,
                sleep INTEGER NOT NULL,
                note TEXT
            )
        """)
        conn.commit()

def save_log(log_date, breakfast, lunch, dinner, movement, sleep, note):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            INSERT INTO daily_logs
            (log_date, breakfast, lunch, dinner, movement, sleep, note)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(log_date) DO UPDATE SET
                breakfast=excluded.breakfast,
                lunch=excluded.lunch,
                dinner=excluded.dinner,
                movement=excluded.movement,
                sleep=excluded.sleep,
                note=excluded.note
        """, (log_date.isoformat(), int(breakfast), int(lunch), int(dinner),
              int(movement), int(sleep), note))
        conn.commit()

def load_logs():
    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql_query(
            "SELECT * FROM daily_logs ORDER BY log_date DESC", conn
        )

init_db()

tab_plan, tab_log, tab_calendar, tab_help = st.tabs(
    ["AI 계획 만들기", "하루 기록", "기록 달력", "사용 방법"]
)

with tab_plan:
    st.subheader("1. 생활 습관 정보")
    c1, c2 = st.columns(2)
    with c1:
        age = st.number_input("나이", min_value=13, max_value=19, value=16, step=1)
        activity = st.selectbox(
            "평소 활동량",
            ["낮음 (주로 앉아서 생활)", "보통 (일상적인 걷기와 활동)", "높음 (운동이나 야외활동이 잦음)"]
        )
        exercise_level = st.selectbox(
            "원하는 운동 난이도",
            ["낮음 (가볍고 부담 적게)", "보통 (적당한 도전)", "높음 (새로운 동작에 도전하되 무리하지 않기)"]
        )
    with c2:
        food_style = st.selectbox(
            "식사 선호",
            ["특별한 선호 없음", "한식 위주", "간단한 조리", "채식 위주"]
        )
        allergies = st.text_input("알레르기 또는 피해야 하는 음식 (없으면 '없음')")
        available_time = st.selectbox(
            "하루에 운동·활동에 사용할 수 있는 시간",
            ["10~15분", "20~30분", "30~45분", "상황에 따라 다름"]
        )
    interests = st.text_area("좋아하는 운동이나 피하고 싶은 운동 (선택)", placeholder="예: 걷기와 자전거를 좋아함")
    goal = st.selectbox(
        "이번 계획에서 가장 중요하게 생각하는 것",
        ["규칙적인 식사", "체력 기르기", "유연성 향상", "일상 활동 늘리기", "건강한 생활 습관 만들기"]
    )

    if st.button("AI 맞춤 계획 생성", type="primary", use_container_width=True):
        api_key = get_api_key()
        if not api_key:
            st.error("OpenAI API 키가 설정되지 않았습니다. 사용 방법 탭의 API 키 설정을 확인하세요.")
        else:
            user_profile = f"""
나이: {age}
평소 활동량: {activity}
원하는 운동 난이도: {exercise_level}
식사 선호: {food_style}
알레르기/피해야 하는 음식: {allergies or '미입력'}
사용 가능한 활동 시간: {available_time}
좋아하거나 피하고 싶은 운동: {interests or '미입력'}
가장 중요한 목표: {goal}
"""
            instructions = """
너는 청소년의 건강한 생활 습관을 돕는 안전한 코치다.
한국어로 답하고, 아래 규칙을 반드시 지켜라.
- 체중 감량, 체중 목표, 체지방 감소, 외모 평가를 목표로 설정하지 않는다.
- 칼로리, 섭취 제한, 단식, 끼니 거르기, 보상 운동을 제안하지 않는다.
- BMI, BMR, TDEE 또는 목표 체중 도달 날짜를 계산하거나 추정하지 않는다.
- 균형 잡힌 일반 식사 예시를 제시하고 양을 줄이라고 하지 않는다.
- 아침/점심/저녁은 다양한 식품군을 포함한 평범한 메뉴로 제안한다.
- 음식 알레르기와 피해야 하는 음식은 반드시 반영한다.
- 운동은 안전하고 즐거운 활동 위주로 제안하며, 통증·어지럼·과도한 피로가 있으면 중단하고 쉬도록 안내한다.
- 높은 난이도를 선택해도 무리한 고강도 운동이나 매일 강한 운동을 권하지 않는다.
- 충분한 휴식과 수면을 계획에 포함한다.
- 의료 진단이나 개인별 치료 조언을 하지 않는다.
출력 구성:
1) 오늘의 생활 습관 방향
2) 아침·점심·저녁 메뉴 예시
3) 운동/신체활동 종류와 안전한 방법
4) 낮음/보통/높음 선택에 맞춘 난이도 조절
5) 휴식과 수면 팁
6) 알레르기 및 안전 관련 확인사항
"""
            try:
                with st.spinner("AI가 생활 습관 계획을 만들고 있습니다..."):
                    client = OpenAI(api_key=api_key)
                    response = client.responses.create(
                        model="gpt-5.5",
                        instructions=instructions,
                        input=user_profile,
                        max_output_tokens=1800,
                        store=False
                    )
                st.session_state["generated_plan"] = response.output_text
            except Exception as e:
                st.error(f"AI 요청 중 오류가 발생했습니다: {e}")

    if st.session_state.get("generated_plan"):
        st.subheader("AI가 생성한 계획")
        st.markdown(st.session_state["generated_plan"])
        st.download_button(
            "계획표 다운로드",
            data=st.session_state["generated_plan"],
            file_name=f"건강_생활_계획_{date.today().isoformat()}.txt",
            mime="text/plain",
            use_container_width=True
        )

with tab_log:
    st.subheader("2. 하루 생활 습관 기록")
    st.write("체중이 아니라 하루의 건강 습관 실천 여부를 기록합니다.")
    log_date = st.date_input("기록 날짜", value=date.today(), key="log_date")
    c1, c2 = st.columns(2)
    with c1:
        breakfast = st.checkbox("아침 식사를 챙겼다")
        lunch = st.checkbox("점심 식사를 챙겼다")
        dinner = st.checkbox("저녁 식사를 챙겼다")
    with c2:
        movement = st.checkbox("즐거운 신체활동을 했다")
        sleep = st.checkbox("충분한 휴식을 취했다")
    note = st.text_area("오늘의 메모 (선택)", placeholder="예: 산책을 해서 기분이 좋았음")
    if st.button("오늘 기록 저장", type="primary"):
        save_log(log_date, breakfast, lunch, dinner, movement, sleep, note)
        st.success("기록을 저장했습니다.")

    logs = load_logs()
    if not logs.empty:
        existing = logs[logs["log_date"] == log_date.isoformat()]
        if not existing.empty:
            st.caption("선택한 날짜에 저장된 기록이 있습니다. 체크 상태를 불러오려면 아래 기록 달력 탭에서 확인할 수 있습니다.")

with tab_calendar:
    st.subheader("3. 월별 기록 달력")
    today = date.today()
    ycol, mcol = st.columns(2)
    year = ycol.number_input("연도", min_value=2020, max_value=2100, value=today.year, step=1)
    month = mcol.selectbox("월", list(range(1, 13)), index=today.month - 1)
    logs = load_logs()
    logged_dates = set(logs["log_date"].tolist()) if not logs.empty else set()
    cal = calendar.Calendar(firstweekday=6)
    weeks = cal.monthdayscalendar(int(year), int(month))
    grid = []
    for week in weeks:
        row = []
        for day in week:
            if day == 0:
                row.append("")
            else:
                mark = "●" if date(int(year), int(month), day).isoformat() in logged_dates else ""
                row.append(f"{day} {mark}".strip())
        grid.append(row)
    st.dataframe(pd.DataFrame(grid, columns=["일", "월", "화", "수", "목", "금", "토"]),
                 hide_index=True, use_container_width=True)
    st.caption("● 표시가 있는 날짜에는 기록이 저장되어 있습니다.")

    if not logs.empty:
        st.subheader("최근 기록")
        view = logs.copy()
        view["실천 항목 수"] = view[["breakfast", "lunch", "dinner", "movement", "sleep"]].sum(axis=1)
        view = view.rename(columns={"log_date": "날짜", "note": "메모"})
        st.dataframe(view[["날짜", "실천 항목 수", "메모"]], hide_index=True, use_container_width=True)
        chart = logs.copy()
        chart["date"] = pd.to_datetime(chart["log_date"])
        chart["실천 항목 수"] = chart[["breakfast", "lunch", "dinner", "movement", "sleep"]].sum(axis=1)
        st.line_chart(chart.set_index("date")[["실천 항목 수"]].sort_index())
    else:
        st.caption("아직 저장된 기록이 없습니다.")

with tab_help:
    st.subheader("4. 설치 및 API 키 설정")
    st.markdown("""
**① 필요한 파일**

- `app.py`
- `requirements.txt`

**② OpenAI API 키 준비**

OpenAI API를 사용하려면 API 키와 별도 API 사용 요금이 필요할 수 있습니다. ChatGPT 구독과 API 사용 요금은 별개입니다.

**③ Streamlit Cloud에 배포한 경우**

1. Streamlit Cloud에서 해당 앱의 Settings를 엽니다.
2. Secrets 항목에 아래 내용을 입력합니다.
3. 저장한 뒤 앱을 다시 실행합니다.

```toml
OPENAI_API_KEY = "발급받은_API_키"
```

**④ 로컬에서 실행하는 경우**

프로젝트 폴더에 `.streamlit` 폴더를 만들고, 그 안에 `secrets.toml` 파일을 만든 뒤 위 내용을 입력합니다.

**주의:** `secrets.toml`은 GitHub 저장소에 올리지 마세요. API 키를 `app.py`에 직접 입력하지 마세요.

**⑤ 실행 명령**

```bash
pip install -r requirements.txt
streamlit run app.py
```

이 앱의 기록은 SQLite 파일(`routine_log.db`)에 저장됩니다. 배포 환경에 따라 앱 재배포나 저장소 초기화 시 기록이 유지되지 않을 수 있으므로 실제 장기 운영 전에는 별도 데이터베이스 연결이 필요합니다.
""")
    st.markdown("공식 문서: [OpenAI Responses API](https://developers.openai.com/api/reference/python/resources/responses) · [Streamlit Secrets](https://docs.streamlit.io/develop/concepts/connections/secrets-management)")
