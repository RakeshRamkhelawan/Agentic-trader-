import pytest
import sys
import os
import time

def main():
    """
    Run the full OODA Platform Verification Suite.
    """
    print("="*80)
    print("OODA Platform Verification Scheme")
    print("="*80)
    
    # Define test groups
    test_groups = {
        "Foundational Types": [
            "backend/tests/test_ooda_types.py"
        ],
        "Designated Agents": [
            "backend/tests/test_agents_specialized.py"
        ],
        "Execution Layer (Hot Path)": [
            "backend/tests/test_fast_config.py",
            "backend/tests/test_hot_path_engine.py",
            "backend/tests/test_order_executor.py"
        ],
        "OODA Coordination & E2E": [
            "backend/tests/test_ooda_coordinator.py",
            "backend/tests/test_end_to_end_flow.py"
        ],
        "Governance & Safety": [
            "backend/tests/test_circuit_breaker.py",
            "backend/tests/test_ooda_coordinator_rbac.py", 
            "backend/tests/test_decision_audit.py"
        ],
        "RAG & Memory": [
            "backend/tests/test_rag_vector_memory.py"
        ]
    }
    
    # Collect all files
    all_tests = []
    for group, tests in test_groups.items():
        all_tests.extend(tests)
        
    start_time = time.time()
    
    # Run pytest
    # -v: verbose
    # -x: stop on first failure (optional, maybe better to run all)
    args = ["-v"] + all_tests
    
    print(f"Running {len(all_tests)} test suites across {len(test_groups)} groups...")
    
    ret_code = pytest.main(args)
    
    duration = time.time() - start_time
    
    print("\n" + "="*80)
    if ret_code == 0:
        print(f"VERIFICATION SUCCESSFUL ({duration:.2f}s)")
        print("All systems operational. Ready for deployment/handover.")
        sys.exit(0)
    else:
        print(f"VERIFICATION FAILED ({duration:.2f}s)")
        print("Please review the errors above.")
        sys.exit(ret_code)

if __name__ == "__main__":
    # Ensure we are in the root directory
    if not os.path.exists("backend"):
        print("Error: Please run this script from the project root directory.")
        sys.exit(1)
        
    main()
