"""
APJ Swarm Validation Execution Script
Run the complete test harness validation
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import after path fix
try:
    from tests.integration.test_validation_harness import TestHarness
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're running from the project root directory")
    sys.exit(1)


async def run_quick_test():
    """Run a quick 10-task test"""
    print("🔍 Quick Test: 10 tasks only")
    
    try:
        harness = TestHarness()
        result = await harness.run_test_suite(10)
        print(f"Result: {result.status}")
        print(f"Tasks: {result.task_count}")
        print(f"Time: {result.execution_time:.1f}s")
        print(f"Specialist routing: {result.routing_metrics['overall_specialist_rate']:.1%}")
        return result.status == "PASSED"
    except Exception as e:
        print(f"Error: {e}")
        return False


async def main():
    """Main execution function"""
    
    print("🚀 APJ Swarm Routing Validation System")
    print("=" * 60)
    print("This validation system tests the complete APJ routing")
    print("system with 10, 50, and 100 task scenarios.")
    print("=" * 60)
    
    # Phase 1: Small Validation (10 tasks)
    print("\n🔍 Phase 1: Small Validation (10 tasks)")
    print("Testing basic routing functionality...")
    
    try:
        harness = TestHarness()
        result_10 = await harness.run_test_suite(10)
        print(f"✅ Phase 1: {result_10.status}")
        print(f"   Tasks: {result_10.task_count}")
        print(f"   Time: {result_10.execution_time:.1f}s")
        print(f"   Specialist routing: {result_10.routing_metrics['overall_specialist_rate']:.1%}")
        
        if result_10.status != "PASSED":
            print("❌ Phase 1 failed - stopping execution")
            return False
            
    except Exception as e:
        print(f"❌ Phase 1 error: {e}")
        return False
    
    # Phase 2: Medium Validation (50 tasks)
    print("\n🔍 Phase 2: Medium Validation (50 tasks)")
    print("Testing routing with larger task set...")
    
    try:
        result_50 = await harness.run_test_suite(50)
        print(f"✅ Phase 2: {result_50.status}")
        print(f"   Tasks: {result_50.task_count}")
        print(f"   Time: {result_50.execution_time:.1f}s")
        print(f"   Specialist routing: {result_50.routing_metrics['overall_specialist_rate']:.1%}")
        
        if result_50.status != "PASSED":
            print("❌ Phase 2 failed - stopping execution")
            return False
            
    except Exception as e:
        print(f"❌ Phase 2 error: {e}")
        return False
    
    # Phase 3: Full Validation (100 tasks)
    print("\n🔍 Phase 3: Full Validation (100 tasks)")
    print("Testing complete routing system...")
    
    try:
        result_100 = await harness.run_test_suite(100)
        print(f"✅ Phase 3: {result_100.status}")
        print(f"   Tasks: {result_100.task_count}")
        print(f"   Time: {result_100.execution_time:.1f}s")
        print(f"   Specialist routing: {result_100.routing_metrics['overall_specialist_rate']:.1%}")
        
        if result_100.status != "PASSED":
            print("❌ Phase 3 failed")
            return False
            
    except Exception as e:
        print(f"❌ Phase 3 error: {e}")
        return False
    
    # Summary
    print("\n🎉 ALL VALIDATION PHASES COMPLETE")
    print("=" * 60)
    print("Summary:")
    print(f"  Phase 1: {result_10.status} ({result_10.task_count} tasks, {result_10.execution_time:.1f}s)")
    print(f"  Phase 2: {result_50.status} ({result_50.task_count} tasks, {result_50.execution_time:.1f}s)")
    print(f"  Phase 3: {result_100.status} ({result_100.task_count} tasks, {result_100.execution_time:.1f}s)")
    
    # Final validation
    overall_success = all([
        result_10.status == "PASSED",
        result_50.status == "PASSED",
        result_100.status == "PASSED"
    ])
    
    if overall_success:
        print("\n✅ VALIDATION SUCCESSFUL")
        print("The APJ routing system is ready for production!")
        print("Proceed to 473-task scale with confidence.")
    else:
        print("\n❌ VALIDATION FAILED")
        print("Review failures and fix issues before scaling.")
    
    return overall_success


def run_quick_test():
    """Run a quick 10-task test"""
    print("🔍 Quick Test: 10 tasks only")
    
    async def quick_test():
        try:
            result = await run_small_validation()
            print(f"Result: {result.status}")
            print(f"Tasks: {result.task_count}")
            print(f"Time: {result.execution_time:.1f}s")
            print(f"Specialist routing: {result.routing_metrics['overall_specialist_rate']:.1%}")
            return result.status == "PASSED"
        except Exception as e:
            print(f"Error: {e}")
            return False
    
    return asyncio.run(quick_test())


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        # Quick test mode
        success = run_quick_test()
        sys.exit(0 if success else 1)
    else:
        # Full validation
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
