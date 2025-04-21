"""
Master test script for running all test types:
- Model unit tests
- View/URL tests
- Workflow tests
- UI integration tests
"""
import os
import sys
import django
import unittest
from django.test.runner import DiscoverRunner

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pos_venda.settings')
django.setup()

# Import workflow test
from test_workflows import WorkflowTester

def run_django_tests():
    """Run standard Django tests"""
    print("\n=== Running Django Unit Tests ===\n")
    test_runner = DiscoverRunner(verbosity=1)
    failures = test_runner.run_tests(["clientes", "equipamentos", "assistencia", "stock", "notas"])
    return failures == 0

def run_workflow_tests():
    """Run workflow integration tests"""
    print("\n=== Running Workflow Tests ===\n")
    tester = WorkflowTester()
    return tester.run_all_tests()

def run_all_tests():
    """Run all test suites"""
    django_tests_passed = run_django_tests()
    workflow_tests_passed = run_workflow_tests()

    print("\n=== Final Test Results ===")
    print(f"Django Unit Tests: {'PASSED' if django_tests_passed else 'FAILED'}")
    print(f"Workflow Tests: {'PASSED' if workflow_tests_passed else 'FAILED'}")

    overall_success = django_tests_passed and workflow_tests_passed
    print(f"\nOverall Result: {'PASSED' if overall_success else 'FAILED'}")

    return overall_success

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
