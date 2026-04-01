"""PortDetector i18n — Korean / English translation module."""

from __future__ import annotations

_current_lang = "ko"

TRANSLATIONS = {
    # ── Navigation / Tabs ──
    "nav.dashboard": {"ko": "대시보드", "en": "Dashboard"},
    "nav.scanner": {"ko": "포트 스캔", "en": "Scanner"},
    "nav.discovery": {"ko": "네트워크 탐색", "en": "Discovery"},
    "nav.traceroute": {"ko": "경로 추적", "en": "Traceroute"},
    "nav.interfaces": {"ko": "네트워크 인터페이스", "en": "Interfaces"},
    "nav.serial": {"ko": "시리얼/NMEA", "en": "Serial/NMEA"},
    "nav.history": {"ko": "이벤트 이력", "en": "History"},
    "nav.report": {"ko": "가동률 리포트", "en": "Report"},
    "nav.settings": {"ko": "설정", "en": "Settings"},

    # ── Dashboard ──
    "dash.title": {"ko": "대시보드", "en": "Dashboard"},
    "dash.add_device": {"ko": "+ 장치 추가", "en": "+ Add Device"},
    "dash.monitored": {"ko": "모니터링", "en": "Monitored"},
    "dash.stable": {"ko": "정상", "en": "Stable"},
    "dash.attention": {"ko": "주의", "en": "Attention"},
    "dash.offline": {"ko": "오프라인", "en": "Offline"},
    "dash.rtt_trend": {"ko": "RTT 추이", "en": "RTT trend"},
    "dash.rtt_subtitle": {
        "ko": "선택된 장치의 지연 변화를 집중 표시합니다. 빈 구간은 핑 실패입니다.",
        "en": "Missing points indicate failed pings. Focus stays on the selected device to reduce chart noise.",
    },
    "dash.no_samples": {"ko": "아직 지연 데이터가 없습니다.", "en": "No latency samples yet."},
    "dash.no_devices_headline": {"ko": "등록된 장치가 없습니다", "en": "No devices configured yet"},
    "dash.no_devices_detail": {
        "ko": "선박의 포트와 장치를 추가하면 PortDetector가 실시간 상태를 요약합니다.",
        "en": "Add the ports and devices that matter on the vessel so PortDetector can summarize real health.",
    },
    "dash.no_devices_context": {
        "ko": "'장치 추가'를 누르고 중요도를 설정하면 알림이 우선순위에 따라 작동합니다.",
        "en": "Use Add Device and assign importance so alerts can prioritize the systems that matter most.",
    },
    "dash.waiting_sweep": {"ko": "첫 모니터링 결과를 기다리는 중", "en": "Waiting for first monitoring sweep"},
    "dash.waiting_detail": {
        "ko": "첫 핑 주기가 완료되면 대시보드가 현재 상태를 요약합니다.",
        "en": "The dashboard will summarize current health once the first ping cycle completes.",
    },
    "dash.selected_device": {"ko": "선택된 장치", "en": "Selected device"},
    "dash.select_prompt": {"ko": "장치 카드를 클릭하면 상세 정보를 확인할 수 있습니다.", "en": "Select a device card to inspect it."},
    "dash.open_scanner": {"ko": "스캐너에서 열기", "en": "Open In Scanner"},
    "dash.waiting_data": {"ko": "데이터 대기 중", "en": "Waiting for data"},

    # ── Dashboard / Overview dynamic ──
    "dash.immediate_attention": {"ko": "{count}개 장치에 즉각 조치가 필요합니다", "en": "{count} device(s) need immediate attention"},
    "dash.needs_review": {"ko": "{count}개 장치 확인이 필요합니다", "en": "{count} device(s) need review"},
    "dash.all_stable": {"ko": "모든 장치가 정상입니다", "en": "All monitored devices are currently stable"},
    "dash.all_stable_detail": {
        "ko": "{count}개 장치가 현재 모니터링 기준 내에서 정상 응답 중입니다.",
        "en": "{count} device(s) are responding within the current monitoring threshold.",
    },
    "dash.overview_context": {
        "ko": "핑 주기 {interval}초 | 지연 임계치 {threshold} ms | 3회 연속 지연 시 알림",
        "en": "Ping every {interval} sec | Delay threshold {threshold} ms | Latency alerts start after 3 consecutive slow replies",
    },
    "dash.review_detail": {
        "ko": "정상 {stable} / 오프라인 {offline} / 지연 {delayed}. 우선 확인: {name}.",
        "en": "{stable} stable / {offline} offline / {delayed} high-latency. Top review target: {name}.",
    },

    # ── Device States (monitoring_presenter) ──
    "status.connected": {"ko": "정상", "en": "Stable"},
    "status.delayed": {"ko": "지연 중", "en": "High latency"},
    "status.disconnected": {"ko": "응답 없음", "en": "No response"},
    "status.waiting": {"ko": "데이터 대기 중", "en": "Waiting for data"},
    "status.disabled": {"ko": "모니터링 비활성", "en": "Monitoring disabled"},
    "status.disabled_reason": {
        "ko": "프로필에 저장되었지만 실시간 모니터링에서 제외된 장치입니다.",
        "en": "This device is saved in the profile but excluded from live polling.",
    },
    "status.waiting_first": {"ko": "첫 모니터링 결과 대기 중", "en": "Waiting for the first monitoring result"},

    # ── Status reasons ──
    "reason.connected": {"ko": "핑 응답: {rtt} ms", "en": "Ping responded in {rtt} ms."},
    "reason.connected_ok": {"ko": "핑이 정상 응답했습니다.", "en": "Ping responded normally."},
    "reason.delayed": {
        "ko": "핑 응답 {rtt} ms - 지연 임계치 {threshold} ms를 초과했습니다.",
        "en": "Ping responded in {rtt} ms, above the {threshold} ms delay threshold.",
    },
    "reason.delayed_no_rtt": {
        "ko": "지연 임계치 {threshold} ms보다 느리게 응답했습니다.",
        "en": "Response arrived slower than the {threshold} ms delay threshold.",
    },
    "reason.disconnected": {
        "ko": "최근 모니터링 주기에서 핑 응답이 없었습니다.",
        "en": "No ping reply was received during the latest monitoring cycle.",
    },
    "reason.unknown": {"ko": "첫 모니터링 결과를 기다리는 중입니다.", "en": "Waiting for the first monitoring result."},

    # ── Severity labels ──
    "severity.stable": {"ko": "정상", "en": "Stable"},
    "severity.info": {"ko": "정보", "en": "Info"},
    "severity.advisory": {"ko": "참고", "en": "Advisory"},
    "severity.warning": {"ko": "주의", "en": "Warning"},
    "severity.critical": {"ko": "위험", "en": "Critical"},
    "severity.emergency": {"ko": "긴급", "en": "Emergency"},

    # ── Importance labels ──
    "importance.critical": {"ko": "핵심", "en": "Critical"},
    "importance.high": {"ko": "중요", "en": "Important"},
    "importance.standard": {"ko": "표준", "en": "Standard"},
    "importance.optional": {"ko": "선택", "en": "Optional"},

    # ── Action text ──
    "action.connected_ports": {
        "ko": "호스트 도달 정상. 앱 문제 시 스캐너에서 참조 포트 {ports}를 확인하세요.",
        "en": "Host reachability is healthy. If the application still feels down, open Scanner and verify reference ports {ports}.",
    },
    "action.connected_no_ports": {
        "ko": "도달성 정상. 간헐적 문제가 보고되면 관찰을 계속하세요.",
        "en": "Reachability is healthy. Keep observing only if operators still report intermittent issues.",
    },
    "action.delayed_long_ports": {
        "ko": "지연이 수 회 지속 중. 인터페이스 부하를 확인하고 참조 포트 {ports}를 점검하세요.",
        "en": "Latency has stayed high for several checks. Review interface load and verify reference ports {ports} before escalating.",
    },
    "action.delayed_long_no_ports": {
        "ko": "지연이 수 회 지속 중. 에스컬레이션 전에 인터페이스 부하를 확인하세요.",
        "en": "Latency has stayed high for several checks. Review interface load before escalating.",
    },
    "action.delayed_short_ports": {
        "ko": "한 주기 더 관찰하거나, 서비스 불안정 시 참조 포트 {ports}를 확인하세요.",
        "en": "Watch another cycle or verify reference ports {ports} if the service feels unstable.",
    },
    "action.delayed_short_no_ports": {
        "ko": "에스컬레이션 전에 한 주기 더 관찰하세요.",
        "en": "Watch another cycle before escalating.",
    },
    "action.disconnected_ports": {
        "ko": "전원, 케이블, 라우팅, VPN 상태를 먼저 확인하세요. 핑 복구 후 참조 포트 {ports}를 점검하세요.",
        "en": "Check power, cabling, routing, or VPN first. Once ping recovers, verify reference ports {ports}.",
    },
    "action.disconnected_no_ports": {
        "ko": "전원, 케이블, 라우팅 또는 VPN 상태를 먼저 확인하세요.",
        "en": "Check power, cabling, routing, or VPN state first.",
    },
    "action.waiting": {"ko": "모니터링 데이터를 기다리는 중입니다.", "en": "Waiting for monitoring data."},

    # ── Relative time ──
    "time.just_now": {"ko": "방금 변경", "en": "Changed just now"},
    "time.sec_ago": {"ko": "{n}초 전 변경", "en": "Changed {n} sec ago"},
    "time.min_ago": {"ko": "{n}분 전 변경", "en": "Changed {n} min ago"},
    "time.hr_ago": {"ko": "{n}시간 전 변경", "en": "Changed {n} hr ago"},
    "time.day_ago": {"ko": "{n}일 전 변경", "en": "Changed {n} day(s) ago"},
    "time.no_change": {"ko": "최근 변경 없음", "en": "No recent change"},

    # ── Report reasons ──
    "report.uptime": {"ko": "가동률 {pct}%", "en": "{pct}% uptime"},
    "report.disconnects": {"ko": "단절 {n}회", "en": "{n} disconnect(s)"},
    "report.avg_rtt_above": {"ko": "평균 RTT {rtt} ms (임계치 초과)", "en": "average RTT {rtt} ms above threshold"},
    "report.avg_rtt_normal": {"ko": "평균 RTT {rtt} ms", "en": "average RTT {rtt} ms"},
    "report.state_changes": {"ko": "상태 변경 {n}회", "en": "{n} state changes"},
    "report.action_stable": {"ko": "즉각 조치 불필요. 정상 모니터링을 유지하세요.", "en": "No immediate action. Keep this device in normal monitoring."},
    "report.action_latency": {
        "ko": "지연 추이를 관찰하고, 서비스 저하 시 참조 포트 {ports}를 점검하세요.",
        "en": "Watch latency and verify reference ports {ports} if operators feel service slowdown.",
    },
    "report.action_latency_no_ports": {
        "ko": "지연 추이를 관찰하고, 인터페이스 부하를 점검하세요.",
        "en": "Watch latency trend and review interface load if operators feel slowdown.",
    },
    "report.action_disconnects": {
        "ko": "단절 발생 구간을 확인하고, 복구 후 참조 포트 {ports}를 점검하세요.",
        "en": "Review the disconnect windows first, then verify reference ports {ports} once host reachability is stable.",
    },
    "report.action_disconnects_no_ports": {
        "ko": "반복 단절 구간과 상위 네트워크/전원 상태를 점검하세요.",
        "en": "Review repeated disconnect windows and upstream network/power state.",
    },
    "report.no_ports": {"ko": "참조 포트 없음", "en": "No reference ports"},

    # ── Scanner ──
    "scanner.title": {"ko": "포트 스캐너", "en": "Port Scanner"},
    "scanner.target_ip": {"ko": "대상 IP", "en": "Target IP"},
    "scanner.ports": {"ko": "포트", "en": "Ports"},
    "scanner.protocol": {"ko": "프로토콜", "en": "Protocol"},
    "scanner.scan": {"ko": "스캔", "en": "Scan"},
    "scanner.stop": {"ko": "중지", "en": "Stop"},
    "scanner.scanning": {"ko": "스캔 중...", "en": "Scanning..."},
    "scanner.invalid_ip": {"ko": "IP 주소 형식이 올바르지 않습니다", "en": "Invalid IP address format"},
    "scanner.complete": {
        "ko": "스캔 완료: {total}개 포트 / {open}개 열림 / {closed}개 닫힘",
        "en": "Scan complete: {total} ports scanned / {open} open / {closed} closed",
    },
    "scanner.loaded": {"ko": "{ip} 대상과 참조 포트 {ports}를 불러왔습니다.", "en": "Loaded device target {ip} with reference ports {ports}."},
    "scanner.loaded_ip": {"ko": "{ip} 대상을 불러왔습니다.", "en": "Loaded device target {ip}."},
    "scanner.col_port": {"ko": "포트", "en": "Port"},
    "scanner.col_protocol": {"ko": "프로토콜", "en": "Protocol"},
    "scanner.col_state": {"ko": "상태", "en": "State"},
    "scanner.col_service": {"ko": "서비스", "en": "Service"},

    # ── Discovery ──
    "discovery.title": {"ko": "서브넷 탐색", "en": "Subnet Discovery"},
    "discovery.subnet": {"ko": "서브넷:", "en": "Subnet:"},
    "discovery.discover": {"ko": "탐색", "en": "Discover"},
    "discovery.scanning": {"ko": "서브넷 스캔 중...", "en": "Scanning subnet..."},
    "discovery.invalid_subnet": {"ko": "서브넷 형식이 올바르지 않습니다 (예: 192.168.1)", "en": "Invalid subnet format (e.g. 192.168.1)"},
    "discovery.progress": {"ko": "{scanned}/{total} 스캔 완료 - {found}개 호스트 발견", "en": "Scanned {scanned}/{total} - Found {found} hosts"},
    "discovery.complete": {"ko": "탐색 완료: {count}개 활성 호스트", "en": "Discovery complete: {count} active hosts found"},
    "discovery.col_ip": {"ko": "IP 주소", "en": "IP Address"},
    "discovery.col_rtt": {"ko": "RTT (ms)", "en": "RTT (ms)"},
    "discovery.col_hostname": {"ko": "호스트명", "en": "Hostname"},

    # ── Traceroute ──
    "traceroute.title": {"ko": "경로 추적", "en": "Traceroute"},
    "traceroute.target": {"ko": "대상:", "en": "Target:"},
    "traceroute.trace": {"ko": "추적", "en": "Trace"},
    "traceroute.tracing": {"ko": "경로 추적 중...", "en": "Tracing route..."},
    "traceroute.complete": {"ko": "완료: {count}개 홉", "en": "Complete: {count} hops"},
    "traceroute.col_hop": {"ko": "홉", "en": "Hop"},

    # ── Interfaces ──
    "interfaces.title": {"ko": "네트워크 인터페이스", "en": "Network Interfaces"},
    "interfaces.col_name": {"ko": "인터페이스", "en": "Interface"},
    "interfaces.col_status": {"ko": "상태", "en": "Status"},
    "interfaces.col_speed": {"ko": "속도", "en": "Speed"},
    "interfaces.col_sent": {"ko": "송신", "en": "Sent"},
    "interfaces.col_recv": {"ko": "수신", "en": "Received"},
    "interfaces.col_tx": {"ko": "TX 속도", "en": "TX Rate"},
    "interfaces.col_rx": {"ko": "RX 속도", "en": "RX Rate"},

    # ── Serial ──
    "serial.title": {"ko": "시리얼 / NMEA 포트", "en": "Serial / NMEA Ports"},
    "serial.add_monitor": {"ko": "모니터 추가", "en": "Add to Monitor"},
    "serial.detect": {"ko": "포트 검색", "en": "Detect Ports"},
    "serial.no_ports": {"ko": "시리얼 포트 없음 (pyserial 필요)", "en": "No serial ports detected (pyserial required)"},
    "serial.detected": {"ko": "{count}개 포트 감지", "en": "{count} port(s) detected"},
    "serial.monitored": {"ko": "모니터링 중", "en": "Monitored"},
    "serial.available": {"ko": "사용 가능", "en": "Available"},
    "serial.col_port": {"ko": "포트", "en": "Port"},
    "serial.col_status": {"ko": "상태", "en": "Status"},
    "serial.col_desc": {"ko": "설명", "en": "Description"},
    "serial.col_message": {"ko": "메시지", "en": "Message"},
    "serial.col_mfg": {"ko": "제조사", "en": "Manufacturer"},

    # ── History ──
    "history.title": {"ko": "이벤트 이력", "en": "Event History"},
    "history.device": {"ko": "장치:", "en": "Device:"},
    "history.event": {"ko": "이벤트:", "en": "Event:"},
    "history.all_devices": {"ko": "전체 장치", "en": "All devices"},
    "history.all_events": {"ko": "전체 이벤트", "en": "All events"},
    "history.attention_only": {"ko": "주의 필요", "en": "Attention only"},
    "history.disconnects": {"ko": "단절", "en": "Disconnects"},
    "history.high_latency": {"ko": "높은 지연", "en": "High latency"},
    "history.recoveries": {"ko": "복구", "en": "Recoveries"},
    "history.refresh": {"ko": "새로고침", "en": "Refresh"},
    "history.export_csv": {"ko": "CSV 내보내기", "en": "Export CSV"},
    "history.page": {"ko": "페이지 {n}", "en": "Page {n}"},
    "history.prev": {"ko": "이전", "en": "Prev"},
    "history.next": {"ko": "다음", "en": "Next"},
    "history.col_timestamp": {"ko": "시각", "en": "Timestamp"},
    "history.col_device": {"ko": "장치", "en": "Device"},
    "history.col_change": {"ko": "변경", "en": "Change"},
    "history.col_severity": {"ko": "심각도", "en": "Severity"},
    "history.col_detail": {"ko": "상세", "en": "Why It Matters"},
    "history.col_rtt": {"ko": "RTT (ms)", "en": "RTT (ms)"},
    "history.summary": {
        "ko": "현재 필터: {total}건 | 단절 {disc}건 | 지연 {delayed}건 | 복구 {conn}건",
        "en": "In current filter: {total} events | {disc} disconnects | {delayed} latency events | {conn} recoveries",
    },
    "history.event_connected": {"ko": "복구됨", "en": "Recovered"},
    "history.event_delayed": {"ko": "지연 발생", "en": "High latency"},
    "history.event_disconnected": {"ko": "단절됨", "en": "Disconnected"},

    # ── Report ──
    "report.title": {"ko": "가동률 리포트", "en": "Uptime Report"},
    "report.period": {"ko": "기간:", "en": "Period:"},
    "report.last_24h": {"ko": "최근 24시간", "en": "Last 24 hours"},
    "report.last_12h": {"ko": "최근 12시간", "en": "Last 12 hours"},
    "report.last_48h": {"ko": "최근 48시간", "en": "Last 48 hours"},
    "report.last_7d": {"ko": "최근 7일", "en": "Last 7 days"},
    "report.generate": {"ko": "생성", "en": "Generate"},
    "report.export_excel": {"ko": "Excel 내보내기", "en": "Export Excel"},
    "report.generate_prompt": {"ko": "리포트를 생성하면 기간별 가동률을 요약합니다.", "en": "Generate a report to summarize the fleet health over time."},
    "report.no_devices": {"ko": "선택 기간에 해당하는 장치가 없습니다.", "en": "No devices found in the selected period."},
    "report.export_first": {"ko": "먼저 리포트를 생성하세요.", "en": "Generate a report first."},
    "report.exported": {"ko": "리포트 내보내기 완료:\n{path}", "en": "Report exported to:\n{path}"},
    "report.col_device": {"ko": "장치", "en": "Device"},
    "report.col_importance": {"ko": "중요도", "en": "Importance"},
    "report.col_health": {"ko": "상태", "en": "Health"},
    "report.col_uptime": {"ko": "가동률 %", "en": "Uptime %"},
    "report.col_disconnects": {"ko": "단절 수", "en": "Disconnects"},
    "report.col_avg_rtt": {"ko": "평균 RTT (ms)", "en": "Avg RTT (ms)"},
    "report.col_changes": {"ko": "상태 변경", "en": "Status Changes"},
    "report.col_detail": {"ko": "상세", "en": "Why It Matters"},
    "report.col_action": {"ko": "조치", "en": "Next Action"},

    # ── Settings ──
    "settings.title": {"ko": "설정", "en": "Settings"},
    "settings.language": {"ko": "언어", "en": "Language"},
    "settings.lang_ko": {"ko": "한국어", "en": "한국어 (Korean)"},
    "settings.lang_en": {"ko": "English", "en": "English"},
    "settings.monitoring": {"ko": "모니터링", "en": "Monitoring"},
    "settings.ping_interval": {"ko": "핑 주기:", "en": "Ping Interval:"},
    "settings.interface_poll": {"ko": "인터페이스 주기:", "en": "Interface Poll:"},
    "settings.delay_threshold": {"ko": "지연 임계치:", "en": "Delay Threshold:"},
    "settings.alerts": {"ko": "알림", "en": "Alerts"},
    "settings.alert_enabled": {"ko": "상태 변경 시 알림", "en": "Enable status change alerts"},
    "settings.sound_enabled": {"ko": "단절 시 소리 알림", "en": "Sound alert on disconnect"},
    "settings.escalation": {"ko": "에스컬레이션 (3/10회 연속 실패 시 강화)", "en": "Escalation (louder after 3/10 consecutive failures)"},
    "settings.vessel_presets": {"ko": "선박 프리셋", "en": "Vessel Presets"},
    "settings.preset_desc": {"ko": "선박 유형에 맞는 프리셋 장치 구성을 불러옵니다.", "en": "Load a preset device configuration for your vessel type."},
    "settings.load_preset": {"ko": "프리셋 적용", "en": "Load Preset"},
    "settings.import_yaml": {"ko": "YAML 가져오기", "en": "Import YAML"},
    "settings.profiles": {"ko": "프로젝트 프로필", "en": "Project Profiles"},
    "settings.profile_desc": {"ko": "프로젝트/선박별 장치 구성을 저장하고 불러올 수 있습니다.", "en": "Save/load device configurations for different projects or vessels."},
    "settings.profile_name": {"ko": "프로필 이름 (예: Orsted Vessel A)", "en": "Profile name (e.g. Orsted Vessel A)"},
    "settings.vessel_name": {"ko": "선박명 (선택)", "en": "Vessel name (optional)"},
    "settings.save_current": {"ko": "현재 상태 저장", "en": "Save Current"},
    "settings.load": {"ko": "불러오기", "en": "Load"},
    "settings.delete": {"ko": "삭제", "en": "Delete"},
    "settings.safety_backups": {"ko": "안전 백업", "en": "Safety Backups"},
    "settings.backup_desc": {
        "ko": "프리셋/프로필/설정 교체 전에 자동 백업이 생성됩니다. 수동 생성 및 복원도 가능합니다.",
        "en": "A backup is created before preset/profile/config replacement. You can also create and restore backups manually.",
    },
    "settings.select_backup": {"ko": "복원할 백업 선택", "en": "Select backup to restore"},
    "settings.refresh": {"ko": "새로고침", "en": "Refresh"},
    "settings.create_backup": {"ko": "백업 생성", "en": "Create Backup"},
    "settings.restore": {"ko": "복원", "en": "Restore"},
    "settings.configuration": {"ko": "설정 파일", "en": "Configuration"},
    "settings.import_config": {"ko": "설정 가져오기", "en": "Import Config"},
    "settings.export_config": {"ko": "설정 내보내기", "en": "Export Config"},
    "settings.save_settings": {"ko": "설정 저장", "en": "Save Settings"},

    # ── Device dialog ──
    "device.add_title": {"ko": "장치 추가", "en": "Add Device"},
    "device.edit_title": {"ko": "장치 편집", "en": "Edit Device"},
    "device.name": {"ko": "이름:", "en": "Name:"},
    "device.ip": {"ko": "IP:", "en": "IP:"},
    "device.ports": {"ko": "포트:", "en": "Ports:"},
    "device.category": {"ko": "카테고리:", "en": "Category:"},
    "device.importance": {"ko": "중요도:", "en": "Importance:"},
    "device.description": {"ko": "설명:", "en": "Description:"},
    "device.monitoring_enabled": {"ko": "모니터링 활성화", "en": "Monitoring enabled"},
    "device.cancel": {"ko": "취소", "en": "Cancel"},
    "device.save": {"ko": "저장", "en": "Save"},
    "device.add": {"ko": "추가", "en": "Add"},
    "device.name_required": {"ko": "이름을 입력하세요", "en": "Name is required"},
    "device.ip_required": {"ko": "IP 주소를 입력하세요", "en": "IP address is required"},

    # ── Tray ──
    "tray.show": {"ko": "열기", "en": "Show"},
    "tray.exit": {"ko": "종료", "en": "Exit"},

    # ── Alert messages ──
    "alert.recovered": {"ko": "{name}: 정상 복구되었습니다.", "en": "{name}: Recovered and is back online."},
    "alert.recovered_latency": {"ko": "{name}: 지연이 해소되어 정상 범위로 돌아왔습니다.", "en": "{name}: Latency recovered and is back within threshold."},
    "alert.critical_latency": {
        "ko": "{name}: {count}회 연속 높은 지연이 발생했습니다.",
        "en": "{name}: High latency persisted for {count} consecutive checks.",
    },
    "alert.warning_latency": {
        "ko": "{name}: {count}회 연속 임계치 초과 지연 중입니다.",
        "en": "{name}: Latency is above threshold for {count} consecutive checks.",
    },
    "alert.emergency": {"ko": "{name}: 긴급 ({count}회 연속 실패)", "en": "{name}: EMERGENCY ({count} consecutive failures)"},
    "alert.critical": {"ko": "{name}: 위험 ({count}회 연속 실패)", "en": "{name}: CRITICAL ({count} consecutive failures)"},
    "alert.disconnected": {"ko": "{name}: 연결 끊김", "en": "{name}: Disconnected"},

    # ── Panel guides (subtitle help text) ──
    "guide.dashboard": {
        "ko": "선박 장비의 핑 상태를 실시간으로 모니터링합니다. 장치를 추가하고 카드를 클릭하면 상세 정보를 볼 수 있습니다.",
        "en": "Monitor ping status of vessel equipment in real-time. Add devices and click cards to see details.",
    },
    "guide.scanner": {
        "ko": "대상 IP의 열린 포트를 스캔합니다. 대시보드에서 장치를 선택하면 IP와 포트가 자동으로 채워집니다.",
        "en": "Scan open ports on a target IP. Selecting a device from the dashboard auto-fills the IP and ports.",
    },
    "guide.discovery": {
        "ko": "서브넷 내 활성 호스트를 자동 탐색합니다. 현재 네트워크의 서브넷이 기본 입력됩니다.",
        "en": "Auto-discover active hosts in a subnet. Your current network subnet is pre-filled.",
    },
    "guide.traceroute": {
        "ko": "대상 IP까지의 네트워크 경로를 홉별로 추적합니다. 지연이 높은 구간을 확인할 수 있습니다.",
        "en": "Trace the network path to a target IP hop by hop. Identify high-latency segments.",
    },
    "guide.interfaces": {
        "ko": "현재 PC의 네트워크 인터페이스 상태와 트래픽을 실시간으로 표시합니다.",
        "en": "Display real-time status and traffic of this PC's network interfaces.",
    },
    "guide.serial": {
        "ko": "선박 장비의 시리얼(COM) 포트를 감지하고 연결 상태를 모니터링합니다. pyserial 설치 필요.",
        "en": "Detect and monitor serial (COM) ports for vessel equipment. Requires pyserial.",
    },
    "guide.history": {
        "ko": "장치 상태 변경 이력을 시간순으로 기록합니다. 필터로 특정 장치나 이벤트만 볼 수 있습니다.",
        "en": "Record device status change history chronologically. Use filters to view specific devices or events.",
    },
    "guide.report": {
        "ko": "기간별 장치 가동률과 단절 통계를 요약합니다. Excel로 내보내 보고서에 활용할 수 있습니다.",
        "en": "Summarize device uptime and disconnect stats by period. Export to Excel for reporting.",
    },
    "guide.settings": {
        "ko": "모니터링 주기, 알림, 선박 프리셋, 프로필 관리 등을 설정합니다.",
        "en": "Configure monitoring intervals, alerts, vessel presets, and profile management.",
    },

    # ── NetworkMap ──
    "nav.networkmap": {"ko": "네트워크 맵", "en": "Network Map"},
    "netmap.title": {"ko": "네트워크 맵", "en": "Network Map"},
    "guide.networkmap": {
        "ko": "선박 LAN의 장비 토폴로지를 시각화합니다. 서브넷을 스캔하면 자동으로 노드가 배치되며, 드래그로 위치를 조정할 수 있습니다.",
        "en": "Visualize vessel LAN equipment topology. Scan a subnet to auto-place nodes, then drag to adjust layout.",
    },
    "netmap.subnet": {"ko": "서브넷:", "en": "Subnet:"},
    "netmap.scan": {"ko": "스캔", "en": "Scan"},
    "netmap.stop": {"ko": "중지", "en": "Stop"},
    "netmap.scanning": {"ko": "서브넷 스캔 중...", "en": "Scanning subnet..."},
    "netmap.scan_complete": {"ko": "스캔 완료: {count}개 호스트 발견", "en": "Scan complete: {count} hosts found"},
    "netmap.no_hosts": {"ko": "활성 호스트가 없습니다. 서브넷을 확인하세요.", "en": "No active hosts found. Check the subnet."},
    "netmap.monitoring": {"ko": "모니터링 중 ({count}개 노드)", "en": "Monitoring {count} node(s)"},
    "netmap.export_png": {"ko": "PNG 내보내기", "en": "Export PNG"},
    "netmap.export_csv": {"ko": "CSV 내보내기", "en": "Export CSV"},
    "netmap.save_layout": {"ko": "레이아웃 저장", "en": "Save Layout"},
    "netmap.load_layout": {"ko": "레이아웃 불러오기", "en": "Load Layout"},
    "netmap.layout_saved": {"ko": "레이아웃이 저장되었습니다: {path}", "en": "Layout saved: {path}"},
    "netmap.layout_loaded": {"ko": "레이아웃을 불러왔습니다: {count}개 노드", "en": "Layout loaded: {count} nodes"},
    "netmap.clear": {"ko": "초기화", "en": "Clear"},
    "netmap.auto_layout": {"ko": "자동 배치", "en": "Auto Layout"},
    "netmap.zoom_fit": {"ko": "전체 보기", "en": "Fit View"},
    "netmap.port_scan": {"ko": "포트 스캔 중...", "en": "Scanning ports..."},
    "netmap.invalid_subnet": {"ko": "서브넷 형식이 올바르지 않습니다 (예: 192.168.1)", "en": "Invalid subnet format (e.g. 192.168.1)"},
    # Node detail popup
    "netmap.detail_ip": {"ko": "IP 주소", "en": "IP Address"},
    "netmap.detail_mac": {"ko": "MAC 주소", "en": "MAC Address"},
    "netmap.detail_hostname": {"ko": "호스트명", "en": "Hostname"},
    "netmap.detail_rtt": {"ko": "응답시간", "en": "Response Time"},
    "netmap.detail_ports": {"ko": "열린 포트", "en": "Open Ports"},
    "netmap.detail_type": {"ko": "장비 유형", "en": "Device Type"},
    "netmap.detail_label": {"ko": "사용자 라벨", "en": "User Label"},
    "netmap.detail_status": {"ko": "상태", "en": "Status"},
    "netmap.online": {"ko": "온라인", "en": "Online"},
    "netmap.offline": {"ko": "오프라인", "en": "Offline"},
    "netmap.set_label": {"ko": "라벨 설정", "en": "Set Label"},
    "netmap.label_prompt": {"ko": "이 장비의 이름을 입력하세요:", "en": "Enter a name for this device:"},
    # Device type inference
    "netmap.type_router": {"ko": "라우터/게이트웨이", "en": "Router/Gateway"},
    "netmap.type_switch": {"ko": "스위치", "en": "Switch"},
    "netmap.type_server": {"ko": "서버", "en": "Server"},
    "netmap.type_workstation": {"ko": "워크스테이션", "en": "Workstation"},
    "netmap.type_marine": {"ko": "해양 장비", "en": "Marine Equipment"},
    "netmap.type_unknown": {"ko": "알 수 없음", "en": "Unknown"},

    # ── Common ──
    "common.traffic_active": {"ko": "트래픽: 활성", "en": "Traffic: Active"},
    "common.traffic_disabled": {"ko": "트래픽: 비활성", "en": "Traffic: Disabled"},
    "common.no_backup": {"ko": "백업이 없습니다.", "en": "No backups created yet."},
    "common.validation_error": {"ko": "입력 오류", "en": "Validation Error"},
    "common.export": {"ko": "내보내기", "en": "Export"},
    "common.import": {"ko": "가져오기", "en": "Import"},
    "common.error": {"ko": "오류", "en": "Error"},
    "common.confirm": {"ko": "확인", "en": "Confirm"},
}


def set_language(lang: str):
    """Set current language ('ko' or 'en')."""
    global _current_lang
    _current_lang = lang if lang in ("ko", "en") else "ko"


def get_language() -> str:
    return _current_lang


def t(key: str, **kwargs) -> str:
    """Get translated string. Supports {placeholder} formatting."""
    entry = TRANSLATIONS.get(key)
    if entry is None:
        return key
    text = entry.get(_current_lang, entry.get("en", key))
    if kwargs:
        try:
            text = text.format(**kwargs)
        except (KeyError, IndexError):
            pass
    return text
