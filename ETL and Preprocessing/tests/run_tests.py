#!/usr/bin/env python
import pytest
import sys
import os
import time
import json
import multiprocessing
from datetime import datetime
from typing import Dict, Any

def get_optimal_workers() -> int:
    """Calculate optimal number of worker processes"""
    cpu_count = multiprocessing.cpu_count()
    # Use 75% of available CPUs to avoid overloading
    return max(int(cpu_count * 0.75), 1)

def run_tests() -> Dict[str, Any]:
    """Run the test suite with optimized parallel execution and profiling."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Calculate optimal workers
    n_workers = get_optimal_workers()
    
    # Configure pytest arguments with optimizations
    pytest_args = [
        "-v",
        "--tb=short",
        f"-n {n_workers}",  # Parallel execution with optimal workers
        "--dist=loadscope",  # Distribute tests by scope
        "--asyncio-mode=auto",
        f"--html=reports/report_{timestamp}.html",
        "--cov=Datapipeline",
        "--cov-report=term-missing:skip-covered",
        "--setup-show",  # Show fixture setup times
        "--durations=10",  # Show 10 slowest tests
        "--profile",  # Enable profiling
        "--profile-svg",  # Generate SVG profile visualization
        "-W", "ignore::DeprecationWarning"
    ]
    
    # Run integration tests separately
    integration_args = pytest_args + [
        "tests/integration",  # Integration test directory
        "--integration-cover",  # Special coverage for integration tests
    ]
    
    # Create reports directory
    os.makedirs("reports", exist_ok=True)
    os.makedirs("reports/profile", exist_ok=True)
    
    # Start timing
    start_time = time.time()
    
    # Run unit tests first
    print("Running unit tests...")
    unit_result = pytest.main(pytest_args + ["tests"])
    
    # Run integration tests
    print("\nRunning integration tests...")
    integration_result = pytest.main(integration_args)
    
    # Calculate execution time
    execution_time = time.time() - start_time
    
    # Prepare test results
    test_results = {
        "timestamp": timestamp,
        "execution_time": execution_time,
        "unit_tests_exit_code": unit_result,
        "integration_tests_exit_code": integration_result,
        "status": "Success" if unit_result == 0 and integration_result == 0 else "Failure",
        "workers_used": n_workers,
        "report_files": {
            "html": f"reports/report_{timestamp}.html",
            "coverage": "reports/coverage/index.html",
            "profile": f"reports/profile/prof_{timestamp}.svg"
        }
    }
    
    return test_results

if __name__ == "__main__":
    results = run_tests()
    
    # Print minimal summary
    print(f"\nStatus: {results['status']}")
    print(f"Time: {results['execution_time']:.2f}s")
    print(f"Workers Used: {results['workers_used']}")
    
    sys.exit(results["unit_tests_exit_code"] if results["status"] == "Failure" else 0)