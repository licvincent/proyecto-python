import logging
import pandas as pd
import plotly.express as px
import dash
from dash import dcc, html
import os
import sys

# Configuración del logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# URL del archivo CSV
url = 'https://raw.githubusercontent.com/licvincent/Hipertension_Arterial_Mexico/refs/heads/main/Hipertension_Arterial_Mexico_v3.csv'

try:
    logger.info('Iniciando carga de datos desde la URL: %s', url)
    df = pd.read_csv(url)
    logger.info('Datos cargados correctamente')
    logger.debug('Primeras filas del DataFrame: %s', df.head())
    logger.debug('Estadísticas del DataFrame: %s', df.describe())

    # Validar valores únicos en la columna 'sexo'
    logger.info('Valores únicos en la columna "sexo": %s', df['sexo'].unique())

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
    fig = px.bar(grouped,
                 x='Grupo_Edad',
                 y='Riesgo (%)',
                 color='sexo',
                 barmode='group',
                 title='Riesgo de Hipertensión por Sexo y Grupo de Edad',
                 labels={'Grupo_Edad': 'Grupo de Edad', 'Riesgo (%)': 'Porcentaje de Hipertensión'},
                 color_discrete_map={
                     'Hombre': 'blue',
                     'Mujer': 'pink'
                 }
                 )

    # Crear la app de Dash
    app = dash.Dash(__name__)
    app.title = "Dashboard de Hipertensión"
    server = app.server  # Necesario para Heroku

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
        port = int(os.environ.get("PORT", 5000))
        app.run_server(host='0.0.0.0', port=port, debug=False)

except Exception as e:
    logger.error('Error inesperado: %s', e)
    sys.exit(1)
