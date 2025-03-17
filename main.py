#!/usr/bin/env python3
"""
Main application for cloning and analyzing GitHub repositories.
This script specifically targets https://github.com/huannv-sys/mik.git
"""

import os
import sys
import shutil
import tempfile
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash

from utils.git_operations import clone_repository
from utils.file_operations import detect_languages, get_file_statistics
from utils.report_generator import generate_report
from analyzers.generic_analyzer import analyze_repository

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['REPO_DIR'] = os.path.join(tempfile.gettempdir(), 'repo_analysis')

@app.route('/')
def index():
    """Render the main page"""
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    """Handle repository analysis request"""
    repo_url = request.form.get('repo_url', 'https://github.com/huannv-sys/mik.git')
    
    try:
        # Create a temporary directory for the repository
        if os.path.exists(app.config['REPO_DIR']):
            shutil.rmtree(app.config['REPO_DIR'])
        os.makedirs(app.config['REPO_DIR'])
        
        # Clone the repository
        print(f"Cloning repository: {repo_url}")
        clone_dir = clone_repository(repo_url, app.config['REPO_DIR'])
        
        if not clone_dir:
            flash("Failed to clone repository. Please check the URL and try again.", "error")
            return redirect(url_for('index'))
        
        # Detect languages in the repository
        print("Detecting programming languages...")
        languages = detect_languages(clone_dir)
        
        # Get file statistics
        print("Gathering file statistics...")
        file_stats = get_file_statistics(clone_dir)
        
        # Analyze the repository
        print("Analyzing repository for issues...")
        analysis_results = analyze_repository(clone_dir, languages)
        
        # Generate the report
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        report = generate_report(repo_url, clone_dir, languages, file_stats, analysis_results, timestamp)
        
        # Clean up cloned repository
        shutil.rmtree(clone_dir)
        
        return render_template('report.html', report=report)
    
    except Exception as e:
        flash(f"An error occurred: {str(e)}", "error")
        return redirect(url_for('index'))

@app.route('/analyze_hardcoded', methods=['GET'])
def analyze_hardcoded():
    """Analyze the hardcoded repository URL"""
    # Hardcoded to analyze https://github.com/huannv-sys/mik.git
    repo_url = "https://github.com/huannv-sys/mik.git"
    
    try:
        # Create a temporary directory for the repository
        if os.path.exists(app.config['REPO_DIR']):
            shutil.rmtree(app.config['REPO_DIR'])
        os.makedirs(app.config['REPO_DIR'])
        
        # Clone the repository
        print(f"Cloning repository: {repo_url}")
        clone_dir = clone_repository(repo_url, app.config['REPO_DIR'])
        
        if not clone_dir:
            flash("Failed to clone repository. Please check the URL and try again.", "error")
            return redirect(url_for('index'))
        
        # Detect languages in the repository
        print("Detecting programming languages...")
        languages = detect_languages(clone_dir)
        
        # Get file statistics
        print("Gathering file statistics...")
        file_stats = get_file_statistics(clone_dir)
        
        # Analyze the repository
        print("Analyzing repository for issues...")
        analysis_results = analyze_repository(clone_dir, languages)
        
        # Generate the report
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        report = generate_report(repo_url, clone_dir, languages, file_stats, analysis_results, timestamp)
        
        # Clean up cloned repository
        shutil.rmtree(clone_dir)
        
        return render_template('report.html', report=report)
    
    except Exception as e:
        flash(f"An error occurred: {str(e)}", "error")
        return redirect(url_for('index'))

if __name__ == '__main__':
    # Ensure the temporary directory exists
    if not os.path.exists(app.config['REPO_DIR']):
        os.makedirs(app.config['REPO_DIR'])
    
    print("Starting repository analysis server...")
    print("Open http://localhost:5000 in your browser")
    
    # Default analyze the hardcoded repository on startup
    app.run(host='0.0.0.0', port=5000, debug=True)
