import reflex as rx
# La importación del State es crucial para que el componente pueda acceder a los datos
from developer.state import State

# Helper para renderizar las filas de la tabla de viajes
def render_viaje_row(row: dict):
    return rx.table.row(
        rx.table.cell(row["intIdViaje"]),
        rx.table.cell(row["Origen"]),
        rx.table.cell(row["Destino"]),
        rx.table.cell((row["floatDistanciaGoogle"])), 
        rx.table.cell((row["strMillasVacias"])),
        rx.table.cell((row["strRate"])),
        rx.table.cell(row["FechaRecoleccion"]),
        rx.table.cell(row["ViajeTipo"]),
        rx.table.cell(row["Internacional"]),
        rx.table.cell(row["TIPO"]),
        rx.table.cell(row["STATUS"])
    )

def viajes_modal():
    """Componente que renderiza el modal de detalle de viajes."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(f"Viajes de {State.selected_cliente.get('strNombreCte', '')}"),
            rx.vstack(
                rx.table.root(
                    rx.table.header(
                        # --- CORRECCIÓN: Esta es la cabecera correcta para los viajes ---
                        rx.table.row(
                            rx.table.column_header_cell("Viaje"),
                            rx.table.column_header_cell("Origen"),
                            rx.table.column_header_cell("Destino"),
                            rx.table.column_header_cell("Millas Carg."),
                            rx.table.column_header_cell("Millas Vacías"),
                            rx.table.column_header_cell("Rate"),
                            rx.table.column_header_cell("Fecha"),
                            rx.table.column_header_cell("Viaje Tipo"),
                            rx.table.column_header_cell("Internacional"),
                            rx.table.column_header_cell("TIPO"),
                            rx.table.column_header_cell("STATUS")
                        )
                    ),
                    rx.table.body(
                        rx.foreach(State.viajes_data, render_viaje_row)
                    )
                ),
                # Paginación del modal
                rx.hstack(
                    rx.button("Anterior", on_click=State.prev_viajes_page, disabled=State.viajes_page <= 1),
                    rx.text(f"Página {State.viajes_page} de {((State.viajes_total_items -1) // State.viajes_limit) + 1}"),
                    rx.button("Siguiente", on_click=State.next_viajes_page, disabled=(State.viajes_page * State.viajes_limit) >= State.viajes_total_items),
                    justify="center",
                    width="100%",
                    margin_top="1"
                ),
                rx.hstack(
                    rx.dialog.close(
                        rx.button("Cerrar")
                        ),
                        justify="center",
                        width="100%",
                        margin_top="1em"
                ),
            ),
            style={"max_width": "1000px"}
        ),
        # El modal se abre si la variable de estado es "viajes"
        open=(State.modal_abierto == "viajes"),
        on_open_change=lambda _: State.cerrar_modal()
    )