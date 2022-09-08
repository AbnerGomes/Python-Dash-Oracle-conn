#imports
import sqlalchemy
#import os

import cx_Oracle
import config #arquivo contendo informações de acesso ao banco de dados

from dash import dash
from dash import dcc
from dash import html
import pandas as pd
from plotly import graph_objects as go
from plotly import express as px

#connect database
def connect():
   return cx_Oracle.connect(
      config.username,
        config.password,
        config.dsn,
       encoding=config.encoding)
    
cnxn = sqlalchemy.create_engine(
            'oracle://',
            creator=connect)

##read data
df = pd.read_sql(
"SELECT sum(sessions) sessoes , osuser FROM (SELECT S.MACHINE, S.USERNAME, S.OSUSER, S.PROGRAM , S.MODULE , COUNT(*) SESSIONS FROM GV$SESSION S GROUP BY S.MACHINE, S.USERNAME, S.OSUSER, S.PROGRAM, S.MODULE ORDER BY S.MACHINE, S.USERNAME, S.OSUSER, S.PROGRAM, S.MODULE ) WHERE Upper(osuser) LIKE'%API%' GROUP BY osuser",
cnxn)

##web app
app_name = 'dash-oracle-python'
 
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
 
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.title = 'Parking - Dash using Oracle + Python'


##layout
#bar chart
trace = go.Bar(x=df.osuser, y=df.sessoes, name='osuser')

#pie chart
tracepie = go.Pie(  labels=df['osuser'],values = df['sessoes'] )
 

app.layout = html.Div([html.Div([html.H4("Quantidade sessoes por api", style={'textAlign': 'center'}),
dcc.Graph(
id='example-graph0',
figure={
'data': [trace]
})
], className="container"), html.Div([html.H4("Percentagem sessoes por api", style={'textAlign': 'center'}),
dcc.Graph(
id='example-graph',
figure={
'data': [tracepie]
})
])
], className="container")


##run app
if __name__ == '__main__':
	app.run_server(debug=True)
