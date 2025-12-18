
import requests

class APICaller:
    def get(self, url):
        try:
            r = requests.get(url, timeout=10)
            return r.json()
        except Exception as e:
            return {"error": str(e)}
