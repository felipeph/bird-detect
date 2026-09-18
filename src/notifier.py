import sys
import threading
import urllib.request
import subprocess

def notify_event(title: str, message: str, ntfy_topic: str = "fph-bird-detect", toast: bool = True, sound: bool = True):
    """
    Dispara notificações de forma assíncrona em thread daemon para não travar o fluxo principal.
    - Windows Toast Notification nativo
    - Alerta sonoro (Beep)
    - Notificação remota push via ntfy.sh
    """
    def _worker():
        # 1. Alerta Sonoro
        if sound and sys.platform == "win32":
            try:
                import winsound
                winsound.Beep(1000, 350)
            except Exception:
                try:
                    subprocess.run(
                        ["powershell", "-NoProfile", "-Command", "[console]::beep(1000, 350)"],
                        capture_output=True,
                        timeout=2
                    )
                except Exception:
                    pass

        # 2. Windows Toast Notification
        if toast and sys.platform == "win32":
            try:
                ps_script = f"""
                [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] > $null
                $template = [Windows.UI.Notifications.ToastTemplateType]::ToastText02
                $xml = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent($template)
                $texts = $xml.GetElementsByTagName("text")
                $texts[0].AppendChild($xml.CreateTextNode("{title}")) > $null
                $texts[1].AppendChild($xml.CreateTextNode("{message}")) > $null
                $toast = [Windows.UI.Notifications.ToastNotification]::new($xml)
                [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("BirdDetect").Show($toast)
                """
                subprocess.run(["powershell", "-NoProfile", "-Command", ps_script], capture_output=True, timeout=5)
            except Exception:
                pass

        # 3. NTFY Push Notification
        if ntfy_topic:
            try:
                url = f"https://ntfy.sh/{ntfy_topic}"
                req = urllib.request.Request(
                    url,
                    data=message.encode("utf-8"),
                    headers={
                        "Title": title.encode("utf-8"),
                        "Priority": "default",
                        "Tags": "bird,camera"
                    },
                    method="POST"
                )
                with urllib.request.urlopen(req, timeout=10):
                    pass
            except Exception:
                pass

    threading.Thread(target=_worker, daemon=True).start()

def notify_completion(project_id: str, total_images: int, detected_count: int, elapsed_str: str, out_dir: str, ntfy_topic: str = "fph-bird-detect", toast: bool = True, sound: bool = True):
    """Gera o relatório resumido e dispara os alertas assíncronos."""
    title = f"Bird Detect - Concluído: {project_id}"
    message = (
        f"Projeto: {project_id}\n"
        f"Imagens Processadas: {total_images}\n"
        f"Aves Detectadas: {detected_count}\n"
        f"Tempo Total: {elapsed_str}\n"
        f"Destino: {out_dir}"
    )
    notify_event(title, message, ntfy_topic=ntfy_topic, toast=toast, sound=sound)
