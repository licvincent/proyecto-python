import logging
import pandas as pd
import plotly.express as px
import dash
from dash import dcc, html
import os
import requests
import sys

# Configuración del logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# URL del archivo CSV desde una variable de entorno
url = os.environ.get('CSV_URL', 'https://raw.githubusercontent.com/licvincent/Hipertension_Arterial_Mexico/refs/heads/main/Hipertension_Arterial_Mexico_v3.csv')

# Verificar la URL del CSV
try:
    response = requests.head(url)
    response.raise_for_status()  # Lanza una excepción para códigos de error (4xx o 5xx)
    logger.info(f"URL del CSV verificada: {url}")
except requests.exceptions.RequestException as e:
    logger.error(f"Error al verificar la URL del CSV: {e}")
    sys.exit(1)

try:
    logger.info('Iniciando carga de datos desde la URL')
    df = pd.read_csv(url)
    logger.info('Datos cargados correctamente')

    # Creación de Grupos de Edad
    def categorize_age(edad):
        if edad < 18:
            return 'Niños'
        elif edad < 36:
            return 'Jóvenes'
        elif edad < 61:
            return 'Adultos'
        else:
            return 'Adultos Mayores'

    df['Grupo_Edad'] = df['edad'].apply(categorize_age)

    # Agrupar por 'Sexo' y 'Grupo_Edad' y calcular la media de hipertensión
    grouped = df.groupby(['sexo', 'Grupo_Edad'])['riesgo_hipertension'].mean().reset_index()

    # Convertir la proporción a porcentaje
    grouped['Riesgo (%)'] = grouped['riesgo_hipertension'] * 100

    # Mapear valores de sexo a etiquetas
    sexo_labels = {1: 'Hombre', 2: 'Mujer'}
    grouped['sexo'] = grouped['sexo'].map(sexo_labels)

    # Crear la visualización
    color_map = {'Hombre': 'blue', 'Mujer': 'pink'}
    fig = px.bar(grouped,
                x='Grupo_Edad',
                y='Riesgo (%)',
                color='sexo',
                barmode='group',
                title='Riesgo de Hipertensión por Sexo y Grupo de Edad',
                labels={'Grupo_Edad': 'Grupo de Edad', 'Riesgo (%)': 'Porcentaje de Hipertensión'},
                color_discrete_map=color_map
                )

    # Crear la app de Dash
    app = dash.Dash(__name__)
    app.title = "Dashboard de Hipertensión"
    server = app.server

    app.layout = html.Div(style={'backgroundColor': '#F9F9F9', 'padding': '20px'}, children=[
        html.Div([
            html.H1("Dashboard de Hipertensión Arterial en México", style={'textAlign': 'center'}),
            html.P("Comparación del riesgo de hipertensión entre hombres y mujeres agrupados por edades.", style={'textAlign': 'center'})
        ], style={'padding': '20px', 'backgroundColor': '#e9ecef', 'marginBottom': '20px'}),
        html.Div([
            dcc.Graph(id='graph', figure=fig)
        ])
    ])

    if __name__ == '__main__':
        app.run_server(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)), debug=False)

except pd.errors.ParserError as e:
    logger.error('Error al leer el archivo CSV: %s', e)
except Exception as e:
    logger.error('Error inesperado: %s', e)
