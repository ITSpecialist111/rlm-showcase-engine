import sys
import os

# Add root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rlm_engine import REPLExecutor

def test_repl_basic():
    print("Testing REPL Basic Execution...")
    repl = REPLExecutor({"x": 10})
    
    # Test 1: Simple execution
    code = "print('Hello World')"
    output = repl.execute(code)
    assert "Hello World" in output
    print("PASS: Simple print")

    # Test 2: State persistence
    code_1 = "y = x + 5"
    repl.execute(code_1)
    code_2 = "print(y)"
    output_2 = repl.execute(code_2)
    assert "15" in output_2
    print("PASS: State persistence")

    # Test 3: Error handling
    code_err = "print(undefined_var)"
    output_err = repl.execute(code_err)
    assert "NameError" in output_err
    print("PASS: Error handling")

if __name__ == "__main__":
    test_repl_basic()
