import numpy as np
from scipy import stats
import pickle
from typing import Dict
from fastapi import FastAPI


# Función para preparar los datos en una matriz numpy
def preparacion_datos(datos: Dict) -> np.ndarray:
    """Convierte un diccionario de datos en una matriz NumPy de 2 columnas."""
    # Usar una lista por comprensión es más conciso y a menudo más rápido.
    return np.array([[v["año"], v["precio"]] for v in datos.values()])
   
    # Se puede usar un bucle for explícito para mayor claridad.
    # matriz = []
    
    # for d in datos:
    #    matriz.append([datos[d]["año"], datos[d]["precio"]])
        
    # return np.array(matriz) """

# Función para calcular el porcentaje de elementos dentro del intervalo z-score
def z_score(arr: np.ndarray, z: float) -> float:
    """Calcula el porcentaje de elementos dentro de un intervalo z-score."""
    media = np.mean(arr)
    est = np.std(arr)

    li = media - z * est
    ld = media + z * est

    outliers_count = np.sum((arr < li) | (arr > ld))
    dentro = round((((len(arr) - outliers_count) / len(arr)) * 100), 2)
    return dentro

# Función para estandarizar y escalar los datos
def standard_scaler(arr: np.ndarray) -> np.ndarray:
    """Aplica la estandarización Z-score de forma vectorizada."""
    media = np.mean(arr)
    est = np.std(arr)
    # La operación se aplica a todo el array a la vez, mucho más rápido que un bucle.
    return (arr - media) / est

# Función para calcular la correlación de Pearson
def pearson_corr(var1: np.ndarray, var2: np.ndarray) -> float:
    """Calcula el coeficiente de correlación de Pearson."""
    return stats.pearsonr(var1, var2)[0]

# Función para la transformación logarítmica
def log_trans(arr: np.ndarray) -> np.ndarray:
    """Aplica una transformación logarítmica al array."""
    return np.log(arr)

###############################################################################
# Carga de datos y configuración de la API
###############################################################################

# Cargar los datos una sola vez al iniciar la app
# Esto evita leer el archivo del disco en cada petición a la API.
try:
    with open("data_sample.pkl", "br") as archivo:
        datos_cargados = pickle.load(archivo)
    
    # Pre-procesamos los datos para tenerlos listos
    MATRIZ_DATOS = preparacion_datos(datos_cargados)
    COL_ANYOS = MATRIZ_DATOS.T[0]
    COL_PRECIOS = MATRIZ_DATOS.T[1]

except FileNotFoundError:
    print("ERROR: El archivo 'data_sample.pkl' no se encontró. La API no podrá funcionar correctamente.")
    MATRIZ_DATOS, COL_ANYOS, COL_PRECIOS = None, None, None

app = FastAPI(
    title="API de Análisis Estadístico de Precios de Coches",
    description="Una API para analizar la relación entre el año y el precio de los coches.",
    version="1.0.0"
)

@app.get("/")
def root():
    """Ruta raíz de bienvenida a la API."""
    return {
        "mensaje": "Bienvenido a la API de Análisis Estadístico de Precios de Coches",
        "version": "1.0.0",
        "rutas_disponibles": {
            "/": "Esta ruta (información de bienvenida)",
            "/analisis": "Realiza el análisis estadístico completo",
            "/docs": "Documentación interactiva (Swagger UI)",
            "/redoc": "Documentación alternativa (ReDoc)"
        }
    }

@app.get("/analisis")
def analizar_datos(z: int = 3):
    """
    Realiza un análisis estadístico completo sobre los datos de coches.
    """
    if MATRIZ_DATOS is None:
        return {"error": "Los datos no pudieron ser cargados al iniciar el servidor."}

    # Los cálculos se hacen sobre los datos ya cargados en memoria
    std_anyos = standard_scaler(COL_ANYOS)
    std_precios = standard_scaler(COL_PRECIOS)
    log_precios = log_trans(COL_PRECIOS)

    return {
        "1. Identificacion de Outliers (z-score)": {
            "z_value": z,
            "porcentaje_dentro_intervalo_anyos": f"{z_score(COL_ANYOS, z)}%",
            "porcentaje_dentro_intervalo_precios": f"{z_score(COL_PRECIOS, z)}%"
        },
        "2. Correlacion de Pearson (Datos Estandarizados)": {
            "correlacion_anyos_precios": pearson_corr(std_anyos, std_precios)
        },
        "3. Correlacion de Pearson (con Transformacion Logaritmica)": {
            "descripcion": "Correlación entre los años estandarizados y el logaritmo de los precios.",
            "correlacion_anyos_log_precios": pearson_corr(std_anyos, log_precios)
        }
    }