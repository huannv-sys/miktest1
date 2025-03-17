"""
Git operations utility module.
Provides functions for interacting with Git repositories.
"""

import os
import subprocess
from typing import Optional

def clone_repository(repo_url: str, target_dir: str) -> Optional[str]:
    """
    Clone a Git repository to a local directory.
    
    Args:
        repo_url: URL of the Git repository
        target_dir: Directory to clone the repository into
        
    Returns:
        Path to the cloned repository directory or None if failed
    """
    try:
        # Create the target directory if it doesn't exist
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)
        
        # Clone the repository
        result = subprocess.run(
            ["git", "clone", repo_url, target_dir],
            capture_output=True,
            text=True,
            check=True
        )
        
        print(f"Git clone output: {result.stdout}")
        
        if os.path.exists(target_dir) and os.path.isdir(target_dir):
            return target_dir
        return None
    except subprocess.CalledProcessError as e:
        print(f"Git clone error: {e.stderr}")
        return None
    except Exception as e:
        print(f"Error cloning repository: {str(e)}")
        return None

def get_git_info(repo_dir: str) -> dict:
    """
    Get information about a Git repository.
    
    Args:
        repo_dir: Path to the Git repository
        
    Returns:
        Dictionary containing repository information
    """
    info = {}
    
    try:
        # Get the current branch
        result = subprocess.run(
            ["git", "-C", repo_dir, "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            check=True
        )
        info["branch"] = result.stdout.strip()
        
        # Get the latest commit hash
        result = subprocess.run(
            ["git", "-C", repo_dir, "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True
        )
        info["commit"] = result.stdout.strip()
        
        # Get the remote URL
        result = subprocess.run(
            ["git", "-C", repo_dir, "config", "--get", "remote.origin.url"],
            capture_output=True,
            text=True,
            check=True
        )
        info["remote_url"] = result.stdout.strip()
        
        # Get the last commit date
        result = subprocess.run(
            ["git", "-C", repo_dir, "log", "-1", "--format=%cd"],
            capture_output=True,
            text=True,
            check=True
        )
        info["last_commit_date"] = result.stdout.strip()
        
        # Get commit count
        result = subprocess.run(
            ["git", "-C", repo_dir, "rev-list", "--count", "HEAD"],
            capture_output=True,
            text=True,
            check=True
        )
        info["commit_count"] = result.stdout.strip()
        
    except subprocess.CalledProcessError:
        # If any command fails, just leave that field empty
        pass
    except Exception as e:
        print(f"Error getting Git information: {str(e)}")
    
    return info
