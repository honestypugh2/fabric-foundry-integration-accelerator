"""Development startup owns its processes and propagates failures."""

import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import pytest

from fabric_foundry_accelerator.services.devserver import run_servers

pytestmark = pytest.mark.skipif(os.name != "posix", reason="Development launcher requires POSIX")


@pytest.mark.parametrize("exit_code, expected", [(7, 7), (0, 1)])
def test_exit_stops_the_other_server(tmp_path: Path, exit_code: int, expected: int) -> None:
    pid_file = tmp_path / "server.pid"
    sleeper = (
        "import os,time; from pathlib import Path; "
        f"Path({str(pid_file)!r}).write_text(str(os.getpid())); time.sleep(30)"
    )
    quitter = (
        "import time; from pathlib import Path; "
        f"p=Path({str(pid_file)!r}); "
        "\nwhile not p.exists(): time.sleep(0.01)\n"
        f"raise SystemExit({exit_code})"
    )
    assert (
        run_servers(((sys.executable, "-c", sleeper), (sys.executable, "-c", quitter))) == expected
    )
    with pytest.raises(ProcessLookupError):
        os.kill(int(pid_file.read_text()), 0)


def test_start_failure_stops_already_started_server(tmp_path: Path) -> None:
    assert (
        run_servers(
            (
                (sys.executable, "-c", "import time; time.sleep(30)"),
                (str(tmp_path / "missing-executable"),),
            )
        )
        == 1
    )


@pytest.mark.parametrize("stop_signal", [signal.SIGTERM, signal.SIGINT])
def test_termination_signal_stops_supervisor_and_child(
    tmp_path: Path, stop_signal: signal.Signals
) -> None:
    pid_file = tmp_path / "child.pid"
    child = (
        "import os,time; from pathlib import Path; "
        f"Path({str(pid_file)!r}).write_text(str(os.getpid())); time.sleep(30)"
    )
    process = subprocess.Popen(  # noqa: S603 - fixed Python executable and synthetic test code
        (
            sys.executable,
            "-c",
            "import signal,sys; "
            "from fabric_foundry_accelerator.services.devserver import _interrupt,run_servers; "
            "signal.signal(signal.SIGTERM,_interrupt); "
            f"raise SystemExit(run_servers(((sys.executable,'-c',{child!r}),)))",
        ),
        stderr=subprocess.PIPE,
    )
    try:
        deadline = time.monotonic() + 10
        while not pid_file.exists() and time.monotonic() < deadline:
            time.sleep(0.01)
        assert pid_file.exists()
        process.send_signal(stop_signal)
        process.communicate(timeout=10)
        assert process.returncode == 130
        with pytest.raises(ProcessLookupError):
            os.kill(int(pid_file.read_text()), 0)
    finally:
        if process.poll() is None:
            process.terminate()
            process.communicate(timeout=10)
