import logging
import pandas as pd
import plotly.express as px
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import os
import requests
import sys

# Configuración del logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# URL del archivo CSV desde una variable de entorno
url = os.environ.get('CSV_URL', 'https://raw.githubusercontent.com/licvincent/Hipertension_Arterial_Mexico/refs/heads/main/Hipertension_Arterial_Mexico_v3.csv')

logger.info(f"URL del CSV configurada: {url}")

# Verificar la URL del CSV
try:
    logger.info("Verificando la URL del CSV...")
    response = requests.head(url)
    response.raise_for_status()  # Lanza una excepción para códigos de error (4xx o 5xx)
    logger.info(f"URL del CSV verificada correctamente: {url}")
except requests.exceptions.RequestException as e:
    logger.error(f"Error al verificar la URL del CSV: {e}")
    sys.exit(1)

try:
    logger.info('Iniciando carga de datos desde la URL')
    df = pd.read_csv(url, encoding='utf-8')  # Asegurar encoding utf-8
    logger.info('Datos cargados correctamente')
    logger.info(f"Forma del DataFrame: {df.shape}")  # Agregar forma del dataframe

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

    logger.info("Categorizando edades...")
    df['Grupo_Edad'] = df['edad'].apply(categorize_age)
    logger.info("Edades categorizadas.")

    # Mapear valores de sexo a etiquetas
    sexo_labels = {1: 'Hombre', 2: 'Mujer'}
    logger.info("Mapeando etiquetas de sexo...")
    df['sexo'] = df['sexo'].map(sexo_labels)
    logger.info("Etiquetas de sexo mapeadas.")

    # Crear la app de Dash
    logger.info("Creando la app de Dash...")
    app = dash.Dash(__name__)
    app.title = "Dashboard de Hipertensión"
    server = app.server

    app.layout = html.Div(style={'backgroundColor': '#F9F9F9', 'padding': '20px'}, children=[
        html.Div([
            html.H1("Dashboard de Hipertensión Arterial en México", style={'textAlign': 'center'}),
            html.P("Comparación del riesgo de hipertensión entre hombres y mujeres agrupados por edades.", style={'textAlign': 'center'})
        ], style={'padding': '20px', 'backgroundColor': '#e9ecef', 'marginBottom': '20px'}),
        html.Div([
            dcc.Dropdown(
                id='grupo-edad-dropdown',
                options=[{'label': i, 'value': i} for i in df['Grupo_Edad'].unique()],
                value=df['Grupo_Edad'].unique(),  # Mostrar todos los grupos por defecto
                multi=True
            ),
            dcc.Graph(id='graph')
        ])
    ])
    logger.info("App de Dash creada.")

    # Callback para actualizar el gráfico
    @app.callback(
        Output('graph', 'figure'),
        Input('grupo-edad-dropdown', 'value')
    )
    def update_graph(selected_grupos):
        logger.info(f"Actualizando gráfico con grupos seleccionados: {selected_grupos}")
        filtered_df = df[df['Grupo_Edad'].isin(selected_grupos)]
        grouped = filtered_df.groupby(['sexo', 'Grupo_Edad'])['riesgo_hipertension'].mean().reset_index()
        grouped['Riesgo (%)'] = grouped['riesgo_hipertension'] * 100
        color_map = {'Hombre': 'blue', 'Mujer': 'pink'}
        fig = px.bar(grouped,
                       x='Grupo_Edad',
                       y='Riesgo (%)',
                       color='sexo',
                       barmode='group',
                       title='Riesgo de Hipertensión por Sexo y Grupo de Edad',
                       labels={'Grupo_Edad': 'Grupo de Edad', 'Riesgo (%)': 'Porcentaje de Hipertensión'},
                       color_discrete_map=color_map)
        logger.info("Gráfico actualizado.")
        return fig

    if __name__ == '__main__':
        logger.info("Iniciando el servidor...")
        app.run_server(debug=False)
        logger.info("Servidor iniciado.")

except pd.errors.ParserError as e:
    logger.error(f'Error al leer el archivo CSV: {e}')
except Exception as e:
    logger.error(f'Error inesperado: {e}')
