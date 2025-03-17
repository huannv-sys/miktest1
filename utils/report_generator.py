"""
Report generator utility module.
Provides functions for generating repository analysis reports.
"""

import os
from datetime import datetime
from typing import Dict, Any, List

from utils.git_operations import get_git_info
from utils.file_operations import find_todo_comments

def generate_report(
    repo_url: str,
    repo_dir: str,
    languages: Dict[str, int],
    file_stats: Dict[str, Any],
    analysis_results: Dict[str, Any],
    timestamp: str
) -> Dict[str, Any]:
    """
    Generate a comprehensive report of the repository analysis.
    
    Args:
        repo_url: URL of the repository
        repo_dir: Path to the repository directory
        languages: Dictionary of detected languages and their line counts
        file_stats: Statistics about files in the repository
        analysis_results: Results of the code analysis
        timestamp: Timestamp of when the analysis was performed
        
    Returns:
        Dictionary containing the complete analysis report
    """
    # Get Git repository information
    git_info = get_git_info(repo_dir)
    
    # Find TODO comments
    todo_comments = find_todo_comments(repo_dir)
    
    # Count issues by severity
    issue_counts = {
        "error": 0,
        "warning": 0,
        "security": 0,
        "info": 0,
        "lint": 0
    }
    
    # Count general issues
    for issue in analysis_results.get("general_issues", []):
        issue_type = issue.get("type", "info")
        if issue_type in issue_counts:
            issue_counts[issue_type] += 1
    
    # Count security issues
    for issue in analysis_results.get("security_issues", []):
        issue_type = issue.get("type", "security")
        if issue_type in issue_counts:
            issue_counts[issue_type] += 1
    
    # Count best practices issues
    for issue in analysis_results.get("best_practices", []):
        issue_type = issue.get("type", "info")
        if issue_type in issue_counts:
            issue_counts[issue_type] += 1
    
    # Count language-specific issues
    for language, issues in analysis_results.get("language_specific_issues", {}).items():
        for file_issues in issues:
            for issue in file_issues.get("issues", []):
                issue_type = issue.get("type", "info")
                if issue_type in issue_counts:
                    issue_counts[issue_type] += 1
    
    # Compile the full report
    report = {
        "repository": {
            "url": repo_url,
            "git_info": git_info
        },
        "summary": {
            "analysis_timestamp": timestamp,
            "languages": languages,
            "file_stats": file_stats,
            "issue_counts": issue_counts,
            "total_issues": sum(issue_counts.values())
        },
        "todo_comments": todo_comments,
        "issues": analysis_results
    }
    
    return report
