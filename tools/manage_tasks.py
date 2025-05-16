#!/usr/bin/env python
"""
Task Management Script for MaiVid Studio

This script helps manage tasks between TASK.md and COMPLETED.md.
It moves recently completed tasks from TASK.md to the appropriate section in COMPLETED.md.
"""

import re
import os
from datetime import datetime

TASK_FILE = "K:\\MaiVid_Studio\\TASK.md"
COMPLETED_FILE = "K:\\MaiVid_Studio\\COMPLETED.md"

def get_recently_completed_tasks():
    """Extract recently completed tasks from TASK.md"""
    with open(TASK_FILE, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Find the Recently Completed section
    recently_completed_pattern = r"## Recently Completed\s+((?:- \[x\].*?\n)+)"
    match = re.search(recently_completed_pattern, content)
    
    if not match:
        print("No recently completed tasks found.")
        return []
    
    # Extract task lines
    tasks_text = match.group(1)
    tasks = [line.strip() for line in tasks_text.split('\n') if line.strip()]
    
    return tasks

def categorize_task(task):
    """Determine which section in COMPLETED.md the task belongs to"""
    task_lower = task.lower()
    
    if any(keyword in task_lower for keyword in ['fix', 'fixed', 'issue', 'error', 'bug']):
        return "## Discovered and Fixed Issues"
    elif any(keyword in task_lower for keyword in ['ui', 'interface', 'design', 'style', 'css', 'visual']):
        return "## Completed Feature Enhancements"
    elif any(keyword in task_lower for keyword in ['test', 'verify', 'validate']):
        return "## Completed Feature Enhancements"
    else:
        return "## Completed Priority Tasks"

def update_completed_file(tasks):
    """Add tasks to the appropriate sections in COMPLETED.md"""
    if not tasks:
        return
    
    with open(COMPLETED_FILE, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Group tasks by category
    categorized_tasks = {}
    for task in tasks:
        category = categorize_task(task)
        if category not in categorized_tasks:
            categorized_tasks[category] = []
        categorized_tasks[category].append(task)
    
    # Update each category in the content
    new_content = content
    for category, category_tasks in categorized_tasks.items():
        # Find the category section
        section_pattern = f"{re.escape(category)}(.*?)(?:^##|$)"
        section_match = re.search(section_pattern, content, re.DOTALL | re.MULTILINE)
        
        if section_match:
            # Add tasks to the beginning of the section
            section_content = section_match.group(1)
            updated_section = f"{category}\n" + "\n".join(category_tasks) + "\n" + section_content.lstrip()
            new_content = new_content.replace(f"{category}{section_content}", updated_section)
    
    # Write the updated content back to the file
    with open(COMPLETED_FILE, 'w', encoding='utf-8') as file:
        file.write(new_content)
    
    print(f"Added {len(tasks)} tasks to COMPLETED.md")

def clear_recently_completed():
    """Clear the recently completed section in TASK.md"""
    with open(TASK_FILE, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Replace the recently completed section with just the header
    updated_content = re.sub(
        r"## Recently Completed\s+((?:- \[x\].*?\n)+)",
        "## Recently Completed\n\n",
        content
    )
    
    with open(TASK_FILE, 'w', encoding='utf-8') as file:
        file.write(updated_content)
    
    print("Cleared recently completed tasks from TASK.md")

def main():
    print("MaiVid Studio Task Manager")
    print("=========================")
    
    tasks = get_recently_completed_tasks()
    
    if tasks:
        print(f"Found {len(tasks)} recently completed tasks:")
        for task in tasks:
            print(f"  {task}")
        
        # Add tasks to COMPLETED.md
        update_completed_file(tasks)
        
        # Clear recently completed section in TASK.md
        clear_recently_completed()
        
        print("\nTask management complete!")
    else:
        print("No tasks to process.")

if __name__ == "__main__":
    main()
