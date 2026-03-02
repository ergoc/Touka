import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()


@dataclass
class ModelConfig:
    repo_id: str = "mradermacher/Llama-3.2-1B-Instruct-Uncensored-GGUF"
    filename: str = "Llama-3.2-1B-Instruct-Uncensored.Q5_K_M.gguf"
    model_dir: str = "./models"
    n_ctx: int = 2048
    n_threads: int = 1
    n_batch: int = 512
    n_gpu_layers: int = 0
    max_tokens: int = 256
    temperature: float = 0.8
    top_k: int = 40
    top_p: float = 0.95
    repeat_penalty: float = 1.05


@dataclass
class ServerConfig:
    port: int = int(os.environ.get("PORT", 3000))
    host: str = os.environ.get("HOST", "0.0.0.0")
    log_level: str = os.environ.get("LOG_LEVEL", "info")


@dataclass
class Config:
    model: ModelConfig = field(default_factory=ModelConfig)
    server: ServerConfig = field(default_factory=ServerConfig)

    @property
    def version(self) -> str:
        from touka.core.touka import VERSION
        return VERSION


cfg = Config()