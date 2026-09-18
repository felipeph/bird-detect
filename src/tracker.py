import os
import json
import re
import datetime

def generate_project_id(source_dir: str) -> str:
    """
    Gera um identificador de projeto no formato: <NomeDaPasta>_YYYY-MM-DD_HH-MM-SS
    Higieniza o nome da pasta para ser seguro em sistemas de arquivos.
    """
    abs_dir = os.path.abspath(source_dir)
    folder_name = os.path.basename(abs_dir.rstrip("\\/"))
    if not folder_name:
        folder_name = "Projeto"
    # Substitui caracteres inválidos por underscore
    sanitized = re.sub(r'[^\w\-]', '_', folder_name)
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    return f"{sanitized}_{timestamp}"

def load_project_status(project_id: str, logs_dir: str = "logs") -> dict:
    """Carrega ou inicializa o arquivo status.json do projeto."""
    status_path = os.path.join(logs_dir, project_id, "status.json")
    if os.path.exists(status_path):
        try:
            with open(status_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
            
    now_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return {
        "project_id": project_id,
        "created_at": now_str,
        "last_updated": now_str,
        "stages": {},
        "metrics": {}
    }

def _save_project_status(project_id: str, data: dict, logs_dir: str = "logs"):
    """Salva atomicamente o status.json para evitar corrupção de arquivo."""
    status_dir = os.path.join(logs_dir, project_id)
    os.makedirs(status_dir, exist_ok=True)
    status_path = os.path.join(status_dir, "status.json")
    tmp_path = status_path + ".tmp"
    
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.flush()
        os.fsync(f.fileno())
    
    os.replace(tmp_path, status_path)

def update_stage_status(project_id: str, stage_key: str, status: str, logs_dir: str = "logs"):
    """Atualiza o status de uma etapa ('in_progress', 'completed', 'failed')."""
    data = load_project_status(project_id, logs_dir)
    now_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    data["last_updated"] = now_str
    
    stage = data.get("stages", {}).get(stage_key, {})
    stage["status"] = status
    stage["updated_at"] = now_str
    
    if status == "in_progress" and "started_at" not in stage:
        stage["started_at"] = now_str
    elif status == "completed":
        stage["completed_at"] = now_str
        
    data.setdefault("stages", {})[stage_key] = stage
    _save_project_status(project_id, data, logs_dir)

def update_project_info(project_id: str, metrics: dict, logs_dir: str = "logs"):
    """Salva metadados e métricas adicionais do projeto (ex: contagem de fotos, aves)."""
    data = load_project_status(project_id, logs_dir)
    data["last_updated"] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    data.setdefault("metrics", {}).update(metrics)
    _save_project_status(project_id, data, logs_dir)

def get_completed_stages_summary(project_id: str, logs_dir: str = "logs") -> str:
    """Retorna uma string resumida das etapas concluídas."""
    if not project_id:
        return "Nenhuma"
    data = load_project_status(project_id, logs_dir)
    stages = data.get("stages", {})
    completed = [k for k, v in stages.items() if v.get("status") == "completed"]
    if not completed:
        return "Nenhuma etapa concluída"
    return ", ".join(completed)

