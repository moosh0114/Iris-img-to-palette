from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    repo_root: Path = Path(__file__).resolve().parent.parent
    max_upload_bytes: int = 10 * 1024 * 1024
    max_batch_images: int = 1000
    upload_chunk_size: int = 1024 * 1024
    history_limit: int = 20
    model_similarity_threshold: float = 0.03

    @property
    def data_dir(self) -> Path:
        return self.repo_root / "data"

    @property
    def upload_dir(self) -> Path:
        return self.data_dir / "uploads"

    @property
    def db_path(self) -> Path:
        return self.data_dir / "app.db"

    @property
    def model_path(self) -> Path:
        primary_path = self.repo_root / "models" / "palette_scorer.pth"
        if primary_path.exists():
            return primary_path
        return self.repo_root / "models" / "Iris1.0.pth"


settings = Settings()
