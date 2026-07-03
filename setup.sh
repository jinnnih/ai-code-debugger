#!/bin/bash

echo "================================================"
echo "   AI 디버깅 도구 - 초기 설정"
echo "================================================"

DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

# Python 버전 확인
PYTHON=$(command -v python3 || command -v python)
if [ -z "$PYTHON" ]; then
  echo "❌ Python이 설치되어 있지 않습니다."
  exit 1
fi
echo "✅ Python: $($PYTHON --version)"

# 가상환경 생성
echo ""
echo "가상환경 생성 중..."
$PYTHON -m venv venv
source venv/bin/activate
echo "✅ 가상환경 생성 완료"

# 패키지 설치
echo ""
echo "패키지 설치 중..."
pip install --upgrade pip -q
pip install -r requirements.txt
echo "✅ 패키지 설치 완료"

# .env 파일 생성
if [ ! -f ".env" ]; then
  echo ""
  echo "ANTHROPIC_API_KEY 입력 (Claude Pro 구독 시 발급 가능):"
  read -r api_key
  echo "ANTHROPIC_API_KEY=$api_key" > .env
  echo "✅ .env 파일 생성 완료"
else
  echo "✅ .env 파일이 이미 있습니다"
fi

# results 디렉토리 생성
mkdir -p results

echo ""
echo "================================================"
echo "   설정 완료! 시작 방법:"
echo "   bash start.sh"
echo "================================================"
