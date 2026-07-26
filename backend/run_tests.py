import unittest
import sys

if __name__ == "__main__":
    print("Launching AegisOne Advanced Detection Engine Test Suite...")
    suite = unittest.defaultTestLoader.discover("app/tests", pattern="test_*.py")
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    if not result.wasSuccessful():
        print("Tests FAILED!")
        sys.exit(1)
    
    print("All tests completed successfully!")
    sys.exit(0)
