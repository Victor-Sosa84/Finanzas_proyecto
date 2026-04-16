"""
main.py
=======
Punto de entrada de FinanzasPro.

Cómo correr:
    python main.py

Comando para instalar librerias necesarias:
    python -m venv venv
    venv\Scripts\activate # En Windows
    source venv/bin/activate # En Linux/Mac
    pip install -r requirements.txt
"""

from interfaz.app import iniciar

if __name__ == "__main__":
    iniciar()