from ast import expr_context
from fastapi import FastAPI, HTTPException, Query
import pymysql
from pymysql.cursors import DictCursor
from fastapi.middleware.cors import CORSMiddleware
from datetime import date, datetime
import httpx
from typing import Optional

app = FastAPI()

# Configura CORS para permitir conexiones desde Reflex
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "API funcionando"}

def getConnection():
    return pymysql.connect(
        host='52.12.110.149',
        user='newvirus',
        password='3d462a1b271d-4fc4-4c2748f0-9422-fb9f2f3d137d81bd',
        db='admin_zaroprod',
        port=3306,
        charset='latin1',
        cursorclass=pymysql.cursors.DictCursor
    )
    
@app.get("/choferes")
def get_choferes():
    conn = getConnection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    CAST(intIdChofer AS CHAR) as id,
                    CAST(strNombreChofer AS CHAR) as nombre,
                    IFNULL(CAST(strCiudadChofer AS CHAR), '') as ciudad
                FROM choferes
            """)
            resultados = cursor.fetchall()
            
            # Limpieza adicional de datos (por si hay caracteres extraños)
            datos_limpios = []
            for fila in resultados:
                fila_limpia = {k: v.strip() if isinstance(v, str) else str(v) for k, v in fila.items()}
                datos_limpios.append(fila_limpia)
            
            return {"data": datos_limpios}
    finally:
        conn.close()
        
@app.get("/viajes")
def get_viajes():
    conn = getConnection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT *
                FROM viajes
            """)
            resultados = cursor.fetchall()
            
            # Limpieza adicional de datos (por si hay caracteres extraños)
            datos_limpios = []
            for fila in resultados:
                fila_limpia = {k: v.strip() if isinstance(v, str) else str(v) for k, v in fila.items()}
                datos_limpios.append(fila_limpia)
            
            return {"data": datos_limpios}
    finally:
        conn.close()
        
@app.get("/clientes")
def get_clientes():
    conn = getConnection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT *
                FROM clientes
            """)
            resultados = cursor.fetchall()
            
            # Limpieza adicional de datos (por si hay caracteres extraños)
            datos_limpios = []
            for fila in resultados:
                fila_limpia = {k: v.strip() if isinstance(v, str) else str(v) for k, v in fila.items()}
                datos_limpios.append(fila_limpia)
            
            return {"data": datos_limpios}
    finally:
        conn.close()
        
@app.get("/embarques")
def embarques():
    conn = getConnection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT *
                FROM embarques e 
            """)
            resultados = cursor.fetchall()
            # Limpieza adicional de datos (por si hay caracteres extraños)
            datos_limpios = []
            for fila in resultados:
                fila_limpia = {k: v.strip() if isinstance(v, str) else str(v) for k, v in fila.items()}
                datos_limpios.append(fila_limpia)
            
            return {"data": datos_limpios}
    finally:
        conn.close()
        


# En tu archivo de FastAPI

@app.get("/reporte-clientes/")
async def get_reporte_clientes(
    fecha_inicio: date = Query(None),
    fecha_fin: date = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    sucursal: Optional[str] = Query(None)
):
    # 1. La consulta base ahora solo contiene los JOINs y filtros de fecha
    filter_params = []
    join_conditions = []
    
    # Prepara las condiciones de fecha para el JOIN
    if fecha_inicio:
        join_conditions.append("DATE(emb.dateFechaRecoleccion) >= %s")
        filter_params.append(fecha_inicio)
    if fecha_fin:
        join_conditions.append("DATE(emb.dateFechaRecoleccion) <= %s")
        filter_params.append(fecha_fin)
    if sucursal is not None:
        join_conditions.append("emb.intSucursal = %s")
        filter_params.append(sucursal)   
    # Construye las cadenas de texto para las condiciones
    join_conditions_sql = ("AND " + " AND ".join(join_conditions)) if join_conditions else ""
    
    # Prepara la búsqueda por nombre del cliente para el WHERE
    where_conditions = []
    where_params = []
    
    if search:
        where_conditions.append("cl.strNombreCte LIKE %s")
        where_params.append(f"%{search}%")
 
        # --- INICIO DE LA DEPURACIÓN ---
    # Imprime el valor y tipo de 'sucursal' que llega a la API
    print(f">>> DEBUG: Recibido sucursal = {sucursal}, Tipo = {type(sucursal)}")

    if sucursal is not None:
        # Imprime un mensaje si la condición se cumple
        print(f">>> DEBUG: El filtro 'if sucursal' se activó para el valor {sucursal}")
        where_conditions.append("cl.intIdCliente IN (SELECT DISTINCT intIdCliente FROM embarques WHERE intSucursal = %s)")
        where_params.append(sucursal)
    # --- FIN DE LA DEPURACIÓN ---
    
    # Construye las cadenas de texto para las condiciones
    where_conditions_sql = ("WHERE " + " AND ".join(where_conditions)) if where_conditions else ""
    
    try:
        with getConnection() as conn:
            with conn.cursor() as cursor:
                # 2. La consulta de conteo ahora es más simple: cuenta clientes
                count_query = f"SELECT COUNT(*) as total FROM clientes cl {where_conditions_sql}"
                cursor.execute(count_query, where_params)
                total_count = cursor.fetchone()['total']           
                
                # 3. La consulta de datos principal, reescrita
                offset = (page - 1) * limit
                data_query = f"""
                    SELECT 
                        cl.intIdCliente,
                        cl.strNombreCte, 
                        ROUND(COALESCE(COUNT(v.intIdViaje), 0), 2) as Viajes,
                        ROUND(COALESCE(SUM(emb.floatDistanciaGoogle), 0), 2) as millasCargadas,
                        ROUND(COALESCE(SUM(v.strMillasVacias), 0), 2) as millasVacias,
                        ROUND(COALESCE(SUM(emb.strRate), 0), 2) as Rate,
                        COALESCE(SUM(emb.floatDistanciaGoogle + v.strMillasVacias), 0) as millasTotales,
                        COUNT(IF(intDirEntraSale=2,1,NULL)) AS NB,
                        COUNT(IF(intDirEntraSale=1,1,NULL)) AS SB,
                        CASE 
                            WHEN SUM(emb.floatDistanciaGoogle + v.strMillasVacias) > 0 
                            THEN ROUND(COALESCE(SUM(emb.strRate), 0) / (SUM(emb.floatDistanciaGoogle + v.strMillasVacias)), 0)    
                            ELSE 0
                        END as rate_perMile,
                        IF(emb.intSucursal = 1, 'RAM','ZARO') as Sucursal
                    FROM 
                        clientes cl
                    LEFT JOIN 
                        embarques emb ON cl.intIdCliente = emb.intIdCliente {join_conditions_sql}
                    LEFT JOIN 
                        viajes_embarques ve ON emb.intIdEmbarque = ve.intIdEmbarque
                    LEFT JOIN 
                        viajes v ON ve.intIdViaje = v.intIdViaje
                    {where_conditions_sql}
                    GROUP BY 
                        cl.intIdCliente, cl.strNombreCte
                    ORDER BY 
                        cl.strNombreCte
                    LIMIT %s OFFSET %s
                """
                # Los parámetros son los de la búsqueda + los de la fecha + la sucursal + los de paginación
                final_params = filter_params + where_params + [limit, offset]
                cursor.execute(data_query, final_params)
                results = cursor.fetchall()
                
                #Nueva Consulta para totales
                grand_totals_query = f"""
                    SELECT
                        COALESCE(SUM(sub.Viajes), 0) as total_viajes,
                        COALESCE(SUM(sub.millasCargadas), 0) as total_millas,
                        COALESCE(SUM(sub.Rate), 0) as total_rate,
                        COALESCE(SUM(sub.millasVacias), 0) as millasVacias,
                        COALESCE(SUM(sub.NB), 0) as NB,
                        COALESCE(SUM(sub.SB), 0) as SB,
                        COALESCE(SUM(sub.rate_perMile), 0) as rate_perMile
                    FROM (
                        SELECT 
                            COUNT(v.intIdViaje) as Viajes,
                            SUM(emb.floatDistanciaGoogle) as millasCargadas,
                            SUM(emb.strRate) as Rate,
                            SUM(v.strMillasVacias) as millasVacias,
                            COUNT(IF(intDirEntraSale=2,1,NULL)) AS NB,
                            COUNT(IF(intDirEntraSale=1,1,NULL)) AS SB,
                            CASE 
                            WHEN SUM(emb.floatDistanciaGoogle + v.strMillasVacias) > 0 
                            THEN ROUND(COALESCE(SUM(emb.strRate), 0) / (SUM(emb.floatDistanciaGoogle + v.strMillasVacias)), 0)    
                            ELSE 0
                        END as rate_perMile
                        FROM clientes cl
                        LEFT JOIN embarques emb ON cl.intIdCliente = emb.intIdCliente {join_conditions_sql}
                        LEFT JOIN viajes_embarques ve ON emb.intIdEmbarque = ve.intIdEmbarque
                        LEFT JOIN viajes v ON ve.intIdViaje = v.intIdViaje
                        {where_conditions_sql}
                        GROUP BY cl.intIdCliente
                    ) as sub
                """
                totals_params =filter_params + where_params
                cursor.execute(grand_totals_query, totals_params)
                grand_totals = cursor.fetchone()

                # La respuesta sigue teniendo la misma estructura
                return {
                    "total": total_count,
                    "page": page,
                    "limit": limit,
                    "data": results,
                    "grand_totals": grand_totals
                }

    except Exception as e:
        print(f"Error en la base de datos: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
# Endpoint para detalle de viajes por cliente
@app.get("/viajes-cliente/{id_cliente}")
async def get_viajes_cliente(
    id_cliente: int,
    fecha_inicio: date = Query(None),
    fecha_fin: date = Query(None),
    page: int = Query(1, ge=1, description="Número de página"),
    limit: int = Query(10, ge=1, le=100, description="Registros por página")
):
    # --- 1. Construir la base de la consulta y los filtros ---
    base_query = """
        FROM embarques e
        LEFT JOIN viajes_embarques ve ON ve.intIdEmbarque = e.intIdEmbarque
        LEFT JOIN viajes v ON v.intIdViaje = ve.intIdViaje
        WHERE e.intIdCliente = %s
    """
    params = [id_cliente]
    
    conditions = []
    if fecha_inicio:
        conditions.append("DATE(e.dateFechaRecoleccion) >= %s")
        params.append(fecha_inicio)
    if fecha_fin:
        conditions.append("DATE(e.dateFechaRecoleccion) <= %s")
        params.append(fecha_fin)

    if conditions:
        base_query += " AND " + " AND ".join(conditions)

    try:
        with getConnection() as conn:
            with conn.cursor() as cursor:
                # --- 2. Ejecutar la consulta para el conteo total ---
                count_query = f"SELECT COUNT(*) as total {base_query}"
                cursor.execute(count_query, params)
                total_count = cursor.fetchone()['total']

                # --- 3. Ejecutar la consulta para los datos paginados ---
                offset = (page - 1) * limit
                data_query = f"""
                    SELECT
                        v.intIdViaje,
                        e.strCiudadDe as Origen,
                        e.strCiudadPara as Destino,
                        e.floatDistanciaGoogle,
                        v.strMillasVacias,
                        e.strRate,
                        e.dateFechaRecoleccion as FechaRecoleccion,
                        IF(e.intDirEntraSale=2,'NB','SB') as ViajeTipo
                    {base_query}
                    ORDER BY e.dateFechaRecoleccion DESC
                    LIMIT %s OFFSET %s
                """
                # Agregamos los parámetros de paginación al final
                data_params = params + [limit, offset]
                cursor.execute(data_query, data_params)
                
                # Asumiendo que usas un DictCursor como en los ejemplos anteriores
                results = cursor.fetchall()
                
                return {
                    "total": total_count,
                    "page": page,
                    "limit": limit,
                    "data": results,
                    "sucursal": sucursal
                }
    except Exception as e:  
        raise HTTPException(status_code=500, detail=str(e))
    
    
    
@app.get("/comparativa-cliente/{id_cliente}")
async def get_comparativa_cliente(
    id_cliente: int,
    fecha_inicio_a: date = Query(..., description="Inicio del Periodo A"),
    fecha_fin_a: date = Query(..., description="Fin del Periodo A"),
    fecha_inicio_b: date = Query(..., description="Inicio del Periodo B"),
    fecha_fin_b: date = Query(..., description="Fin del Periodo B")
):
    query = """
        SELECT
            cl.strNombreCte,
            -- Agregación Condicional para el Periodo A
            COALESCE(SUM(CASE WHEN emb.dateFechaRecoleccion BETWEEN %s AND %s THEN emb.strRate ELSE 0 END), 0) as Rate_A,
            COALESCE(SUM(CASE WHEN emb.dateFechaRecoleccion BETWEEN %s AND %s THEN emb.floatDistanciaGoogle ELSE 0 END), 0) as Millas_A,
            COUNT(CASE WHEN emb.dateFechaRecoleccion BETWEEN %s AND %s THEN v.intIdViaje END) as Viajes_A,

            -- Agregación Condicional para el Periodo B
            COALESCE(SUM(CASE WHEN emb.dateFechaRecoleccion BETWEEN %s AND %s THEN emb.strRate ELSE 0 END), 0) as Rate_B,
            COALESCE(SUM(CASE WHEN emb.dateFechaRecoleccion BETWEEN %s AND %s THEN emb.floatDistanciaGoogle ELSE 0 END), 0) as Millas_B,
            COUNT(CASE WHEN emb.dateFechaRecoleccion BETWEEN %s AND %s THEN v.intIdViaje END) as Viajes_B
        FROM
            clientes cl
        LEFT JOIN
            embarques emb ON cl.intIdCliente = emb.intIdCliente
        LEFT JOIN
            viajes_embarques ve ON emb.intIdEmbarque = ve.intIdEmbarque
        LEFT JOIN
            viajes v ON ve.intIdViaje = v.intIdViaje
        WHERE
            cl.intIdCliente = %s
        GROUP BY
            cl.intIdCliente, cl.strNombreCte;
    """
    
    # El orden de los parámetros debe coincidir exactamente con los %s en la consulta
    params = [
        fecha_inicio_a, fecha_fin_a, # Periodo A - Rate
        fecha_inicio_a, fecha_fin_a, # Periodo A - Millas
        fecha_inicio_a, fecha_fin_a, # Periodo A - Viajes
        fecha_inicio_b, fecha_fin_b, # Periodo B - Rate
        fecha_inicio_b, fecha_fin_b, # Periodo B - Millas
        fecha_inicio_b, fecha_fin_b, # Periodo B - Viajes
        id_cliente
    ]
    
    try:
        with getConnection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                result = cursor.fetchone()
                if not result:
                    raise HTTPException(status_code=404, detail="Cliente no encontrado")
                return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/sucursales/")
async def get_sucursales():
    query = """
        SELECT DISTINCT
            emb.intSucursal,
            IF(emb.intSucursal = 1, 'RAM', 'ZARO') as strNombreSucursal
        FROM embarques emb
        WHERE emb.intSucursal IN (1,2)
    """
    try:
        with getConnection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                results = cursor.fetchall()
                return {"data": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))