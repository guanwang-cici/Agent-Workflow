from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from dotenv import load_dotenv

from app.orchestration.workflow import WorkflowConfig, run_workflow


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the five-agent delivery workflow.")
    parser.add_argument("request", help="The user request to implement.")
    parser.add_argument("--workspace", default=None, help="Workspace path to inspect and modify.")
    parser.add_argument("--test-command", default=None, help="Command used by the tester agent.")
    parser.add_argument("--deploy-command", default=None, help="Command used by the deployer agent.")
    return parser


async def async_main() -> None:
    load_dotenv()
    args = build_parser().parse_args()

    config = WorkflowConfig.from_env(
        workspace_path=Path(args.workspace) if args.workspace else None,
        test_command=args.test_command,
        deploy_command=args.deploy_command,
    )
    report = await run_workflow(args.request, config)
    print(report.model_dump_json(indent=2))


def main() -> None:
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
