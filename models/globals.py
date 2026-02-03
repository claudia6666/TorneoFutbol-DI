"""
Módulo para almacenar objetos globales de la aplicación
"""
db_connection = None
def set_db_connection(db):
    """Establece la conexión global de la base de datos."""
    global db_connection
    db_connection = db
def get_db_connection():
    """Retorna la conexión global de la base de datos."""
    return db_connection
