"""Compatibility entrypoint; prefer yarn dev:prepare and yarn dev:start."""
from mfaa import main

if __name__ == "__main__":
    raise SystemExit(main(["prepare"]))
