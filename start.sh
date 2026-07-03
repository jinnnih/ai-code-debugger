#!/bin/bash

echo "================================================"
echo "   AI 디버깅 도구 시작"
echo "================================================"

# 프로젝트 루트
DIR="$(cd "$(dirname "$0")" && pwd)"

# API 키 확인
if [ -f "$DIR/.env" ]; then
  export $(grep -v '^#' "$DIR/.env" | xargs)
  echo "✅ .env 파일에서 API 키를 불러왔습니다"
fi

if [ -z "$GEMINI_API_KEY" ]; then
  echo "❌ GEMINI_API_KEY가 설정되지 않았습니다"
  echo ""
  echo ".env 파일에 아래 내용을 추가하세요:"
  echo "GEMINI_API_KEY=여기에_키_입력"
  exit 1
else
  echo "✅ Gemini API 키 확인됨"
fi

# 가상환경 활성화
if [ -d "$DIR/venv" ]; then
  echo "✅ 가상환경 활성화"
  source "$DIR/venv/bin/activate"
else
  echo "⚠️  가상환경이 없습니다. setup.sh를 먼저 실행하세요."
  echo "    bash setup.sh"
  exit 1
fi

# 결과 디렉토리 생성
mkdir -p "$DIR/results"

echo ""
echo "🚀 서버 시작 중..."
echo "📍 주소: http://localhost:8000"
echo "📚 API 문서: http://localhost:8000/docs"
echo ""
echo "종료: Ctrl+C"
echo "================================================"

cd "$DIR/backend"
python main.py
