# RE:Born AI Server

> **RE:Born** — AI 기반 스마트 업사이클링 및 올바른 분리배출 통합 솔루션 앱의 **AI 분석 서버**입니다.
> 사용자가 촬영한 물건 사진을 Gemini 2.5 Flash로 분석해 재질 · 상태 등급 · 업사이클링 가능 여부를 판단하고, 맞춤 리폼 가이드와 분리배출 방법을 생성합니다.

- 기간: 2026.03.04 ~ 2026.06.17 (교내 START-UP PROJECT 수업, 3인 팀)
- 담당: 김도윤 (팀장 · DB 설계 · AI 엔진 구축)

## 관련 저장소

| 구분 | 저장소 |
|---|---|
| Frontend (Flutter) | [reborn-frontend](https://github.com/douni05/reborn-frontend) |
| Backend (Spring Boot) | [reborn-backend](https://github.com/douni05/reborn-backend) |
| AI Server (FastAPI) | **reborn-ai** (현재 저장소) |

## 시스템 구조

```
Flutter App ──REST──▶ Spring Boot (메인 서버) ──HTTP──▶ FastAPI (AI 서버) ──▶ Gemini 2.5 Flash
  ML Kit 사물 분류        회원 · 리폼 · XP · DB 저장         프롬프트 · 응답 파싱
```

앱이 ML Kit로 사물을 1차 분류한 라벨과 촬영 이미지를 보내면, Spring Boot 서버가 이 AI 서버를 호출하고 결과를 DB에 저장합니다.

## 기술 스택

- Python, FastAPI, Uvicorn
- Google Gemini 2.5 Flash API (`google-generativeai`)
- python-dotenv (API 키 환경변수 관리)

## API

| Method | Path | 설명 |
|---|---|---|
| GET | `/` | 헬스 체크 |
| POST | `/analyze-v2` | 물건 분석. 이미지가 있으면 이미지+텍스트(멀티모달), 없으면 라벨만으로 분석 |
| POST | `/verify-reform` | 리폼 완료 사진을 보고 실제로 리폼됐는지 판단 (경험치 지급용) |
| GET | `/daily-tip` | 오늘의 친환경 실천 팁 생성 |

### `/analyze-v2` 요청 · 응답 예시

```json
// Request
{ "label": "jeans", "imageBase64": "<base64 이미지 (선택)>" }

// Response
{
  "label": "jeans",
  "materialType": "데님",
  "conditionGrade": "A",
  "isReformable": true,
  "difficulty": "Easy",
  "reformTitle": "청바지로 실용적인 토트백 만들기",
  "reformPlan": "step1: ...\nstep2: ...\nstep3: ...",
  "materials": "가위, 바늘, 실, 재봉틀(권장)",
  "estimatedTime": "약 2~3시간",
  "estimatedCost": "없음",
  "disposalGuide": "step1: ...\nstep2: ...\nstep3: ..."
}
```

## 트러블슈팅 — AI 응답 형식이 흔들려도 앱이 멈추지 않게

**문제**  Gemini 응답이 JSON 형식을 벗어나(코드블록 · 설명 문장 추가) 파싱에 실패했고, 앱의 분석 화면이 멈추는 문제가 발생했습니다.

**해결**
1. **프롬프트 고정** — 모든 필드와 값의 범위(A/B/C, Easy/Normal/Hard)를 JSON 템플릿으로 명시하고 "JSON만 출력"하도록 지시
2. **파싱 검증** — 응답에서 ```` ```json ```` 코드블록을 제거한 뒤 파싱하고, 실패하면 분리배출 안내 기본값으로 대체 (`parse_response`)
3. **이중 방어** — Spring Boot 서버에서도 AI 서버 호출이 실패하면 fallback 응답을 반환

**결과**  AI 응답이 어긋나도 항상 같은 형식의 결과가 앱에 전달되어 분석 중 앱 멈춤이 해결되었습니다.

## 실행 방법

```bash
pip install -r requirements.txt

# .env 파일 생성 (저장소에 올리지 않음)
echo "GEMINI_API_KEY=발급받은_키" > .env

uvicorn main:app --reload --port 8000
```

- API 문서: http://localhost:8000/docs
- Spring Boot 서버는 `AI_SERVER_URL`(기본값 `http://localhost:8000`)로 이 서버를 호출합니다.
