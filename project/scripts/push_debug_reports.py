#!/usr/bin/env python3
"""
Push debug reports to GitHub
"""
import os
import json
import subprocess
import logging
from datetime import datetime

# Configuration
DEBUG_QUEUE_DIR = "/tmp/lxcloud_debug_queue"
REPO_DIR = "/opt/LXCloud"
DEBUG_BRANCH_PREFIX = "debug-reports"
MAX_REPORTS_PER_PUSH = 10


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('/var/log/lxcloud/debug_pusher.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger('debug_pusher')


def run_git_command(cmd, cwd=REPO_DIR):
    """Run git command and return result"""
    try:
        result = subprocess.run(
            cmd, shell=True, cwd=cwd,
            capture_output=True, text=True, check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        raise Exception(f"Git command failed: {cmd}\n{e.stderr}")


def push_debug_reports(logger):
    """Push pending debug reports to GitHub"""
    
    if not os.path.exists(DEBUG_QUEUE_DIR):
        logger.info("No debug queue directory found")
        return
    
    # Find pending reports
    reports = []
    for file in os.listdir(DEBUG_QUEUE_DIR):
        if file.endswith('.json'):
            filepath = os.path.join(DEBUG_QUEUE_DIR, file)
            try:
                with open(filepath, 'r') as f:
                    report = json.load(f)
                    reports.append((file, report, filepath))
            except Exception as e:
                logger.warning(f"Failed to read report {file}: {e}")
    
    if not reports:
        logger.info("No debug reports to push")
        return
    
    # Limit reports per push
    reports = reports[:MAX_REPORTS_PER_PUSH]
    
    # Create debug branch
    date_str = datetime.now().strftime("%Y-%m-%d")
    branch_name = f"{DEBUG_BRANCH_PREFIX}/{date_str}"
    
    try:
        # Ensure we're on main and up to date
        run_git_command("git checkout main")
        run_git_command("git pull origin main")
        
        # Create or switch to debug branch
        try:
            run_git_command(f"git checkout {branch_name}")
        except Exception:
            run_git_command(f"git checkout -b {branch_name}")
        
        # Create debug reports directory
        debug_dir = os.path.join(REPO_DIR, "debug_reports", date_str)
        os.makedirs(debug_dir, exist_ok=True)
        
        # Copy reports and create summary
        summary = {
            "date": date_str,
            "total_reports": len(reports),
            "reports": []
        }
        
        for filename, report, source_path in reports:
            dest_path = os.path.join(debug_dir, filename)
            
            # Copy report
            with open(dest_path, 'w') as f:
                json.dump(report, f, indent=2)
            
            # Add to summary
            summary["reports"].append({
                "filename": filename,
                "error_type": report.get("error_type", "unknown"),
                "timestamp": report.get("timestamp", ""),
                "request_path": report.get("request_info", {}).get("path", "")
            })
            
            # Remove from queue
            os.remove(source_path)
            logger.info(f"Processed report: {filename}")
        
        # Create summary file
        summary_path = os.path.join(debug_dir, "summary.json")
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)
        
        # Git add and commit
        run_git_command(f"git add debug_reports/{date_str}/")
        commit_msg = f"debug: add {len(reports)} error reports for {date_str}"
        run_git_command(f'git commit -m "{commit_msg}"')
        
        # Push to GitHub
        run_git_command(f"git push origin {branch_name}")
        
        msg = f"Successfully pushed {len(reports)} debug reports"
        logger.info(f"{msg} to {branch_name}")
        
        # Switch back to main
        run_git_command("git checkout main")
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to push debug reports: {e}")
        try:
            run_git_command("git checkout main")
        except subprocess.CalledProcessError:
            pass


if __name__ == "__main__":
    main_logger = setup_logging()
    push_debug_reports(main_logger)