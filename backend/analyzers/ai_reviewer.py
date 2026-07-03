"""Groq (Llama 3.3 70B) 기반 다중 검토 시스템 - 완전 무료, 하루 14,400회"""
import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '../../.env'))

client = Groq(api_key=os.environ["GROQ_API_KEY"])

MODEL = "llama-3.3-70b-versatile"

SYSTEM_PROMPT = """당신은 매우 꼼꼼한 시니어 소프트웨어 엔지니어입니다.
코드를 여러 번 검토하고, 숨겨진 버그와 개선점을 찾는 것을 좋아합니다.
한국어로 친절하고 구체적으로 설명해주세요. 항상 라인번호와 예시를 들어주세요."""


class AICodeReviewer:
    def __init__(self):
        self.history = []

    def _reset_chat(self):
        """새로운 검토 세션 시작"""
        self.history = []

    def _ask(self, prompt: str) -> str:
        """Groq과 대화 (대화 히스토리 유지, 429 시 재시도)"""
        import time
        self.history.append({"role": "user", "content": prompt})

        for attempt in range(3):
            try:
                response = client.chat.completions.create(
                    model=MODEL,
                    messages=[{"role": "system", "content": SYSTEM_PROMPT}] + self.history,
                    max_tokens=2048,
                    temperature=0.3
                )
                reply = response.choices[0].message.content
                self.history.append({"role": "assistant", "content": reply})
                return reply
            except Exception as e:
                if "429" in str(e) and attempt < 2:
                    wait = 30 * (attempt + 1)
                    print(f"Rate limit 대기 중... {wait}초 후 재시도 ({attempt+1}/3)")
                    time.sleep(wait)
                else:
                    raise

    def review_code(self, code: str, language: str = "python") -> dict:
        """다중 관점에서 코드를 꼼꼼히 검토"""
        self._reset_chat()

        reviews = {
            "bug_security":    self._review_bugs_security(code, language),
            "performance":     self._review_performance(code, language),
            "best_practices":  self._review_best_practices(code, language),
            "logic_validation":self._review_logic(code, language),
        }

        if self._contains_ros(code):
            reviews["ros_robotics"] = self._review_ros(code)
        if self._contains_cv(code):
            reviews["computer_vision"] = self._review_cv(code)
        if self._contains_ml(code):
            reviews["machine_learning"] = self._review_ml(code)

        fix_guide = self._generate_fix_guide()

        return {
            "status": "검토 완료",
            "reviews": reviews,
            "fix_guide": fix_guide,
            "summary": "다중 각도에서의 깊이 있는 코드 검토가 완료되었습니다."
        }

    def _review_bugs_security(self, code: str, language: str) -> dict:
        prompt = f"""다음 {language} 코드에서 버그와 보안 취약점을 찾아주세요.

```{language}
{code}
```

확인 항목:
1. 메모리 누수 또는 리소스 누수
2. 타입 에러 또는 타입 변환 문제
3. 보안 취약점 (SQL Injection, XSS, eval 사용 등)
4. NULL/None 체크 누락
5. 예외 처리 누락
6. 동시성 문제 (Race condition)

발견된 각 문제마다 라인번호와 수정 방법을 제시해주세요."""

        review = self._ask(prompt)
        double_check = self._ask(
            "위에서 지적한 문제들 외에 놓친 부분이 있는지 다시 한 번 꼼꼼히 검토해주세요. "
            "특히 엣지 케이스(edge case)를 중심으로 확인해주세요."
        )
        return {"review": review, "double_check": double_check}

    def _review_performance(self, code: str, language: str) -> dict:
        prompt = f"""다음 {language} 코드의 성능 문제를 분석해주세요:

```{language}
{code}
```

확인 항목:
1. 시간 복잡도 (Big O)
2. 공간 복잡도
3. 불필요한 루프 또는 중복 연산
4. 데이터 구조 선택의 적절성
5. I/O 성능 문제
6. 캐싱 가능성

각 문제에 최적화 방안을 코드 예시와 함께 제시해주세요."""

        review = self._ask(prompt)
        double_check = self._ask(
            "성능 최적화 제안 중에서 실제 효과가 큰 항목 TOP 3를 뽑아 우선순위를 매겨주세요. "
            "구현 난이도도 함께 알려주세요."
        )
        return {"review": review, "double_check": double_check}

    def _review_best_practices(self, code: str, language: str) -> dict:
        prompt = f"""다음 {language} 코드에서 코딩 스타일과 Best Practices를 검토해주세요:

```{language}
{code}
```

확인 항목:
1. 네이밍 컨벤션 (변수, 함수, 클래스 이름)
2. 함수/메서드의 크기와 책임 (Single Responsibility)
3. 주석의 필요성과 명확성
4. 코드 재사용성 (DRY 원칙)
5. 모듈화와 캡슐화
6. 언어별 관례 준수 여부

개선 제안을 구체적인 예시 코드와 함께 제시해주세요."""

        review = self._ask(prompt)
        double_check = self._ask(
            "제시한 개선사항을 '필수', '권장', '선택사항' 3단계로 구분하고 "
            "가장 중요한 것부터 우선순위를 매겨주세요."
        )
        return {"review": review, "double_check": double_check}

    def _review_logic(self, code: str, language: str) -> dict:
        prompt = f"""다음 {language} 코드의 논리를 검증해주세요:

```{language}
{code}
```

확인 항목:
1. 함수/메서드의 입력과 출력의 일관성
2. 경계값(Edge case) 처리 (빈 입력, 최댓값, 최솟값)
3. 음수, 0, 오버플로우 처리
4. 루프의 종료 조건
5. 재귀 호출의 기저 조건 (Base case)
6. 상태 관리와 처리 순서의 정확성

각 문제에서 발생 가능한 버그 시나리오를 구체적으로 설명해주세요."""

        review = self._ask(prompt)
        double_check = self._ask(
            "코드를 반대 방향으로 생각해봤을 때 "
            "예상과 다르게 동작할 수 있는 케이스가 있을까요?"
        )
        return {"review": review, "double_check": double_check}

    def _review_ros(self, code: str) -> dict:
        prompt = f"""다음은 ROS 또는 자율주행 관련 코드입니다:

```python
{code}
```

ROS 프레임워크 관점에서 검토해주세요:
1. 노드(Node)와 토픽(Topic) 설계의 적절성
2. 메시지 타입 사용의 정확성
3. 좌표계(TF) 변환 오류
4. 시간 동기화 문제
5. 콜백 함수의 스레드 안전성
6. 자율주행: 센서 융합, 경로 계획, 임계값 설정"""

        review = self._ask(prompt)
        double_check = self._ask(
            "ROS 타이밍 이슈나 Race condition, 실제 로봇에서 위험을 유발할 수 있는 코드가 있나요?"
        )
        return {"review": review, "double_check": double_check}

    def _review_cv(self, code: str) -> dict:
        prompt = f"""다음은 OpenCV를 사용한 영상처리 코드입니다:

```python
{code}
```

영상처리 관점에서 검토해주세요:
1. 이미지 포맷과 채널 관리 (BGR vs RGB)
2. 메모리 할당과 해제
3. 성능: 픽셀 단위 연산 vs 벡터화 연산
4. 알고리즘 선택: 특징 검출, 번호판/차로 검출의 적절성
5. 이미지 경계값 처리
6. 데이터 타입 올바른 사용"""

        review = self._ask(prompt)
        double_check = self._ask(
            "번호판 인식이나 차로 검출의 정확도와 실시간 처리 속도를 높이기 위한 방법이 있을까요?"
        )
        return {"review": review, "double_check": double_check}

    def _review_ml(self, code: str) -> dict:
        prompt = f"""다음은 머신러닝/딥러닝 코드입니다:

```python
{code}
```

AI/ML 관점에서 검토해주세요:
1. 데이터 전처리의 정확성 (정규화, 클래스 불균형)
2. 모델 아키텍처 선택의 적절성 (ANN/DNN/CNN/RNN)
3. 하이퍼파라미터 설정
4. 과적합/과소적합 가능성
5. train/val/test 분리의 정확성
6. 파인튜닝 시 레이어 동결 전략"""

        review = self._ask(prompt)
        double_check = self._ask(
            "모델 일반화 성능을 높이기 위한 데이터 증강(augmentation) 전략과 "
            "자율주행 환경에 특화된 데이터 처리 방법을 제안해주세요."
        )
        return {"review": review, "double_check": double_check}

    def _generate_fix_guide(self) -> str:
        prompt = """지금까지 분석한 내용을 바탕으로 수정 가이드를 작성해주세요.

아래 형식으로 작성해주세요:

🔴 [즉시 수정 필수]
1. 어디: (함수명 또는 라인번호)
   무엇: (문제 요약)
   수정 방법: (구체적인 수정 방법 또는 수정 코드)

🟡 [개선 권장]
1. 어디: ...
   무엇: ...
   수정 방법: ...

🔵 [선택적 개선]
1. 어디: ...
   무엇: ...
   수정 방법: ...

문제가 없는 카테고리는 생략하고, 각 항목은 간결하게 핵심만 적어주세요."""
        return self._ask(prompt)

    @staticmethod
    def _contains_ros(code: str) -> bool:
        return any(k in code for k in ['rospy', 'ROS_INFO', 'nav_msgs', 'geometry_msgs', 'sensor_msgs', 'rclpy'])

    @staticmethod
    def _contains_cv(code: str) -> bool:
        return any(k in code for k in ['cv2', 'imread', 'imshow', 'VideoCapture', 'cvtColor'])

    @staticmethod
    def _contains_ml(code: str) -> bool:
        return any(k in code for k in ['tensorflow', 'torch', 'keras', 'model.fit', 'sklearn', 'DataLoader', 'Sequential'])
