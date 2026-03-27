import yaml
import os

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
current_directory = os.getcwd()
# logger.info(f"Current working directory: {current_directory}")

class Config:
    _cfg = None


    @classmethod
    
    def load(cls, path="E:/Projects/Agent Orchestrator Platform/aiagentplatform2/llm/config.yaml"):
        logger.info(f"Loading config from {path}")
        if cls._cfg is None:
            with open(path, "r") as f:
                cls._cfg = yaml.safe_load(f)
        return cls._cfg