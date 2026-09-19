import json
import os
import sys

CONFIG_PATH = "config.json"

DEFAULT_CONFIG = {
    "yolo_confidence": 0.25,
    "last_source_dir": None,
    "recent_projects": [],
    "ntfy_topic": "fph-bird-detect",
    "enable_toast": True,
    "enable_sound": True
}

def load_config() -> dict:
    if not os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_CONFIG, f, indent=4, ensure_ascii=False)
        return DEFAULT_CONFIG.copy()
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Garante retrocompatibilidade com chaves ausentes
        updated = False
        for key, val in DEFAULT_CONFIG.items():
            if key not in data:
                data[key] = val
                updated = True
        if updated:
            save_config(data)
        return data
    except Exception:
        return DEFAULT_CONFIG.copy()

def save_config(config: dict):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4, ensure_ascii=False)

def get_last_source_dir(config: dict):
    """Retorna o último diretório de origem se existir no disco."""
    path = config.get("last_source_dir")
    if path and os.path.exists(path) and os.path.isdir(path):
        return path
    return None

def add_recent_project(config: dict, path: str):
    """Atualiza o último diretório usado e adiciona à lista de projetos recentes."""
    abs_path = os.path.abspath(path)
    config["last_source_dir"] = abs_path
    
    recents = config.get("recent_projects", [])
    if abs_path in recents:
        recents.remove(abs_path)
    recents.insert(0, abs_path)
    config["recent_projects"] = recents[:5]
    
    save_config(config)

def configure_menu():
    config = load_config()
    editable_keys = ["yolo_confidence", "ntfy_topic", "enable_toast", "enable_sound"]
    while True:
        print("\n" + "=" * 50)
        print("         MENU DE CONFIGURACOES GERAIS")
        print("=" * 50)
        for i, key in enumerate(editable_keys):
            print(f"[{i+1}] {key}: {config.get(key, DEFAULT_CONFIG.get(key))}")
        print(f"[{len(editable_keys)+1}] Salvar e Voltar")
        print("-" * 50)
        
        choice = input(f"Selecione uma opcao para editar [1-{len(editable_keys)+1}]: ").strip()
        try:
            choice_idx = int(choice) - 1
            if choice_idx == len(editable_keys):
                save_config(config)
                print("[+] Configuracoes salvas com sucesso!")
                break
            if 0 <= choice_idx < len(editable_keys):
                key = editable_keys[choice_idx]
                curr_val = config.get(key, DEFAULT_CONFIG.get(key))
                new_val = input(f"Novo valor para '{key}' (atual: {curr_val}): ").strip()
                if not new_val:
                    print("[-] Valor mantido.")
                    continue
                if isinstance(curr_val, bool):
                    config[key] = new_val.lower() in ('true', '1', 'yes', 'y', 'sim', 's')
                elif isinstance(curr_val, int):
                    config[key] = int(new_val)
                elif isinstance(curr_val, float):
                    config[key] = float(new_val)
                else:
                    config[key] = new_val
                print(f"[+] '{key}' atualizado para: {config[key]}")
            else:
                print("[-] Opcao invalida.")
        except ValueError:
            print("[-] Entrada invalida.")

