from __future__ import annotations
import subprocess
from dataclasses import dataclass
from typing import Sequence

@dataclass
class CommandResult:
    returncode: int
    stdout: str
    stderr: str
    @property
    def combined(self) -> str:
        return "\n".join(x for x in (self.stdout, self.stderr) if x).strip()

def run_command(args: Sequence[str], timeout: int = 60, check: bool = False) -> CommandResult:
    try:
        completed = subprocess.run(list(args), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=timeout, check=False)
    except FileNotFoundError as exc:
        raise RuntimeError(f"Không tìm thấy lệnh: {args[0]}") from exc
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"Lệnh timeout sau {timeout}s: {' '.join(args)}") from exc
    result = CommandResult(completed.returncode, completed.stdout.strip(), completed.stderr.strip())
    if check and result.returncode != 0:
        raise RuntimeError(f"Lệnh thất bại ({result.returncode}): {' '.join(args)}\n{result.combined}")
    return result
