# AI 건강 습관 플래너
- `app.py`: Streamlit GUI
- `requirements.txt`: 필요한 패키지

실행:
```bash
pip install -r requirements.txt
streamlit run app.py
```

Streamlit Cloud Settings > Secrets:
```toml
OPENAI_API_KEY = "발급받은_API_키"
```
API 키를 공개 저장소에 올리지 마세요. 성장기 사용자를 고려해 체중 감량 처방과 칼로리 제한 기능은 제공하지 않습니다.
