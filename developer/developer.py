import reflex as rx
from developer.pages.dashboard import dashboard
from developer.pages.reporte_clientes import reporte_clientes
from developer.theme import theme
from developer.api import api_app

app = rx.App(
    theme=theme,
    api_transformer=api_app,
)



app.add_page(dashboard, route="/")
app.add_page(reporte_clientes, route="/reporte_clientes")
