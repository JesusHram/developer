import reflex as rx
import httpx
from typing import List, Optional

class State(rx.State):
    reporte_data: List[dict] = []
    viajes_data: List[dict] = []
    grand_totals: dict = {}
    loading: bool = False
    error: str = ""
    modal_abierto: str = ""
    selected_cliente: dict = {}
    fecha_inicio: str = ""
    fecha_fin: str = ""
    search_query: str = "" 
    
    # Paginación
    page: int = 1
    limit: int = 10
    total_items: int = 0
    
    #Variables de comparacion
    fecha_inicio_a: str = ""
    fecha_fin_a: str = ""
    fecha_inicio_b: str = ""
    fecha_fin_b: str = ""
    comparativa_data: dict = {}
    comparativa_error: str = ""
    sucursal: Optional[str] = ""
    sucursales_list: List[dict] = []

    
    @rx.var
    def viajes_diferencia(self) -> int:
        """Calcula la diferencia de viajes entre los dos periodos."""
        viajes_a = self.comparativa_data.get("Viajes_A", 0)
        viajes_b = self.comparativa_data.get("Viajes_B", 0)
        return viajes_b - viajes_a
    
    @rx.var
    def rate_diferencia(self) -> float:
        """Calcula la diferencia de rate entre los dos periodos."""
        rate_a = self.comparativa_data.get("Rate_A", 0)
        rate_b = self.comparativa_data.get("Rate_B", 0)
        return rate_b - rate_a
    
    @rx.var
    def sumMillasCargadas(self) -> float:
        "Calcula la suma total de milals Cargadas"
        if not self.reporte_data:
            return 0.0
        return sum(float(cliente.get("MillasCargadas", 0)) for cliente in self.reporte_data)
    
    @rx.var
    def sucursal_seleccionada_nombre(self) -> str:
        if not self.sucursal:
            return "Selecciona una sucursal..."

        for s in self.sucursales_list:
            if str(s.get("intSucursal")) == self.sucursal:
                return s.get("strNombreSucursal", "Error")
        
        return "Selecciona una sucursal..."
    
    def handle_sucursal_change(self, index: int):
        try: 
            selected_sucursal_dic = self.sucursales_list[index]
            selected_id = str(selected_sucursal_dic["intSucursal"])
            
            print(f"Sucursal seleccionada (por índice {index}): '{selected_id}'")
            
            self.sucursal = selected_id
            self.page = 1
        except IndexError:
            print(f"Error: El índice {index} está fuera de rango.")
    
    def abrir_modal(self, nombre_modal: str, cliente: dict):
        """Abre un modal específico y carga sus datos si es necesario."""
        self.selected_cliente = cliente
        self.modal_abierto = nombre_modal
        
        # Si el modal a abrir es el de "viajes", resetea su paginación y carga los datos.
        if nombre_modal == "viajes":
            self.viajes_page = 1
            yield type(self).cargar_viajes_cliente(cliente)
            
        if nombre_modal == "comparativa":
            self.comparativa_data = {}
            self.comparativa_error = ""
            self.fecha_inicio_a = ""
            self.fecha_fin_a = ""
            self.fecha_inicio_b = ""
            self.fecha_fin_b = ""

    def cerrar_modal(self):
        """Cierra cualquier modal que esté abierto."""
        self.modal_abierto = ""
        # Opcional: Limpia los datos para liberar memoria
        self.viajes_data = []
        self.selected_cliente = {}
    
    def next_page(self):
        # Solo avanza si no estás en la última página
        if (self.page * self.limit) < self.total_items:
            self.page += 1
            yield type(self).cargar_reporte # Llama al evento para recargar

    def prev_page(self):
        # Solo retrocede si no estás en la primera página
        if self.page > 1:
            self.page -= 1
            yield type(self).cargar_reporte # Llama al evento para recargar
    
    viajes_page: int = 1
    viajes_limit: int = 10  # Un límite más pequeño para el modal
    viajes_total_items: int = 0
    
    def next_viajes_page(self):
        """Avanza a la siguiente página de viajes en el modal."""
        if (self.viajes_page * self.viajes_limit) < self.viajes_total_items:
            self.viajes_page += 1
            # Recarga los datos del cliente que ya está seleccionado
            yield type(self).cargar_viajes_cliente(self.selected_cliente)
    
    @rx.var
    def total_pages(self) -> int:
        """Calcula el número total de páginas."""
        if self.total_items == 0:
            return 1
        return ((self.total_items - 1) // self.limit) + 1

    @rx.var
    def prev_disabled(self) -> bool:
        """Determina si el botón 'Anterior' debe estar deshabilitado."""
        return self.page <= 1 or self.loading

    @rx.var
    def next_disabled(self) -> bool:
        """Determina si el botón 'Siguiente' debe estar deshabilitado."""
        return self.page >= self.total_pages or self.loading
    
    
    def prev_viajes_page(self):
        """Retrocede a la página de viajes en el modal."""
        if self.viajes_page > 1:
            self.viajes_page -= 1
            yield type(self).cargar_viajes_cliente(self.selected_cliente)
    
    async def on_load(self):
        yield type(self).cargar_sucursales()
    
    async def cargar_sucursales(self):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get("http://localhost:8000/sucursales/")
            response_data = response.json()
            self.sucursales_list = response_data.get("data", [])
        except Exception as e:
            self.error = f"Error: {str(e)}"
            
    @rx.var
    def sucursal_options(self) -> list[dict]:
        """Prepara la lista completa de opciones para el select."""
        # Empieza con la opción estática para "Todas"
        options = [{"value": "all", "label": "Todas las Sucursales"}]
        
        # Añade las sucursales de la lista
        for s in self.sucursales_list:
            options.append({
                "value": str(s.get("intSucursal")),
                "label": s.get("strNombreSucursal"),
            })
        return options

    def on_sucursal_change(self, selected_value: str):
        if selected_value == "all":
            self.sucursal = ""
        else:
            self.sucursal = selected_value

    async def cargar_reporte(self):
        self.loading = True
        self.error = ""
        try:
            params = {
            "page": self.page,
            "limit": self.limit
            }
            if self.fecha_inicio:
                params["fecha_inicio"] = self.fecha_inicio
            if self.fecha_fin:
                params["fecha_fin"] = self.fecha_fin     
            if self.search_query:
                params["search"] = self.search_query
            if self.sucursal:
                params["sucursal"] = self.sucursal
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "http://localhost:8000/reporte-clientes/",
                    params=params
                )
            response_data = response.json()
            self.reporte_data = response_data.get("data", [])
            self.total_items = response_data.get("total", 0)
            self.grand_totals = response_data.get("grand_totals", {})
                #print("Datos", self.reporte_data)
        except Exception as e:
            self.error = f"Error: {str(e)}"
        finally:
            self.loading = False

    def limpiar_filtros(self):
        self.fecha_inicio = ""
        self.fecha_fin = ""
        self.search_query = ""
        self.sucursal = ""
        self.page = 1
        self.reporte_data = []
        self.total_items = 0
        self.grand_totals = {}

    async def cargar_viajes_cliente(self, cliente: dict): # Acepta el dict completo
        if self.selected_cliente.get("intIdCliente") != cliente.get("intIdCliente"):
            self.viajes_page = 1
            
        self.selected_cliente = cliente
        id_cliente = cliente.get("intIdCliente")
        
        try:
            # CORRECCIÓN: Usa las variables de paginación del modal
            params = {
                "page": self.viajes_page,
                "limit": self.viajes_limit,
            }
            if self.fecha_inicio:
                params["fecha_inicio"] = self.fecha_inicio
            if self.fecha_fin:
                params["fecha_fin"] = self.fecha_fin
            if self.sucursal:
                params["sucursal"] = self.sucursal
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"http://localhost:8000/viajes-cliente/{id_cliente}",
                    params=params
                )
            
            response_data = response.json()
            self.viajes_data = response_data.get("data", [])
            # CORRECCIÓN: Actualiza el total de items del modal
            self.viajes_total_items = response_data.get("total", 0)
            self.show_modal = True
            
        except Exception as e:
            self.error = f"Error al cargar viajes: {str(e)}"

    async def cargar_comparativa(self):
        """Carga los datos para la comparación, validando las fechas primero."""
        self.comparativa_error = "" # Resetea el error
        self.comparativa_data = {}  # Limpia los datos anteriores

        # Validación: Verifica que todas las fechas estén seleccionadas
        if not all([self.fecha_inicio_a, self.fecha_fin_a, self.fecha_inicio_b, self.fecha_fin_b]):
            self.comparativa_error = "Por favor, completa los cuatro campos de fecha."
            return # Detiene la ejecución si faltan fechas

        if not self.selected_cliente:
            self.comparativa_error = "Error: No se ha seleccionado ningún cliente."
            return

        id_cliente = self.selected_cliente.get("intIdCliente")
        params = {
            "fecha_inicio_a": self.fecha_inicio_a,
            "fecha_fin_a": self.fecha_fin_a,
            "fecha_inicio_b": self.fecha_inicio_b,
            "fecha_fin_b": self.fecha_fin_b,
        }
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"http://localhost:8000/comparativa-cliente/{id_cliente}",
                    params=params
                )
            if response.status_code != 200:
                self.comparativa_error = f"Error de API: {response.text}"
                return

            self.comparativa_data = response.json()
        except Exception as e:
            self.comparativa_error = f"Error de conexión: {str(e)}"
            
    @rx.var
    def active_page(self) -> str:
        """Devuelve la ruta de la página actual."""
        return self.router.page.path