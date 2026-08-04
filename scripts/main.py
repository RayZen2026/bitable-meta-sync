"""
bitable-meta-sync SKILL 入口

子命令:
  extract  - 抽取源表字段 schema 到存储表
  dry-run  - 计算 diff 并输出报告 (阶段 2 stub)
  apply    - 把存储表 target 列写回源表 (阶段 3 stub)

路径 A: 单 slash command + argparse 路由
"""
import argparse
import json
import logging
import sys
from pathlib import Path

# 允许从 SKILL 根目录 import scripts.*
SKILL_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(SKILL_ROOT))

from scripts.common import setup_logger  # noqa: E402
from scripts.preflight import preflight, PreflightError  # noqa: E402
from scripts import extract  # noqa: E402
from scripts import dry_run  # noqa: E402
from scripts import apply as apply_mod  # noqa: E402

logger = logging.getLogger("bitable-meta-sync")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bitable-meta-sync",
        description="飞书多维表格字段元数据双向同步工具 v0.2.4 (中文列名 + extract + wiki URL + _SCHEMA 默认 + --new-base 新建 base)",
    )
    sub = parser.add_subparsers(dest="subcommand", required=True)

    # extract
    p_ext = sub.add_parser("extract", help="抽取源表字段 schema 到存储表")
    p_ext.add_argument("--source-url", required=True, help="源 bitable URL")
    p_ext.add_argument("--source-table", required=True, help="源表名")
    p_ext.add_argument("--storage-url", default=None,
                       help="存储表所在的 bitable URL (与 --new-base 互斥)")
    p_ext.add_argument("--storage-table", default=None,
                       help="存储表名 (缺省 = source-table + _SCHEMA 后缀)")
    p_ext.add_argument("--new-base", action="store_true",
                       help="创建新 bitable app 作为 storage (与 --storage-url 互斥)")
    p_ext.add_argument("--new-base-name", default=None,
                       help="新 base 名称 (缺省 = source-table + _SCHEMA)")
    p_ext.add_argument("--folder-token", default=None,
                       help="新 base 所在 folder token (缺省 = 我的空间 root)")
    p_ext.add_argument("--skip-preflight", action="store_true",
                       help="跳过 preflight 自检 (调试用)")

    # dry-run (阶段 2 stub)
    p_dr = sub.add_parser("dry-run", help="计算 diff 并输出报告 (阶段 2 stub)")
    p_dr.add_argument("--source-url", required=True)
    p_dr.add_argument("--source-table", required=True)
    p_dr.add_argument("--storage-url", required=True)

    # apply (阶段 3 stub)
    p_app = sub.add_parser("apply", help="把存储表 target 列写回源表 (阶段 3 stub)")
    p_app.add_argument("--source-url", required=True)
    p_app.add_argument("--source-table", required=True)
    p_app.add_argument("--storage-url", required=True)
    p_app.add_argument("--conflict", default="abort",
                       choices=["abort", "skip", "force"],
                       help="冲突处理策略 (缺省 abort)")
    p_app.add_argument("--scope", default="all",
                       choices=["all", "specified"],
                       help="apply 范围 (缺省 all)")
    p_app.add_argument("--confirm", action="store_true",
                       help="跳过 TTY 二次确认 (cron 用)")

    return parser


def _run_extract(args) -> int:
    """extract 子命令"""
    if not args.skip_preflight:
        try:
            # preflight 源表; storage 在 new_base 模式下由 extract 内部创建
            # 这里用 source_url 兜底, 实际存储表创建后 extract 会再确认
            preflight(args.source_url, args.storage_url or args.source_url)
        except PreflightError as e:
            logger.error("preflight 失败: %s", e)
            print(json.dumps({"ok": False, "error": {"code": "E_PREFLIGHT", "message": str(e)}},
                             ensure_ascii=False, indent=2))
            return 1

    try:
        result = extract.extract(
            source_url=args.source_url,
            source_table_name=args.source_table,
            storage_url=args.storage_url,
            storage_table_name=args.storage_table,
            new_base=args.new_base,
            new_base_name=args.new_base_name,
            folder_token=args.folder_token,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except Exception as e:
        logger.exception("extract 失败")
        print(json.dumps({"ok": False, "error": {"code": "E_EXTRACT", "message": str(e)}},
                         ensure_ascii=False, indent=2))
        return 1


def _run_dry_run(args) -> int:
    """dry-run 子命令 (阶段 2 stub)"""
    result = dry_run.dry_run(
        source_url=args.source_url,
        source_table_name=args.source_table,
        storage_url=args.storage_url,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok") else 1


def _run_apply(args) -> int:
    """apply 子命令 (阶段 3 stub)"""
    result = apply_mod.apply(
        source_url=args.source_url,
        source_table_name=args.source_table,
        storage_url=args.storage_url,
        conflict=args.conflict,
        scope=args.scope,
        confirm=args.confirm,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok") else 1


def main(argv=None) -> int:
    setup_logger()
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.subcommand == "extract":
        return _run_extract(args)
    elif args.subcommand == "dry-run":
        return _run_dry_run(args)
    elif args.subcommand == "apply":
        return _run_apply(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
