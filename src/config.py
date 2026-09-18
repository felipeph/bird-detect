import json
import os
import sys

CONFIG_PATH = "config.json"

DEFAULT_CONFIG = {
    "algo": "MOG2",
    "history": 100,
    "threshold": 512.0,
    "detectShadows": False,
    "min_contour_area": 50
}

def load_config() -> dict:
    if not os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "w") as f:
            json.dump(DEFAULT_CONFIG, f, indent=4)
        return DEFAULT_CONFIG.copy()
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)

def save_config(config: dict):
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=4)

def configure_menu():
    config = load_config()
    while True:
        print("\n--- OpenCV Configuration Menu ---")
        keys = list(config.keys())
        for i, key in enumerate(keys):
            print(f"[{i+1}] {key}: {config[key]}")
        print(f"[{len(keys)+1}] Sair e Salvar")
        
        choice = input("Selecione uma opcao para editar: ").strip()
        try:
            choice_idx = int(choice) - 1
            if choice_idx == len(keys):
                save_config(config)
                print("Configuracao salva!")
                break
            if 0 <= choice_idx < len(keys):
                key = keys[choice_idx]
                new_val = input(f"Novo valor para {key} (atual: {config[key]}): ").strip()
                # Parse type based on existing
                if isinstance(config[key], bool):
                    config[key] = new_val.lower() in ('true', '1', 'yes', 'y')
                elif isinstance(config[key], int):
                    config[key] = int(new_val)
                elif isinstance(config[key], float):
                    config[key] = float(new_val)
                else:
                    config[key] = new_val
            else:
                print("Opcao invalida.")
        except ValueError:
            print("Entrada invalida.")
