import reflex as rx
from developer.state import State # Asegúrate que la ruta a tu State sea correcta

def sidebar_link(icon: str, text: str, url: str):
    """Un link estilizado para el sidebar que resalta si está activo."""
    is_active = (State.active_page == url)

    return rx.link(
        rx.hstack(
            rx.icon(tag=icon, size=15),
            rx.text(text, size="2"),
            # Estilos condicionales
            style=rx.cond(
                is_active,
                # Estilo para el link ACTIVO
                {
                    "background_color": rx.color("accent", 9),
                    "color": "white",
                    "box_shadow": f"0 0 10px {rx.color('accent', 10)}",
                },
                # Estilo para el link NORMAL
                {
                    "color": rx.color("accent", 11),
                }
            ),
            padding_x="1em",
            padding_y="0.75em",
            border_radius="8px",
            width="100%",
            transition="all 0.3s ease",
            _hover={
                "background_color": rx.color("accent", 4),
            },
        ),
        href=url,
        width="100%",
        text_decoration="none"
    )

def sidebar():
    """El sidebar con diseño moderno basado en el tema de la aplicación."""
    return rx.box(
        rx.vstack(
            rx.heading("Zaro Transportation", size="3", padding="1em", color=rx.color("accent", 12)),
            rx.divider(),
            rx.vstack(
                sidebar_link("layout-dashboard", "Dashboard", "/"),
                sidebar_link("users", "Clientes", "/reporte_clientes"),
                spacing="3",
                padding_x="1em",
                width="100%",
            ),
            rx.spacer(),
            rx.divider(),
            rx.hstack(
                rx.avatar(fallback="JZ", size="3"),
                rx.vstack(
                    rx.text("Jesus Zaro", weight="bold", size="3", color=rx.color("accent", 12)),
                    rx.text("Administrador", size="2", color=rx.color("accent", 10)),
                    spacing="0",
                    align_items="flex-start"
                ),
                padding="1em",
                width="100%",
                align_items="center",
            ),
            height="100dvh",
            width="100%",
            spacing="2"
        ),
        width="250px",
        height="100vh",
        position="fixed",
        left="0",
        top="0",
        background_color=rx.color("accent", 2, alpha=True),
        backdrop_filter="blur(16px)",
        border_right=f"1.5px solid {rx.color('accent', 5)}",
        zIndex=10
    )