"""Traceroute service using Windows tracert command."""

import re
import subprocess


def traceroute(ip, max_hops=30, timeout_ms=3000):
    """Run traceroute and return list of hops."""
    hops = []
    try:
        result = subprocess.run(
            ["tracert", "-d", "-w", str(timeout_ms), "-h", str(max_hops), ip],
            capture_output=True, text=True, timeout=max_hops * 5,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        lines = result.stdout.strip().split('\n')

        for line in lines:
            # Match lines like: "  1     1 ms     1 ms     1 ms  192.168.1.1"
            # or "  2     *        *        *     Request timed out."
            match = re.match(
                r'\s*(\d+)\s+(?:([<\d]+)\s*ms|\*)\s+(?:([<\d]+)\s*ms|\*)\s+(?:([<\d]+)\s*ms|\*)\s+([\d.]+|Request timed out\.)',
                line
            )
            if match:
                hop_num = int(match.group(1))
                rtts = []
                for g in [match.group(2), match.group(3), match.group(4)]:
                    if g:
                        g = g.replace('<', '')
                        try:
                            rtts.append(int(g))
                        except ValueError:
                            rtts.append(None)
                    else:
                        rtts.append(None)

                addr = match.group(5)
                if addr == 'Request timed out.':
                    addr = '*'

                avg_rtt = None
                valid_rtts = [r for r in rtts if r is not None]
                if valid_rtts:
                    avg_rtt = sum(valid_rtts) // len(valid_rtts)

                hops.append({
                    "hop": hop_num,
                    "ip": addr,
                    "rtt1": rtts[0],
                    "rtt2": rtts[1],
                    "rtt3": rtts[2],
                    "avg_rtt": avg_rtt,
                })

    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass

    return hops
