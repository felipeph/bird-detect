import argparse
import os
import sys
import time
import datetime

from config import load_config, save_config, configure_menu, get_last_source_dir, add_recent_project
from tracker import load_project_status, update_stage_status, generate_project_id, update_project_info, get_completed_stages_summary
from ui_progress import VerticalProgressUI
from detector import BirdDetector
from notifier import notify_completion

# Configura encoding no Windows
try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

def sanitize_path(path_str: str) -> str:
    """Limpa caminhos decorrentes de digitação ou drag & drop no terminal."""
    if not path_str:
        return ""
    p = path_str.strip()
    if p.startswith("&"):
        p = p[1:].strip()
    if (p.startswith('"') and p.endswith('"')) or (p.startswith("'") and p.endswith("'")):
        p = p[1:-1].strip()
    return os.path.normpath(p)

def find_all_images(source_dir: str) -> list:
    """Busca todas as fotos JPG, JPEG e PNG na pasta, ignorando saídas anteriores."""
    valid_exts = {".jpg", ".jpeg", ".png"}
    images = []
    if not source_dir or not os.path.exists(source_dir):
        return images
    
    ignore_dirs = {"detected", "annotated", "__pycache__", ".git", "logs", "output"}
    for root, dirs, files in os.walk(source_dir):
        dirs[:] = [d for d in dirs if d.lower() not in ignore_dirs]
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext in valid_exts:
                images.append(os.path.join(root, f))
    return sorted(images)

def print_banner(config: dict, current_source: str, img_count: int, project_id: str = None):
    """Exibe cabeçalho decorado com metadados do projeto ativo e parâmetros."""
    print("\n" + "=" * 66)
    print("         BIRD DETECT - DETECÇÃO INTELIGENTE DE AVES")
    print("   Visão Computacional IA (YOLOv8 Medium) & Pipeline Autônomo")
    print("=" * 66)
    
    source_display = os.path.abspath(current_source) if current_source else "Nenhuma pasta selecionada (Use a opção [1])"
    proj_display = project_id if project_id else "Nenhum projeto ativo"
    stages_summary = get_completed_stages_summary(project_id) if project_id else "Nenhuma"
    
    conf = config.get("yolo_confidence", 0.25)
    ntfy_topic = config.get("ntfy_topic", "fph-bird-detect")
    
    print(f" PROJETO           : {proj_display}")
    print(f" ETAPAS CONCLUÍDAS : {stages_summary}")
    print("-" * 66)
    print(" CONFIGURAÇÃO ATIVA:")
    print(f"   • Pasta de Imagens  : {source_display}")
    if current_source:
        print(f"   • Fotos na Pasta    : {img_count} imagem(ns) encontrada(s)")
        print(f"   • Saída (Detectadas): {os.path.join(source_display, 'detected')}")
        print(f"   • Saída (Anotadas)  : {os.path.join(source_display, 'annotated')}")
    print(f"   • Inteligência Art. : YOLOv8 Medium (Confiança={conf * 100:.0f}%)")
    print(f"   • Notificações      : Toast Windows + Som + ntfy ({ntfy_topic})")
    print("=" * 66)

def select_source_dir(config: dict) -> str:
    """Menu interativo para definir nova pasta de fotos via digitação ou drag & drop."""
    current_source = get_last_source_dir(config)
    print("\n" + "=" * 66)
    print("            SELEÇÃO DA PASTA DE IMAGENS DO PROJETO")
    print("=" * 66)
    if current_source:
        print(f"Pasta de origem atual: {os.path.abspath(current_source)}")
    else:
        print("Pasta de origem atual: Nenhuma pasta configurada.")
    print("\nOpções:")
    print("  [1] Digitar ou arrastar e soltar (drag & drop) o caminho da pasta...")
    print("  [2] Usar diretório atual (.)")
    print("  [0] Cancelar / Manter pasta anterior")
    print("-" * 66)
    
    choice = input("Escolha uma opção [0-2]: ").strip()
    if choice == "1":
        path_input = input("\nDigite ou arraste a pasta aqui: ").strip()
        cleaned = sanitize_path(path_input)
        if not cleaned:
            print("[-] Nenhum caminho informado. Mantendo pasta anterior.")
            return current_source
        if not os.path.exists(cleaned):
            print(f"[-] Erro: O caminho '{cleaned}' não foi encontrado.")
            return current_source
        if not os.path.isdir(cleaned):
            print(f"[-] Erro: O caminho informado não é uma pasta válida.")
            return current_source
            
        imgs = find_all_images(cleaned)
        add_recent_project(config, cleaned)
        print(f"[+] Pasta definida com sucesso: {os.path.abspath(cleaned)}")
        print(f"[+] Imagens válidas encontradas: {len(imgs)}")
        return cleaned
    elif choice == "2":
        cur_abs = os.path.abspath(".")
        imgs = find_all_images(cur_abs)
        add_recent_project(config, cur_abs)
        print(f"[+] Pasta definida para o diretório atual: {cur_abs}")
        print(f"[+] Imagens válidas encontradas: {len(imgs)}")
        return cur_abs
    elif choice == "0":
        print("[+] Pasta mantida.")
        return current_source
    else:
        print("[-] Opção inválida. Pasta mantida.")
        return current_source

def select_recent_project(config: dict) -> str:
    """Permite selecionar rapidamente uma pasta a partir do histórico de projetos recentes."""
    recents = config.get("recent_projects", [])
    valid_recents = [p for p in recents if os.path.exists(p) and os.path.isdir(p)]
    
    if not valid_recents:
        print("\n[-] Nenhum projeto recente encontrado no histórico.")
        return get_last_source_dir(config)
        
    print("\n" + "=" * 66)
    print("                  PROJETOS RECENTES")
    print("=" * 66)
    for i, p in enumerate(valid_recents, 1):
        imgs = len(find_all_images(p))
        print(f"  [{i}] {p} ({imgs} imagem(ns))")
    print("  [0] Voltar ao Menu Principal")
    print("-" * 66)
    
    choice = input(f"Selecione um projeto [1-{len(valid_recents)} ou 0]: ").strip()
    try:
        idx = int(choice)
        if idx == 0:
            return get_last_source_dir(config)
        if 1 <= idx <= len(valid_recents):
            selected = valid_recents[idx - 1]
            add_recent_project(config, selected)
            print(f"[+] Projeto ativo alterado para: {selected}")
            return selected
        else:
            print("[-] Opção inválida.")
    except ValueError:
        print("[-] Entrada inválida.")
    return get_last_source_dir(config)

def run_detection_pipeline(source_dir: str, config: dict, is_test: bool = False) -> bool:
    """Executa o pipeline completo de detecção de pássaros com UI vertical e notificações."""
    if is_test:
        source_dir = "test_images"
        out_detected = os.path.join("output", "test_detected")
        out_annotated = os.path.join("output", "test_annotated")
    else:
        if not source_dir or not os.path.exists(source_dir):
            print("\n[-] Erro: Nenhuma pasta válida selecionada. Use a opção [1] no menu.")
            return False
        out_detected = os.path.join(source_dir, "detected")
        out_annotated = os.path.join(source_dir, "annotated")
        
    os.makedirs(out_detected, exist_ok=True)
    os.makedirs(out_annotated, exist_ok=True)
    
    img_files = find_all_images(source_dir)
    if not img_files:
        print(f"\n[-] Nenhuma imagem válida (.jpg, .jpeg, .png) encontrada em: {source_dir}")
        return False
        
    project_id = generate_project_id(source_dir)
    load_project_status(project_id)
    update_stage_status(project_id, "detection", "in_progress")
    
    ui = VerticalProgressUI(f"Bird Detect - {project_id}", len(img_files), config)
    ui.start()
    
    detector = BirdDetector(config)
    detected_count = 0
    start_time = time.time()
    
    try:
        for idx, img_path in enumerate(img_files):
            found = detector.process_image(img_path, out_detected, out_annotated)
            if found:
                detected_count += 1
            ui.update(1, status_msg=f"Aves detectadas: {detected_count}", current_filename=os.path.basename(img_path))
            
        elapsed_sec = int(time.time() - start_time)
        elapsed_str = str(datetime.timedelta(seconds=elapsed_sec))
        
        update_stage_status(project_id, "detection", "completed")
        update_project_info(project_id, {
            "source_dir": os.path.abspath(source_dir),
            "out_detected": os.path.abspath(out_detected),
            "out_annotated": os.path.abspath(out_annotated),
            "total_images": len(img_files),
            "detected_count": detected_count,
            "elapsed_seconds": elapsed_sec,
            "elapsed_str": elapsed_str
        })
    except KeyboardInterrupt:
        update_stage_status(project_id, "detection", "failed")
        ui.stop()
        print("\n[!] Processo interrompido pelo usuário.")
        return False
    finally:
        ui.stop()
        
    elapsed_sec = int(time.time() - start_time)
    elapsed_str = str(datetime.timedelta(seconds=elapsed_sec))
    
    print("\n" + "=" * 66)
    print("            RELATÓRIO DE EXECUÇÃO - BIRD DETECT")
    print("=" * 66)
    print(f"  • Projeto ID           : {project_id}")
    print(f"  • Imagens Processadas  : {len(img_files)}")
    print(f"  • Aves Detectadas      : {detected_count}")
    print(f"  • Tempo Total          : {elapsed_str}")
    print(f"  • Imagens Brutas Salvas: {out_detected}")
    print(f"  • Imagens Anotadas     : {out_annotated}")
    print("=" * 66)
    
    # Notificações assíncronas (Toast + Som + ntfy)
    ntfy_topic = config.get("ntfy_topic", "fph-bird-detect")
    enable_toast = config.get("enable_toast", True)
    enable_sound = config.get("enable_sound", True)
    notify_completion(
        project_id=project_id,
        total_images=len(img_files),
        detected_count=detected_count,
        elapsed_str=elapsed_str,
        out_dir=out_detected,
        ntfy_topic=ntfy_topic,
        toast=enable_toast,
        sound=enable_sound
    )
    return True

def interactive_menu():
    """Menu principal com interface interativa e navegação por projetos."""
    config = load_config()
    current_source = get_last_source_dir(config)
    
    while True:
        try:
            img_count = len(find_all_images(current_source)) if current_source else 0
            print_banner(config, current_source, img_count)
            
            print("MENU PRINCIPAL:")
            print("  [ENTER] Executar Detecção na pasta ativa")
            print("  " + "-" * 58)
            print("  [1] Selecionar Pasta de Imagens (Digitar ou Arrastar e Soltar)")
            print("  [2] Selecionar Projeto Recente")
            print("  [3] Modo Teste Rápido (Executar validação em 'test_images')")
            print("  [4] Menu de Configurações (YOLO, ntfy, som)")
            print("  [0] Sair")
            print("=" * 66)
            
            choice = input("Selecione uma opção [0-4 ou pressione ENTER para executar]: ").strip()
            
            if choice == "":
                if not current_source or not os.path.exists(current_source):
                    print("\n[-] Nenhuma pasta válida selecionada. Escolha a opção [1] primeiro.")
                    input("\nPressione Enter para continuar...")
                    continue
                run_detection_pipeline(current_source, config, is_test=False)
                input("\nPressione Enter para continuar...")
            elif choice == "1":
                current_source = select_source_dir(config)
            elif choice == "2":
                current_source = select_recent_project(config)
            elif choice == "3":
                print("\n[+] Iniciando Modo de Teste Rápido em 'test_images'...")
                run_detection_pipeline("test_images", config, is_test=True)
                input("\nPressione Enter para continuar...")
            elif choice == "4":
                configure_menu()
                config = load_config()
            elif choice == "0":
                print("\n[+] Encerrando o Bird Detect. Até logo!")
                break
            else:
                print("\n[-] Opção inválida.")
                time.sleep(1)
        except (KeyboardInterrupt, EOFError):
            print("\n\n[+] Encerrando o Bird Detect. Até logo!")
            break

def main():
    parser = argparse.ArgumentParser(description="Bird Detect - Detector de Pássaros (YOLOv8 AI)")
    parser.add_argument("--input", default=None, help="Diretório com as imagens de entrada (execução direta)")
    parser.add_argument("--out-detected", default=None, help="Diretório de saída para imagens brutas")
    parser.add_argument("--out-annotated", default=None, help="Diretório de saída para imagens anotadas")
    parser.add_argument("--test", action="store_true", help="Executa o modo de teste em 'test_images' e encerra")
    parser.add_argument("--menu", action="store_true", help="Força a abertura do menu interativo")
    
    args = parser.parse_args()
    config = load_config()
    
    # Se argumentos diretos foram fornecidos, executa em modo não-interativo (batch/script)
    if args.test:
        run_detection_pipeline("test_images", config, is_test=True)
        return
        
    if args.input:
        cleaned = sanitize_path(args.input)
        add_recent_project(config, cleaned)
        run_detection_pipeline(cleaned, config, is_test=False)
        return
        
    # Modo padrão: Menu interativo
    interactive_menu()

if __name__ == "__main__":
    main()

