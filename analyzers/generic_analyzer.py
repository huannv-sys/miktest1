"""
Generic code analyzer module.
Provides functions to analyze repositories regardless of language.
"""

import os
from typing import List, Dict, Any

from analyzers.python_analyzer import analyze_python_directory
from analyzers.java_analyzer import analyze_java_directory
from analyzers.js_analyzer import analyze_js_directory

def analyze_repository(repo_dir: str, languages: Dict[str, int]) -> Dict[str, Any]:
    """
    Analyze a repository for potential issues.
    
    Args:
        repo_dir: Path to the repository directory
        languages: Dictionary of detected languages and their line counts
        
    Returns:
        Dictionary containing analysis results
    """
    results = {
        "general_issues": check_general_issues(repo_dir),
        "language_specific_issues": {},
        "security_issues": check_security_issues(repo_dir),
        "best_practices": check_best_practices(repo_dir),
    }
    
    # Analyze based on detected languages
    if "Python" in languages:
        results["language_specific_issues"]["Python"] = analyze_python_directory(repo_dir)
    
    if "Java" in languages:
        results["language_specific_issues"]["Java"] = analyze_java_directory(repo_dir)
    
    if "JavaScript" in languages or "TypeScript" in languages:
        results["language_specific_issues"]["JavaScript/TypeScript"] = analyze_js_directory(repo_dir)
    
    return results

def check_general_issues(repo_dir: str) -> List[Dict[str, Any]]:
    """
    Check for general repository issues.
    
    Args:
        repo_dir: Path to the repository directory
        
    Returns:
        List of issues found
    """
    issues = []
    
    # Check for .gitignore
    if not os.path.isfile(os.path.join(repo_dir, '.gitignore')):
        issues.append({
            "type": "warning",
            "message": "Repository is missing a .gitignore file"
        })
    
    # Check for README
    readme_exists = any(
        os.path.isfile(os.path.join(repo_dir, readme_name))
        for readme_name in ['README.md', 'README.txt', 'README']
    )
    if not readme_exists:
        issues.append({
            "type": "warning",
            "message": "Repository is missing a README file"
        })
    
    # Check for LICENSE
    license_exists = any(
        os.path.isfile(os.path.join(repo_dir, license_name))
        for license_name in ['LICENSE', 'LICENSE.txt', 'LICENSE.md']
    )
    if not license_exists:
        issues.append({
            "type": "info",
            "message": "Repository is missing a LICENSE file"
        })
    
    # Check for large files
    large_files = []
    for root, _, files in os.walk(repo_dir):
        for file in files:
            file_path = os.path.join(root, file)
            try:
                if os.path.getsize(file_path) > 10 * 1024 * 1024:  # 10 MB
                    rel_path = os.path.relpath(file_path, repo_dir)
                    large_files.append(rel_path)
            except OSError:
                pass
    
    if large_files:
        issues.append({
            "type": "warning",
            "message": f"Repository contains large files that should not be in Git: {', '.join(large_files)}"
        })
    
    return issues

def check_security_issues(repo_dir: str) -> List[Dict[str, Any]]:
    """
    Check for security issues in the repository.
    
    Args:
        repo_dir: Path to the repository directory
        
    Returns:
        List of security issues found
    """
    issues = []
    
    # Check for sensitive files
    sensitive_patterns = [
        '.env', 'id_rsa', '.pem', '.key', 'credentials.json', 
        'secrets.yml', 'secrets.yaml', 'secrets.json'
    ]
    
    for root, _, files in os.walk(repo_dir):
        for file in files:
            if any(pattern in file.lower() for pattern in sensitive_patterns):
                rel_path = os.path.relpath(os.path.join(root, file), repo_dir)
                issues.append({
                    "type": "security",
                    "message": f"Potentially sensitive file found: {rel_path}"
                })
    
    return issues

def check_best_practices(repo_dir: str) -> List[Dict[str, Any]]:
    """
    Check for adherence to best practices.
    
    Args:
        repo_dir: Path to the repository directory
        
    Returns:
        List of best practice issues found
    """
    issues = []
    
    # Check for CI/CD configuration
    ci_configs = [
        '.github/workflows', '.travis.yml', '.gitlab-ci.yml', 
        'Jenkinsfile', '.circleci'
    ]
    
    has_ci = False
    for config in ci_configs:
        if os.path.exists(os.path.join(repo_dir, config)):
            has_ci = True
            break
    
    if not has_ci:
        issues.append({
            "type": "info",
            "message": "Repository does not appear to have CI/CD configuration"
        })
    
    # Check for project structure
    has_tests = False
    for root, dirs, _ in os.walk(repo_dir):
        if 'tests' in dirs or 'test' in dirs:
            has_tests = True
            break
    
    if not has_tests:
        issues.append({
            "type": "warning",
            "message": "Repository may not have a tests directory"
        })
    
    return issues
