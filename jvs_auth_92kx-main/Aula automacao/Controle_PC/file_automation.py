import os
import shutil
import zipfile

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

    def _walk_seguro(self, base):
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = [d for d in dirnames if d not in self.ignore_folders and not d.startswith('.')]
            yield dirpath, dirnames, filenames

    def cria_pasta(self, caminho):
        try:
            caminho_abs = self._resolver_caminho(caminho)
            os.makedirs(caminho_abs, exist_ok=True)
            return f"Pasta criada com sucesso: {caminho_abs}"
        except Exception as e:
            return f"Erro ao criar pasta: {str(e)}"

    def abrir_pasta(self, nome_pasta):
        try:
            caminho_direto = self.base_folders.get(nome_pasta.lower())
            if caminho_direto and os.path.exists(caminho_direto):
                os.startfile(caminho_direto)
                return f"Abrindo {nome_pasta}."

            for base_name, base_path in self.base_folders.items():
                if base_name in ["area de trabalho", "documentos", "downloads"]:
                    for dirpath, dirnames, _ in self._walk_seguro(base_path):
                        for d in dirnames:
                            if d.lower() == nome_pasta.lower():
                                full_path = os.path.join(dirpath, d)
                                os.startfile(full_path)
                                return f"Pasta encontrada e aberta em: {full_path}"
            
            return f"Pasta '{nome_pasta}' não encontrada nos locais padrão."
        except Exception as e:
            return f"Erro ao abrir pasta: {str(e)}"

    def buscar_e_abrir_arquivo(self, nome_arquivo):
        try:
            for _, base_path in self.base_folders.items():
                for dirpath, _, filenames in self._walk_seguro(base_path):
                    for f in filenames:
                        if nome_arquivo.lower() in f.lower():
                            full_path = os.path.join(dirpath, f)
                            os.startfile(full_path)
                            return f"Arquivo encontrado e aberto: {full_path}"
            return f"Arquivo '{nome_arquivo}' não encontrado."
        except Exception as e:
            return f"Erro ao buscar/abrir arquivo: {str(e)}"

    def deletar_item(self, caminho):
        try:
            path_abs = self._resolver_caminho(caminho)
            if os.path.isfile(path_abs):
                os.remove(path_abs)
                return f"Arquivo deletado: {path_abs}"
            elif os.path.isdir(path_abs):
                shutil.rmtree(path_abs)
                return f"Diretório deletado: {path_abs}"
            return f"Caminho não encontrado: {path_abs}"
        except Exception as e:
            return f"Erro ao deletar: {str(e)}"

    def mover_item(self, origem, destino):
        try:
            origem_abs = self._resolver_caminho(origem)
            destino_abs = self._resolver_caminho(destino)
            shutil.move(origem_abs, destino_abs)
            return f"Movido de {origem_abs} para {destino_abs}."
        except Exception as e:
            return f"Erro ao mover: {str(e)}"

    def copiar_item(self, origem, destino):
        try:
            origem_abs = self._resolver_caminho(origem)
            destino_abs = self._resolver_caminho(destino)
            if os.path.isdir(origem_abs): shutil.copytree(origem_abs, destino_abs)
            else: shutil.copy2(origem_abs, destino_abs)
            return f"Copiado de {origem_abs} para {destino_abs}."
        except Exception as e:
            return f"Erro ao copiar: {str(e)}"

    def renomear_item(self, caminho, novo_nome):
        try:
            path_abs = self._resolver_caminho(caminho)
            diretorio = os.path.dirname(path_abs)
            novo_caminho = os.path.join(diretorio, novo_nome)
            os.rename(path_abs, novo_caminho)
            return f"Renomeado para {novo_nome}."
        except Exception as e:
            return f"Erro ao renomear: {str(e)}"

    def organizar_pasta(self, caminho):
        try:
            path_abs = self._resolver_caminho(caminho)
            extensoes = {
                'Imagens': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'],
                'Documentos': ['.pdf', '.doc', '.docx', '.txt', '.xlsx', '.pptx', '.csv'],
                'Videos': ['.mp4', '.mkv', '.avi', '.mov'],
                'Musicas': ['.mp3', '.wav', '.flac'],
                'Compactados': ['.zip', '.rar', '.7z'],
                'Executaveis': ['.exe', '.msi', '.bat']
            }

            for item in os.listdir(path_abs):
                item_path = os.path.join(path_abs, item)
                if os.path.isfile(item_path):
                    ext = os.path.splitext(item)[1].lower()
                    movido = False
                    for pasta, exts in extensoes.items():
                        if ext in exts:
                            pasta_destino = os.path.join(path_abs, pasta)
                            os.makedirs(pasta_destino, exist_ok=True)
                            shutil.move(item_path, os.path.join(pasta_destino, item))
                            movido = True
                            break
                    if not movido:
                        pasta_outros = os.path.join(path_abs, 'Outros')
                        os.makedirs(pasta_outros, exist_ok=True)
                        shutil.move(item_path, os.path.join(pasta_outros, item))
            return "Pasta organizada com sucesso."
        except Exception as e:
            return f"Erro ao organizar pasta: {str(e)}"

    def compactar_pasta(self, caminho):
        try:
            path_abs = self._resolver_caminho(caminho).rstrip('/\\')
            shutil.make_archive(path_abs, 'zip', path_abs)
            return f"Compactado em: {path_abs}.zip"
        except Exception as e:
            return f"Erro ao compactar: {str(e)}"
