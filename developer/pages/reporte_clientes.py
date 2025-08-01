from developer.components.layout import layout
from developer.components.viajes_modal import viajes_modal
from developer.components.comparativa_modal import comparativa_modal
from developer.state import State
import reflex as rx
from datetime import datetime
import httpx
from typing import List


def reporte_clientes():
    """
    Renderiza la página principal del reporte de clientes, incluyendo
    filtros, una tabla principal paginada y un modal de detalles.
    """
    
    def render_acciones(row: dict):
        """Crea el menú desplegable de acciones para cada fila."""
        return rx.dropdown_menu.root(
            rx.dropdown_menu.trigger(
                rx.button("Acciones", size="1")
            ),
            rx.dropdown_menu.content(
                rx.dropdown_menu.item(
                    "Ver Viajes", 
                    on_click=lambda: State.abrir_modal("viajes", row),
                ),
                rx.dropdown_menu.item("Comparativa", on_click=lambda: State.abrir_modal("comparativa", row)),
                rx.dropdown_menu.item("Editar Cliente (Próximamente)", disabled=True),
                rx.dropdown_menu.separator(),
                rx.dropdown_menu.item("Eliminar", color_scheme="red", disabled=True)
            )
        )

    def render_row(row: dict):
        """Crea una fila completa para la tabla de clientes."""
        return rx.table.row(
            rx.table.cell((row["intIdCliente"])),
            rx.table.cell(row["strNombreCte"]),
            rx.table.cell((row["Viajes"])),
            rx.table.cell((row["millasCargadas"])),
            rx.table.cell((row["millasVacias"])),
            rx.table.cell((row["Rate"])),
            rx.table.cell((row["rate_perMile"])),
            rx.table.cell((row["NB"])),
            rx.table.cell((row["SB"])),
            rx.table.cell((row["Sucursal"])),
            rx.table.cell(render_acciones(row))
        )

    return layout(
        rx.vstack(
            rx.heading("Reporte de Clientes", size="5"),
            # Filtros y Búsqueda
            rx.center(
                rx.card(
                    rx.hstack(
                        rx.input(type="date", value=State.fecha_inicio, on_change=State.set_fecha_inicio, disabled=State.loading),
                        rx.text("a"),
                        rx.input(type="date", value=State.fecha_fin, on_change=State.set_fecha_fin, disabled=State.loading),
                        rx.input(placeholder="Buscar por nombre...", value=State.search_query, on_change=State.set_search_query, margin_left="2em", disabled=State.loading),
                        #rx.text(f"Periodo de fechas: {State.fecha_inicio} a {State.fecha_fin}"),
                        rx.select.root(
                            rx.select.trigger(placeholder="Todas las Sucursales"),
                            rx.select.content(
                                rx.foreach(
                                    State.sucursal_options,
                                    lambda option: rx.select.item(
                                        option["label"],
                                        value=option["value"],
                                        key=option["value"]
                                    )
                                ),
                            ),
                            value=State.sucursal,
                            on_change=State.on_sucursal_change,
                            disabled=State.loading,
                            margin_left="1em",
                        ),
                        rx.button("Aplicar Filtros", on_click=State.cargar_reporte,disabled=State.loading),
                        rx.button ("Limpiar Filtros", 
                                   on_click=State.limpiar_filtros,
                                   color_scheme="red",
                                   disabled=State.loading),
                        spacing="3",
                        width="100%",
                        margin_bottom="1",
                    ),
                ),
            ),
            # Tabla Principal dentro de una Card
            rx.card(   
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell("ID Cliente"),
                            rx.table.column_header_cell("Nombre Cliente"),
                            rx.table.column_header_cell("Total Viajes"),
                            rx.table.column_header_cell("Millas Cargadas"),
                            rx.table.column_header_cell("Millas Vacías"),
                            rx.table.column_header_cell("Rate Total"),
                            rx.table.column_header_cell("Rate/Milla con vacias"),
                            rx.table.column_header_cell("NB"),
                            rx.table.column_header_cell("SB"),
                            rx.table.column_header_cell("Sucursal"),
                            rx.table.column_header_cell("Acciones"),
                        )
                    ),
                    rx.table.body(
                        rx.foreach(State.reporte_data, render_row)
                    ),
                    variant="surface",
                    size="2",
                    width="100%",
                ),
                width="100%"
            ),
            
            # Paginación de la Tabla Principal
            rx.hstack(
                rx.button("Anterior", on_click=State.prev_page, disabled=State.prev_disabled),
                rx.text(f"Página {State.page} de {State.total_pages}"),
                rx.button("Siguiente", on_click=State.next_page, disabled=State.next_disabled),
                justify="center",
                align="center",
                width="100%",
                margin_top="1"
            ),
            
            rx.card(
                rx.table.root(
                        rx.table.row(
                            rx.table.cell(f"Millas Cargadas: {State.grand_totals.get('total_millas', 0)}"),
                            rx.table.cell(f"Millas Vacias: {State.grand_totals.get('millasVacias', 0)}"),
                            rx.table.cell(f"Rate Total: {State.grand_totals.get('total_rate', 0)}"),
                            rx.table.cell(f"Rate/Milla con vacias: {State.grand_totals.get('rate_perMile', 0)}"),
                            rx.table.cell(f"NB: {State.grand_totals.get('NB', 0)}"),
                            rx.table.cell(f"SB: {State.grand_totals.get('SB', 0)}"),
                        ),
                ),
            spacing="3"
            ),
            
            # El componente del modal se llama aquí
            viajes_modal(),
            comparativa_modal(),
            
            # Propiedades del contenedor principal
            spacing="3",
            width="100%",
            padding="2",
            on_mount=State.on_load,
        )
    )
