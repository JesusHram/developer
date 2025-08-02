from ast import expr_context
from fastapi import FastAPI, HTTPException, Query
import pymysql
from pymysql.cursors import DictCursor
from fastapi.middleware.cors import CORSMiddleware
from datetime import date, datetime
import httpx
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="API Developer",
    version="1.0",
    description="API para la aplicación de desarrolladores",
)

# Configura CORS para permitir conexiones desde Reflex
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

db_host = os.getenv("DB_HOST")
db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")
db_name = os.getenv("DB_NAME")
db_port = 3306

@app.get("/")
def read_root():
    return {"message": "API funcionando"}

def getConnection():
    return pymysql.connect(
        host=db_host,
        user=db_user,
        password=db_password,
        db=db_name,
        port=db_port,
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
        

@app.get("/reporte-clientes/")
async def get_reporte_clientes(
    fecha_inicio: date = Query(None),
    fecha_fin: date = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    sucursal: Optional[str] = Query(None)
):
    print(f"\n>>> API RECIBIÓ PETICIÓN PARA PÁGINA: {page}")
    # Parámetros para la subconsulta (actividad)
    subquery_params = []
    subquery_conditions = ["emb.intOcupado != 0"]
    if fecha_inicio:
        subquery_conditions.append("DATE(emb.dateFechaRecoleccion) >= %s")
        subquery_params.append(fecha_inicio)
    if fecha_fin:
        subquery_conditions.append("DATE(emb.dateFechaRecoleccion) <= %s")
        subquery_params.append(fecha_fin)
    
    subquery_where_sql = "WHERE " + " AND ".join(subquery_conditions)

    # Parámetros para la consulta principal (clientes)
    main_params = []
    main_conditions = []
    if search:
        main_conditions.append("cl.strNombreCte LIKE %s")
        main_params.append(f"%{search}%")
    if sucursal:
        main_conditions.append("cl.intSucursal = %s")
        main_params.append(sucursal)
        
    main_where_sql = ("WHERE " + " AND ".join(main_conditions)) if main_conditions else ""
    
    try:
        with getConnection() as conn:
            with conn.cursor() as cursor:
                # El conteo se hace sobre la consulta principal de clientes
                count_query = f"SELECT COUNT(*) as total FROM clientes cl {main_where_sql}"
                cursor.execute(count_query, main_params)
                total_count = cursor.fetchone()['total']

                offset = (page - 1) * limit
                data_query = f"""
                    SELECT
                        cl.intIdCliente,
                        cl.strNombreCte,
                        COALESCE(metrics.Viajes, 0) as Viajes,
                        COALESCE(metrics.millasCargadas, 0) as millasCargadas,
                        COALESCE(metrics.millasVacias, 0) as millasVacias,
                        COALESCE(metrics.Rate, 0) as Rate,
                        COALESCE(metrics.NB, 0) AS NB,
                        COALESCE(metrics.SB, 0) AS SB,
                        COALESCE(metrics.rate_perMile, 0) as rate_perMile,
                        IF(cl.intSucursal = 1, 'RAM','ZARO') as Sucursal
                    FROM
                        clientes cl
                    LEFT JOIN (
                        SELECT
                            emb.intIdCliente,
                            COUNT(v.intIdViaje) as Viajes,
                            SUM(emb.floatDistanciaGoogle) as millasCargadas,
                            SUM(v.strMillasVacias) as millasVacias,
                            SUM(emb.strRate) as Rate,
                            COUNT(IF(emb.intDirEntraSale = 2, 1, NULL)) AS NB,
                            COUNT(IF(emb.intDirEntraSale = 1, 1, NULL)) AS SB,
                            CASE
                                WHEN SUM(emb.floatDistanciaGoogle + v.strMillasVacias) > 0
                                THEN SUM(emb.strRate) / SUM(emb.floatDistanciaGoogle + v.strMillasVacias)
                                ELSE 0
                            END as rate_perMile
                        FROM
                            embarques emb
                        INNER JOIN
                            viajes_embarques ve ON emb.intIdEmbarque = ve.intIdEmbarque
                        INNER JOIN
                            viajes v ON ve.intIdViaje = v.intIdViaje
                        {subquery_where_sql}
                        GROUP BY
                            emb.intIdCliente
                    ) AS metrics ON cl.intIdCliente = metrics.intIdCliente
                    {main_where_sql}
                    ORDER BY
                        cl.strNombreCte
                    LIMIT %s OFFSET %s
                """
                
                final_params = subquery_params + main_params + [limit, offset]
                
                cursor.execute(data_query, final_params)
                results = cursor.fetchall()
                
                
                print(f">>> CALCULANDO OFFSET: {offset} (para página {page})")
                
                total_millas_Cargadas = sum(row.get('millasCargadas', 0) for row in results)
                total_millas_Vacias = sum(row.get('millasVacias', 0) for row in results)
                total_rate = sum(row.get('Rate', 0) for row in results)
                
                millas_totales = total_millas_Cargadas + total_millas_Vacias
                rate_per_mile_general = (total_rate / millas_totales) if millas_totales > 0 else 0
                

                grand_totals = {
                    "total_millas": millas_totales,
                    "millasVacias": total_millas_Vacias,
                    "total_rate": total_rate,
                    "rate_perMile": rate_per_mile_general,
                    "NB": sum(row.get('NB', 0) for row in results),
                    "SB": sum(row.get('SB', 0) for row in results),
                }

                
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
    limit: int = Query(10, ge=1, le=100, description="Registros por página"),
    sucursal: Optional[str] = Query(None)
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
    if sucursal:
        conditions.append("e.intSucursal = %s")
        params.append(sucursal)

    conditions.append("v.intIdViaje IS NOT NULL")
    
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
                        CASE
                            WHEN e.intDirEntraSale = 1 THEN 'NB'
                            WHEN e.intDirEntraSale = 2 THEN 'SB'
                        END AS ViajeTipo,
                    CASE
                        WHEN e.intInternacional = 1 OR e.intIdEmbarqueInternacional > 0 THEN 'Internacional'
                        ELSE 'Nacional'
                    END AS Internacional,
                    CASE
                        WHEN e.intInternacional = 1 OR e.intIdEmbarqueInternacional > 0 THEN
                            CASE
                                WHEN e.intDirEntraSale = 1 THEN 'NB D2D'
                                WHEN e.intDirEntraSale = 2 THEN 'SB D2D'
                            END
                        ELSE
                            CASE
                                WHEN e.intDirEntraSale = 1 THEN 'NB'
                                WHEN e.intDirEntraSale = 2 THEN 'SB'
                            END
                    END AS TIPO,
                    CASE
                        WHEN e.intCargado = 1 AND e.intTrompo = 0 AND e.intVacio = 0 THEN 'Cargado'
                        WHEN e.intVacio = 1 AND e.intCargado = 0 AND e.intTrompo = 0 THEN 'Vacío'
                        WHEN e.intTrompo = 1 AND e.intCargado = 0 AND e.intVacio = 0 THEN 'Trompo'
                        ELSE 'Desconocido'
                    END AS STATUS
                    {base_query}
                    ORDER BY e.dateFechaRecoleccion DESC
                    LIMIT %s OFFSET %s
                """
                # Agregamos los parámetros de paginación al final
                data_params = params + [limit, offset]
                cursor.execute(data_query, data_params)
                
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
            COALESCE(SUM(CASE WHEN DATE(emb.dateFechaRecoleccion) BETWEEN %s AND %s THEN emb.strRate ELSE 0 END), 0) as Rate_A,
            COALESCE(SUM(CASE WHEN DATE(emb.dateFechaRecoleccion) BETWEEN %s AND %s THEN emb.floatDistanciaGoogle ELSE 0 END), 0) as Millas_A,
            COUNT(CASE WHEN DATE(emb.dateFechaRecoleccion) BETWEEN %s AND %s THEN v.intIdViaje END) as Viajes_A,

            -- Agregación Condicional para el Periodo B
            COALESCE(SUM(CASE WHEN DATE(emb.dateFechaRecoleccion) BETWEEN %s AND %s THEN emb.strRate ELSE 0 END), 0) as Rate_B,
            COALESCE(SUM(CASE WHEN DATE(emb.dateFechaRecoleccion) BETWEEN %s AND %s THEN emb.floatDistanciaGoogle ELSE 0 END), 0) as Millas_B,
            COUNT(CASE WHEN DATE(emb.dateFechaRecoleccion) BETWEEN %s AND %s THEN v.intIdViaje END) as Viajes_B
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
            cl.intSucursal,
            IF(cl.intSucursal = 1, 'RAM', 'ZARO') as strNombreSucursal
        FROM clientes cl
        WHERE cl.intSucursal IN (1,2)
    """
    try:
        with getConnection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                results = cursor.fetchall()
                return {"data": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    
@app.get("/reporte-camiones/")
async def get_reporte_camiones():
    
    query = """
    """
    try:
        with getConnection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                results = cursor.fetchall()
                return {"data": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))