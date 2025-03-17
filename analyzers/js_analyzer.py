"""
JavaScript code analyzer module.
Provides functions to analyze JavaScript files for common issues.
"""

import os
import re
import subprocess
from typing import List, Dict, Any

def analyze_js_file(file_path: str) -> Dict[str, Any]:
    """
    Analyze a JavaScript file for potential issues.
    
    Args:
        file_path: Path to the JavaScript file
        
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
            lines = content.split('\n')
    except Exception as e:
        return {
            "file": file_path,
            "issues": [{"type": "error", "message": f"Failed to read file: {str(e)}"}]
        }
    
    # Check for console.log usage
    for i, line in enumerate(lines):
        if "console.log" in line and not line.strip().startswith('//'):
            issues.append({
                "type": "warning",
                "line": i + 1,
                "message": "console.log statements should be removed in production code"
            })
    
    # Check for eval usage
    eval_regex = re.compile(r'\beval\s*\(')
    for i, line in enumerate(lines):
        if eval_regex.search(line) and not line.strip().startswith('//'):
            issues.append({
                "type": "security",
                "line": i + 1,
                "message": "Usage of eval is discouraged due to security risks"
            })
    
    # Check for hard-coded credentials
    password_regex = re.compile(r'[pP]assword\s*[:=]\s*[\'"][^\'"]+[\'"]')
    api_key_regex = re.compile(r'[aA]pi[kK]ey\s*[:=]\s*[\'"][^\'"]+[\'"]')
    
    for i, line in enumerate(lines):
        if password_regex.search(line):
            issues.append({
                "type": "security",
                "line": i + 1,
                "message": "Hard-coded password found"
            })
        
        if api_key_regex.search(line):
            issues.append({
                "type": "security",
                "line": i + 1,
                "message": "Hard-coded API key found"
            })
    
    # Check for potential XSS vulnerabilities
    innerHTML_regex = re.compile(r'\.innerHTML\s*=')
    document_write_regex = re.compile(r'document\.write\s*\(')
    
    for i, line in enumerate(lines):
        if innerHTML_regex.search(line):
            issues.append({
                "type": "security",
                "line": i + 1,
                "message": "Using .innerHTML can lead to XSS vulnerabilities"
            })
        
        if document_write_regex.search(line):
            issues.append({
                "type": "security",
                "line": i + 1,
                "message": "document.write() can lead to XSS vulnerabilities"
            })
    
    # Run ESLint if available
    try:
        result = subprocess.run(
            ["eslint", "--format=json", file_path],
            capture_output=True,
            text=True,
            check=False
        )
        if result.stdout:
            # Process ESLint output if available
            try:
                import json
                eslint_results = json.loads(result.stdout)
                for file_result in eslint_results:
                    if file_result.get("filePath") == file_path:
                        for message in file_result.get("messages", []):
                            issues.append({
                                "type": "lint",
                                "line": message.get("line", 0),
                                "message": message.get("message", "Unknown ESLint issue")
                            })
            except Exception:
                pass
    except FileNotFoundError:
        # ESLint not available, skip this check
        pass
    
    return {
        "file": file_path,
        "issues": issues
    }

def analyze_js_directory(directory: str) -> List[Dict[str, Any]]:
    """
    Analyze all JavaScript files in a directory.
    
    Args:
        directory: Directory path to analyze
        
    Returns:
        List of dictionaries containing analysis results
    """
    results = []
    
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(('.js', '.jsx', '.ts', '.tsx')):
                file_path = os.path.join(root, file)
                results.append(analyze_js_file(file_path))
                
    return results
