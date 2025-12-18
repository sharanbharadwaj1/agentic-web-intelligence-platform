
import pandas as pd

class FileManager:
    def read_csv(self, path):
        return pd.read_csv(path)

    def write_csv(self, df, path):
        df.to_csv(path, index=False)
