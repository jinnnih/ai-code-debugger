"""정적 코드 분석 - AST 기반"""
import ast
import re
from typing import List, Dict

class StaticAnalyzer:
    def __init__(self):
        self.issues = []

    def analyze_python(self, code: str) -> dict:
        """Python 코드의 정적 분석"""
        self.issues = []

        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return {
                "status": "syntax_error",
                "error": str(e),
                "line": e.lineno,
                "message": "문법 오류가 있습니다. 수정 후 다시 시도해주세요."
            }

        # 여러 분석 수행
        self._check_unused_variables(tree, code)
        self._check_missing_docstrings(tree)
        self._check_complexity(tree)
        self._check_imports(tree)
        self._check_dangerous_patterns(code)

        return {
            "status": "success",
            "total_issues": len(self.issues),
            "issues": self.issues,
            "severity_breakdown": self._count_severity()
        }

    def _check_unused_variables(self, tree: ast.AST, code: str):
        """사용하지 않는 변수 검사"""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                defined_vars = set()
                used_vars = set()

                for child in ast.walk(node):
                    if isinstance(child, ast.Assign):
                        for target in child.targets:
                            if isinstance(target, ast.Name):
                                defined_vars.add(target.id)
                    elif isinstance(child, ast.Name) and isinstance(child.ctx, ast.Load):
                        used_vars.add(child.id)

                unused = defined_vars - used_vars
                for var in unused:
                    if not var.startswith('_'):
                        self.issues.append({
                            "type": "unused_variable",
                            "severity": "warning",
                            "variable": var,
                            "function": node.name,
                            "message": f"변수 '{var}'가 정의되었지만 사용되지 않습니다."
                        })

    def _check_missing_docstrings(self, tree: ast.AST):
        """문서 문자열(docstring) 누락 검사"""
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                if not ast.get_docstring(node):
                    self.issues.append({
                        "type": "missing_docstring",
                        "severity": "info",
                        "name": node.name,
                        "message": f"{'함수' if isinstance(node, ast.FunctionDef) else '클래스'} '{node.name}'에 설명이 없습니다."
                    })

    def _check_complexity(self, tree: ast.AST):
        """순환 복잡도(Cyclomatic Complexity) 검사"""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                complexity = self._calculate_complexity(node)
                if complexity > 10:
                    self.issues.append({
                        "type": "high_complexity",
                        "severity": "warning",
                        "function": node.name,
                        "complexity": complexity,
                        "message": f"함수 '{node.name}'의 복잡도가 높습니다 (복잡도: {complexity}). 함수를 분리하는 것을 권장합니다."
                    })

    def _calculate_complexity(self, node: ast.AST) -> int:
        """순환 복잡도 계산"""
        complexity = 1
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
        return complexity

    def _check_imports(self, tree: ast.AST):
        """import 관련 검사"""
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.startswith('_'):
                        self.issues.append({
                            "type": "dangerous_import",
                            "severity": "warning",
                            "module": alias.name,
                            "message": f"비공개 모듈 '{alias.name}'을 import하고 있습니다."
                        })

    def _check_dangerous_patterns(self, code: str):
        """위험한 패턴 검사"""
        patterns = {
            r'eval\s*\(': {
                "type": "dangerous_eval",
                "severity": "critical",
                "message": "eval()을 사용하고 있습니다. 보안 위험이 있습니다."
            },
            r'exec\s*\(': {
                "type": "dangerous_exec",
                "severity": "critical",
                "message": "exec()을 사용하고 있습니다. 보안 위험이 있습니다."
            },
            r'except\s*:\s*pass': {
                "type": "bare_except",
                "severity": "warning",
                "message": "모든 예외를 무시하고 있습니다. 특정 예외를 처리하세요."
            },
            r'global\s+': {
                "type": "global_usage",
                "severity": "info",
                "message": "global 키워드를 사용하고 있습니다. 필요한지 다시 검토하세요."
            }
        }

        for pattern, info in patterns.items():
            if re.search(pattern, code):
                self.issues.append(info)

    def _count_severity(self) -> dict:
        """심각도별 이슈 분류"""
        severity_count = {"critical": 0, "warning": 0, "info": 0}
        for issue in self.issues:
            severity = issue.get("severity", "info")
            if severity in severity_count:
                severity_count[severity] += 1
        return severity_count

    def analyze_c(self, code: str) -> dict:
        """C 언어 기본 분석"""
        issues = []

        # 메모리 누수 패턴
        malloc_count = code.count('malloc(')
        free_count = code.count('free(')
        if malloc_count > free_count:
            issues.append({
                "type": "memory_leak_risk",
                "severity": "critical",
                "message": f"malloc() {malloc_count}번, free() {free_count}번 호출됨. 메모리 누수 위험이 있습니다.",
                "malloc_calls": malloc_count,
                "free_calls": free_count
            })

        # 문자열 버퍼 오버플로우
        if re.search(r'gets\s*\(|scanf\s*\(\s*"%s"', code):
            issues.append({
                "type": "buffer_overflow",
                "severity": "critical",
                "message": "gets() 또는 안전하지 않은 scanf()를 사용하고 있습니다. fgets() 또는 scanf_s()를 사용하세요."
            })

        # NULL 포인터 체크
        if 'malloc(' in code and 'if (' not in code:
            issues.append({
                "type": "missing_null_check",
                "severity": "warning",
                "message": "malloc() 후 NULL 포인터 체크가 없습니다."
            })

        return {
            "status": "success",
            "language": "C",
            "total_issues": len(issues),
            "issues": issues
        }

    def analyze_spring_boot(self, code: str) -> dict:
        """Spring Boot 코드 기본 분석"""
        issues = []

        # SQL Injection 체크
        if re.search(r'@Query|SQL|sql', code, re.IGNORECASE):
            if '+' in code and 'String' in code:
                issues.append({
                    "type": "sql_injection_risk",
                    "severity": "critical",
                    "message": "문자열 연결로 SQL 쿼리를 작성하고 있습니다. PreparedStatement 또는 @Query with 파라미터를 사용하세요."
                })

        # 트랜잭션 관리
        if '@Transactional' not in code and ('save(' in code or 'delete(' in code or 'update(' in code):
            issues.append({
                "type": "missing_transactional",
                "severity": "warning",
                "message": "@Transactional 어노테이션이 없습니다. 데이터 일관성을 위해 추가하세요."
            })

        return {
            "status": "success",
            "language": "Spring Boot",
            "total_issues": len(issues),
            "issues": issues
        }
