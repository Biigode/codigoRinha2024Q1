import os
import multiprocessing
import uvicorn
from gunicorn.app.base import BaseApplication
from dotenv import load_dotenv
from routes import app

# Simulando a criação de uma aplicação FastAPI
# app = FastAPI()

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# Verifica se está em modo produção
is_production = os.getenv("PRODUCTION", "false").lower() == "true"

# Determina o número de núcleos do CPU para configurar os workers
NUM_CORES = multiprocessing.cpu_count()


class StandaloneGunicornApplication(BaseApplication):
    """
    Uma classe personalizada para executar o Gunicorn + Uvicorn em conjunto com a aplicação FastAPI.
    """

    def __init__(self, application, options=None):
        self.application = application
        self.options = options or {}
        super().__init__()

    def load_config(self):
        config = {
            key: value
            for key, value in self.options.items()
            if key in self.cfg.settings and value is not None
        }
        for key, value in config.items():
            self.cfg.set(key.lower(), value)

    def load(self):
        return self.application


if __name__ == "__main__":
    host = os.getenv("APP_HOST", "127.0.0.1")
    port = int(os.getenv("APP_PORT", "8000"))
    if not is_production:
        # Executa a aplicação com Uvicorn diretamente em modo de desenvolvimento
        uvicorn.run(app=app, host=host, port=port, workers=1)
    else:
        # Opções para configurar o Gunicorn + Uvicorn em produção
        gunicorn_options = {
            "bind": f"{host}:{port}",
            "workers": max(
                (2 * NUM_CORES) + 1, 2
            ),  # Ajusta o número mínimo de workers para 2
            # "workers": 2,
            "worker_class": "uvicorn.workers.UvicornWorker",
            "preload_app": False,  # Cautela ao habilitar o preload
        }
        StandaloneGunicornApplication(app, gunicorn_options).run()
