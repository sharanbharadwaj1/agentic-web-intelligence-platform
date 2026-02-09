import yaml
import os


current_directory = os.getcwd()
print(f"Current working directory: {current_directory}")

class Config:
    _cfg = None


    @classmethod
    
    def load(cls, path="E:/Projects/Agent Orchestrator Platform/aiagentplatform2/llm/config.yaml"):
        print(f"Loading config from {path}")
        if cls._cfg is None:
            with open(path, "r") as f:
                cls._cfg = yaml.safe_load(f)
        return cls._cfg