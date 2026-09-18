import os
import json
import datetime

def load_project_status(project_id: str, logs_dir: str = "logs") -> dict:
    """Loads or initializes the project status.json."""
    status_path = os.path.join(logs_dir, project_id, "status.json")
    if os.path.exists(status_path):
        with open(status_path, "r", encoding="utf-8") as f:
            return json.load(f)
            
    now_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return {
        "project_id": project_id,
        "created_at": now_str,
        "last_updated": now_str,
        "stages": {}
    }

def update_stage_status(project_id: str, stage_key: str, status: str, logs_dir: str = "logs"):
    """Updates a specific stage status ('in_progress', 'completed', 'failed')."""
    data = load_project_status(project_id, logs_dir)
    now_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    stage = data["stages"].get(stage_key, {})
    stage["status"] = status
    stage["updated_at"] = now_str
    
    if status == "in_progress" and "started_at" not in stage:
        stage["started_at"] = now_str
    elif status == "completed":
        stage["completed_at"] = now_str
        
    data["stages"][stage_key] = stage
    
    status_path = os.path.join(logs_dir, project_id, "status.json")
    os.makedirs(os.path.dirname(status_path), exist_ok=True)
    with open(status_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
