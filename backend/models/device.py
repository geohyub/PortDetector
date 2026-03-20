"""Device data model."""

import re
from dataclasses import dataclass, field, asdict
from typing import List


@dataclass
class Device:
    id: str = ""
    name: str = ""
    ip: str = ""
    ports: List[int] = field(default_factory=list)
    category: str = ""
    description: str = ""
    enabled: bool = True

    def validate(self):
        errors = []
        if not self.name or len(self.name) > 64:
            errors.append("Name must be 1-64 characters")
        if not re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', self.ip):
            errors.append("Invalid IPv4 address format")
        else:
            parts = self.ip.split('.')
            if any(int(p) > 255 for p in parts):
                errors.append("IP octets must be 0-255")
        for port in self.ports:
            if not (1 <= port <= 65535):
                errors.append("Ports must be 1-65535")
                break
        return errors

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data):
        return cls(
            id=data.get('id', ''),
            name=data.get('name', ''),
            ip=data.get('ip', ''),
            ports=data.get('ports', []),
            category=data.get('category', ''),
            description=data.get('description', ''),
            enabled=data.get('enabled', True),
        )
