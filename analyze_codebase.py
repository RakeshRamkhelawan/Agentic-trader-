import re
from pathlib import Path

BASE_DIR = Path(
    r"c:\Users\rsram\Downloads\agentic_trader_platform_1734_20260109_210621"
)


def read_file_safe(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except (IOError, UnicodeDecodeError):
        return ""


def analyze_api_endpoints(api_dir):
    endpoints = {}
    api_files = list(api_dir.glob("*.py"))

    for file in api_files:
        content = read_file_safe(file)
        if not content:
            continue

        routes = re.findall(
            r'@router\.(get|post|put|delete|patch|websocket)\(["\']([^"\']+)',
            content,
            re.IGNORECASE,
        )
        if routes:
            endpoints[file.name] = routes

        ws_patterns = re.findall(
            r"websocket|SSE|EventSource|async def.*stream", content, re.IGNORECASE
        )
        if ws_patterns:
            if file.name not in endpoints:
                endpoints[file.name] = []
            endpoints[file.name].append(("websocket", "real-time support detected"))

    return endpoints


def analyze_backend_schemas(core_dir):
    schemas = {}
    schema_dir = core_dir / "schemas"
    if schema_dir.exists():
        for file in schema_dir.glob("*.py"):
            content = read_file_safe(file)
            classes = re.findall(r"class\s+(\w+)\(.*BaseModel.*\):", content)
            if classes:
                schemas[file.name] = classes
    return schemas


def parse_phase_document(doc_path):
    content = read_file_safe(doc_path)
    phases = {}

    phase_sections = re.findall(
        r"##\s+(Phase\s+\d+[:\s]+[^\n]+)(.*?)(?=##\s+Phase|\Z)", content, re.DOTALL
    )

    for phase_header, phase_content in phase_sections:
        phase_num = re.search(r"Phase\s+(\d+)", phase_header)
        if phase_num:
            phase_id = f"Phase {phase_num.group(1)}"

            tasks = re.findall(r"###\s+(Task\s+[\d\.]+[:\s]+[^\n]+)", phase_content)
            microtasks = re.findall(r"####\s+(Microtask\s+[\d\.]+)", phase_content)

            phases[phase_id] = {
                "header": phase_header.strip(),
                "tasks": [t.strip() for t in tasks],
                "microtask_count": len(microtasks),
            }

    return phases


def analyze_agent_files(agents_dir):
    agents = {}
    for file in agents_dir.glob("*.py"):
        if file.name.startswith("__"):
            continue
        content = read_file_safe(file)

        classes = re.findall(r"class\s+(\w+Agent)\(.*\):", content)
        elements = re.findall(r'element\s*[=:]\s*["\'](\w+)', content, re.IGNORECASE)
        gunas = re.findall(r"guna|sattva|rajas|tamas", content, re.IGNORECASE)

        agents[file.name] = {
            "classes": classes,
            "elements": list(set(elements)),
            "has_guna_logic": len(gunas) > 0,
        }

    return agents


def main():
    print("=" * 80)
    print("SAMKHYA YOGA AGENTIC TRADER - CODEBASE ANALYSIS")
    print("=" * 80)

    backend_dir = BASE_DIR / "backend"
    api_dir = backend_dir / "api"
    core_dir = backend_dir / "core"
    agents_dir = backend_dir / "agents"
    docs_dir = BASE_DIR / "docs"

    print("\n[1] BACKEND API ENDPOINTS ANALYSIS")
    print("-" * 80)
    endpoints = analyze_api_endpoints(api_dir)
    for filename, routes in endpoints.items():
        print(f"\n{filename}:")
        for method, path in routes[:5]:
            print(f"  {method.upper():10s} {path}")

    print("\n[2] BACKEND SCHEMAS (Data Models)")
    print("-" * 80)
    schemas = analyze_backend_schemas(core_dir)
    for filename, classes in schemas.items():
        print(f"\n{filename}: {', '.join(classes[:5])}")

    print("\n[3] AGENT FILES ANALYSIS")
    print("-" * 80)
    agents = analyze_agent_files(agents_dir)
    for filename, info in list(agents.items())[:10]:
        print(f"\n{filename}:")
        print(f"  Classes: {', '.join(info['classes'])}")
        print(f"  Elements: {', '.join(info['elements']) or 'None'}")
        print(f"  Guna Logic: {'Yes' if info['has_guna_logic'] else 'No'}")

    print("\n[4] PHASE DOCUMENTS PARSING")
    print("-" * 80)

    master_kanban = docs_dir / "kanban" / "SAMKHYA_MASTER_KANBAN_TDD.md"
    fase_01 = docs_dir / "kanban" / "FASE_01_CONSCIOUSNESS_OODA_NAVAGRAHA_BRIDGE.md"

    if master_kanban.exists():
        phases = parse_phase_document(master_kanban)
        print(f"\nMaster Kanban: {len(phases)} phases found")
        for phase_id, data in list(phases.items())[:3]:
            print(f"\n{phase_id}: {data['header']}")
            print(
                f"  Tasks: {len(data['tasks'])}, Microtasks: {data['microtask_count']}"
            )

    if fase_01.exists():
        content = read_file_safe(fase_01)
        microtasks = re.findall(r"####\s+Microtask\s+([\d\.]+)", content)
        print(f"\n\nFASE_01: {len(microtasks)} microtasks detected")
        print(
            f"  Range: {microtasks[0] if microtasks else 'N/A'} to {microtasks[-1] if microtasks else 'N/A'}"
        )

    print("\n[5] EXISTING INFRASTRUCTURE")
    print("-" * 80)

    docker_compose = BASE_DIR / "docker-compose.yml"
    if docker_compose.exists():
        content = read_file_safe(docker_compose)
        services = re.findall(r"^\s{2}(\w+):", content, re.MULTILINE)
        print(f"Docker services: {', '.join(services[:10])}")

    k8s_dir = BASE_DIR / "infrastructure" / "k8s"
    if k8s_dir.exists():
        helm_files = list(k8s_dir.rglob("*.yaml"))
        print(f"Kubernetes manifests: {len(helm_files)} files")

    print("\n[6] WEBSOCKET/REAL-TIME ENDPOINTS")
    print("-" * 80)
    ws_file = api_dir / "websocket_endpoints.py"
    if ws_file.exists():
        content = read_file_safe(ws_file)
        ws_routes = re.findall(r'@router\.websocket\(["\']([^"\']+)', content)
        print(f"WebSocket routes found: {len(ws_routes)}")
        for route in ws_routes[:5]:
            print(f"  {route}")

    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
