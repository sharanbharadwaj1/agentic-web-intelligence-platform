# tools/memory_tool.py
import json
import os
import sqlite3
import time
from pathlib import Path
from llm.groq_client import GroqClient

DB_DIR = Path("memory")
DB_PATH = DB_DIR / "sqlite.db"

class MemoryTool:
    def __init__(self):
        self.llm = GroqClient()
        DB_DIR.mkdir(parents=True, exist_ok=True)
        self._connect_or_recreate()

    def _connect_or_recreate(self):
        try:
            self.con = sqlite3.connect(str(DB_PATH), timeout=10, check_same_thread=False)
            self.cur = self.con.cursor()
            self.cur.execute("PRAGMA journal_mode=WAL;")
            self.cur.execute("PRAGMA synchronous=NORMAL;")
            self.cur.execute(
                "CREATE TABLE IF NOT EXISTS memory(id INTEGER PRIMARY KEY AUTOINCREMENT, text TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
            )
            self.con.commit()
            try:
                self.cur.execute("PRAGMA integrity_check;")
                ok = self.cur.fetchone()
                if ok and ok[0] != "ok":
                    raise sqlite3.DatabaseError("integrity_check returned: " + str(ok))
            except sqlite3.DatabaseError:
                raise
        except sqlite3.DatabaseError:
            if DB_PATH.exists():
                backups_dir = DB_DIR / "backups"
                backups_dir.mkdir(exist_ok=True)
                ts = time.strftime("%Y%m%d_%H%M%S")
                backup_name = backups_dir / f"sqlite.db.corrupt.{ts}"
                try:
                    DB_PATH.rename(backup_name)
                except Exception:
                    DB_PATH.unlink(missing_ok=True)
                print(f"[MemoryTool] Backed up corrupted DB to: {backup_name}")

            self.con = sqlite3.connect(str(DB_PATH), timeout=10, check_same_thread=False)
            self.cur = self.con.cursor()
            self.cur.execute("PRAGMA journal_mode=WAL;")
            self.cur.execute("PRAGMA synchronous=NORMAL;")
            self.cur.execute(
                "CREATE TABLE IF NOT EXISTS memory(id INTEGER PRIMARY KEY AUTOINCREMENT, text TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
            )
            self.con.commit()
            print("[MemoryTool] Created new SQLite DB at:", DB_PATH)

    import json
    def store(self, obj):
        serialized = json.dumps(obj)
        self.cur.execute(
            "INSERT INTO memory(text) VALUES(?)",
            (serialized,)
        )
        self.con.commit()

    def retrieve_latest(self):
        self.cur.execute(
            "SELECT text FROM memory ORDER BY id DESC LIMIT 1"
        )
        row = self.cur.fetchone()
        if not row:
            return None
        return json.loads(row[0])
    
    # def store(self, text: str) -> str:
    #     try:
    #         summary = self.llm.ask(f"Summarize the following for concise memory storage:\n\n{text}")
    #         if not summary or summary.startswith("[Groq Error]"):
    #             summary = text
    #     except Exception:
    #         summary = text
    #     self.cur.execute("INSERT INTO memory(text) VALUES(?)", (summary,))
    #     self.con.commit()
    #     rowid = self.cur.lastrowid

    #     return f"Memory stored id {rowid}"

    # def retrieve_latest(self, limit: int = 1):
    # def retrieve_latest(self):

    #     return self.store[-1]   # not the full list

        # self.cur.execute("SELECT text, created_at FROM memory ORDER BY id DESC LIMIT ?", (limit,))
        # rows = self.cur.fetchall()
        # return rows

    def search(self, q: str, limit: int = 10):
        pattern = f"%{q}%"
        self.cur.execute("SELECT text, created_at FROM memory WHERE text LIKE ? ORDER BY id DESC LIMIT ?", (pattern, limit))
        return self.cur.fetchall()

    def close(self):
        try:
            self.con.close()
        except Exception:
            pass
