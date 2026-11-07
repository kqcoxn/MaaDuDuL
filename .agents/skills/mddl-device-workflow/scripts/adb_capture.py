"""Save a raw ADB PNG without a text-mode pipe; emit capture metadata as JSON."""

import argparse
import json
import struct
import subprocess
import time
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--adb", required=True)
    parser.add_argument("--serial", required=True)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--timeout", type=float, default=15)
    args = parser.parse_args()
    started = time.perf_counter()
    result = subprocess.run(
        [args.adb, "-s", args.serial, "exec-out", "screencap", "-p"],
        capture_output=True,
        check=True,
        timeout=args.timeout,
    )
    data = result.stdout
    if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
        raise RuntimeError("ADB did not return a valid PNG header")
    width, height = struct.unpack(">II", data[16:24])
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(data)
    print(
        json.dumps(
            {
                "path": str(output),
                "serial": args.serial,
                "width": width,
                "height": height,
                "seconds": round(time.perf_counter() - started, 3),
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
