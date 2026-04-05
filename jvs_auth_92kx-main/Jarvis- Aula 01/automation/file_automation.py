import os
import shutil
import logging

logger = logging.getLogger(__name__)

class FileAutomation:
    def __init__(self):
        self.home = os.path.expanduser('~')
        self.desktop = os.path.join(self.home, 'Desktop')
        self.documents = os.path.join(self.home, 'Documents')
        self.downloads = os.path.join(self.home, 'Downloads')
        self.base_folders = {
            "area de trabalho": self.desktop,
            "área de trabalho": self.desktop,
            "desktop": self.desktop,
            "documentos": self.documents,
            "documents": self.documents,
            "downloads": self.downloads,
            "imagens": os.path.join(self.home, 'Pictures'),
            "fotos": os.path.join(self.home, 'Pictures'), 
            "videos": os.path.join(self.home, 'Videos'),
            "musicas": os.path.join(self.home, 'Music'),
            "audio": os.path.join(self.home, 'Music')
        }
        self.ignore_folders = {
            "venv", ".venv", "env", "node_modules", "__pycache__", ".git", ".idea", ".vscode"
        }

    def _resolver_caminho(self, caminho):
        caminho = caminho.strip('\'"').replace('\\', '/')
        caminho_lower = caminho.lower()

        for alias, real_path in self.base_folders.items():
            if caminho_lower == alias:
                return real_path
            if caminho_lower.startswith(alias + "/"):
                return os.path.abspath(os.path.join(real_path, caminho[len(alias)+1:]))
        
        if not os.path.isabs(caminho) and not caminho.startswith('.'):
            return os.path.abspath(os.path.join(self.desktop, caminho))
            
        return os.path.abspath(os.path.expanduser(caminho))

    def create_folder(self, params: dict):
        caminho = params.get("caminho")
        if not caminho:
            return "Erro: Parâmetro 'caminho' é obrigatório."
        try:
            caminho_abs = self._resolver_caminho(caminho)
            os.makedirs(caminho_abs, exist_ok=True)
            logger.info(f"[AUTOMATION] Action: file.create_folder | Path: {caminho_abs}")
            return f"Pasta criada com sucesso: {caminho_abs}"
        except Exception as e:
            logger.error(f"[AUTOMATION] Error in file.create_folder: {str(e)}")
            return f"Erro ao criar pasta: {str(e)}"

    def delete_item(self, params: dict):
        caminho = params.get("caminho")
        if not caminho:
            return "Erro: Parâmetro 'caminho' é obrigatório."
        try:
            path_abs = self._resolver_caminho(caminho)
            if os.path.isfile(path_abs):
                os.remove(path_abs)
                logger.info(f"[AUTOMATION] Action: file.delete_item | File: {path_abs}")
                return f"Arquivo deletado: {path_abs}"
            elif os.path.isdir(path_abs):
                shutil.rmtree(path_abs)
                logger.info(f"[AUTOMATION] Action: file.delete_item | Directory: {path_abs}")
                return f"Diretório deletado: {path_abs}"
            return f"Caminho não encontrado: {path_abs}"
        except Exception as e:
            logger.error(f"[AUTOMATION] Error in file.delete_item: {str(e)}")
            return f"Erro ao deletar: {str(e)}"

    def open_folder(self, params: dict):
        nome_pasta = params.get("nome_pasta")
        if not nome_pasta:
            return "Erro: Parâmetro 'nome_pasta' é obrigatório."
        try:
            caminho_direto = self.base_folders.get(nome_pasta.lower())
            if caminho_direto and os.path.exists(caminho_direto):
                os.startfile(caminho_direto)
                logger.info(f"[AUTOMATION] Action: file.open_folder | Path: {caminho_direto}")
                return f"Abrindo {nome_pasta}."
            
            # Busca simples no desktop se não for alias
            caminho_abs = self._resolver_caminho(nome_pasta)
            if os.path.exists(caminho_abs) and os.path.isdir(caminho_abs):
                os.startfile(caminho_abs)
                logger.info(f"[AUTOMATION] Action: file.open_folder | Path: {caminho_abs}")
                return f"Abrindo pasta em: {caminho_abs}"

            return f"Pasta '{nome_pasta}' não encontrada."
        except Exception as e:
            logger.error(f"[AUTOMATION] Error in file.open_folder: {str(e)}")
            return f"Erro ao abrir pasta: {str(e)}"
