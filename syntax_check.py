#!/usr/bin/env python3
"""
Syntax check script for all Python files.
"""

import ast
import os

def check_syntax(filename):
    """Check syntax of a Python file."""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            source = f.read()
        
        # Parse the source code
        ast.parse(source)
        print(f"✅ {filename}: Syntax OK")
        return True
    except SyntaxError as e:
        print(f"❌ {filename}: Syntax Error")
        print(f"   Line {e.lineno}: {e.text}")
        print(f"   Error: {e.msg}")
        return False
    except Exception as e:
        print(f"⚠️ {filename}: Error reading file - {e}")
        return False

def main():
    """Check syntax of all Python files."""
    print("🔍 Checking syntax of all Python files...")
    print("=" * 50)
    
    python_files = [
        'main.py',
        'config.py',
        'telegram_bot.py',
        'trading_engine.py',
        'api_client.py',
        'trade_logger.py',
        'websocket_handler.py',
        'utils.py'
    ]
    
    all_good = True
    
    for filename in python_files:
        if os.path.exists(filename):
            if not check_syntax(filename):
                all_good = False
        else:
            print(f"⚠️ {filename}: File not found")
    
    print("=" * 50)
    if all_good:
        print("🎉 All files have correct syntax!")
    else:
        print("❌ Some files have syntax errors!")

if __name__ == "__main__":
    main()
