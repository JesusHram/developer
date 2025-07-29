import reflex as rx
from developer.components.sidebar import sidebar

def layout(*children):
    return rx.box(
        sidebar(),
        rx.box(
            *children,
            margin_left="260px",
            padding="2",
            min_height="100vh",
            background_color=rx.color("gray", 1)
        ),
    )