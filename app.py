import streamlit as st

st.set_page_config(page_title="다이어트 계획 도우미", page_icon="📝", layout="centered")

st.title("다이어트 계획 도우미")
st.caption("입력한 정보를 바탕으로 기본 지표를 확인하고, 건강한 생활 습관 계획을 위한 프롬프트를 만들어요.")

st.info(
    "이 프로그램은 의료 도구가 아닙니다. 특히 성장기에는 체중 감량이나 칼로리 제한이 적절하지 않을 수 있습니다. "
    "개인별 식사·운동 계획은 보호자 및 의료 전문가와 상의하세요."
)

with st.form("profile_form"):
    st.subheader("기본 정보")
    height = st.number_input("키 (cm)", min_value=1.0, max_value=250.0, value=160.0, step=0.5)
    weight = st.number_input("현재 체중 (kg)", min_value=1.0, max_value=300.0, value=60.0, step=0.5)
    age = st.number_input("나이", min_value=1, max_value=120, value=16, step=1)
    gender = st.selectbox("성별", ["남", "여"])
    activity = st.selectbox("평소 활동량", ["낮음", "보통", "높음"])
    exercise = st.selectbox("원하는 운동 강도", ["낮음", "보통", "높음"])
    goal_weight = st.number_input(
        "목표 체중 (kg)", min_value=1.0, max_value=300.0,
        value=55.0, step=0.5
    )
    submitted = st.form_submit_button("결과 계산하기", type="primary")

if submitted:
    if goal_weight >= weight:
        st.error("목표 체중은 현재 체중보다 낮게 입력해야 합니다.")
    else:
        height_m = height / 100
        bmi = weight / (height_m ** 2)

        if gender == "남":
            bmr = 10 * weight + 6.25 * height - 5 * age + 5
        else:
            bmr = 10 * weight + 6.25 * height - 5 * age - 161

        activity_factor = {"낮음": 1.375, "보통": 1.55, "높음": 1.725}
        tdee = bmr * activity_factor[activity]

        need_loss = weight - goal_weight

        st.subheader("계산 결과")
        c1, c2, c3 = st.columns(3)
        c1.metric("BMI", f"{bmi:.2f}")
        c2.metric("BMR 추정치", f"{round(bmr):,} kcal/일")
        c3.metric("TDEE 추정치", f"{round(tdee):,} kcal/일")

        st.subheader("목표 체중 정보")
        st.write(f"- 현재 체중: **{weight:g} kg**")
        st.write(f"- 입력한 목표 체중: **{goal_weight:g} kg**")
        st.write(f"- 두 체중의 차이: **{need_loss:.1f} kg**")
        st.write(f"- 원하는 운동 강도: **{exercise}**")

        st.warning(
            "예상 감량 기간이나 칼로리 적자를 자동으로 제시하지 않습니다. "
            "BMI는 성인의 경우에도 참고 지표일 뿐이며, 청소년은 나이와 성장 단계를 고려해 전문가가 해석해야 합니다."
        )

        prompt = f"""당신은 건강한 생활 습관 형성을 돕는 안내자입니다.
아래 정보를 참고하되, 특히 사용자가 성장기일 수 있으므로 무리한 체중 감량이나 칼로리 제한을 권하지 마세요.
정확한 의료 진단을 하지 말고, 필요한 경우 보호자 및 의료 전문가와 상의하도록 안내하세요.

[사용자 정보]
성별: {gender}
나이: {age}세
키: {height:g}cm
현재 체중: {weight:g}kg
사용자가 입력한 목표 체중: {goal_weight:g}kg
평소 활동량: {activity}
원하는 운동 강도: {exercise}
BMI 계산값: {bmi:.2f} (청소년에게는 성인 기준으로 단정해 해석하지 말 것)
BMR 추정값: {round(bmr)} kcal/일
TDEE 추정값: {round(tdee)} kcal/일

다음 내용을 안전과 건강 중심으로 작성해주세요.
1. 규칙적인 식사와 다양한 식품을 포함한 균형 잡힌 식사 아이디어
2. 7일 식사 아이디어 (아침, 점심, 저녁; 칼로리 제한이나 식사 거르기 권장 금지)
3. 즐겁고 무리하지 않는 7일 신체 활동 계획 (휴식 포함, 통증이 있으면 중단)
4. 운동 시 주의사항과 수면·수분 섭취 관련 일반 조언
5. 성장기라면 체중 감량보다 건강한 습관과 전문가 상담을 우선하도록 안내
표를 사용해 보기 쉽게 작성해주세요.
"""

        st.subheader("AI에게 전달할 프롬프트")
        st.text_area("아래 내용을 복사해 ChatGPT에 붙여넣으세요.", value=prompt, height=360)
        st.download_button(
            "프롬프트 텍스트 파일로 저장",
            data=prompt,
            file_name="건강한_생활습관_프롬프트.txt",
            mime="text/plain"
        )
        st.success("결과가 생성되었습니다. 위 프롬프트를 복사하거나 텍스트 파일로 저장하세요.")
