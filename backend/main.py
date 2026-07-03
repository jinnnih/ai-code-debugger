"""AI 디버깅 도구 - FastAPI 백엔드"""
import os
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import json
from datetime import datetime
from pathlib import Path

from analyzers.ai_reviewer import AICodeReviewer
from analyzers.static_analyzer import StaticAnalyzer

# FastAPI 앱 초기화
app = FastAPI(
    title="AI 디버깅 도구",
    description="다중 각도의 꼼꼼한 코드 검토 AI 도구",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 분석기 초기화
ai_reviewer = AICodeReviewer()
static_analyzer = StaticAnalyzer()

# 결과 저장 디렉토리
RESULTS_DIR = Path(__file__).parent.parent / "results"
RESULTS_DIR.mkdir(exist_ok=True)

# 프론트엔드 경로
FRONTEND_DIR = Path(__file__).parent.parent / "frontend"

# 정적 파일 제공
if (FRONTEND_DIR / "static").exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR / "static")), name="static")

@app.get("/", response_class=HTMLResponse)
async def get_frontend():
    """메인 페이지"""
    index_path = FRONTEND_DIR / "templates" / "index.html"
    if index_path.exists():
        with open(index_path, 'r', encoding='utf-8') as f:
            return f.read()
    return "<h1>AI 디버깅 도구</h1><p>프론트엔드를 로드할 수 없습니다.</p>"


@app.post("/api/review")
async def review_code(
    code: str = Form(...),
    language: str = Form(default="python"),
    filename: str = Form(default="code")
):
    """
    코드 검토 API
    - 정적 분석 수행
    - Claude AI로 다중 각도 검토
    """
    try:
        print(f"검토 시작: {filename} ({language})")

        # 1단계: 정적 분석
        print("1단계: 정적 분석 중...")
        if language == "python":
            static_result = static_analyzer.analyze_python(code)
        elif language == "c":
            static_result = static_analyzer.analyze_c(code)
        elif language == "java":
            static_result = static_analyzer.analyze_spring_boot(code)
        else:
            static_result = {"status": "skipped", "message": f"{language}에 대한 정적 분석은 아직 지원하지 않습니다."}

        # 2단계: AI 검토
        print("2단계: AI 다중 검토 중...")
        ai_result = ai_reviewer.review_code(code, language)

        # 결과 종합
        report = {
            "timestamp": datetime.now().isoformat(),
            "filename": filename,
            "language": language,
            "code_length": len(code),
            "static_analysis": static_result,
            "ai_review": ai_result,
            "overall_score": _calculate_score(static_result, ai_result)
        }

        # 결과 저장
        result_file = RESULTS_DIR / f"review_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        print(f"검토 완료! 결과 저장: {result_file}")

        return JSONResponse(content=report, status_code=200)

    except Exception as e:
        print(f"에러 발생: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"검토 중 오류가 발생했습니다: {str(e)}"
        )


@app.post("/api/quick-check")
async def quick_check(code: str = Form(...), language: str = Form(default="python")):
    """
    빠른 확인 - 정적 분석만 수행
    """
    try:
        if language == "python":
            result = static_analyzer.analyze_python(code)
        elif language == "c":
            result = static_analyzer.analyze_c(code)
        elif language == "java":
            result = static_analyzer.analyze_spring_boot(code)
        else:
            result = {"status": "skipped", "message": f"{language} 언어는 지원하지 않습니다"}

        return JSONResponse(content=result, status_code=200)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/results")
async def get_results():
    """저장된 검토 결과 목록"""
    results = []
    for file in sorted(RESULTS_DIR.glob("*.json"), reverse=True)[:10]:
        with open(file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            results.append({
                "filename": data.get("filename"),
                "timestamp": data.get("timestamp"),
                "language": data.get("language"),
                "overall_score": data.get("overall_score"),
                "file": file.name
            })
    return JSONResponse(content=results)


@app.get("/api/results/{result_file}")
async def get_result(result_file: str):
    """특정 검토 결과 조회"""
    result_path = RESULTS_DIR / result_file
    if not result_path.exists():
        raise HTTPException(status_code=404, detail="검토 결과를 찾을 수 없습니다")

    with open(result_path, 'r', encoding='utf-8') as f:
        return JSONResponse(content=json.load(f))


@app.get("/api/health")
async def health_check():
    """헬스 체크"""
    return {"status": "healthy", "message": "AI 디버깅 도구가 정상 작동 중입니다"}


def _calculate_score(static_result: dict, ai_result: dict) -> str:
    """코드 점수 계산"""
    static_issues = static_result.get("total_issues", 0) if static_result.get("status") == "success" else 0
    critical_count = static_result.get("severity_breakdown", {}).get("critical", 0) if static_result.get("status") == "success" else 0

    if critical_count > 0:
        return "🔴 Critical - 즉시 수정 필요"
    elif static_issues > 5:
        return "🟡 Warning - 개선 권장"
    elif static_issues > 0:
        return "🟠 Info - 미미한 개선 항목"
    else:
        return "🟢 Good - 이슈 없음"


if __name__ == "__main__":
    import uvicorn
    print("🚀 AI 디버깅 도구 시작...")
    print("📍 http://localhost:8000")
    print("📚 API 문서: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)
