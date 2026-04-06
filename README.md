# PortDetector

> GeoView 네트워크/포트 모니터링 도구

선박 네트워크 및 GeoView 소프트웨어의 포트 상태를 실시간으로 모니터링하는 도구.
Flask+SocketIO 웹 모드와 PySide6 데스크톱 모드를 지원한다.

**버전**: v2.0.0
**포트**: 5555 (웹 모드)

## 기술 스택

| 구분 | 기술 |
|------|------|
| 언어 | Python 3.10+ |
| 웹 서버 | Flask + Flask-SocketIO |
| 데스크톱 | PySide6 (Qt6) |
| 실시간 통신 | WebSocket (SocketIO) |
| 시스템 모니터링 | psutil |
| 트레이 아이콘 | pystray + Pillow |
| 빌드 | PyInstaller |

## 설치

```bash
pip install -r requirements.txt
```

### requirements.txt
```
flask>=2.0,<3.0
flask-socketio>=5.0
simple-websocket>=0.5
psutil>=5.9
pystray>=0.19
Pillow>=9.0
```

PySide6 데스크톱 모드를 사용하려면 추가 설치:
```bash
pip install PySide6
```

## 실행

### 웹 모드 (Flask + SocketIO)
```bash
python app.py
```
브라우저에서 `http://127.0.0.1:5555` 접속.
시스템 트레이 아이콘으로 백그라운드 실행.

### 데스크톱 모드 (PySide6)
```bash
python main.py
```

### 배치 파일
```bash
run.bat
```

## 주요 기능

### 포트 모니터링
- **Ping Worker**: 등록된 호스트/포트에 주기적 핑 (기본 5초 간격)
- **Scan Worker**: 포트 범위 스캔 (열린 포트 감지)
- **지연 임계값**: 기본 200ms 초과 시 경고

### 네트워크 인터페이스
- **Interface Worker**: 네트워크 인터페이스 상태 주기적 폴링 (3초 간격)
- **트래픽 캡처**: 관리자 권한 시 네트워크 트래픽 모니터링

### 서비스 아키텍처
- **ConfigService**: 설정 관리 (JSON 기반, atomic write로 부분 저장 방지)
- **LogService**: 로그 관리 (최대 10MB, 2개 백업, write/rotate 동시성 보호, history read snapshot 안전)
- **ProfileService**: 호스트/포트 프로필 관리
- **AlertService**: 알림 서비스
- **UptimeService**: 가동시간 추적
- **TrafficService**: 패킷 트래픽 캡처
- **TracerouteService**: 경로 추적
- **DiscoveryService**: 네트워크 장치 탐색

### 스케줄러
- Ping, Scan, Interface 워커를 자동 실행/중지 관리

### 실시간 업데이트
- SocketIO를 통한 상태 변경 실시간 브로드캐스트
- 웹 UI에서 실시간 상태 확인

## 디렉토리 구조

```
PortDetector/
├── app.py              ← 웹 모드 엔트리 (Flask + SocketIO)
├── main.py             ← 데스크톱 모드 엔트리 (PySide6)
├── config.py           상수 정의 (포트, 간격, 임계값)
├── backend/
│   ├── routes.py       REST API 라우트
│   ├── socketio_events.py  SocketIO 이벤트 핸들러
│   ├── workers/        ← 백그라운드 워커
│   │   ├── ping_worker.py      핑 워커
│   │   ├── scan_worker.py      포트 스캔 워커
│   │   ├── interface_worker.py 인터페이스 모니터
│   │   └── scheduler.py        스케줄러
│   └── services/       ← 비즈니스 로직
│       ├── config_service.py    설정 관리
│       ├── log_service.py       로그 관리
│       ├── ping_service.py      핑 서비스
│       ├── scan_service.py      스캔 서비스
│       ├── traffic_service.py   트래픽 캡처
│       ├── profile_service.py   프로필 관리
│       ├── alert_service.py     알림
│       ├── uptime_service.py    가동시간
│       ├── traceroute_service.py 경로추적
│       └── discovery_service.py  장치 탐색
├── frontend/           ← 웹 UI
│   ├── templates/      HTML 템플릿
│   └── static/         CSS, JS, 이미지
├── desktop/            ← PySide6 데스크톱 UI
│   ├── main_window.py  메인 윈도우
│   ├── panels/         UI 패널
│   ├── dialogs/        다이얼로그
│   └── theme.py        테마 설정
├── data/               ← 설정/로그 데이터
└── assets/             ← 아이콘
```

## 라이선스

Proprietary - Geoview Co., Ltd.
