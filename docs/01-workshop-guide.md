# AWS AI League 워크샵 사전 안내자료

> 출처: Notion (2026-05-14 기준)

## 워크샵 개요

AWS AI League는 **제한된 시간 안에 지도를 탐색하여 보물을 얻는 에이전트**를 만들고 개선하며 점수를 높여가는 경쟁형 워크샵입니다.

- 참가자는 **웹 브라우저 기반 실습 환경**에서 Amazon Bedrock AgentCore를 중심으로 AI 에이전트를 구성
- **Lambda**를 활용해 **Python** 코드를 작성·수정, Amazon SageMaker AI 코드 에디터 내장
- **AI Assistant** (Claude Code, Kiro 등) 활용 허용
- 챌린지, 보너스 점수 등 세부 규칙은 **워크샵 당일 공개**

## 사전 준비사항 (필수)

### AWS Builder ID
1. [AWS Builder Center](https://builder.aws.com/) 접속 → 로그인
2. 이메일로 계정 생성 (개인 이메일 가능)
3. 이메일 인증 완료
4. 당일 사용할 이메일/비밀번호 사전 확인

### 환경 확인
- Chrome 브라우저 최신 버전
- 회사 VPN 사용 시 외부 웹 페이지 접속 가능 여부 확인
- 개인 핫스팟 또는 대체 네트워크 준비

### Kiro 설치 (권장)
- [kiro.dev/downloads](https://kiro.dev/downloads/) 에서 다운로드
- GitHub, Google, AWS Builder ID로 로그인
- 신규 사용자: 30일 50크레딧 무료

### Claude Code 사용 가능 (대안)
- 회사 보안 정책 확인 후 사용

## 실습 아키텍처

```
에이전트 (AgentCore)
  ├── Memory (힌트/방문 경로 기억)
  ├── Tools (Lambda 기반 외부 도구)
  │   ├── 경로탐색 Tool
  │   ├── 코인수집 Tool
  │   └── 상태조회 Tool
  └── Guardrails (출력 제어)
```

## 주요 AWS 서비스 (4.1~4.6)

### 4.1 Amazon Bedrock AgentCore
- AI 에이전트가 실제로 실행되는 기반 환경
- **워크샵에서 할 일**: 에이전트 생성, 역할 정의, 도구/메모리/가드레일 연결

### 4.2 AgentCore Memory
- 에이전트가 중요한 정보를 기억하고 다시 활용
- **핵심**: 힌트나 키 값을 저장해 이후 문제 풀 때 재사용
- **워크샵에서 할 일**: 중요 정보 저장, 불러오기, System Prompt에서 Memory 사용 방식 지시

### 4.3 Tools / Gateway
- 에이전트가 외부 도구를 사용할 수 있게 연결하는 통로
- **워크샵에서 할 일**: 도구 연결, 언제 어떤 도구를 쓸지 지시, 불필요한 호출 줄이기

### 4.4 Amazon Bedrock Guardrails
- 에이전트 입력/출력 제어, 안전장치
- **워크샵에서 할 일**: 응답 제어, 챌린지 규칙 준수

### 4.5 AWS Lambda
- 에이전트가 호출하는 도구의 실제 실행 환경
- **워크샵에서 할 일**: Lambda 기반 Tool 호출, 결과 확인, 코드 수정

### 4.6 서비스 요약

| 서비스 | 역할 | 핵심 작업 |
|--------|------|----------|
| AgentCore | 에이전트 실행 환경 | 생성, 역할 정의, 도구/메모리/가드레일 연결 |
| Memory | 정보 기억/재활용 | 힌트·키값 저장, 재사용 |
| Tools/Gateway | 외부 도구 연결 통로 | 경로탐색·코드실행·데이터처리 |
| Guardrails | 안전장치 | 입출력 제어, 규칙 준수 |
| Lambda | 서버리스 실행 | Tool 기능 실행, 결과 반환 |

## FAQ 핵심

- **AWS 계정 필요?** No — 워크샵 인프라 별도 제공. AWS Builder ID만 필요
- **코딩 경험?** 기본 가이드 제공. Lambda Python 코드 수정 능력 있으면 유리
- **점수 산정**: 챌린지 해결 정확도, 과제 완료 여부, 응답 품질, 효율성 기반 자동 계산
