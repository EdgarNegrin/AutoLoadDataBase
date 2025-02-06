import requests
import os

# Usa os.environ para obtener las variables de entorno
NOTION_TOKEN = os.getenv('NOTION_TOKEN')
DATABASE_A_ID = os.getenv('DATABASE_A_ID')
DATABASE_B_ID = os.getenv('DATABASE_B_ID')
IDS_FILAS_B_str = os.getenv('IDS_FILAS_B')

IDS_FILAS_B = IDS_FILAS_B_str.split("\n")

HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

def obtener_filas_a():
    """Obtiene todas las filas de la base de datos A manejando la paginación."""
    ids_filas_a = set()
    url_a = f"https://api.notion.com/v1/databases/{DATABASE_A_ID}/query"
    payload = {}  # Cuerpo vacío para la primera solicitud
    while True:
        response = requests.post(url_a, headers=HEADERS, json=payload)
        if response.status_code != 200:
            print(f"Error al obtener filas de A: {response.text}")
            return set()
        
        data = response.json()
        ids_filas_a.update({fila['id'] for fila in data.get('results', [])})

        # Si hay más páginas, actualizamos el cursor y seguimos solicitando
        if data.get("has_more"):
            payload["start_cursor"] = data["next_cursor"]
        else:
            break  # No hay más páginas, terminamos

    print(f"Se encontraron {len(ids_filas_a)} filas en la base de datos A.")
    return ids_filas_a

def actualizar_filas_b(ids_filas_a):
    """Actualiza varias filas en la base de datos B con los nuevos registros de A sin duplicar relaciones."""
    for id_fila_b in IDS_FILAS_B:
        url_get_b = f"https://api.notion.com/v1/pages/{id_fila_b}"
        response_get_b = requests.get(url_get_b, headers=HEADERS)

        if response_get_b.status_code == 200:
            fila_b = response_get_b.json()
            relaciones_actuales = fila_b['properties'].get("Prioridad2", {}).get("relation", [])
            ids_actuales_b = {relacion["id"] for relacion in relaciones_actuales}

            # Solo agregar los registros de A que NO estén ya en B
            nuevos_ids_a = ids_filas_a - ids_actuales_b

            if nuevos_ids_a:
                print(f"Fila {id_fila_b} en B tiene {len(nuevos_ids_a)} nuevas relaciones para agregar.")

                # Crear una lista combinada sin modificar las relaciones existentes
                relaciones_actualizadas = [{"id": id_a} for id_a in ids_actuales_b] + [{"id": id_a} for id_a in nuevos_ids_a]

                # Actualizar la fila B con los nuevos registros de A
                url_update_b = f"https://api.notion.com/v1/pages/{id_fila_b}"
                data_update_b = {
                    "properties": {
                        "Prioridad2": {
                            "relation": relaciones_actualizadas  # Mantiene las relaciones previas y agrega solo las nuevas
                        }
                    }
                }

                response_update_b = requests.patch(url_update_b, headers=HEADERS, json=data_update_b)

                if response_update_b.status_code == 200:
                    print(f"Fila {id_fila_b} en la base de datos B actualizada correctamente.")
                else:
                    print(f"Error al actualizar la fila {id_fila_b} en B: {response_update_b.text}")
            else:
                print(f"No hay nuevos registros para agregar en la fila {id_fila_b} de B.")
        else:
            print(f"Error al obtener la fila {id_fila_b} en B: {response_get_b.text}")

# Ejecutar el proceso
ids_filas_a = obtener_filas_a()
if ids_filas_a:
    actualizar_filas_b(ids_filas_a)