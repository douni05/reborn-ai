from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import google.generativeai as genai
from dotenv import load_dotenv
import os
import json
import re

load_dotenv()

app = FastAPI()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash")


class LabelRequest(BaseModel):
    label: str


def build_prompt(label: str) -> str:
    return f"""
당신은 업사이클링 전문가입니다.
사용자가 "{label}" 물체를 카메라로 촬영했습니다.

아래 형식을 반드시 지켜서 JSON으로만 응답하세요.
다른 말은 절대 하지 마세요. JSON만 출력하세요.

{{
  "label": "{label}",
  "materialType": "재질을 한국어로 (예: 데님, 플라스틱, 유리, 금속, 나무, 종이)",
  "conditionGrade": "A",
  "isReformable": true,
  "difficulty": "Easy",
  "reformTitle": "리폼 아이디어 제목 (예: 청바지로 토트백 만들기)",
  "reformPlan": "step1: 첫 번째 단계\\nstep2: 두 번째 단계\\nstep3: 세 번째 단계\\nstep4: 네 번째 단계\\nstep5: 다섯 번째 단계",
  "materials": "필요한 재료를 쉼표로 구분 (예: 가위, 바늘, 실, 지퍼)",
  "estimatedTime": "예상 소요 시간 (예: 약 1시간)",
  "estimatedCost": "예상 비용 (예: 없음 또는 약 5,000원)"
}}

각 필드 작성 기준:
- materialType: "{label}"의 주재질을 판단해서 한국어로
- conditionGrade: 일반적인 상태 기준으로 A(좋음) B(보통) C(나쁨) 중 하나
- isReformable: 업사이클링이 현실적으로 가능하면 true, 불가능하면 false
- difficulty: Easy(초보도 가능) Normal(약간의 기술 필요) Hard(전문가 수준) 중 하나
- reformPlan: 각 단계를 \\n으로 구분, 5단계 이내로 구체적으로
- 리폼이 불가능한 경우 isReformable을 false로 하고 reformPlan에 올바른 분리배출 방법을 작성
"""


def parse_response(label: str, raw_text: str) -> dict:
    try:
        cleaned = re.sub(r"```json|```", "", raw_text).strip()
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return {
            "label": label,
            "materialType": "알 수 없음",
            "conditionGrade": "B",
            "isReformable": False,
            "difficulty": "Normal",
            "reformTitle": "분리배출 안내",
            "reformPlan": "step1: 재질을 확인하세요\nstep2: 해당 분리배출함에 배출하세요",
            "materials": "",
            "estimatedTime": "",
            "estimatedCost": ""
        }


@app.get("/")
def health_check():
    return {"status": "ok", "message": "Re:Born AI 서버 정상 동작 중"}


@app.get("/daily-tip")
async def generate_daily_tip():
    prompt = """
당신은 친환경 생활 전문가입니다.
오늘의 실천 팁을 한 가지 알려주세요.

주제는 아래 중 하나를 랜덤으로 선택하세요:
- 의류/섬유 업사이클링
- 올바른 분리배출 방법
- 생활 속 재활용 아이디어
- 친환경 소비 습관

규칙:
- 2문장 이내로 짧고 실용적으로
- 구체적인 사례를 포함할 것
- 딱딱하지 않고 친근한 말투
- JSON 형식으로만 응답: {{"tip": "내용"}}
- 다른 말은 절대 하지 마세요
"""
    try:
        response = model.generate_content(prompt)
        cleaned = re.sub(r"```json|```", "", response.text).strip()
        data = json.loads(cleaned)
        return {"tip": data.get("tip", "오늘도 분리배출 잊지 마세요!")}
    except Exception as e:
        print(f"[daily-tip 오류] {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze-v2")
async def analyze(req: LabelRequest):
    if not req.label or req.label.strip() == "":
        raise HTTPException(status_code=400, detail="label이 비어있어요")

    try:
        prompt = build_prompt(req.label)
        response = model.generate_content(prompt)
        return parse_response(req.label, response.text)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI 분석 실패: {str(e)}")