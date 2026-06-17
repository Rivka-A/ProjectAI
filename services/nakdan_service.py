import requests

class NakdanService:
    def __init__(self):
        # כתובת ה-API של נקדן דיקטה
        self.url = "https://nakdan-u1-0.loadbalancer.dicta.org.il/api"

    def get_vocalized_text(self, raw_text):
        payload = {
            "data": raw_text,
            "genre": "modern",
            "task": "nakdan"
        }
        try:
            response = requests.post(self.url, json=payload)
            response.raise_for_status()  # זורק שגיאה אם יש בעיה בתקשורת
            return response.json()       # מחזיר את התשובה מהשרת
        except requests.exceptions.RequestException as e:
            print(f"שגיאה בתקשורת עם ה-API: {e}")
            return None