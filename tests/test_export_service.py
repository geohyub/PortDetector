"""Tests for PortDetector export helpers."""

from __future__ import annotations

from pathlib import Path

from desktop.services.export_service import export_history_csv, export_report_spreadsheet


def _sample_report_rows() -> list[dict]:
    return [
        {
            "name": "GNSS-01",
            "ip": "10.0.0.1",
            "category": "Sensor",
            "importance": "critical",
            "report_severity": "warning",
            "uptime_pct": 98.2,
            "up_mins": 1420.0,
            "down_mins": 20.0,
            "disconnects": 2,
            "avg_rtt": 210.4,
            "status_changes": 5,
            "report_summary": "High latency and a few disconnects.",
            "report_action": "Check the device and network path.",
        }
    ]


def test_export_report_spreadsheet_creates_file(tmp_path: Path):
    saved = export_report_spreadsheet(
        _sample_report_rows(),
        "1 device needs attention",
        24,
        str(tmp_path / "uptime_report.xlsx"),
    )

    assert Path(saved).exists()
    assert Path(saved).suffix.lower() in {".xlsx", ".csv"}


def test_export_history_csv_creates_file(tmp_path: Path):
    saved = export_history_csv(
        [
            {
                "timestamp": "2026-04-03T10:00:00",
                "device": "GNSS-01 (10.0.0.1)",
                "change": "Disconnected",
                "severity_label": "Critical",
                "detail": "Critical device. Link lost.",
                "rtt": 210,
            }
        ],
        str(tmp_path / "history.csv"),
    )

    assert Path(saved).exists()
    assert "GNSS-01" in Path(saved).read_text(encoding="utf-8")
