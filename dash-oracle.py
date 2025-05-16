from dash.dependencies import Input, Output
import dash

import config #arquivo contendo informações de acesso ao banco de dados
from dash import dash
from dash import dcc
from dash import html
import pandas as pd
import plotly.graph_objects as go

# Inicialize o aplicativo Dash
app = dash.Dash(__name__, suppress_callback_exceptions=True)
import oracledb
#oracledb.init_oracle_client() 
import sqlalchemy 
from sqlalchemy import create_engine, text
# Cria a engine SQLAlchemy usando oracledb como driver
def create_engine_oracle(db_name):
    db_config = config.databases[db_name]
    username = db_config['username']
    password = db_config['password']
    dsn = db_config['dsn']

    # Exemplo de DSN: host:port/service_name
    connection_string = f'oracle+oracledb://{username}:{password}@{dsn}'
    # connection_string = f'oracle+cx_oracle://{username}:{password}@{dsn}'

    return sqlalchemy.create_engine(connection_string)

# Criação das conexões (engines)
cnxn_parking_db = create_engine_oracle('parking_db')
cnxn_pertocad_db = create_engine_oracle('cad_db')
cnxn_pertotrn_db = create_engine_oracle('trn_db')

# cnxn_abner_db = create_engine_oracle('abner_db')

# cnn_park = cnxn_parking_db.connect()
# cnn_cad = cnxn_pertocad_db.connect()
# cnn_trn = cnxn_pertotrn_db.connect()

# with cnxn_parking_db.connect() as connection:
#     result = connection.execute(text("select 'deu certo' from dual"))
#     print(result.fetchone())  # Espera-se que retorne (1,)

# Consultas (sessoes,tablespaces e jobs running)
sessoes = text("""select osuser,sessoes from (SELECT sum(sessions) sessoes , osuser FROM (SELECT S.MACHINE, S.USERNAME, S.OSUSER, S.PROGRAM , S.MODULE , COUNT(*) SESSIONS FROM GV$SESSION S GROUP BY S.MACHINE, S.USERNAME, S.OSUSER, S.PROGRAM, S.MODULE ORDER BY S.MACHINE, S.USERNAME, S.OSUSER, S.PROGRAM, S.MODULE ) WHERE Upper(osuser) not LIKE'%ORACLE%' and  Upper(osuser) not LIKE'%RDS%'  GROUP BY osuser order by 1 desc) where rownum <= 6""")
tablespaces = text("select TABLESPACE_NAME, Livre as MAX_FREE_MB from (select tarea.tablespace_name TABLESPACE_NAME, tarea.tsize MAX_SIZE_MB, tcorrente SIZE_MB, round(tarea.tsize-tcorrente+sum(nvl(free.bytes,0))/1024/1024,0) MAX_FREE_MB, round(((tarea.tsize-tcorrente+sum(nvl(free.bytes,0))/1024/1024)*100)/tarea.tsize,0) Livre from dba_free_space free, (select tablespace_name, sum(a.bytes)/1024/1024 tcorrente, sum(decode(nvl(a.maxbytes,0),0,a.bytes,a.maxbytes))/1024/1024 tsize from dba_data_files A group by tablespace_name) tarea where free.tablespace_name(+)=tarea.tablespace_name group by tarea.tablespace_name, tarea.tsize, tcorrente order by 5 asc) where rownum <= 6")
jobs_running = text("SELECT B.STATE, A.OWNER, A.JOB_NAME JOB_NAME, SUBSTR(A.ELAPSED_TIME,5,9) ELAPSEDTIME, A.ELAPSED_TIME, B.REPEAT_INTERVAL, B.JOB_ACTION, S.PROGRAM, S.MODULE FROM DBA_SCHEDULER_RUNNING_JOBS A INNER JOIN GV$SESSION S ON S.SID = A.SESSION_ID INNER JOIN DBA_SCHEDULER_JOBS B ON A.JOB_NAME = B.JOB_NAME WHERE JOB_ACTION IS NOT NULL and a.owner = b.owner ORDER BY ELAPSEDTIME DESC")
cpu_usage_percent =text("""select cpu_usage from (SELECT   METRIC_NAME, trunc(round(max(VALUE),2)) as cpu_usage FROM   V$SYSMETRIC WHERE  METRIC_NAME IN ( 'Host CPU Utilization (%)') group by METRIC_NAME )""")

# inicia variaveis com dados vazios (Placeholder) para poder usa-las na app layout
trace_prk = go.Bar(x=["Placeholder"], y=[0])  
fig_bar_prk = go.Figure(data=[trace_prk])
tracepie_prk = go.Pie(labels=["Placeholder"], values=[1])  
fig_pie_prk = go.Figure(data=[tracepie_prk])
fig_table_prk = go.Figure(data=[go.Table(header=dict(values=[]), cells=dict(values=[]))])
fig_gauge_prk = go.Figure()

trace_cad = go.Bar(x=["Placeholder"], y=[0])  
fig_bar_cad = go.Figure(data=[trace_cad])
tracepie_cad = go.Pie(labels=["Placeholder"], values=[1])  
fig_pie_cad = go.Figure(data=[tracepie_cad])
fig_table_cad = go.Figure(data=[go.Table(header=dict(values=[]), cells=dict(values=[]))])
fig_gauge_cad = go.Figure()

trace_trn = go.Bar(x=["Placeholder"], y=[0])  
fig_bar_trn = go.Figure(data=[trace_trn])
tracepie_trn = go.Pie(labels=["Placeholder"], values=[1])  
fig_pie_trn = go.Figure(data=[tracepie_trn])
fig_table_trn = go.Figure(data=[go.Table(header=dict(values=[]), cells=dict(values=[]))])
fig_gauge_trn = go.Figure()

prk_cpu ='0'
cad_cpu ='0'
trn_cpu ='0'

def create_card(title, graph_id):
    return html.Div([
        html.H6(title),
        dcc.Graph(id=graph_id, style={"height": "100%", "width": "100%", "display":"flex", "fontSize":"6px"  })

    ], className='card')


def create_layout():
    cards = [
        create_card("Tablespaces - Espaço Livre", "bar-graph-prk"),
        create_card("PRK", "pie-graph-prk"),
        create_card("Jobs em Execução", "table-graph-prk"),
        create_card("Uso de CPU (%)", "gauge-graph-prk"),

        create_card("Tablespaces - Espaço Livre", "bar-graph-cad"),
        create_card("CAD", "pie-graph-cad"),
        create_card("Jobs em Execução", "table-graph-cad"),
        create_card("Uso de CPU (%)", "gauge-graph-cad"),

        create_card("Tablespaces - Espaço Livre", "bar-graph-trn"),
        create_card("TRN", "pie-graph-trn"),
        create_card("Jobs em Execução", "table-graph-trn"),
        create_card("Uso de CPU (%)", "gauge-graph-trn")
    ]

    return html.Div([
        dcc.Interval(id='interval-component', interval=5*1000, n_intervals=0),
        html.Div(cards, className='grid')
    ])

app.layout = create_layout()

# Estilo CSS inline (poderia estar em um arquivo separado)
app.index_string = '''
<!DOCTYPE html>
<html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <title>Dash Layout Preview</title>
        {%metas%}
        {%favicon%}
        {%css%}
        <style>
            html, body {
                margin: 0;
                padding: 0;
                font-family: Arial, sans-serif;
                height: 100vh;
                overflow: hidden;
            }
            .grid {
                display: grid;
                grid-template-columns: repeat(4, 1fr);  /* 4 colunas */
                grid-template-rows: repeat(3, auto);   /* 3 linhas */
                gap: 0px;
                padding: 8px;
                box-sizing: border-box;
                height: 100vh;
                overflow-y: auto;
            }
            .card {
                background: white;
                
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
                border-radius: 5px;
                text-align: center;
                
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                height: 100%;
            }
            .card h4,h6 {
                margin-top: 0;
                font-size: 1rem;
            }
            .card .react-graph-container {
                display: flex;
                justify-content: center;
                align-items: center;
                width: 100%;
                height: 100%;
            }
            /* Responsividade */
            @media screen and (max-width: 1200px) {
                .grid {
                    grid-template-columns: repeat(3, 1fr);
                }
            }
            @media screen and (max-width: 800px) {
                .grid {
                    grid-template-columns: repeat(2, 1fr);
                }
            }
            @media screen and (max-width: 500px) {
                .grid {
                    grid-template-columns: 1fr;
                }
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''
# Callback para atualizar os dados periodicamente
@app.callback(
    [
        Output('bar-graph-prk', 'figure'),
        Output('pie-graph-prk', 'figure'),
        Output('table-graph-prk', 'figure'),
        Output('gauge-graph-prk','figure'),
        Output('bar-graph-cad', 'figure'),
        Output('pie-graph-cad', 'figure'),
        Output('table-graph-cad', 'figure'),
        Output('gauge-graph-cad','figure'),
        Output('bar-graph-trn', 'figure'),
        Output('pie-graph-trn', 'figure'),
        Output('table-graph-trn', 'figure'),
        Output('gauge-graph-trn','figure')
    ],
    Input('interval-component', 'n_intervals')
)
def update_data(n_intervals):
    try:
        # Parking
        with cnxn_parking_db.connect() as connection:
            result = connection.execute(sessoes)
            df_prk_session = pd.DataFrame(result.fetchall(), columns=result.keys())
            # df_prk_session = pd.read_sql_query(sessoes, cnn_park)
            df_prk_session.columns = [col.upper() for col in df_prk_session.columns]

            result = connection.execute(tablespaces)
            # df_prk_tablespace = pd.read_sql_query(tablespaces, cnn_park)
            df_prk_tablespace = pd.DataFrame(result.fetchall(), columns=result.keys())
            
            df_prk_tablespace.columns = [col.upper() for col in df_prk_tablespace.columns]
            print(df_prk_tablespace.columns) 
            result = connection.execute(jobs_running)   
            # df_prk_jobs = pd.read_sql_query(jobs_running, cnn_park)
            df_prk_jobs = pd.DataFrame(result.fetchall(), columns=result.keys())
            df_prk_jobs.columns = [col.upper() for col in df_prk_jobs.columns]
            
            result = connection.execute(cpu_usage_percent)            
            # prk_cpu = int(pd.read_sql_query(cpu_usage_percent, cnn_park).cpu_usage)
            prk_cpu = pd.DataFrame(result.fetchall(), columns=result.keys())
            prk_cpu.columns = [col.upper() for col in prk_cpu.columns]
            print(prk_cpu.columns)
            print(prk_cpu.iloc[0, 0])
            prk_cpu = int(prk_cpu.iloc[0, 0])
    
    except Exception as e:
        print(f"Erro ao carregar dados do Parking: {e}")
        df_prk_session = pd.DataFrame()
        df_prk_tablespace = pd.DataFrame()
        df_prk_jobs = pd.DataFrame()
        prk_cpu = 0

    # Grafo de Barras - Parking
    if not df_prk_tablespace.empty:
        trace_prk = go.Bar(
            x=df_prk_tablespace['TABLESPACE_NAME'],
            y=df_prk_tablespace['MAX_FREE_MB'],
            name='Espaço Livre',
            marker=dict(color='rgb(32, 201, 151)')
        )
        fig_bar_prk = go.Figure(data=[trace_prk])

        fig_bar_prk.update_layout(
            height=230,   # Altura em pixels
            width=500,    # Largura em pixels
            margin=dict(l=50, r=50, t=50, b=80)  # Margens do gráfico
        )
    else:
        fig_bar_prk = go.Figure()

    # Grafo de Pizza - Parking
    if not df_prk_session.empty:
        tracepie_prk = go.Pie(
            labels=df_prk_session['OSUSER'],
            values=df_prk_session['SESSOES'],
            name='SESSOES',# Margens do gráfico
            domain=dict(x=[0, 1], y=[0, 1]),  # Ocupa toda a área, centralizado
            marker=dict(
                colors=[
                    'rgba(32, 201, 151, 1.0)',  # Verde água
                    'rgba(0, 123, 255, 1.0)',   # Azul
                    'rgba(255, 193, 7, 1.0)',   # Amarelo
                    'rgba(220, 53, 69, 1.0)',   # Vermelho
                    'rgba(108, 117, 125, 1.0)', # Cinza
                    'rgba(40, 167, 69, 1.0)'    # Verde escuro
                ]
            )

        )
        fig_pie_prk = go.Figure(data=[tracepie_prk])
        
        fig_pie_prk.update_layout(
        #title='SESSOES',
        height=230,   # Altura em pixels
        width=400,    # Largura em pixels
        margin=dict(l=80, r=150, t=10, b=50),  # Margens do gráfico
        legend=dict(
            x=1.2,  # Posição da legenda à direita do gráfico
            y=0.5,
            xanchor='left',
            yanchor='middle',
            bgcolor='rgba(255,255,255,0)',  # fundo transparente
            borderwidth=0
            )
        )
    else:
        fig_pie_prk = go.Figure()

    # Tabela de Jobs - Parking
    if not df_prk_jobs.empty:
        table_data_prk = df_prk_jobs[['OWNER', 'JOB_NAME', 'ELAPSEDTIME', 'JOB_ACTION']]

        fig_table_prk = go.Figure(data=[go.Table(
            columnwidth=[80, 150, 100, 300],
            header=dict(values=table_data_prk.columns,font=dict(size=12), fill_color='lightgrey'),
            cells=dict(values=[table_data_prk[col] for col in table_data_prk.columns],font=dict(size=10))
        )])

        fig_table_prk.update_layout(
            height=250,   # Altura em pixels
            width=580,
            autosize=False,
            xaxis=dict(
                domain=[0, 1]  # usa todo o espaço horizontal
            ),
            margin=dict(l=0, r=0, t=10, b=0)  # Margens do gráfico
        )
    else:
        fig_table_prk = go.Figure()

    if prk_cpu <= 50:
        cor = "rgba(32, 201, 151, 1.0)"   # Verde
    elif prk_cpu <= 80:
        cor = "rgba(255, 234, 0, 1.0)"   # Amarelo vibrante
    else:
        cor = "red"

    # Gauge de Uso de CPU - Parking
    fig_gauge_prk = go.Figure(go.Indicator(
        mode="gauge+number",
        value=prk_cpu,
        title={'text': "Uso de CPU (%)"},
        gauge={
            'axis': {'range': [0, 100]},
            'bar': {'color': cor, 'thickness': 0.3},
            'bgcolor': "lightgray",  # fundo do gauge
            # 'steps': [  # apenas decorativo, igual à imagem
            #     {'range': [0, 50], 'color': 'rgba(32, 201, 151, 0.2)'},
            #     {'range': [50, 80], 'color': 'rgba(255, 234, 0, 0.2)'},
            #     {'range': [80, 100], 'color': 'rgba(255, 0, 0, 0.2)'}
            # ],
            'threshold': {
                'line': {'color': "black", 'width': 3},
                'thickness': 0.75,
                'value': prk_cpu  # marcador igual ao valor atual
            }
        }
    ))

    fig_gauge_prk.update_layout(
            height=250,   # Altura em pixels
            width=350,
            margin=dict(l=100, r=10, t=10, b=10)  # Margens do gráfico
    )

    # PertoCad
    try:
        with cnxn_pertocad_db.connect() as connection:
            result = connection.execute(sessoes)
            df_cad_session = pd.DataFrame(result.fetchall(), columns=result.keys())
            # df_prk_session = pd.read_sql_query(sessoes, cnn_park)
            df_cad_session.columns = [col.upper() for col in df_cad_session.columns]

            result = connection.execute(tablespaces)
            # df_prk_tablespace = pd.read_sql_query(tablespaces, cnn_park)
            df_cad_tablespace = pd.DataFrame(result.fetchall(), columns=result.keys())            
            df_cad_tablespace.columns = [col.upper() for col in df_cad_tablespace.columns]

            result = connection.execute(jobs_running)   
            # df_prk_jobs = pd.read_sql_query(jobs_running, cnn_park)
            df_cad_jobs = pd.DataFrame(result.fetchall(), columns=result.keys())
            df_cad_jobs.columns = [col.upper() for col in df_cad_jobs.columns]
            
            result = connection.execute(cpu_usage_percent)            
            # prk_cpu = int(pd.read_sql_query(cpu_usage_percent, cnn_park).cpu_usage)
            cad_cpu = pd.DataFrame(result.fetchall(), columns=result.keys())
            cad_cpu.columns = [col.upper() for col in cad_cpu.columns]
            cad_cpu = int(cad_cpu.iloc[0, 0])  

    except Exception as e:
        print(f"Erro ao carregar dados do PertoCad: {e}")
        df_cad_session = pd.DataFrame()
        df_cad_tablespace = pd.DataFrame()
        df_cad_jobs = pd.DataFrame()
        cad_cpu = 0

    # Grafo de Barras - PertoCad
    if not df_cad_tablespace.empty:
        trace_cad = go.Bar(
            x=df_cad_tablespace['TABLESPACE_NAME'],
            y=df_cad_tablespace['MAX_FREE_MB'],
            name='Espaço Livre',
            marker=dict(color='rgb(32, 201, 151)')
        )
        fig_bar_cad = go.Figure(data=[trace_cad])

        fig_bar_cad.update_layout(
            height=230,   # Altura em pixels
            width=500,    # Largura em pixels
            margin=dict(l=50, r=50, t=50, b=80)  # Margens do gráfico
        )

    else:
        fig_bar_cad = go.Figure()

    # Grafo de Pizza - CAD
    if not df_cad_session.empty:
        tracepie_cad = go.Pie(
            labels=df_cad_session['OSUSER'],
            values=df_cad_session['SESSOES'],
            name='SESSOES',# Margens do gráfico
            domain=dict(x=[0, 1], y=[0, 1]),  # Ocupa toda a área, centralizado
            marker=dict(
                colors=[
                    'rgba(32, 201, 151, 1.0)',  # Verde água
                    'rgba(0, 123, 255, 1.0)',   # Azul
                    'rgba(255, 193, 7, 1.0)',   # Amarelo
                    'rgba(220, 53, 69, 1.0)',   # Vermelho
                    'rgba(108, 117, 125, 1.0)', # Cinza
                    'rgba(40, 167, 69, 1.0)'    # Verde escuro
                ]
            )
        )
        fig_pie_cad = go.Figure(data=[tracepie_cad])
        
        fig_pie_cad.update_layout(
            height=230,   # Altura em pixels
            width=400,    # Largura em pixels
            margin=dict(l=80, r=150, t=10, b=50),  # Margens do gráfico
            legend=dict(
                x=1.2,  # Posição da legenda à direita do gráfico
                y=0.5,
                xanchor='left',
                yanchor='middle',
                bgcolor='rgba(255,255,255,0)',  # fundo transparente
                borderwidth=0
                )
        )
    else:
        fig_pie_cad = go.Figure()

    # Tabela de Jobs - PertoCad
    if not df_cad_jobs.empty:
        table_data_cad = df_cad_jobs[['OWNER', 'JOB_NAME', 'ELAPSEDTIME', 'JOB_ACTION']]
        fig_table_cad = go.Figure(data=[go.Table(
            columnwidth=[80, 150, 100, 300],
            header=dict(values=table_data_cad.columns,font=dict(size=12), fill_color='lightgrey'),
            cells=dict(values=[table_data_cad[col] for col in table_data_cad.columns],font=dict(size=10))
        )])

        fig_table_cad.update_layout(
            height=250,   # Altura em pixels
            width=580,
            autosize=False,
            xaxis=dict(
                domain=[0, 1]  # usa todo o espaço horizontal
            ),
            margin=dict(l=0, r=0, t=10, b=0)  # Margens do gráfico
        )
    else:
        fig_table_cad = go.Figure()

    if cad_cpu <= 50:
        cor = "rgba(32, 201, 151, 1.0)"   # Verde
    elif cad_cpu <= 80:
        cor = "rgba(255, 234, 0, 1.0)"   # Amarelo vibrante
    else:
        cor = "red"

    # Gauge de Uso de CPU - PertoCad
    fig_gauge_cad = go.Figure(go.Indicator(
        mode="gauge+number",
        value=cad_cpu,
        title={'text': "Uso de CPU (%)"},
        gauge={
            'axis': {'range': [0, 100]},
            'bar': {'color': cor, 'thickness': 0.3},
            'bgcolor': "lightgray",  # fundo do gauge
            # 'steps': [  # apenas decorativo, igual à imagem
            #     {'range': [0, 50], 'color': 'rgba(32, 201, 151, 0.2)'},
            #     {'range': [50, 80], 'color': 'rgba(255, 234, 0, 0.2)'},
            #     {'range': [80, 100], 'color': 'rgba(255, 0, 0, 0.2)'}
            # ],
            'threshold': {
                'line': {'color': "black", 'width': 3},
                'thickness': 0.75,
                'value': cad_cpu  # marcador igual ao valor atual
            }
        }
    ))

    fig_gauge_cad.update_layout(
            height=250,   # Altura em pixels
            width=350,
            margin=dict(l=100, r=10, t=10, b=10)  # Margens do gráfico
    )

    # PertoTrn
    try:
        with cnxn_pertotrn_db.connect() as connection:
            result = connection.execute(sessoes)
            df_trn_session = pd.DataFrame(result.fetchall(), columns=result.keys())
            # df_prk_session = pd.read_sql_query(sessoes, cnn_park)
            df_trn_session.columns = [col.upper() for col in df_trn_session.columns]

            result = connection.execute(tablespaces)
            # df_prk_tablespace = pd.read_sql_query(tablespaces, cnn_park)
            df_trn_tablespace = pd.DataFrame(result.fetchall(), columns=result.keys())            
            df_trn_tablespace.columns = [col.upper() for col in df_trn_tablespace.columns]

            result = connection.execute(jobs_running)   
            # df_prk_jobs = pd.read_sql_query(jobs_running, cnn_park)
            df_trn_jobs = pd.DataFrame(result.fetchall(), columns=result.keys())
            df_trn_jobs.columns = [col.upper() for col in df_trn_jobs.columns]
            
            result = connection.execute(cpu_usage_percent)            
            # prk_cpu = int(pd.read_sql_query(cpu_usage_percent, cnn_park).cpu_usage)
            trn_cpu = pd.DataFrame(result.fetchall(), columns=result.keys())
            trn_cpu.columns = [col.upper() for col in trn_cpu.columns]
            trn_cpu = int(trn_cpu.iloc[0, 0]) 
    except Exception as e:
        print(f"Erro ao carregar dados do PertoTrn: {e}")
        df_trn_session = pd.DataFrame()
        df_trn_tablespace = pd.DataFrame()
        df_trn_jobs = pd.DataFrame()
        trn_cpu = 0

    # Grafo de Barras - PertoTrn
    if not df_trn_tablespace.empty:
        trace_trn = go.Bar(
            x=df_trn_tablespace['TABLESPACE_NAME'],
            y=df_trn_tablespace['MAX_FREE_MB'],
            name='Espaço Livre',
            marker=dict(color='rgb(32, 201, 151)')
        )
        fig_bar_trn = go.Figure(data=[trace_trn])

        fig_bar_trn.update_layout(
            height=230,   # Altura em pixels
            width=500,    # Largura em pixels
            margin=dict(l=50, r=50, t=50, b=80)  # Margens do gráfico
        )
    else:
        fig_bar_trn = go.Figure()

    # Grafo de Pizza - TRN
    if not df_trn_session.empty:
        tracepie_trn = go.Pie(
            labels=df_trn_session['OSUSER'],
            values=df_trn_session['SESSOES'],
            name='SESSOES',# Margens do gráfico
            domain=dict(x=[0, 1], y=[0, 1]),  # Ocupa toda a área, centralizado
            marker=dict(
                colors=[
                    'rgba(32, 201, 151, 1.0)',  # Verde água
                    'rgba(0, 123, 255, 1.0)',   # Azul
                    'rgba(255, 193, 7, 1.0)',   # Amarelo
                    'rgba(220, 53, 69, 1.0)',   # Vermelho
                    'rgba(108, 117, 125, 1.0)', # Cinza
                    'rgba(40, 167, 69, 1.0)'    # Verde escuro
                ]
            )
        )
        fig_pie_trn = go.Figure(data=[tracepie_trn])
        
        fig_pie_trn.update_layout(
            height=230,   # Altura em pixels
            width=400,    # Largura em pixels
            margin=dict(l=80, r=150, t=10, b=50),  # Margens do gráfico
            legend=dict(
                x=1.2,  # Posição da legenda à direita do gráfico
                y=0.5,
                xanchor='left',
                yanchor='middle',
                bgcolor='rgba(255,255,255,0)',  # fundo transparente
                borderwidth=0
                )
        )
    else:
        fig_pie_trn = go.Figure()

    # Tabela de Jobs - PertoTrn
    if not df_trn_jobs.empty:
        table_data_trn = df_trn_jobs[['OWNER', 'JOB_NAME', 'STATE', 'ELAPSEDTIME', 'JOB_ACTION']]
        fig_table_trn = go.Figure(data=[go.Table(
            columnwidth=[80, 150, 100, 300],
            header=dict(values=table_data_trn.columns,font=dict(size=12), fill_color='lightgrey'),
            cells=dict(values=[table_data_trn[col] for col in table_data_trn.columns],font=dict(size=10))
        )])

        fig_table_trn.update_layout(
            height=250,   # Altura em pixels
            width=580,
            autosize=False,
            xaxis=dict(
                domain=[0, 1]  # usa todo o espaço horizontal
            ),
            margin=dict(l=0, r=0, t=10, b=0)  # Margens do gráfico
        )
    else:
        fig_table_trn = go.Figure()

    if trn_cpu <= 50:
        cor = "rgba(32, 201, 151, 1.0)"   # Verde
    elif trn_cpu <= 80:
        cor = "rgba(255, 234, 0, 1.0)"   # Amarelo vibrante
    else:
        cor = "red"

    # Gauge de Uso de CPU - PertoTrn
    # fig_gauge_trn = go.Figure(go.Indicator(
    #     mode="gauge+number",
    #     value=trn_cpu,
    #     title={'text': "Uso de CPU (%)"},
    #     gauge={'axis': {'range': [None, 100]}, 'steps': [
    #         {'range': [0, 50], 'color': "rgba(32, 201, 151, 1.0)"},
    #         {'range': [50, 80], 'color': "rgba(255, 234, 0, 1.0)"},
    #         {'range': [80, 100], 'color': "red"}
    #     ]}
    # ))
    fig_gauge_trn = go.Figure(go.Indicator(
        mode="gauge+number",
        value=trn_cpu,
        title={'text': "Uso de CPU (%)"},
        gauge={
            'axis': {'range': [0, 100]},
            'bar': {'color': cor, 'thickness': 0.3},
            'bgcolor': "lightgray",  # fundo do gauge
            # 'steps': [  # apenas decorativo, igual à imagem
            #     {'range': [0, 50], 'color': 'rgba(32, 201, 151, 0.2)'},
            #     {'range': [50, 80], 'color': 'rgba(255, 234, 0, 0.2)'},
            #     {'range': [80, 100], 'color': 'rgba(255, 0, 0, 0.2)'}
            #],
            'threshold': {
                'line': {'color': "black", 'width': 3},
                'thickness': 0.75,
                'value': trn_cpu  # marcador igual ao valor atual
            }
        }
    ))

    fig_gauge_trn.update_layout(
            height=250,   # Altura em pixels
            width=350,
            margin=dict(l=100, r=10, t=10, b=10)  # Margens do gráfico
    )

    return [
        fig_bar_prk, fig_pie_prk, fig_table_prk, fig_gauge_prk,
        fig_bar_cad, fig_pie_cad, fig_table_cad, fig_gauge_cad,
        fig_bar_trn, fig_pie_trn, fig_table_trn, fig_gauge_trn
    ]



if __name__ == '__main__':
    app.run_server(debug=True)