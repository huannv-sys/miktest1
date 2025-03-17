"""
Java code analyzer module.
Provides functions to analyze Java files for common issues.
"""

import os
import re
import subprocess
from typing import List, Dict, Any

def analyze_java_file(file_path: str) -> Dict[str, Any]:
    """
    Analyze a Java file for potential issues.
    
    Args:
        file_path: Path to the Java file
        
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
    
    # Check for unused imports
    import_pattern = re.compile(r'import\s+([^;]+);')
    imports = [match.group(1) for match in import_pattern.finditer(content)]
    
    for imp in imports:
        # Extract the class name from the import
        class_name = imp.split('.')[-1]
        if class_name != '*' and class_name not in content[content.find(';', content.find(imp)) + 1:]:
            # Find the line number of this import
            for i, line in enumerate(lines):
                if f"import {imp};" in line:
                    issues.append({
                        "type": "warning",
                        "line": i + 1,
                        "message": f"Unused import: {imp}"
                    })
                    break
    
    # Check for hard-coded credentials
    password_regex = re.compile(r'[pP]assword\s*=\s*[\'"][^\'"]+[\'"]')
    api_key_regex = re.compile(r'[aA]pi[kK]ey\s*=\s*[\'"][^\'"]+[\'"]')
    
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
    
    # Check for empty catch blocks
    catch_block_pattern = re.compile(r'catch\s*\([^)]+\)\s*\{[^}]*\}')
    for match in catch_block_pattern.finditer(content):
        catch_block = match.group(0)
        # Check if the catch block is empty or just has comments
        block_content = catch_block[catch_block.find('{') + 1:catch_block.rfind('}')].strip()
        if not block_content or all(line.strip().startswith('//') for line in block_content.split('\n') if line.strip()):
            line_number = content[:match.start()].count('\n') + 1
            issues.append({
                "type": "warning",
                "line": line_number,
                "message": "Empty catch block"
            })
    
    # Check for System.out.println usage in production code
    for i, line in enumerate(lines):
        if "System.out.println" in line and not line.strip().startswith('//'):
            issues.append({
                "type": "warning",
                "line": i + 1,
                "message": "System.out.println should be avoided in production code, use logging instead"
            })
    
    return {
        "file": file_path,
        "issues": issues
    }

def analyze_java_directory(directory: str) -> List[Dict[str, Any]]:
    """
    Analyze all Java files in a directory.
    
    Args:
        directory: Directory path to analyze
        
    Returns:
        List of dictionaries containing analysis results
    """
    results = []
    
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.java'):
                file_path = os.path.join(root, file)
                results.append(analyze_java_file(file_path))
                
    return results
