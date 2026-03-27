"""Serial (COM) port detection and monitoring service."""

import sys
from typing import List, Optional, Tuple


def list_serial_ports() -> List[dict]:
    """List available COM ports on the system."""
    try:
        import serial.tools.list_ports
        ports = []
        for port in serial.tools.list_ports.comports():
            ports.append({
                'port': port.device,
                'description': port.description,
                'hwid': port.hwid,
                'manufacturer': port.manufacturer or '',
            })
        return ports
    except ImportError:
        return []


def test_serial_port(port: str, baudrate: int = 9600, timeout: float = 2.0) -> Tuple[bool, str]:
    """Test if a serial port is accessible. Returns (success, message)."""
    try:
        import serial
        ser = serial.Serial(port, baudrate=baudrate, timeout=timeout)
        # Try to read a few bytes to see if data is flowing
        data = ser.read(64)
        ser.close()
        if data:
            # Check if it looks like NMEA
            text = data.decode('ascii', errors='replace')
            if '$' in text:
                return True, f"NMEA data detected ({len(data)} bytes)"
            return True, f"Data received ({len(data)} bytes)"
        return True, "Port open (no data within timeout)"
    except ImportError:
        return False, "pyserial not installed"
    except Exception as e:
        return False, str(e)


def read_nmea_sentence(port: str, baudrate: int = 9600, timeout: float = 3.0) -> Optional[str]:
    """Read one NMEA sentence from a serial port."""
    try:
        import serial
        ser = serial.Serial(port, baudrate=baudrate, timeout=timeout)
        line = ser.readline().decode('ascii', errors='replace').strip()
        ser.close()
        return line if line.startswith('$') else None
    except Exception:
        return None
