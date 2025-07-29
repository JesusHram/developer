import reflex as rx
from developer.pages.dashboard import dashboard
from developer.pages.reporte_clientes import reporte_clientes
from developer.theme import theme

app = rx.App(
    theme=theme,
)

app.add_page(dashboard, route="/")
app.add_page(reporte_clientes, route="/reporte_clientes")
