#!/usr/bin/env python3
# -*- coding: utf-8 -*- 
import requests
import os
import sys
import json
import datetime
from pathlib import Path

# GitHub API configuration
github_api_url = "https://api.github.com"
github_repository = os.environ.get("GITHUB_REPOSITORY", "")
github_pr_number = os.environ.get("GITHUB_PR_NUMBER", "")
github_token = os.environ.get("GITHUB_TOKEN", "")
github_workflow_id = os.environ.get("GITHUB_WORKFLOW_ID", "")
github_commit_sha = os.environ.get("GITHUB_COMMIT_SHA", "")
review_type = os.environ.get("REVIEW_TYPE", "changes")

# File paths
review_file_path = "amazon_q_review.md"
if github_workflow_id:
    review_file_path = f"amazon_q_review_{github_workflow_id}.md"

# Constants
LARGE_COMMENT_THRESHOLD_KB = 65  # GitHub has a comment size limit of ~65KB

def read_review_content():
    """Read the review content from the file"""
    try:
        with open(review_file_path, "r") as file:
            return file.read()
    except Exception as e:
        print(f"Failed to read review file: {e}")
        sys.exit(1)

def add_pr_comment(content):
    """Add a comment to a pull request"""
    if not all([github_repository, github_pr_number, github_token]):
        print("Missing required environment variables for PR comment")
        sys.exit(1)
        
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json"
    }

    url = f"{github_api_url}/repos/{github_repository}/issues/{github_pr_number}/comments"
    response = requests.post(url, headers=headers, json={"body": content})

    if response.status_code >= 200 and response.status_code < 300:
        print(f"Successfully added comment: {response.status_code}")
        return True
    else:
        print(f"Failed to add comment: {response.status_code}")
        print(response.text)
        return False

def create_gist(title, content):
    """Create a GitHub Gist for large review content"""
    if not github_token:
        print("Missing GitHub token for Gist creation")
        sys.exit(1)
        
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json"
    }

    url = f"{github_api_url}/gists"
    data = {
        "description": f"Amazon Q Code Review: {title}",
        "public": False,
        "files": {
            f"amazon_q_review_{github_workflow_id}.md": {
                "content": content
            }
        }
    }
    
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code == 201:
        gist_data = response.json()
        gist_url = gist_data.get("html_url")
        print(f"Gist created successfully! URL: {gist_url}")
        return gist_url
    else:
        print(f"Failed to create Gist: {response.status_code}")
        print(response.text)
        return None

def generate_report_title():
    """Generate a title for the report based on the context"""
    current_date = datetime.datetime.now().strftime("%Y-%m-%d")
    if review_type == "changes" and github_pr_number:
        return f"{current_date} PR #{github_pr_number} Review"
    else:
        return f"{current_date} Full Repository Review"

def main():
    # Read the review content
    review_content = read_review_content()
    
    # Add metadata to the content
    metadata = f"""
---
Generated: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Workflow ID: {github_workflow_id}
Commit: {github_commit_sha}
Reviewer: Amazon Q Developer
---

"""
    enhanced_content = metadata + review_content
    
    # Check if this is a large comment
    content_size_kb = len(enhanced_content) / 1024
    is_large_comment = content_size_kb > LARGE_COMMENT_THRESHOLD_KB
    
    # For PR reviews, add comment to PR
    if github_pr_number:
        print(f"Adding review to Pull Request #{github_pr_number}")
        
        if is_large_comment:
            print(f"Large review detected ({content_size_kb:.2f}KB), creating Gist")
            report_title = generate_report_title()
            gist_url = create_gist(report_title, enhanced_content)
            
            if gist_url:
                summary_content = f"""# Amazon Q Code Review

This review was too large to post directly as a comment. 
Please view the full review here: [Complete Code Review]({gist_url})

## Summary
{enhanced_content[:1500]}...

[View full review]({gist_url})
"""
                success = add_pr_comment(summary_content)
            else:
                print("Failed to create Gist, attempting to post truncated review")
                truncated_content = enhanced_content[:60000] + "\n\n... [Review truncated due to size limits] ..."
                success = add_pr_comment(truncated_content)
        else:
            # Add comment to PR directly
            success = add_pr_comment(enhanced_content)
        
        if success:
            print(f"Successfully added review comment to PR #{github_pr_number}")
        else:
            sys.exit(1)
    else:
        # For full repository reviews without PR, just save the file
        print("Full repository review completed. Review saved to file.")
        print(f"Review file: {review_file_path}")

if __name__ == "__main__":
    main()
