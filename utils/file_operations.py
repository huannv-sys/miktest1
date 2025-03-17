"""
File operations utility module.
Provides functions for working with files in a repository.
"""

import os
from typing import Dict, List, Any
import re

def detect_languages(repo_dir: str) -> Dict[str, int]:
    """
    Detect programming languages used in a repository.
    
    Args:
        repo_dir: Path to the repository directory
        
    Returns:
        Dictionary mapping language names to line counts
    """
    extensions_to_languages = {
        '.py': 'Python',
        '.java': 'Java',
        '.js': 'JavaScript',
        '.jsx': 'JavaScript',
        '.ts': 'TypeScript',
        '.tsx': 'TypeScript',
        '.html': 'HTML',
        '.css': 'CSS',
        '.scss': 'SCSS',
        '.go': 'Go',
        '.rb': 'Ruby',
        '.php': 'PHP',
        '.c': 'C',
        '.cpp': 'C++',
        '.h': 'C/C++ Header',
        '.cs': 'C#',
        '.swift': 'Swift',
        '.kt': 'Kotlin',
        '.rs': 'Rust',
        '.md': 'Markdown',
        '.json': 'JSON',
        '.xml': 'XML',
        '.yml': 'YAML',
        '.yaml': 'YAML',
        '.sql': 'SQL',
        '.sh': 'Shell'
    }
    
    language_counts = {}
    
    for root, _, files in os.walk(repo_dir):
        # Skip .git directory
        if '.git' in root.split(os.sep):
            continue
        
        for file in files:
            _, ext = os.path.splitext(file)
            if ext in extensions_to_languages:
                language = extensions_to_languages[ext]
                file_path = os.path.join(root, file)
                
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        line_count = sum(1 for _ in f)
                    
                    if language in language_counts:
                        language_counts[language] += line_count
                    else:
                        language_counts[language] = line_count
                except Exception:
                    # If we can't read the file, just skip it
                    pass
    
    return language_counts

def get_file_statistics(repo_dir: str) -> Dict[str, Any]:
    """
    Get statistics about files in a repository.
    
    Args:
        repo_dir: Path to the repository directory
        
    Returns:
        Dictionary containing file statistics
    """
    stats = {
        "total_files": 0,
        "total_dirs": 0,
        "file_types": {},
        "largest_files": [],
        "newest_files": [],
        "file_count_by_dir": {}
    }
    
    for root, dirs, files in os.walk(repo_dir):
        # Skip .git directory
        if '.git' in root.split(os.sep):
            continue
        
        stats["total_dirs"] += len(dirs)
        stats["total_files"] += len(files)
        
        # Track file count by directory
        rel_path = os.path.relpath(root, repo_dir)
        if rel_path == '.':
            rel_path = 'root'
        stats["file_count_by_dir"][rel_path] = len(files)
        
        for file in files:
            _, ext = os.path.splitext(file)
            
            if ext in stats["file_types"]:
                stats["file_types"][ext] += 1
            else:
                stats["file_types"][ext] = 1
            
            file_path = os.path.join(root, file)
            rel_file_path = os.path.relpath(file_path, repo_dir)
            
            try:
                file_size = os.path.getsize(file_path)
                file_mtime = os.path.getmtime(file_path)
                
                # Track large files
                stats["largest_files"].append({
                    "path": rel_file_path,
                    "size": file_size
                })
                
                # Track newest files
                stats["newest_files"].append({
                    "path": rel_file_path,
                    "mtime": file_mtime
                })
            except OSError:
                # Skip files that we can't access
                pass
    
    # Sort and limit the lists
    stats["largest_files"] = sorted(
        stats["largest_files"], 
        key=lambda x: x["size"], 
        reverse=True
    )[:10]
    
    stats["newest_files"] = sorted(
        stats["newest_files"], 
        key=lambda x: x["mtime"], 
        reverse=True
    )[:10]
    
    return stats

def find_todo_comments(repo_dir: str) -> List[Dict[str, Any]]:
    """
    Find TODO comments in the repository.
    
    Args:
        repo_dir: Path to the repository directory
        
    Returns:
        List of dictionaries containing TODO comment information
    """
    todo_regex = re.compile(r'(TODO|FIXME|HACK|XXX):?\s*(.*)', re.IGNORECASE)
    todos = []
    
    for root, _, files in os.walk(repo_dir):
        # Skip .git directory
        if '.git' in root.split(os.sep):
            continue
        
        for file in files:
            _, ext = os.path.splitext(file)
            if ext in ['.py', '.java', '.js', '.jsx', '.ts', '.tsx', '.c', '.cpp', '.h', '.cs', '.go', '.rb', '.php']:
                file_path = os.path.join(root, file)
                rel_file_path = os.path.relpath(file_path, repo_dir)
                
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        for i, line in enumerate(f):
                            match = todo_regex.search(line)
                            if match:
                                todos.append({
                                    "file": rel_file_path,
                                    "line": i + 1,
                                    "type": match.group(1),
                                    "text": match.group(2).strip()
                                })
                except Exception:
                    # If we can't read the file, just skip it
                    pass
    
    return todos
