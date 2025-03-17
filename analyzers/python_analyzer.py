"""
Python code analyzer module.
Provides functions to analyze Python files for common issues.
"""

import os
import re
import ast
import subprocess
from typing import List, Dict, Any

def analyze_python_file(file_path: str) -> Dict[str, Any]:
    """
    Analyze a Python file for potential issues.
    
    Args:
        file_path: Path to the Python file
        
    Returns:
        Dictionary containing analysis results
    """
    issues = []
    
    # Check if file exists
    if not os.path.isfile(file_path):
        return {
            "file": file_path,
            "issues": [{"type": "error", "message": "File does not exist"}]
        }
    
    # Read file content
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
    except Exception as e:
        return {
            "file": file_path,
            "issues": [{"type": "error", "message": f"Failed to read file: {str(e)}"}]
        }
    
    # Check syntax errors
    try:
        ast.parse(content)
    except SyntaxError as e:
        issues.append({
            "type": "error",
            "line": e.lineno,
            "message": f"Syntax error: {str(e)}"
        })
        
    # Check for common anti-patterns
    if "except:" in content:
        line_number = content.split('\n').index("except:") + 1
        issues.append({
            "type": "warning",
            "line": line_number,
            "message": "Bare 'except' clause should be avoided"
        })
    
    # Check for hard-coded credentials
    password_regex = re.compile(r'password\s*=\s*[\'"][^\'"]+[\'"]', re.IGNORECASE)
    api_key_regex = re.compile(r'api[\-_]?key\s*=\s*[\'"][^\'"]+[\'"]', re.IGNORECASE)
    
    for match in password_regex.finditer(content):
        line_number = content[:match.start()].count('\n') + 1
        issues.append({
            "type": "security",
            "line": line_number,
            "message": "Hard-coded password found"
        })
        
    for match in api_key_regex.finditer(content):
        line_number = content[:match.start()].count('\n') + 1
        issues.append({
            "type": "security",
            "line": line_number,
            "message": "Hard-coded API key found"
        })
    
    # Run pylint if available
    try:
        result = subprocess.run(
            ["pylint", "--output-format=json", file_path],
            capture_output=True,
            text=True,
            check=False
        )
        if result.stdout:
            # Process pylint output if available
            try:
                import json
                pylint_issues = json.loads(result.stdout)
                for issue in pylint_issues:
                    issues.append({
                        "type": "lint",
                        "line": issue.get("line", 0),
                        "message": issue.get("message", "Unknown pylint issue")
                    })
            except Exception:
                pass
    except FileNotFoundError:
        # pylint not available, skip this check
        pass
    
    return {
        "file": file_path,
        "issues": issues
    }

def analyze_python_directory(directory: str) -> List[Dict[str, Any]]:
    """
    Analyze all Python files in a directory.
    
    Args:
        directory: Directory path to analyze
        
    Returns:
        List of dictionaries containing analysis results
    """
    results = []
    
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                results.append(analyze_python_file(file_path))
                
    return results
