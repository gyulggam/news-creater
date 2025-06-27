# 🤖 StockNewsBot

Python 기반 주식 뉴스 텔레그램 봇 - 실시간 주식 뉴스를 카드 형태로 전달

## 📋 프로젝트 개요

StockNewsBot은 주식 관련 뉴스를 자동으로 수집하고 분석하여 텔레그램을 통해 사용자에게 실시간으로 전달하는 봇 서비스입니다.

## ✨ 주요 기능

- 📰 **실시간 뉴스 카드**: 최신 주식뉴스 5건을 카드 형태로 전달
- 📈 **감정 분석**: 뉴스의 긍정/부정/중립 분석 결과 표시
- 🔔 **종목별 구독**: 관심 종목의 뉴스만 선별적으로 수신
- 🔗 **원문 링크**: 각 뉴스 클릭 시 원문 사이트로 이동
- ⚡ **실시간 업데이트**: 새로고침 버튼으로 최신 뉴스 갱신

## 🛠 기술 스택

- **Python 3.13+**
- **python-telegram-bot**: 텔레그램 봇 API
- **BeautifulSoup4**: 웹 크롤링
- **Loguru**: 로깅
- **Python-dotenv**: 환경 변수 관리

## 🚀 빠른 시작

### 1. 저장소 클론 및 환경 설정

```bash
git clone <repository-url>
cd news-creater

# Python 가상환경 생성 및 활성화
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 패키지 설치
pip install python-telegram-bot beautifulsoup4 requests python-dotenv loguru
```

### 2. 텔레그램 봇 생성

1. 텔레그램에서 [@BotFather](https://t.me/botfather)와 대화 시작
2. `/newbot` 명령어로 새 봇 생성
3. 봇 이름과 사용자명 설정
4. 받은 **BOT TOKEN** 복사

### 3. 환경 변수 설정

```bash
# config.env.example을 .env로 복사
cp config.env.example .env

# .env 파일 편집
nano .env
```

`.env` 파일 내용:
```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
NEWS_LIMIT=5
LOG_LEVEL=INFO
```

### 4. 봇 실행

```bash
python main.py
```

## 📱 사용법

### 기본 명령어

- `/start` - 봇 시작 및 환영 메시지
- `/news` - 최신 주식 뉴스 5건 보기
- `/help` - 도움말 보기

### 구독 관리

- `/subscribe [종목코드]` - 특정 종목 구독
- `/unsubscribe [종목코드]` - 구독 해제  
- `/status` - 현재 구독 상태 확인

**종목코드 예시:**
- `005930` - 삼성전자
- `000660` - SK하이닉스
- `035420` - 네이버
- `035720` - 카카오

### 뉴스 카드 사용법

1. `/news` 명령어로 뉴스 카드 요청
2. 카드에 표시된 뉴스 제목과 감정 분석 결과 확인
3. 관심 있는 뉴스의 번호 버튼 클릭하여 원문 확인
4. 🔄 새로고침 버튼으로 최신 뉴스 갱신

## 📂 프로젝트 구조

```
news-creater/
├── main.py                 # 메인 실행 파일
├── requirements.txt        # 패키지 의존성
├── config.env.example     # 환경 변수 예시
├── PRD.md                 # 프로젝트 기획서
├── README.md              # 프로젝트 설명서
├── src/                   # 소스 코드
│   ├── bot/               # 텔레그램 봇 관련
│   │   └── telegram_bot.py
│   ├── crawler/           # 뉴스 크롤링 (예정)
│   ├── database/          # 데이터베이스 (예정)
│   └── utils/             # 유틸리티 (예정)
├── config/                # 설정 파일
├── tests/                 # 테스트 코드
├── logs/                  # 로그 파일
└── venv/                  # Python 가상환경
```

## 🔧 개발 로드맵

### Phase 1 (완료) ✅
- [x] 기본 텔레그램 봇 구축
- [x] 뉴스 카드 UI 구현
- [x] 기본 명령어 구현
- [x] 임시 뉴스 데이터로 테스트

### Phase 2 (진행 예정)
- [ ] 실제 뉴스 크롤링 시스템
- [ ] 데이터베이스 연동
- [ ] 종목별 뉴스 분류
- [ ] 스케줄링 시스템

### Phase 3 (계획)
- [ ] AI 감정 분석 모델
- [ ] 사용자 구독 관리
- [ ] 실시간 알림 시스템
- [ ] 성능 최적화

## 🐛 문제 해결

### 자주 발생하는 오류

1. **"TELEGRAM_BOT_TOKEN이 설정되지 않았습니다"**
   - `.env` 파일에 올바른 봇 토큰이 설정되었는지 확인

2. **봇이 응답하지 않음**
   - 인터넷 연결 상태 확인
   - 봇 토큰의 유효성 확인
   - 텔레그램에서 봇을 먼저 시작했는지 확인

3. **패키지 설치 오류**
   - Python 3.13+ 사용 여부 확인
   - 가상환경이 활성화되었는지 확인

## 📞 지원

문제가 발생하거나 제안사항이 있으시면 GitHub Issues를 통해 알려주세요.

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

---

**개발 시작일**: 2024년 12월  
**현재 버전**: v0.1.0 (MVP)  
**개발자**: @gimjinsu 