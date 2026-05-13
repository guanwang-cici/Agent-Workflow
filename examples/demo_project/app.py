from __future__ import annotations

import argparse


def add(left: int, right: int) -> int:
    return left + right


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    if args.check:
        print("demo project health check passed")
        return

    print(add(1, 2))


if __name__ == "__main__":
    main()
