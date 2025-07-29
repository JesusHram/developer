import reflex as rx
from developer.state import State

def comparativa_modal():
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Comparativa de Periodos"),
            rx.vstack(
                # Entradas de fecha
                rx.hstack(
                    rx.input(type="date", value=State.fecha_inicio_a, on_change=State.set_fecha_inicio_a),
                    rx.text("a"),
                    rx.input(type="date", value=State.fecha_fin_a, on_change=State.set_fecha_fin_a),
                ),
                rx.text("vs."),
                rx.hstack(
                    rx.input(type="date", value=State.fecha_inicio_b, on_change=State.set_fecha_inicio_b),
                    rx.text("a"),
                    rx.input(type="date", value=State.fecha_fin_b, on_change=State.set_fecha_fin_b),
                ),
                rx.button("Comparar", on_click=State.cargar_comparativa, margin_y="1"),

                rx.cond(
                    State.comparativa_error,
                    rx.callout(
                        State.comparativa_error,
                        icon="alert_triangle",
                        color_scheme="red",
                        role="alert",
                        width="100%",
                    ),
                ),
                # Resultados
                rx.cond(
                    State.comparativa_data,
                    rx.card(
                        rx.table.root(
                            rx.table.header(
                                rx.table.row(
                                    rx.table.column_header_cell("Métrica"),
                                    rx.table.column_header_cell("Periodo A"),
                                    rx.table.column_header_cell("Periodo B"),
                                    rx.table.column_header_cell("Diferencia"),
                                )
                            ),
                            rx.table.body(
                                rx.table.row(
                                    rx.table.cell("Total Viajes"),
                                    rx.table.cell(State.comparativa_data.get("Viajes_A", 0)),
                                    rx.table.cell(State.comparativa_data.get("Viajes_B", 0)),
                                    rx.table.cell(f"{State.viajes_diferencia}"),
                                ),
                                rx.table.row(
                                    rx.table.cell("Total Rate"),
                                    rx.table.cell(f"${State.comparativa_data.get('Rate_A', 0):,.2f}"),
                                    rx.table.cell(f"${State.comparativa_data.get('Rate_B', 0):,.2f}"),
                                    rx.table.cell(f"${State.rate_diferencia:,.2f}"),
                                ),
                            ),
                        )
                    )
                ),
                rx.hstack(
                    rx.dialog.close(
                        rx.button("Cerrar")
                        ),
                        justify="center",
                        width="100%",
                        margin_top="1em"
                ),
                spacing="3",
            ),
        ),
        open=(State.modal_abierto == "comparativa"),
        on_open_change=lambda _: State.cerrar_modal()
    )