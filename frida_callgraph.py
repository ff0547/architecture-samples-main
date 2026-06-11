from __future__ import annotations

import argparse
import csv
import html
import json
import subprocess
import threading
import time
import traceback
import webbrowser
from collections import Counter
from pathlib import Path
from typing import Any

import frida
from pyvis.network import Network


PACKAGE_NAME = "com.example.android.architecture.blueprints.main"
AGENT_FILE = Path("trace_java_calls.ts")
OUTPUT_DIR = Path("frida_callgraph_output")


class CallGraphRecorder:
    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.node_counts: Counter[str] = Counter()
        self.edge_counts: Counter[tuple[str, str]] = Counter()
        self.node_metadata: dict[str, dict[str, Any]] = {}

    def on_message(
            self,
            message: dict[str, Any],
            data: bytes | None,
    ) -> None:
        message_type = message.get("type")

        if message_type == "error":
            print()
            print("========== Agent JavaScript Error ==========")
            print(message.get("stack", message))
            print()
            return

        if message_type != "send":
            print("[message]", message)
            return

        payload = message.get("payload", {})
        payload_type = payload.get("type")

        if payload_type == "call":
            self._record_call(payload)
            return

        if payload_type == "scan":
            print(
                "[scan]"
                f" round={payload.get('scanRound', 0)}"
                f" loaded_classes={payload.get('loadedClassCount', 0)}"
                f" hooked_classes={payload.get('hookedClassCount', 0)}"
                f" hooked_methods={payload.get('hookedMethodCount', 0)}"
                f" newly_hooked={payload.get('newlyHookedMethodCount', 0)}"
            )
            return

        if payload_type == "ready":
            print("[ready]", payload.get("message", ""))
            return

        if payload_type == "agent_error":
            print("[agent warning]", payload.get("message", ""))
            return

        print("[send]", payload)

    def _record_call(
            self,
            payload: dict[str, Any],
    ) -> None:
        caller = payload.get("caller")
        callee = payload.get("callee")

        if not isinstance(callee, str) or not callee:
            return

        with self.lock:
            self.node_counts[callee] += 1

            self.node_metadata.setdefault(
                callee,
                {
                    "class_name": payload.get("className", ""),
                    "method_name": payload.get("methodName", ""),
                },
            )

            if isinstance(caller, str) and caller:
                self.node_counts[caller] += 0
                self.edge_counts[(caller, callee)] += 1

    def snapshot(
            self,
    ) -> tuple[
        dict[str, int],
        dict[tuple[str, str], int],
        dict[str, dict[str, Any]],
    ]:
        with self.lock:
            return (
                dict(self.node_counts),
                dict(self.edge_counts),
                dict(self.node_metadata),
            )


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Trace Android Java/Kotlin method calls with Frida "
            "and generate a browser-readable HTML call graph."
        )
    )

    parser.add_argument(
        "--duration",
        type=int,
        default=180,
        help="Capture duration in seconds. Default: 180",
    )

    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Do not automatically open callgraph.html.",
    )

    return parser.parse_args()


def compile_agent() -> str:
    if not AGENT_FILE.exists():
        raise FileNotFoundError(
            f"Missing agent file: {AGENT_FILE.resolve()}"
        )

    print(f"Compiling TypeScript agent: {AGENT_FILE}")

    compiler = frida.Compiler()

    compiler.on(
        "diagnostics",
        lambda diagnostics: print("[compiler]", diagnostics),
    )

    bundle = compiler.build(
        str(AGENT_FILE),
        project_root=str(Path.cwd()),
        bundle_format="iife",
        type_check="none",
        source_maps="omitted",
        compression="none",
        platform="gum",
    )

    print("Agent compilation completed.")

    return bundle


def get_running_app_pid() -> int:
    print(f"Finding PID for package: {PACKAGE_NAME}")

    result = subprocess.run(
        [
            "adb",
            "shell",
            "pidof",
            PACKAGE_NAME,
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )

    output = result.stdout.strip()

    if not output:
        raise RuntimeError(
            "Todo App is not running.\n"
            "Run this command first:\n"
            "adb shell monkey "
            f"-p {PACKAGE_NAME} "
            "-c android.intent.category.LAUNCHER 1"
        )

    first_pid = output.split()[0]

    try:
        pid = int(first_pid)
    except ValueError as error:
        raise RuntimeError(
            f"Invalid PID returned by adb: {output}"
        ) from error

    print(f"Target PID: {pid}")

    return pid


def shorten_label(method_id: str) -> str:
    if "->" not in method_id:
        return method_id[-100:]

    class_name, method_part = method_id.split("->", 1)
    simple_class_name = class_name.rsplit(".", 1)[-1]
    method_name = method_part.split("(", 1)[0]

    return f"{simple_class_name}.{method_name}"


def export_json(
        output_path: Path,
        nodes: dict[str, int],
        edges: dict[tuple[str, str], int],
        metadata: dict[str, dict[str, Any]],
) -> None:
    graph_data = {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "package_name": PACKAGE_NAME,
        "node_count": len(nodes),
        "edge_count": len(edges),
        "nodes": [
            {
                "id": method_id,
                "call_count": count,
                **metadata.get(method_id, {}),
            }
            for method_id, count in sorted(
                nodes.items(),
                key=lambda item: (-item[1], item[0]),
            )
        ],
        "edges": [
            {
                "caller": caller,
                "callee": callee,
                "call_count": count,
            }
            for (caller, callee), count in sorted(
                edges.items(),
                key=lambda item: (-item[1], item[0]),
            )
        ],
    }

    output_path.write_text(
        json.dumps(
            graph_data,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def export_nodes_csv(
        output_path: Path,
        nodes: dict[str, int],
        metadata: dict[str, dict[str, Any]],
) -> None:
    with output_path.open(
            "w",
            newline="",
            encoding="utf-8-sig",
    ) as file:
        writer = csv.writer(file)

        writer.writerow(
            [
                "method_id",
                "class_name",
                "method_name",
                "call_count",
            ]
        )

        for method_id, count in sorted(
                nodes.items(),
                key=lambda item: (-item[1], item[0]),
        ):
            info = metadata.get(method_id, {})

            writer.writerow(
                [
                    method_id,
                    info.get("class_name", ""),
                    info.get("method_name", ""),
                    count,
                ]
            )


def export_edges_csv(
        output_path: Path,
        edges: dict[tuple[str, str], int],
) -> None:
    with output_path.open(
            "w",
            newline="",
            encoding="utf-8-sig",
    ) as file:
        writer = csv.writer(file)

        writer.writerow(
            [
                "caller",
                "callee",
                "call_count",
            ]
        )

        for (caller, callee), count in sorted(
                edges.items(),
                key=lambda item: (-item[1], item[0]),
        ):
            writer.writerow(
                [
                    caller,
                    callee,
                    count,
                ]
            )


def export_html(
        output_path: Path,
        nodes: dict[str, int],
        edges: dict[tuple[str, str], int],
        metadata: dict[str, dict[str, Any]],
) -> None:
    network = Network(
        height="900px",
        width="100%",
        directed=True,
        bgcolor="#111827",
        font_color="#f9fafb",
        heading=(
            "Android Dynamic Method Call Graph"
            f" | nodes={len(nodes)}"
            f" | edges={len(edges)}"
        ),
        select_menu=True,
        filter_menu=True,
        cdn_resources="in_line",
    )

    network.barnes_hut(
        gravity=-30000,
        central_gravity=0.15,
        spring_length=220,
        spring_strength=0.03,
        damping=0.09,
    )

    for method_id, count in sorted(
            nodes.items(),
            key=lambda item: (-item[1], item[0]),
    ):
        info = metadata.get(method_id, {})

        class_name = str(
            info.get("class_name", "")
        )

        method_name = str(
            info.get("method_name", "")
        )

        tooltip = (
            f"<b>Full signature</b><br>"
            f"{html.escape(method_id)}"
            f"<br><br>"
            f"<b>Class</b><br>"
            f"{html.escape(class_name)}"
            f"<br><br>"
            f"<b>Method</b><br>"
            f"{html.escape(method_name)}"
            f"<br><br>"
            f"<b>Calls</b>: {count}"
        )

        network.add_node(
            method_id,
            label=shorten_label(method_id),
            title=tooltip,
            value=max(1, count),
            shape="dot",
        )

    for (caller, callee), count in sorted(
            edges.items(),
            key=lambda item: (-item[1], item[0]),
    ):
        network.add_edge(
            caller,
            callee,
            title=f"Calls: {count}",
            value=max(1, count),
            arrows="to",
        )

    html_content = network.generate_html(
        notebook=False
    )

    output_path.write_text(
        html_content,
        encoding="utf-8",
    )


def export_results(
        recorder: CallGraphRecorder,
) -> Path:
    nodes, edges, metadata = recorder.snapshot()

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    html_path = OUTPUT_DIR / "callgraph.html"
    json_path = OUTPUT_DIR / "callgraph.json"
    nodes_csv_path = OUTPUT_DIR / "nodes.csv"
    edges_csv_path = OUTPUT_DIR / "edges.csv"

    export_json(
        json_path,
        nodes,
        edges,
        metadata,
    )

    export_nodes_csv(
        nodes_csv_path,
        nodes,
        metadata,
    )

    export_edges_csv(
        edges_csv_path,
        edges,
    )

    export_html(
        html_path,
        nodes,
        edges,
        metadata,
    )

    print()
    print("========== Export complete ==========")

    print(f"Nodes : {len(nodes)}")
    print(f"Edges : {len(edges)}")
    print(f"HTML  : {html_path.resolve()}")
    print(f"JSON  : {json_path.resolve()}")
    print(f"CSV   : {nodes_csv_path.resolve()}")
    print(f"CSV   : {edges_csv_path.resolve()}")

    if not nodes:
        print()
        print(
            "[Warning] No project methods were captured. "
            "Operate the app during the capture window."
        )

    return html_path.resolve()


def main() -> int:
    args = parse_arguments()

    session: frida.core.Session | None = None
    script: frida.core.Script | None = None

    try:
        bundle = compile_agent()

        print("Connecting to Android device...")

        device = frida.get_usb_device(
            timeout=10
        )

        print(f"Connected device: {device.name}")

        pid = get_running_app_pid()

        print(f"Attaching to PID: {pid}")

        session = device.attach(
            pid
        )

        recorder = CallGraphRecorder()

        script = session.create_script(
            bundle
        )

        script.on(
            "message",
            recorder.on_message,
        )

        script.load()

        print()
        print("========== Tracing started ==========")
        print(f"Duration : {args.duration} seconds")
        print("Operate the Android app now.")
        print(
            "Press Ctrl+C to stop early "
            "and export results."
        )
        print()

        try:
            time.sleep(
                args.duration
            )

        except KeyboardInterrupt:
            print()
            print("Capture interrupted by user.")

        html_path = export_results(
            recorder
        )

        if not args.no_browser:
            webbrowser.open(
                html_path.as_uri()
            )

        return 0

    except Exception as error:
        print()
        print("========== Error ==========")
        print(error)
        print()

        traceback.print_exc()

        return 1

    finally:
        if script is not None:
            try:
                script.unload()
            except Exception:
                pass

        if session is not None:
            try:
                session.detach()
            except Exception:
                pass


if __name__ == "__main__":
    raise SystemExit(
        main()
    )