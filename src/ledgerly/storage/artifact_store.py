import shutil
from pathlib import Path
from datetime import datetime

class ArtifactStore:
    def __init__(self, base_dir: Path):
        self.storage_dir = base_dir / "data" / "imports"
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def save_artifact(self, file_bytes: bytes, original_name: str, custom_name: str = None) -> Path:
        """Stores the uploaded file under data/imports/YYYY/MM/ with custom or default filename."""
        now = datetime.now()
        target_dir = self.storage_dir / str(now.year) / f"{now.month:02d}"
        target_dir.mkdir(parents=True, exist_ok=True)

        ext = Path(original_name).suffix
        filename = (custom_name.strip() if custom_name else Path(original_name).stem) + ext
        
        # Sanitize filename
        safe_filename = "".join(c for c in filename if c.isalnum() or c in ("-", "_", "."))
        target_path = target_dir / safe_filename

        # If file exists, append timestamp
        if target_path.exists():
            target_path = target_dir / f"{target_path.stem}_{now.strftime('%H%M%S')}{ext}"

        with open(target_path, "wb") as f:
            f.write(file_bytes)

        return target_path