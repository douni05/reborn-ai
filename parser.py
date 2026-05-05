import json
import re


def parse_response(label: str, raw_text: str) -> dict:
    try:
        # ```json ... ``` 형식 제거
        cleaned = re.sub(r"```json|```", "", raw_text).strip()
        data = json.loads(cleaned)
        return data

    except json.JSONDecodeError:
        # 파싱 실패 시 기본값 반환
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