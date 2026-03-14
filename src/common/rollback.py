"""
Model Rollback Framework — Phase 8.2

Manages model versioning and provides atomic rollback to Known Good States (KGS).
Prevents deployment of degraded models identified by the Risk Engine.
"""

import logging
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

class ModelRollbackManager:
    """
    Handles model weights promotion and rollback.
    Maintains a 'active' symlink to the current production model.
    """
    
    def __init__(self, model_dir: str = "models/"):
        self.model_path = Path(model_dir)
        self.active_link = self.model_path / "active"
        self.kgs_link = self.model_path / "kgs" # Known Good State
        self.model_path.mkdir(parents=True, exist_ok=True)

    def promote_to_active(self, model_version: str) -> bool:
        """Atomically update the active model symlink."""
        new_model = self.model_path / model_version
        if not new_model.exists():
            logger.error(f"Cannot promote {model_version}: weights file not found.")
            return False
            
        # Update KGS if current active is stable
        if self.active_link.exists():
            if self.kgs_link.exists():
                self.kgs_link.unlink()
            # Move old active to KGS
            target = self.active_link.resolve()
            self.kgs_link.symlink_to(target)
            self.active_link.unlink()
            
        self.active_link.symlink_to(new_model)
        logger.info(f"Model {model_version} promoted to ACTIVE.")
        return True

    def rollback(self) -> bool:
        """Revert active model to the Known Good State (KGS)."""
        if not self.kgs_link.exists():
            logger.error("Rollback failed: No Known Good State (KGS) found.")
            return False
            
        kgs_target = self.kgs_link.resolve()
        logger.warning(f"ROLLBACK TRIGGERED: Reverting from {self.active_link.resolve().name} to {kgs_target.name}")
        
        if self.active_link.exists():
            self.active_link.unlink()
            
        self.active_link.symlink_to(kgs_target)
        logger.info("Rollback complete. System is back on KGS.")
        return True

    def list_versions(self) -> list[str]:
        """List all available model versions in the directory."""
        return [p.name for p in self.model_path.iterdir() if p.is_file()]
