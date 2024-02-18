import os
import platform
from dotenv import load_dotenv
from routes import (
    app,
)  # Assegure-se de que esta importação é a correta para a sua estrutura de projeto

load_dotenv()

if platform.system() == "Windows":
    import uvicorn

    if __name__ == "__main__":
        host = os.getenv("APP_HOST", "127.0.0.1")
        port = os.getenv("APP_PORT", "8000")
        uvicorn.run(app, host=host, port=int(port))
else:
    from gunicorn.app.base import BaseApplication

    class Application(BaseApplication):

        def __init__(self, app, options=None):
            self.options = options or {}
            self.application = app
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
        port = os.getenv("APP_PORT", "8000")
        options = {
            "bind": f"{host}:{port}",
            "workers": 4,
            "worker_class": "uvicorn.workers.UvicornWorker",
        }

        Application(app, options).run()
