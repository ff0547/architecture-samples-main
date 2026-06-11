#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
apk_static_report.py

用途：
1. 使用 Androguard 分析一个 APK。
2. 提取项目内类、方法、方法调用关系。
3. 根据 Manifest 入口和调用关系生成核心功能逻辑子图。
4. 导出可视化图文件（GML / GraphML）和 CSV / JSON / Markdown 报告。
5. 可选读取 JaCoCo XML，导出“测试实际覆盖的方法”。

说明：
- APK 静态分析本身无法判断哪些方法在测试运行时被真正执行。
- 如需输出“测试覆盖的方法”，请额外传入 JaCoCo XML：
    --jacoco-xml path\\to\\jacocoTestReport.xml
- 未提供 JaCoCo XML 时，脚本仍会输出静态可达方法，但不会将其误称为测试覆盖率。

依赖：
    python -m pip install androguard networkx

示例：
    python apk_static_report.py ^
      --apk "C:\\Users\\fsqfs\\Desktop\\architecture-samples-apks\\universal.apk" ^
      --output "C:\\Users\\fsqfs\\Desktop\\androguard_full_report"

可选：
    python apk_static_report.py ^
      --apk "C:\\Users\\fsqfs\\Desktop\\architecture-samples-apks\\universal.apk" ^
      --output "C:\\Users\\fsqfs\\Desktop\\androguard_full_report" ^
      --jacoco-xml "C:\\path\\to\\jacocoTestReport.xml"
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import defaultdict, deque
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Optional
import xml.etree.ElementTree as ET

try:
    import networkx as nx
except ImportError as exc:
    raise SystemExit(
        "缺少 networkx。请执行：python -m pip install networkx"
    ) from exc

try:
    from androguard.misc import AnalyzeAPK
except ImportError as exc:
    raise SystemExit(
        "缺少 androguard。请执行：python -m pip install androguard"
    ) from exc


# ============================================================
# 数据结构
# ============================================================

@dataclass
class MethodRow:
    signature: str
    class_name: str
    java_class_name: str
    method_name: str
    descriptor: str
    access_flags: str
    is_external: bool
    is_project_method: bool
    code_size: int
    incoming_project_calls: int = 0
    outgoing_project_calls: int = 0
    outgoing_external_calls: int = 0
    reachable_from_manifest_entry: bool = False
    core_score: int = 0


@dataclass
class CallRow:
    caller_signature: str
    caller_class: str
    caller_method: str
    callee_signature: str
    callee_class: str
    callee_method: str
    callee_descriptor: str
    bytecode_offset: int
    callee_is_external: bool
    callee_is_project_method: bool


@dataclass
class CoverageRow:
    class_name: str
    java_class_name: str
    method_name: str
    descriptor: str
    signature: str
    instruction_covered: int
    instruction_missed: int
    line_covered: int
    line_missed: int
    branch_covered: int
    branch_missed: int
    covered: bool
    exists_in_apk_project_methods: bool = False


# ============================================================
# 基础工具
# ============================================================

def call_or_default(obj: Any, method_name: str, default: Any = "") -> Any:
    """安全调用对象方法。不同 Androguard 版本中部分方法可能不存在。"""
    fn = getattr(obj, method_name, None)
    if not callable(fn):
        return default
    try:
        result = fn()
        return default if result is None else result
    except Exception:
        return default


def unwrap_method(obj: Any) -> Any:
    """
    MethodAnalysis.get_method() -> EncodedMethod / ExternalMethod。
    如果传入对象本身已经是底层方法，则直接返回。
    """
    fn = getattr(obj, "get_method", None)
    if callable(fn):
        try:
            value = fn()
            if value is not None:
                return value
        except Exception:
            pass
    return obj


def method_parts(method_analysis_or_method: Any) -> tuple[str, str, str, str]:
    """返回：class_name, method_name, descriptor, access_flags。"""
    method = unwrap_method(method_analysis_or_method)
    class_name = str(call_or_default(method, "get_class_name", ""))
    method_name = str(call_or_default(method, "get_name", ""))
    descriptor = str(call_or_default(method, "get_descriptor", ""))
    access_flags = str(call_or_default(method, "get_access_flags_string", ""))
    return class_name, method_name, descriptor, access_flags


def is_external_method(method_analysis_or_method: Any) -> bool:
    fn = getattr(method_analysis_or_method, "is_external", None)
    if callable(fn):
        try:
            return bool(fn())
        except Exception:
            pass

    method = unwrap_method(method_analysis_or_method)
    fn = getattr(method, "is_external", None)
    if callable(fn):
        try:
            return bool(fn())
        except Exception:
            pass

    return method.__class__.__name__.lower().startswith("external")


def method_signature(method_analysis_or_method: Any) -> str:
    class_name, method_name, descriptor, _ = method_parts(method_analysis_or_method)
    return f"{class_name}->{method_name}{descriptor}"


def descriptor_to_java_name(class_name: str) -> str:
    """
    Lcom/example/Foo; -> com.example.Foo
    [Lcom/example/Foo; 等数组描述符也尽量处理。
    """
    value = class_name.strip()
    while value.startswith("["):
        value = value[1:]
    if value.startswith("L") and value.endswith(";"):
        value = value[1:-1]
    return value.replace("/", ".")


def normalize_manifest_component(package_name: str, component_name: str) -> str:
    """
    Manifest 组件名转 Java 全限定类名。
    .TodoActivity -> package.TodoActivity
    TodoActivity  -> package.TodoActivity
    com.demo.TodoActivity -> 原样保留
    """
    value = (component_name or "").strip()
    if not value:
        return value
    if value.startswith("."):
        return package_name + value
    if "." not in value:
        return f"{package_name}.{value}"
    return value


def java_name_to_descriptor(java_name: str) -> str:
    return "L" + java_name.replace(".", "/") + ";"


def safe_code_size(method_analysis: Any) -> int:
    fn = getattr(method_analysis, "get_length", None)
    if callable(fn):
        try:
            return int(fn())
        except Exception:
            pass

    method = unwrap_method(method_analysis)
    code = call_or_default(method, "get_code", None)
    if code is None:
        return 0

    # 不同版本兼容：尽量通过原始字节码长度估算
    try:
        bc = code.get_bc()
        raw = bc.get_raw()
        return len(raw)
    except Exception:
        return 0


def write_csv(path: Path, rows: Iterable[Any], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as fp:
        writer = csv.DictWriter(fp, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            if hasattr(row, "__dataclass_fields__"):
                writer.writerow(asdict(row))
            elif isinstance(row, dict):
                writer.writerow(row)
            else:
                raise TypeError(f"不支持的 CSV 行类型：{type(row)!r}")


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fp:
        json.dump(data, fp, ensure_ascii=False, indent=2)


def safe_graph_node_id(signature: str) -> str:
    return signature


def stringify_graph_attributes(graph: nx.Graph) -> nx.Graph:
    """
    GML / GraphML 对属性类型要求严格。
    统一将 None、复杂对象等转换为可序列化标量。
    """
    clean = graph.__class__()

    for node, attrs in graph.nodes(data=True):
        clean_attrs = {}
        for key, value in attrs.items():
            if value is None:
                clean_attrs[key] = ""
            elif isinstance(value, (str, int, float, bool)):
                clean_attrs[key] = value
            else:
                clean_attrs[key] = str(value)
        clean.add_node(node, **clean_attrs)

    if graph.is_multigraph():
        for source, target, key, attrs in graph.edges(keys=True, data=True):
            clean_attrs = {}
            for attr_key, value in attrs.items():
                if value is None:
                    clean_attrs[attr_key] = ""
                elif isinstance(value, (str, int, float, bool)):
                    clean_attrs[attr_key] = value
                else:
                    clean_attrs[attr_key] = str(value)
            clean.add_edge(source, target, key=key, **clean_attrs)
    else:
        for source, target, attrs in graph.edges(data=True):
            clean_attrs = {}
            for attr_key, value in attrs.items():
                if value is None:
                    clean_attrs[attr_key] = ""
                elif isinstance(value, (str, int, float, bool)):
                    clean_attrs[attr_key] = value
                else:
                    clean_attrs[attr_key] = str(value)
            clean.add_edge(source, target, **clean_attrs)

    return clean


# ============================================================
# Manifest、类、方法、调用关系
# ============================================================

def get_manifest_info(apk: Any) -> dict[str, Any]:
    package_name = str(call_or_default(apk, "get_package", ""))
    main_activity = str(call_or_default(apk, "get_main_activity", ""))

    activities = [
        normalize_manifest_component(package_name, str(x))
        for x in call_or_default(apk, "get_activities", [])
    ]
    services = [
        normalize_manifest_component(package_name, str(x))
        for x in call_or_default(apk, "get_services", [])
    ]
    receivers = [
        normalize_manifest_component(package_name, str(x))
        for x in call_or_default(apk, "get_receivers", [])
    ]
    providers = [
        normalize_manifest_component(package_name, str(x))
        for x in call_or_default(apk, "get_providers", [])
    ]

    if main_activity:
        main_activity = normalize_manifest_component(package_name, main_activity)

    components = []
    for component_type, values in (
        ("main_activity", [main_activity] if main_activity else []),
        ("activity", activities),
        ("service", services),
        ("receiver", receivers),
        ("provider", providers),
    ):
        for value in values:
            if value:
                components.append(
                    {
                        "type": component_type,
                        "java_class_name": value,
                        "descriptor": java_name_to_descriptor(value),
                    }
                )

    # 去重
    unique_components = []
    seen = set()
    for item in components:
        key = (item["type"], item["descriptor"])
        if key not in seen:
            seen.add(key)
            unique_components.append(item)

    return {
        "package_name": package_name,
        "version_code": str(call_or_default(apk, "get_androidversion_code", "")),
        "version_name": str(call_or_default(apk, "get_androidversion_name", "")),
        "min_sdk": str(call_or_default(apk, "get_min_sdk_version", "")),
        "target_sdk": str(call_or_default(apk, "get_target_sdk_version", "")),
        "main_activity": main_activity,
        "permissions": sorted(str(x) for x in call_or_default(apk, "get_permissions", [])),
        "activities": sorted(set(activities)),
        "services": sorted(set(services)),
        "receivers": sorted(set(receivers)),
        "providers": sorted(set(providers)),
        "components": unique_components,
    }


def choose_project_prefix(manifest_info: dict[str, Any], user_prefix: Optional[str]) -> tuple[str, str]:
    """
    返回：
      java_prefix，例如 com.example.android.architecture.blueprints
      descriptor_prefix，例如 Lcom/example/android/architecture/blueprints/
    """
    java_prefix = (user_prefix or manifest_info["package_name"]).strip()
    java_prefix = java_prefix.rstrip(".")
    descriptor_prefix = "L" + java_prefix.replace(".", "/") + "/"
    return java_prefix, descriptor_prefix


def collect_methods_and_calls(
    dx: Any,
    descriptor_prefix: str,
) -> tuple[
    dict[str, MethodRow],
    list[CallRow],
    nx.MultiDiGraph,
    nx.MultiDiGraph,
]:
    """
    返回：
      project_methods: 项目内方法字典
      all_calls_from_project: 从项目方法发出的所有调用
      full_graph: 项目方法 -> 任意目标方法
      project_graph: 项目方法 -> 项目方法
    """
    project_methods: dict[str, MethodRow] = {}
    method_analysis_by_signature: dict[str, Any] = {}

    # 第一次遍历：收集项目内部方法
    for method_analysis in dx.get_methods():
        class_name, method_name, descriptor, access_flags = method_parts(method_analysis)
        if not class_name.startswith(descriptor_prefix):
            continue

        signature = method_signature(method_analysis)
        row = MethodRow(
            signature=signature,
            class_name=class_name,
            java_class_name=descriptor_to_java_name(class_name),
            method_name=method_name,
            descriptor=descriptor,
            access_flags=access_flags,
            is_external=is_external_method(method_analysis),
            is_project_method=True,
            code_size=safe_code_size(method_analysis),
        )
        project_methods[signature] = row
        method_analysis_by_signature[signature] = method_analysis

    full_graph = nx.MultiDiGraph()
    project_graph = nx.MultiDiGraph()
    calls: list[CallRow] = []

    def add_node_if_absent(
        graph: nx.MultiDiGraph,
        signature: str,
        class_name: str,
        method_name: str,
        descriptor: str,
        external: bool,
        project: bool,
    ) -> None:
        if signature not in graph:
            graph.add_node(
                safe_graph_node_id(signature),
                signature=signature,
                class_name=class_name,
                java_class_name=descriptor_to_java_name(class_name),
                method_name=method_name,
                descriptor=descriptor,
                external=bool(external),
                project=bool(project),
            )

    # 第二次遍历：读取 XREF 调用关系
    for caller_signature, caller_row in project_methods.items():
        caller_analysis = method_analysis_by_signature[caller_signature]

        add_node_if_absent(
            full_graph,
            caller_signature,
            caller_row.class_name,
            caller_row.method_name,
            caller_row.descriptor,
            caller_row.is_external,
            True,
        )
        add_node_if_absent(
            project_graph,
            caller_signature,
            caller_row.class_name,
            caller_row.method_name,
            caller_row.descriptor,
            caller_row.is_external,
            True,
        )

        get_xref_to = getattr(caller_analysis, "get_xref_to", None)
        if not callable(get_xref_to):
            continue

        try:
            xrefs = list(get_xref_to())
        except Exception:
            xrefs = []

        for xref in xrefs:
            # 官方常见结构：(ClassAnalysis, MethodAnalysis, offset)
            if not isinstance(xref, (tuple, list)) or len(xref) < 3:
                continue

            callee_analysis = xref[1]
            try:
                offset = int(xref[2])
            except Exception:
                offset = -1

            callee_class, callee_name, callee_descriptor, _ = method_parts(callee_analysis)
            callee_signature = method_signature(callee_analysis)
            callee_external = is_external_method(callee_analysis)
            callee_project = callee_class.startswith(descriptor_prefix)

            calls.append(
                CallRow(
                    caller_signature=caller_signature,
                    caller_class=caller_row.class_name,
                    caller_method=caller_row.method_name,
                    callee_signature=callee_signature,
                    callee_class=callee_class,
                    callee_method=callee_name,
                    callee_descriptor=callee_descriptor,
                    bytecode_offset=offset,
                    callee_is_external=callee_external,
                    callee_is_project_method=callee_project,
                )
            )

            add_node_if_absent(
                full_graph,
                callee_signature,
                callee_class,
                callee_name,
                callee_descriptor,
                callee_external,
                callee_project,
            )
            full_graph.add_edge(
                caller_signature,
                callee_signature,
                offset=offset,
            )

            if callee_project:
                add_node_if_absent(
                    project_graph,
                    callee_signature,
                    callee_class,
                    callee_name,
                    callee_descriptor,
                    callee_external,
                    True,
                )
                project_graph.add_edge(
                    caller_signature,
                    callee_signature,
                    offset=offset,
                )

    # 统计度数与外部调用
    outgoing_external_count: dict[str, int] = defaultdict(int)
    for call in calls:
        if not call.callee_is_project_method:
            outgoing_external_count[call.caller_signature] += 1

    for signature, row in project_methods.items():
        row.incoming_project_calls = int(project_graph.in_degree(signature))
        row.outgoing_project_calls = int(project_graph.out_degree(signature))
        row.outgoing_external_calls = outgoing_external_count[signature]

    return project_methods, calls, full_graph, project_graph


def collect_project_classes(
    project_methods: dict[str, MethodRow]
) -> list[dict[str, Any]]:
    by_class: dict[str, list[MethodRow]] = defaultdict(list)
    for row in project_methods.values():
        by_class[row.class_name].append(row)

    rows = []
    for class_name, methods in sorted(by_class.items()):
        rows.append(
            {
                "class_name": class_name,
                "java_class_name": descriptor_to_java_name(class_name),
                "method_count": len(methods),
                "total_code_size": sum(x.code_size for x in methods),
                "incoming_project_calls": sum(x.incoming_project_calls for x in methods),
                "outgoing_project_calls": sum(x.outgoing_project_calls for x in methods),
                "outgoing_external_calls": sum(x.outgoing_external_calls for x in methods),
            }
        )
    return rows


# ============================================================
# 静态可达分析与核心功能子图
# ============================================================

LIFECYCLE_NAMES = {
    "onCreate", "onStart", "onResume", "onPause", "onStop",
    "onDestroy", "onReceive", "onBind", "onClick", "invoke",
}

DOMAIN_KEYWORDS = (
    "task", "todo", "load", "save", "insert", "update", "delete",
    "remove", "add", "complete", "clear", "refresh", "observe",
    "repository", "datasource", "viewmodel", "usecase", "filter",
    "sync", "fetch", "get", "set",
)


def mark_manifest_reachable_methods(
    project_methods: dict[str, MethodRow],
    project_graph: nx.MultiDiGraph,
    manifest_info: dict[str, Any],
) -> set[str]:
    """
    从 Manifest 组件类的方法出发，在项目内部调用图中做 BFS。
    这是“静态可达方法”，不是动态测试覆盖率。
    """
    entry_class_descriptors = {
        item["descriptor"] for item in manifest_info.get("components", [])
    }

    seeds = {
        signature
        for signature, row in project_methods.items()
        if row.class_name in entry_class_descriptors
    }

    reachable = set(seeds)
    queue: deque[str] = deque(seeds)

    while queue:
        source = queue.popleft()
        for target in project_graph.successors(source):
            if target not in reachable:
                reachable.add(target)
                queue.append(target)

    for signature in reachable:
        if signature in project_methods:
            project_methods[signature].reachable_from_manifest_entry = True

    return reachable


def calculate_core_scores(project_methods: dict[str, MethodRow]) -> list[MethodRow]:
    """
    启发式核心分数：
    - 项目内入度、出度越高，通常越接近业务逻辑核心。
    - 调用外部 API 越多，通常承担更多实际行为。
    - 生命周期和常见业务方法名适度加分。
    - Manifest 静态可达方法加分。
    """
    for row in project_methods.values():
        score = (
            row.incoming_project_calls * 2
            + row.outgoing_project_calls * 3
            + min(row.outgoing_external_calls, 20)
            + min(row.code_size // 32, 20)
        )

        name_lower = row.method_name.lower()
        class_lower = row.java_class_name.lower()

        if row.method_name in LIFECYCLE_NAMES:
            score += 8

        if any(keyword in name_lower or keyword in class_lower for keyword in DOMAIN_KEYWORDS):
            score += 5

        if row.reachable_from_manifest_entry:
            score += 4

        if row.method_name in {"<init>", "<clinit>"}:
            score -= 4

        row.core_score = int(score)

    return sorted(
        project_methods.values(),
        key=lambda item: (
            item.core_score,
            item.outgoing_project_calls,
            item.incoming_project_calls,
            item.code_size,
        ),
        reverse=True,
    )


def build_core_logic_subgraph(
    project_graph: nx.MultiDiGraph,
    ranked_methods: list[MethodRow],
    top_n: int,
    max_nodes: int,
) -> tuple[nx.MultiDiGraph, list[str]]:
    """
    以核心分数最高的方法为种子，保留：
    - 种子
    - 种子的直接调用目标
    - 直接调用种子的方法
    - 再补充一层邻居
    """
    seeds = [
        row.signature
        for row in ranked_methods
        if row.signature in project_graph
    ][:top_n]

    selected: set[str] = set(seeds)
    frontier: set[str] = set(seeds)

    for _ in range(2):
        next_frontier: set[str] = set()
        for node in frontier:
            next_frontier.update(project_graph.successors(node))
            next_frontier.update(project_graph.predecessors(node))

        next_frontier -= selected

        # 限制子图规模，优先保留高分节点
        if len(selected) + len(next_frontier) > max_nodes:
            score_map = {row.signature: row.core_score for row in ranked_methods}
            next_frontier = set(
                sorted(
                    next_frontier,
                    key=lambda x: score_map.get(x, 0),
                    reverse=True,
                )[: max(0, max_nodes - len(selected))]
            )

        selected.update(next_frontier)
        frontier = next_frontier

        if not frontier or len(selected) >= max_nodes:
            break

    subgraph = project_graph.subgraph(selected).copy()

    score_map = {row.signature: row.core_score for row in ranked_methods}
    for node in subgraph.nodes:
        subgraph.nodes[node]["core_score"] = int(score_map.get(node, 0))
        subgraph.nodes[node]["is_core_seed"] = bool(node in seeds)

    return subgraph, seeds


def write_mermaid_subgraph(path: Path, graph: nx.MultiDiGraph, max_edges: int = 80) -> None:
    """
    输出可复制到 Mermaid 编辑器中的核心逻辑图。
    为避免图过大，只保留前 max_edges 条边。
    """
    node_alias: dict[str, str] = {}
    lines = ["flowchart LR"]

    for index, node in enumerate(graph.nodes()):
        alias = f"M{index}"
        node_alias[node] = alias

        attrs = graph.nodes[node]
        java_class = str(attrs.get("java_class_name", ""))
        class_simple = java_class.split(".")[-1] if java_class else ""
        method_name = str(attrs.get("method_name", ""))
        label = f"{class_simple}.{method_name}".replace('"', "'")
        lines.append(f'    {alias}["{label}"]')

    seen_edges = set()
    edge_count = 0
    for source, target in graph.edges():
        pair = (source, target)
        if pair in seen_edges:
            continue
        seen_edges.add(pair)

        if source not in node_alias or target not in node_alias:
            continue

        lines.append(f"    {node_alias[source]} --> {node_alias[target]}")
        edge_count += 1

        if edge_count >= max_edges:
            break

    if graph.number_of_edges() > max_edges:
        lines.append(
            f"    %% 图中实际边数为 {graph.number_of_edges()}，"
            f"此 Mermaid 文件仅显示前 {max_edges} 条边。"
        )

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


# ============================================================
# JaCoCo 测试覆盖率
# ============================================================

def read_counter(node: ET.Element, counter_type: str) -> tuple[int, int]:
    for counter in node.findall("counter"):
        if counter.attrib.get("type") == counter_type:
            missed = int(counter.attrib.get("missed", "0"))
            covered = int(counter.attrib.get("covered", "0"))
            return covered, missed
    return 0, 0


def parse_jacoco_xml(
    jacoco_xml: Path,
    apk_project_method_signatures: set[str],
) -> list[CoverageRow]:
    """
    解析 JaCoCo XML。
    JaCoCo 的 method desc 通常与 DEX descriptor 格式一致，可用于精确匹配。
    """
    root = ET.parse(jacoco_xml).getroot()
    rows: list[CoverageRow] = []

    for package in root.findall("package"):
        package_name = package.attrib.get("name", "")

        for class_node in package.findall("class"):
            class_path = class_node.attrib.get("name", "")
            if not class_path:
                class_path = package_name

            class_descriptor = f"L{class_path};"
            java_class_name = descriptor_to_java_name(class_descriptor)

            for method_node in class_node.findall("method"):
                method_name = method_node.attrib.get("name", "")
                descriptor = method_node.attrib.get("desc", "")
                signature = f"{class_descriptor}->{method_name}{descriptor}"

                instruction_covered, instruction_missed = read_counter(
                    method_node, "INSTRUCTION"
                )
                line_covered, line_missed = read_counter(method_node, "LINE")
                branch_covered, branch_missed = read_counter(method_node, "BRANCH")

                covered = (
                    instruction_covered > 0
                    or line_covered > 0
                    or branch_covered > 0
                )

                rows.append(
                    CoverageRow(
                        class_name=class_descriptor,
                        java_class_name=java_class_name,
                        method_name=method_name,
                        descriptor=descriptor,
                        signature=signature,
                        instruction_covered=instruction_covered,
                        instruction_missed=instruction_missed,
                        line_covered=line_covered,
                        line_missed=line_missed,
                        branch_covered=branch_covered,
                        branch_missed=branch_missed,
                        covered=covered,
                        exists_in_apk_project_methods=(
                            signature in apk_project_method_signatures
                        ),
                    )
                )

    return rows


# ============================================================
# 报告输出
# ============================================================

def write_class_method_tree(path: Path, project_methods: dict[str, MethodRow]) -> None:
    by_class: dict[str, list[MethodRow]] = defaultdict(list)
    for method in project_methods.values():
        by_class[method.java_class_name].append(method)

    lines = []
    for java_class_name in sorted(by_class):
        lines.append(java_class_name)
        for method in sorted(
            by_class[java_class_name],
            key=lambda item: (item.method_name, item.descriptor),
        ):
            flags = f" [{method.access_flags}]" if method.access_flags else ""
            lines.append(
                f"    └── {method.method_name}{method.descriptor}{flags}"
            )
        lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")


def write_markdown_summary(
    path: Path,
    apk_path: Path,
    output_dir: Path,
    manifest_info: dict[str, Any],
    java_prefix: str,
    project_classes: list[dict[str, Any]],
    project_methods: dict[str, MethodRow],
    calls: list[CallRow],
    ranked_methods: list[MethodRow],
    core_subgraph: nx.MultiDiGraph,
    reachable: set[str],
    coverage_rows: Optional[list[CoverageRow]],
    jacoco_xml: Optional[Path],
) -> None:
    project_to_project_calls = [
        call for call in calls if call.callee_is_project_method
    ]
    external_calls = [
        call for call in calls if not call.callee_is_project_method
    ]

    lines = [
        "# APK 静态分析报告",
        "",
        "## 1. 分析对象",
        "",
        f"- APK 文件：`{apk_path}`",
        f"- 报告目录：`{output_dir}`",
        f"- 分析时间：`{datetime.now().isoformat(timespec='seconds')}`",
        f"- 项目包名前缀：`{java_prefix}`",
        "",
        "## 2. APK 基本信息",
        "",
        f"- 应用包名：`{manifest_info['package_name']}`",
        f"- versionCode：`{manifest_info['version_code']}`",
        f"- versionName：`{manifest_info['version_name']}`",
        f"- minSdkVersion：`{manifest_info['min_sdk']}`",
        f"- targetSdkVersion：`{manifest_info['target_sdk']}`",
        f"- 主 Activity：`{manifest_info['main_activity']}`",
        "",
        "## 3. 静态分析统计",
        "",
        f"- 项目内类数量：`{len(project_classes)}`",
        f"- 项目内方法数量：`{len(project_methods)}`",
        f"- 项目方法之间的调用记录数量：`{len(project_to_project_calls)}`",
        f"- 项目方法调用外部方法的记录数量：`{len(external_calls)}`",
        f"- 从 Manifest 组件入口静态可达的方法数量：`{len(reachable)}`",
        f"- 核心逻辑子图节点数量：`{core_subgraph.number_of_nodes()}`",
        f"- 核心逻辑子图边数量：`{core_subgraph.number_of_edges()}`",
        "",
        "## 4. Manifest 组件入口",
        "",
    ]

    if manifest_info["components"]:
        for item in manifest_info["components"]:
            lines.append(
                f"- `{item['type']}`：`{item['java_class_name']}`"
            )
    else:
        lines.append("- 未读取到 Manifest 组件。")

    lines.extend(
        [
            "",
            "## 5. 核心功能逻辑方法（启发式排序）",
            "",
            "说明：核心分数根据项目内调用入度、出度、外部 API 调用次数、"
            "方法体大小、Manifest 静态可达性以及常见业务方法名综合计算。"
            "它用于快速定位重点逻辑，不等同于人工确认后的业务语义。",
            "",
        ]
    )

    for index, row in enumerate(ranked_methods[:30], start=1):
        lines.append(
            f"{index}. `{row.signature}`  "
            f"core_score=`{row.core_score}`，"
            f"项目内入度=`{row.incoming_project_calls}`，"
            f"项目内出度=`{row.outgoing_project_calls}`，"
            f"外部调用=`{row.outgoing_external_calls}`，"
            f"静态可达=`{row.reachable_from_manifest_entry}`"
        )

    lines.extend(
        [
            "",
            "## 6. 测试覆盖方法",
            "",
        ]
    )

    if coverage_rows is None:
        lines.extend(
            [
                "- 未提供 JaCoCo XML，因此本报告无法判断测试运行时真正覆盖了哪些方法。",
                "- APK 静态分析只能生成调用关系和 Manifest 入口静态可达方法，"
                "不能替代 JaCoCo 等动态覆盖率数据。",
                "- 如需导出真实覆盖方法，请运行脚本时增加："
                "`--jacoco-xml path\\to\\jacocoTestReport.xml`。",
            ]
        )
    else:
        covered_rows = [row for row in coverage_rows if row.covered]
        mapped_rows = [
            row for row in covered_rows if row.exists_in_apk_project_methods
        ]
        lines.extend(
            [
                f"- JaCoCo XML：`{jacoco_xml}`",
                f"- JaCoCo 中的方法总数：`{len(coverage_rows)}`",
                f"- JaCoCo 中至少执行过一次的方法数：`{len(covered_rows)}`",
                f"- 与 APK 项目方法精确匹配的已覆盖方法数：`{len(mapped_rows)}`",
            ]
        )

    lines.extend(
        [
            "",
            "## 7. 输出文件说明",
            "",
            "- `01_apk_info.json`：APK 基本信息和 Manifest 组件。",
            "- `02_project_classes.csv`：项目内类列表及统计。",
            "- `03_project_methods.csv`：项目内方法列表及调用统计。",
            "- `04_method_calls_all.csv`：项目方法发出的全部调用。",
            "- `05_method_calls_project_only.csv`：项目内部方法调用关系。",
            "- `06_static_reachable_methods.csv`：从 Manifest 入口静态可达的方法。",
            "- `07_core_methods.csv`：核心功能逻辑方法启发式排序。",
            "- `08_core_logic_subgraph.gml`：核心逻辑子图，可使用 Gephi 打开。",
            "- `09_core_logic_subgraph.graphml`：核心逻辑子图的 GraphML 文件。",
            "- `10_core_logic_subgraph.mmd`：核心逻辑 Mermaid 子图。",
            "- `11_project_callgraph.gml`：完整项目内调用图。",
            "- `12_project_callgraph.graphml`：完整项目内调用图的 GraphML 文件。",
            "- `13_class_method_tree.txt`：类与方法层级结构。",
            "- `14_test_covered_methods.csv`：JaCoCo 已覆盖方法；仅在提供 JaCoCo XML 时生成。",
            "- `15_test_coverage_all_methods.csv`：JaCoCo 全部方法；仅在提供 JaCoCo XML 时生成。",
            "",
            "## 8. 结论边界",
            "",
            "- `06_static_reachable_methods.csv` 表示静态调用图上的可达方法，"
            "不是测试运行时实际覆盖方法。",
            "- `14_test_covered_methods.csv` 才是基于 JaCoCo XML 的动态测试覆盖结果。",
            "- Kotlin、Compose、Hilt、Room 等框架可能生成额外类和方法。"
            "可通过 `--package-prefix` 缩小分析范围。",
            "",
        ]
    )

    path.write_text("\n".join(lines), encoding="utf-8")


def export_report(
    apk_path: Path,
    output_dir: Path,
    package_prefix: Optional[str],
    jacoco_xml: Optional[Path],
    core_top_n: int,
    core_max_nodes: int,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    print("[1/7] 正在读取 APK 和 DEX，请等待……")
    apk, dex_objects, analysis = AnalyzeAPK(str(apk_path))

    print("[2/7] 正在读取 Manifest……")
    manifest_info = get_manifest_info(apk)
    java_prefix, descriptor_prefix = choose_project_prefix(
        manifest_info, package_prefix
    )

    print(f"      应用包名：{manifest_info['package_name']}")
    print(f"      项目分析前缀：{java_prefix}")

    print("[3/7] 正在提取项目类、方法和方法调用关系……")
    project_methods, calls, full_graph, project_graph = collect_methods_and_calls(
        analysis, descriptor_prefix
    )
    project_classes = collect_project_classes(project_methods)

    print("[4/7] 正在计算 Manifest 入口静态可达方法……")
    reachable = mark_manifest_reachable_methods(
        project_methods, project_graph, manifest_info
    )

    print("[5/7] 正在生成核心功能逻辑子图……")
    ranked_methods = calculate_core_scores(project_methods)
    core_subgraph, core_seeds = build_core_logic_subgraph(
        project_graph,
        ranked_methods,
        top_n=core_top_n,
        max_nodes=core_max_nodes,
    )

    print("[6/7] 正在导出 CSV、JSON 和图文件……")
    write_json(
        output_dir / "01_apk_info.json",
        {
            "apk_path": str(apk_path),
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "package_prefix": java_prefix,
            "descriptor_prefix": descriptor_prefix,
            "dex_count": len(dex_objects),
            **manifest_info,
        },
    )

    write_csv(
        output_dir / "02_project_classes.csv",
        project_classes,
        [
            "class_name",
            "java_class_name",
            "method_count",
            "total_code_size",
            "incoming_project_calls",
            "outgoing_project_calls",
            "outgoing_external_calls",
        ],
    )

    write_csv(
        output_dir / "03_project_methods.csv",
        sorted(project_methods.values(), key=lambda x: x.signature),
        list(MethodRow.__dataclass_fields__.keys()),
    )

    write_csv(
        output_dir / "04_method_calls_all.csv",
        calls,
        list(CallRow.__dataclass_fields__.keys()),
    )

    write_csv(
        output_dir / "05_method_calls_project_only.csv",
        [call for call in calls if call.callee_is_project_method],
        list(CallRow.__dataclass_fields__.keys()),
    )

    write_csv(
        output_dir / "06_static_reachable_methods.csv",
        [
            asdict(project_methods[signature])
            for signature in sorted(reachable)
            if signature in project_methods
        ],
        list(MethodRow.__dataclass_fields__.keys()),
    )

    write_csv(
        output_dir / "07_core_methods.csv",
        [asdict(row) for row in ranked_methods],
        list(MethodRow.__dataclass_fields__.keys()),
    )

    clean_core_graph = stringify_graph_attributes(core_subgraph)
    clean_project_graph = stringify_graph_attributes(project_graph)

    nx.write_gml(clean_core_graph, output_dir / "08_core_logic_subgraph.gml")
    nx.write_graphml(
        clean_core_graph, output_dir / "09_core_logic_subgraph.graphml"
    )
    write_mermaid_subgraph(
        output_dir / "10_core_logic_subgraph.mmd", clean_core_graph
    )

    nx.write_gml(clean_project_graph, output_dir / "11_project_callgraph.gml")
    nx.write_graphml(
        clean_project_graph, output_dir / "12_project_callgraph.graphml"
    )

    write_class_method_tree(
        output_dir / "13_class_method_tree.txt", project_methods
    )

    coverage_rows: Optional[list[CoverageRow]] = None
    if jacoco_xml is not None:
        print("      正在解析 JaCoCo XML……")
        coverage_rows = parse_jacoco_xml(
            jacoco_xml, set(project_methods.keys())
        )
        covered_rows = [row for row in coverage_rows if row.covered]

        write_csv(
            output_dir / "14_test_covered_methods.csv",
            covered_rows,
            list(CoverageRow.__dataclass_fields__.keys()),
        )
        write_csv(
            output_dir / "15_test_coverage_all_methods.csv",
            coverage_rows,
            list(CoverageRow.__dataclass_fields__.keys()),
        )
    else:
        (output_dir / "14_test_coverage_notice.txt").write_text(
            "未提供 JaCoCo XML。\n"
            "APK 静态分析无法判断哪些方法在测试运行时真正被执行。\n"
            "如需导出测试覆盖方法，请重新运行脚本并增加：\n"
            "--jacoco-xml path\\to\\jacocoTestReport.xml\n",
            encoding="utf-8",
        )

    write_json(
        output_dir / "16_core_logic_metadata.json",
        {
            "core_seed_methods": core_seeds,
            "core_subgraph_nodes": core_subgraph.number_of_nodes(),
            "core_subgraph_edges": core_subgraph.number_of_edges(),
            "project_graph_nodes": project_graph.number_of_nodes(),
            "project_graph_edges": project_graph.number_of_edges(),
            "full_graph_nodes": full_graph.number_of_nodes(),
            "full_graph_edges": full_graph.number_of_edges(),
        },
    )

    write_markdown_summary(
        output_dir / "00_summary.md",
        apk_path=apk_path,
        output_dir=output_dir,
        manifest_info=manifest_info,
        java_prefix=java_prefix,
        project_classes=project_classes,
        project_methods=project_methods,
        calls=calls,
        ranked_methods=ranked_methods,
        core_subgraph=core_subgraph,
        reachable=reachable,
        coverage_rows=coverage_rows,
        jacoco_xml=jacoco_xml,
    )

    print("[7/7] 完成。")
    print()
    print("========== APK 静态分析完成 ==========")
    print(f"报告目录：{output_dir}")
    print(f"项目类数量：{len(project_classes)}")
    print(f"项目方法数量：{len(project_methods)}")
    print(
        "项目内部调用数量："
        f"{sum(1 for call in calls if call.callee_is_project_method)}"
    )
    print(f"静态可达方法数量：{len(reachable)}")
    print(f"核心子图节点数量：{core_subgraph.number_of_nodes()}")
    print(f"核心子图边数量：{core_subgraph.number_of_edges()}")
    if coverage_rows is None:
        print("测试覆盖方法：未导出（未提供 JaCoCo XML）")
    else:
        print(
            "测试覆盖方法数量："
            f"{sum(1 for row in coverage_rows if row.covered)}"
        )
    print("====================================")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "使用 Androguard 从 APK 提取类、方法、调用关系、"
            "核心逻辑子图，并可选合并 JaCoCo 测试覆盖方法。"
        )
    )
    parser.add_argument(
        "--apk",
        required=True,
        help="待分析 APK 的完整路径。",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="报告输出目录。",
    )
    parser.add_argument(
        "--package-prefix",
        default=None,
        help=(
            "只分析该 Java 包名前缀下的项目类。"
            "默认使用 APK applicationId。"
            "例如：com.example.android.architecture.blueprints"
        ),
    )
    parser.add_argument(
        "--jacoco-xml",
        default=None,
        help="可选：JaCoCo XML 报告路径，用于导出测试实际覆盖的方法。",
    )
    parser.add_argument(
        "--core-top-n",
        type=int,
        default=20,
        help="核心逻辑子图的高分种子方法数量，默认 20。",
    )
    parser.add_argument(
        "--core-max-nodes",
        type=int,
        default=180,
        help="核心逻辑子图最大节点数，默认 180。",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    apk_path = Path(args.apk).expanduser().resolve()
    output_dir = Path(args.output).expanduser().resolve()
    jacoco_xml = (
        Path(args.jacoco_xml).expanduser().resolve()
        if args.jacoco_xml
        else None
    )

    if not apk_path.is_file():
        print(f"[失败] APK 文件不存在：{apk_path}", file=sys.stderr)
        return 1

    if apk_path.suffix.lower() != ".apk":
        print(
            f"[失败] 输入文件不是 .apk：{apk_path}",
            file=sys.stderr,
        )
        return 1

    if jacoco_xml is not None and not jacoco_xml.is_file():
        print(
            f"[失败] JaCoCo XML 文件不存在：{jacoco_xml}",
            file=sys.stderr,
        )
        return 1

    try:
        export_report(
            apk_path=apk_path,
            output_dir=output_dir,
            package_prefix=args.package_prefix,
            jacoco_xml=jacoco_xml,
            core_top_n=max(1, args.core_top_n),
            core_max_nodes=max(10, args.core_max_nodes),
        )
        return 0
    except Exception as exc:
        print(f"[失败] 分析过程中发生异常：{exc}", file=sys.stderr)
        print(
            "可尝试先执行：python -m pip install --upgrade androguard networkx",
            file=sys.stderr,
        )
        raise


if __name__ == "__main__":
    raise SystemExit(main())
