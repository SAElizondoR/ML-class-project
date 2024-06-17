import io
from typing import Tuple, List
import requests
from bs4 import BeautifulSoup
import pandas as pd
from tabulate import tabulate

def get_soup(url: str) -> BeautifulSoup:
    """
    Obtener el objeto BeautifulSoup a partir de una URL.

    Args:
    - url (str): La URL de la página web de la que se va a obtener el objeto
    BeautifulSoup.

    Returns:
    - BeautifulSoup: El objeto BeautifulSoup que representa la estructura de la
    página web.
    """
    try:
        response = requests.get(url, timeout=10)
        # Lanza una excepción si hay un error en la solicitud HTTP.
        response.raise_for_status()
        return BeautifulSoup(response.content, 'html.parser')
    except requests.exceptions.RequestException as e:
        print(f"Error al obtener la página web: {e}")
        return None

def get_csv_from_url(url: str) -> pd.DataFrame:
    """
    Carga un archivo CSV desde una URL en una tabla de Pandas.

    Args:
    - url (str): La URL del archivo CSV.

    Returns:
    - pd.DataFrame: Una tabla de Pandas que contiene los datos del archivo CSV.
    """
    try:
        response = requests.get(url, timeout=10)
        # Lanza una excepción si hay un error en la solicitud HTTP
        response.raise_for_status()
        s = response.content
        return pd.read_csv(io.StringIO(s.decode('utf-8')))
    except requests.exceptions.RequestException as e:
        print(f"Error al obtener el archivo CSV desde la URL: {e}")
        return pd.DataFrame()

def print_tabulate(data_frame: pd.DataFrame):
    """
    Imprime una tabla de Pandas.

    Args:
    - data_frame (pd.DataFrame): La tabla de Pandas que se imprimirá.
    """
    print(tabulate(data_frame, headers=data_frame.columns, tablefmt='orgtbl'))


def limpiar_nombre_dependencia(nombre_sucio: str) -> str:
    """
    Limpia el nombre de una dependencia eliminando las dos primeras palabras.

    Args:
    - nombre_sucio (str): El nombre de la dependencia que se va a limpiar.

    Returns:
    - str: El nombre de la dependencia limpio.
    """
    nombre_en_partes = nombre_sucio.split(' ')
    return ' '.join(nombre_en_partes[2:])

def obtener_cantidad_de_filas(data_frame: pd.DataFrame) -> int:
    """
    Obtiene la cantidad de filas en una tabla de Pandas.

    Args:
    - df (pd.DataFrame): La tabla de Pandas de la que se va a obtener la
    cantidad de filas.

    Returns:
    - int: La cantidad de filas en la tabla.
    """
    return len(data_frame.index)

def limpiar_dato_sueldo(sueldo_txt: str) -> float:
    """
    Convierte un sueldo en formato de cadena de caracteres a un valor numérico
    de punto flotante.

    Args:
    - sueldo_txt (str): El sueldo que se va a limpiar.

    Returns:
    - float: El sueldo limpio como un valor numérico.
    """
    return float(sueldo_txt[2:].replace(",", ""))

def get_dependencias_uanl() -> Tuple[List,List[str],List[str]]:
    """
    Obtiene las dependencias, meses y años disponibles en la página de
    transparencia de la UANL.

    Returns:
    - Tuple[List, List[str], List[str]]: Una tupla que contiene la lista de
    dependencias, la lista de meses y la lista de años disponibles.
    """
    enlace = "http://transparencia.uanl.mx/remuneraciones_mensuales/bxd.php"
    soup = get_soup(enlace)
    table = soup.find_all("table")[0].find_all('tr')
    dependencias = [(option['value'], limpiar_nombre_dependencia(option.text))
                    for option in table[1].find_all("option")]
    meses = [option['value'] for option in table[2].find_all('td')[0]
                                                    .find_all("option")]
    anios = [option['value'] for option in table[2].find_all('td')[1]
                                                    .find_all("option")]
    return (dependencias, meses, anios)

def get_pages(periodo: str, area: str) -> List[str]:
    """
    Obtiene los enlaces de las páginas disponibles para un período y área
    específicos.

    Args:
    - período (str): El período para el que se desean obtener los enlaces.
    - area (str): El área para la que se desean obtener los enlaces.

    Returns:
    - List[str]: Lista de los enlaces disponibles.
    """
    enlace = "http://transparencia.uanl.mx/remuneraciones_mensuales/" \
                + f"bxd.php?pag_act=1&id_area_form={area}&mya_det={periodo}"
    soup = get_soup(enlace)
    try:
        links = soup.find_all("table")[1].find_all('a')
    except IndexError as e:
        print(e)
        return []
    return ['1'] + [link.text for link in links]

def get_info_transparencia_uanl(periodo: str, area: str,
                                    page: int = 1) -> pd.DataFrame:
    """
    Obtiene información de transparencia de la UANL para un periodo y área
    específicos.

    Args:
    - periodo (str): El período para el que se desea obtener la información.
    - area (str): El área para la que se desea obtener la información.
    - page (int): El número de página de la que se desea obtener la información
    (opcional, por defecto 1).

    Returns:
    - pd.DataFrame: Una tabla de Pandas que contiene la información obtenida.
    """
    enlace = "http://transparencia.uanl.mx/remuneraciones_mensuales/" \
            + "bxd.php?pag_act={page}&id_area_form={area}&mya_det={periodo}"
    soup = get_soup(enlace)
    table = soup.find_all("table")
    try:
        table_row = table[2].find_all('tr')
        list_of_lists = [[row_column.text.strip()
                            for row_column in row.find_all('td')]
                            for row in table_row]
        data_frame = pd.DataFrame(list_of_lists[1:], columns=list_of_lists[0])
        data_frame["Sueldo Neto"] = data_frame["Sueldo Neto"] \
                                        .transform(limpiar_dato_sueldo)
        data_frame = data_frame.drop(['Detalle'], axis=1)
    except IndexError as e:
        print(f"pagina sin informacion a: {area}, per: {periodo}, page:{page}")
        print(e)
        data_frame = pd.DataFrame()
    return data_frame

def unir_datos(lista_df: List[pd.DataFrame], dep:str, m: str,
                    a:str) -> pd.DataFrame:
    """
    Unir múltiples tablas en una sola, añadiendo información de dependencia,
    mes y año.

    Args:
    - lista_df (List[pd.DataFrame]): Lista de tablas que se van a unir.
    - dep (str): La dependencia de la que se va a agrega información.
    - m (str): El mes para el que se va a agregar información.
    - a (str): El año para el que se va a agregar información.

    Returns:
    - pd.DataFrame: La tabla resultante después de unir las demás y agregar
    información.
    """
    if len(lista_df) > 0:
        data_frame = pd.concat(lista_df)
        data_frame["dependencia"] = [dep[1] for i in
                            range(0, obtener_cantidad_de_filas(data_frame))]
        data_frame["mes"] = [m for i in
                            range(0, obtener_cantidad_de_filas(data_frame))]
        data_frame["anio"] = [a for i in
                            range(0, obtener_cantidad_de_filas(data_frame))]
    else:
        data_frame= pd.DataFrame()
    return data_frame

listado_dependencias, listado_meses, listado_anios = get_dependencias_uanl()

ldfs = []
for anio in listado_anios:
    for mes in listado_meses:
        for dependencia in listado_dependencias:
            pages = get_pages(f"{mes}{anio}", dependencia[0])
            print(f"m: {mes} a: {anio} d: {dependencia} p: {pages}")
            ldf = [get_info_transparencia_uanl(f"{mes}{anio}", dependencia[0],
                    page) for page in pages]
            udf = unir_datos(ldf, dependencia, mes, anio)
            ldfs.append(udf)

df = pd.concat(ldfs)
df.to_csv("csv/uanl2021.csv", index=False)
