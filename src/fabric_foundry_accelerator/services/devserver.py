"""Supervise the two local development servers on POSIX hosts."""

import os
import signal
import subprocess
import sys
import time
from collections.abc import Sequence
from contextlib import suppress


def _stop(process: subprocess.Popen[bytes]) -> None:
    """Stop only the process group created for this server, including npm's child."""
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        process.poll()
        try:
            os.killpg(process.pid, 0)
        except ProcessLookupError:
            break
        time.sleep(0.05)
    else:
        with suppress(ProcessLookupError):
            os.killpg(process.pid, signal.SIGKILL)
    process.wait()


def run_servers(commands: Sequence[Sequence[str]]) -> int:
    """Run servers until either exits; stop all owned groups and return a failure status."""
    processes: list[subprocess.Popen[bytes]] = []
    try:
        for command in commands:
            processes.append(subprocess.Popen(command, start_new_session=True))  # noqa: S603 - fixed developer commands, no shell
        while True:
            for process in processes:
                status = process.poll()
                if status is not None:
                    sys.stderr.write(f"Development server {process.args!r} exited ({status}).\n")
                    return status if status > 0 else 1
            time.sleep(0.05)
    except OSError as error:
        sys.stderr.write(f"Cannot start development servers: {error}\n")
        return 1
    except KeyboardInterrupt:
        return 130
    finally:
        for process in processes:
            _stop(process)


def _interrupt(_signum: int, _frame: object) -> None:
    raise KeyboardInterrupt


def main() -> int:
    """Start the API and Vite from the repository root; forward API flags verbatim."""
    signal.signal(signal.SIGTERM, _interrupt)
    return run_servers(
        (
            (sys.executable, "-m", "fabric_foundry_accelerator.cli", "serve", "api", *sys.argv[1:]),
            ("npm", "--prefix", "frontend", "run", "dev"),
        )
    )


if __name__ == "__main__":
    raise SystemExit(main())
