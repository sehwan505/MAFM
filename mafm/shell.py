"""MAFM 셸 모듈.

대화형 파일 관리 셸 인터페이스를 제공합니다.
"""

import argparse
import os
import subprocess
import tempfile
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING

from mafm.agent.graph import graph
from mafm.rag.embedding import initialize_model
from mafm.rag.fileops import make_soft_links

if TYPE_CHECKING:
    from subprocess import CompletedProcess


class ShellContext:
    """셸 컨텍스트를 관리하는 클래스.

    Attributes:
        link_dir: 현재 활성화된 임시 링크 디렉토리.
        root_dir: 루트 디렉토리 경로.
    """

    def __init__(self, root_dir: str) -> None:
        """ShellContext를 초기화합니다.

        Args:
            root_dir: 루트 디렉토리 경로.
        """
        self.link_dir: TemporaryDirectory[str] | None = None
        self.root_dir = root_dir

    def cleanup_link_dir(self) -> None:
        """링크 디렉토리를 정리합니다."""
        if self.link_dir is not None:
            self.link_dir.cleanup()
            self.link_dir = None


def execute_command(
    command: str,
    context: ShellContext,
) -> "CompletedProcess[bytes] | None":
    """명령어를 실행합니다.

    Args:
        command: 실행할 명령어 문자열.
        context: 셸 컨텍스트.

    Returns:
        명령어 실행 결과. 실패 시 None.
    """
    temp_dir_path = os.path.join(os.getcwd(), "temp")

    if not os.path.exists(temp_dir_path):
        os.makedirs(temp_dir_path)

    try:
        cmd_parts = command.strip().split()
        if cmd_parts[0] == "mlink":
            if len(cmd_parts) < 2:
                print("mlink: missing arguments. Usage: mlink <query>")
                return None

            prompt = " ".join(cmd_parts[1:])
            paths = graph(prompt)

            temp_dir = tempfile.TemporaryDirectory(dir=temp_dir_path)

            result = make_soft_links(paths, temp_dir)
            print(f"Soft links created: {result}")

            os.chdir(temp_dir.name)
            context.link_dir = temp_dir
            return None

        elif cmd_parts[0] == "cd":
            try:
                if cmd_parts[1] == "~":
                    os.chdir(os.path.expanduser("~"))
                else:
                    os.chdir(cmd_parts[1])
            except IndexError:
                print("cd: missing argument")
            except FileNotFoundError:
                print(f"cd: no such file or directory: {cmd_parts[1]}")
            return None

        else:
            return subprocess.run(cmd_parts, check=True)

    except subprocess.CalledProcessError as e:
        print(f"Command failed: {e}")
        return None
    except FileNotFoundError:
        print(f"Command not found: {command}")
        return None


def shell(root_dir: str) -> None:
    """대화형 셸을 시작합니다.

    Args:
        root_dir: 루트 디렉토리 경로.
    """
    initialize_model()
    print("model")

    context = ShellContext(root_dir)

    while True:
        cwd = os.getcwd()
        if context.link_dir is not None and context.link_dir.name not in cwd:
            context.cleanup_link_dir()

        command = input(f"{cwd} $ ")
        command = command.encode("utf-8").decode("utf-8")

        if command.strip().lower() in ["exit", "quit"]:
            print("쉘 종료 중...")
            break
        elif command.strip() == "":
            continue
        else:
            execute_command(command, context)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MAFM shell")
    parser.add_argument("-r", "--root", help="Root directory path")
    args = parser.parse_args()

    if not args.root:
        print("Root directory path is required.")
    else:
        shell(args.root)
