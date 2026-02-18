import re
from collections import defaultdict
from pathlib import Path

BASE_DIR = Path(
    r"c:\Users\rsram\Downloads\agentic_trader_platform_1734_20260109_210621"
)


def read_file_safe(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return ""


def extract_phases_detailed(content):
    phases = {}

    phase_pattern = r"##\s*(?:Phase|PHASE|Fase|FASE)\s*(\d+)[:\s]*([^\n]+)(.*?)(?=##\s*(?:Phase|PHASE|Fase|FASE)\s*\d+|\Z)"
    matches = re.finditer(phase_pattern, content, re.DOTALL | re.IGNORECASE)

    for match in matches:
        phase_num = match.group(1)
        phase_title = match.group(2).strip()
        phase_content = match.group(3)

        tasks = re.findall(
            r"###\s*(?:Task|TASK)\s*([\d\.]+)[:\s]*([^\n]+)",
            phase_content,
            re.IGNORECASE,
        )
        microtasks = re.findall(
            r"####\s*(?:Microtask|MICROTASK)\s*([\d\.]+)[:\s]*([^\n]+)",
            phase_content,
            re.IGNORECASE,
        )

        dependencies = re.findall(
            r"(?:depends on|requires|after|blocked by)[:\s]*([^\n]+)",
            phase_content,
            re.IGNORECASE,
        )

        effort = re.search(
            r"(?:effort|estimate|time)[:\s]*(\d+)\s*(?:hours|days|weeks)",
            phase_content,
            re.IGNORECASE,
        )

        phases[f"Phase {phase_num}"] = {
            "title": phase_title,
            "tasks": [(t[0], t[1]) for t in tasks],
            "microtasks": [(m[0], m[1]) for m in microtasks],
            "microtask_count": len(microtasks),
            "dependencies": dependencies,
            "effort": effort.group(0) if effort else "Unknown",
        }

    return phases


def analyze_api_detailed():
    api_dir = BASE_DIR / "backend" / "api"
    api_analysis = {}

    key_files = [
        "websocket_endpoints.py",
        "trading_api.py",
        "dashboard.py",
        "main.py",
        "gateway.py",
    ]

    for filename in key_files:
        filepath = api_dir / filename
        if not filepath.exists():
            continue

        content = read_file_safe(filepath)

        routes = re.findall(
            r'@(?:router|app)\.(get|post|put|delete|websocket|patch)\(["\']([^"\']+)["\']',
            content,
            re.IGNORECASE,
        )

        response_models = re.findall(r"response_model\s*=\s*(\w+)", content)

        ws_features = []
        if "websocket" in content.lower():
            ws_features.append("WebSocket support")
        if "sse" in content.lower() or "server-sent" in content.lower():
            ws_features.append("SSE support")
        if "stream" in content.lower():
            ws_features.append("Streaming support")

        data_fields = re.findall(r"class\s+(\w+)\(BaseModel\):", content)

        api_analysis[filename] = {
            "routes": routes,
            "response_models": response_models,
            "realtime_features": ws_features,
            "data_models": data_fields,
        }

    return api_analysis


def analyze_navagraha_integration():
    navagraha_files = []
    backend_dir = BASE_DIR / "backend"

    for py_file in backend_dir.rglob("*.py"):
        content = read_file_safe(py_file)
        if any(
            keyword in content.lower()
            for keyword in [
                "navagraha",
                "ephemeris",
                "kerykeion",
                "pyswisseph",
                "rahu",
                "kala",
            ]
        ):
            navagraha_files.append(
                {
                    "file": str(py_file.relative_to(BASE_DIR)),
                    "has_cache": "cache" in content.lower(),
                    "has_websocket": "websocket" in content.lower(),
                    "classes": re.findall(r"class\s+(\w+)", content)[:3],
                }
            )

    return navagraha_files


def main():
    print("=" * 100)
    print("DEEP DOCUMENTATION & CODEBASE ANALYSIS")
    print("=" * 100)

    handover = BASE_DIR / "HANDOVER_CONTEXT.md"
    master_kanban = BASE_DIR / "docs" / "kanban" / "SAMKHYA_MASTER_KANBAN_TDD.md"
    fase_01 = (
        BASE_DIR / "docs" / "kanban" / "FASE_01_CONSCIOUSNESS_OODA_NAVAGRAHA_BRIDGE.md"
    )
    epic_01 = BASE_DIR / "docs" / "reports" / "EPIC_01_CODE_REVIEW.md"

    print("\n[1] MASTER KANBAN PHASE EXTRACTION")
    print("-" * 100)
    if master_kanban.exists():
        content = read_file_safe(master_kanban)
        phases = extract_phases_detailed(content)

        print(f"Total Phases Found: {len(phases)}\n")
        for phase_id, data in phases.items():
            print(f"{phase_id}: {data['title']}")
            print(
                f"  Tasks: {len(data['tasks'])}, Microtasks: {data['microtask_count']}, Effort: {data['effort']}"
            )
            if data["dependencies"]:
                print(f"  Dependencies: {data['dependencies'][:2]}")
    else:
        print("⚠ Master Kanban not found")

    print("\n[2] FASE 01 DETAILED MICROTASK ANALYSIS")
    print("-" * 100)
    if fase_01.exists():
        content = read_file_safe(fase_01)
        phases = extract_phases_detailed(content)

        all_microtasks = []
        for phase_id, data in phases.items():
            all_microtasks.extend(data["microtasks"])

        print(f"Total Microtasks in FASE 01: {len(all_microtasks)}")

        if all_microtasks:
            print("\nFirst 5 microtasks:")
            for mt_id, mt_title in all_microtasks[:5]:
                print(f"  {mt_id}: {mt_title[:70]}")

            print("\nLast 5 microtasks:")
            for mt_id, mt_title in all_microtasks[-5:]:
                print(f"  {mt_id}: {mt_title[:70]}")

            task_groups = defaultdict(int)
            for mt_id, _ in all_microtasks:
                task_base = ".".join(mt_id.split(".")[:2])
                task_groups[task_base] += 1

            print("\nMicrotasks by Task Group:")
            for task_id, count in sorted(task_groups.items()):
                print(f"  Task {task_id}: {count} microtasks")
    else:
        print("⚠ FASE 01 not found")

    print("\n[3] API ENDPOINTS DETAILED ANALYSIS")
    print("-" * 100)
    api_data = analyze_api_detailed()

    for filename, data in api_data.items():
        print(f"\n{filename}:")
        print(f"  Routes: {len(data['routes'])} endpoints")
        if data["routes"]:
            for method, path in data["routes"][:3]:
                print(f"    {method.upper():10s} {path}")

        if data["realtime_features"]:
            print(f"  Real-time: {', '.join(data['realtime_features'])}")

        if data["data_models"]:
            print(f"  Data Models: {', '.join(data['data_models'][:3])}")

    print("\n[4] NAVAGRAHA INTEGRATION POINTS")
    print("-" * 100)
    navagraha_files = analyze_navagraha_integration()

    print(f"Files with Navagraha/Ephemeris logic: {len(navagraha_files)}\n")
    for item in navagraha_files[:10]:
        print(f"{item['file']}:")
        print(
            f"  Cache: {'Yes' if item['has_cache'] else 'No'}, WebSocket: {'Yes' if item['has_websocket'] else 'No'}"
        )
        if item["classes"]:
            print(f"  Classes: {', '.join(item['classes'])}")

    print("\n[5] HANDOVER CONTEXT KEY SECTIONS")
    print("-" * 100)
    if handover.exists():
        content = read_file_safe(handover)

        sections = re.findall(r"^##\s+([^\n]+)", content, re.MULTILINE)
        print(f"Major sections: {len(sections)}")
        for section in sections[:15]:
            print(f"  • {section}")

        architecture_patterns = re.findall(
            r"(?:OODA|Navagraha|Guna|Tattva|Element|Agent)", content, re.IGNORECASE
        )
        print(
            f"\nArchitecture Keywords: {len(set(architecture_patterns))} unique mentions"
        )

        apis_mentioned = re.findall(r"(?:API|endpoint|route|/\w+)", content)
        print(f"API References: {len(apis_mentioned)} mentions")
    else:
        print("⚠ Handover Context not found")

    print("\n[6] EPIC 01 CODE REVIEW FINDINGS")
    print("-" * 100)
    if epic_01.exists():
        content = read_file_safe(epic_01)

        findings = re.findall(
            r"(?:TODO|FIXME|WARNING|ERROR|BUG|ISSUE)[:\s]*([^\n]+)",
            content,
            re.IGNORECASE,
        )
        print(f"Code Review Items: {len(findings)}")
        for finding in findings[:5]:
            print(f"  • {finding[:80]}")

        recommendations = re.findall(
            r"(?:recommend|suggest|should|must)[:\s]*([^\n]+)", content, re.IGNORECASE
        )
        print(f"\nRecommendations: {len(recommendations)}")
        for rec in recommendations[:5]:
            print(f"  • {rec[:80]}")
    else:
        print("⚠ EPIC 01 Code Review not found")

    print("\n" + "=" * 100)
    print("DEEP ANALYSIS COMPLETE")
    print("=" * 100)


if __name__ == "__main__":
    main()
