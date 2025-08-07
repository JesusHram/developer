import os
import reflex as rx
from dotenv import load_dotenv

load_dotenv()


API_URL = os.getenv("API_URL", "http://localhost:8000")


config = rx.Config(
    app_name="developer",
    api_url=API_URL,
    cors_allowed_origins=[
        "http://localhost:3000",
         API_URL,
        "http://dashboard.zarotransportation.com",
        "https://dashboard.zarotransportation.com",
    ],
    tailwind={
        "theme": {
            "extend": {
                "colors": {
                    "primary": {"50": "#f0f9ff", "100": "#e0f2fe", "200": "#bae6fd", "300": "#7dd3fc", "400": "#38bdf8", "500": "#0ea5e9", "600": "#0284c7", "700": "#0369a1", "800": "#075985", "900": "#0c4a6e"},
                }
            }
        }
    }
)
