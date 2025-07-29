from developer.components.layout import layout
import reflex as rx

def dashboard():
    return layout(
        rx.box(
            rx.heading("Dashboard", size="5"),
            padding="2",
            width="100%"
        ),
    )