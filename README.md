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

로컬 사전 점검만 실행하려면:
```bash
python app.py --doctor
```
이 명령은 설정, 저장소, 백업 디렉터리, 모니터링 전제조건을 확인하지만 실제 장비, 원격 포트, 브라우저 자동 실행, 장시간 패킷 캡처는 확인하지 않는다.

운영용 JSON 패킷을 파일로 남기려면:
```bash
python app.py --doctor --doctor-export data\doctor-web.json
```
이 파일에는 동일한 로컬 전용 점검 결과와 함께 packaged-vs-source runtime 경로, 필수 리소스 존재 여부, 각 체크의 상태/메시지가 들어가며, 새 머신 인수인계용으로 재사용할 수 있다.
내보내기는 임시 파일을 거쳐 원자적으로 완료되므로, 중간 실패가 나도 기존 패킷을 부분적으로 덮어쓰지 않는다.

### 데스크톱 모드 (PySide6)
```bash
python main.py
```

로컬 사전 점검만 실행하려면:
```bash
python main.py --doctor
```
이 명령은 데스크톱 실행에 필요한 로컬 의존성과 저장소 상태를 확인하지만 실제 장비, 원격 포트, 장시간 패킷 캡처는 확인하지 않는다.

운영용 JSON 패킷을 파일로 남기려면:
```bash
python main.py --doctor --doctor-export data\doctor-desktop.json
```
이 패킷은 로컬 전용 결과만 담으며, packaged-vs-source runtime 경로와 리소스 존재 여부까지 함께 기록하지만, 살아 있는 장비의 도달 가능성을 보장한다고 주장하지 않는다.
내보내기는 원자적으로 기록되므로, 실패 시에도 이전 파일이 그대로 유지된다.

### 패키지 빌드 및 자체 검증
```bash
build.bat
```
이 빌드는 `main.py` 기반의 데스크톱 EXE를 만들고, 바로 그 EXE를 `--doctor --doctor-export %TEMP%\PortDetector-desktop-doctor.json`으로 다시 실행한다.
즉, 이 흐름은 "패키지된 데스크톱 런타임이 로컬 전용 doctor/export를 실제로 끝까지 수행하는지"를 증명하는 용도이며, 실제 장비 도달성이나 현장 네트워크 상태까지는 확인하지 않는다.

### 배치 파일
```bash
run.bat
```
예:
```bash
run.bat --doctor
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
