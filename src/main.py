import argparse
import os
import glob
from config import load_config, configure_menu
from tracker import load_project_status, update_stage_status
from ui_progress import VerticalProgressUI
from detector import BirdDetector

def main():
    parser = argparse.ArgumentParser(description="Detector de Passaros (Background Subtraction)")
    parser.add_argument("--input", default="test_images", help="Diretorio com as imagens de entrada")
    parser.add_argument("--out-detected", default="output/detected", help="Diretorio de saida para imagens brutas")
    parser.add_argument("--out-annotated", default="output/annotated", help="Diretorio de saida para imagens anotadas")
    parser.add_argument("--menu", action="store_true", help="Abre o menu interativo de configuracoes antes de rodar")
    
    args = parser.parse_args()

    if args.menu:
        configure_menu()

    config = load_config()
    
    os.makedirs(args.out_detected, exist_ok=True)
    os.makedirs(args.out_annotated, exist_ok=True)

    img_files = sorted(glob.glob(os.path.join(args.input, "*.jpg"))) + \
                sorted(glob.glob(os.path.join(args.input, "*.png")))
    
    if not img_files:
        print(f"Nenhuma imagem encontrada em {args.input}")
        return

    project_id = "bird_detection_run"
    load_project_status(project_id) # initial load
    
    ui = VerticalProgressUI("Bird Detection Pipeline", len(img_files), config)
    ui.start()
    
    update_stage_status(project_id, "detection", "in_progress")

    detector = BirdDetector(config)

    detected_count = 0
    try:
        for idx, img_path in enumerate(img_files):
            found = detector.process_image(img_path, args.out_detected, args.out_annotated)
            if found:
                detected_count += 1
            
            ui.update(1, status_msg=f"Passaros encontrados: {detected_count}")
            
        update_stage_status(project_id, "detection", "completed")
    except KeyboardInterrupt:
        update_stage_status(project_id, "detection", "failed")
        ui.stop()
        print("\nProcesso interrompido pelo usuario.")
    finally:
        ui.stop()
        print(f"Processamento concluido! Total de passaros detectados: {detected_count}")

if __name__ == "__main__":
    main()
