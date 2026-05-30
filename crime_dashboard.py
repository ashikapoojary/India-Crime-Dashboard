import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from dash import Dash, dcc, html, Input, Output, State, dash_table
import dash_bootstrap_components as dbc
import warnings
warnings.filterwarnings('ignore')

# ── Load & prep ────────────────────────────────────────────────────────────────
df = pd.read_csv('crime_dataset_india.csv')
df.columns = df.columns.str.strip()
df['Victim Age'] = pd.to_numeric(df['Victim Age'], errors='coerce')
df['Date of Occurrence'] = pd.to_datetime(df['Date of Occurrence'], dayfirst=True, errors='coerce')
df['Year'] = df['Date of Occurrence'].dt.year
df['Month'] = df['Date of Occurrence'].dt.month

GENDER_MAP = {'M': 'Male', 'F': 'Female', 'X': 'Other'}
df['Gender Label'] = df['Victim Gender'].map(GENDER_MAP).fillna('Unknown')

CRIMES = sorted(df['Crime Description'].dropna().unique().tolist())
CITIES = sorted(df['City'].dropna().unique().tolist())

# ── Colour palette ────────────────────────────────────────────────────────────
BG        = '#0b0f1a'
CARD_BG   = '#111827'
BORDER    = '#1e2d40'
ACCENT1   = '#00d4ff'
ACCENT2   = '#ff4d6d'
ACCENT3   = '#ffd166'
ACCENT4   = '#06d6a0'
TEXT_PRIM = '#e2e8f0'
TEXT_SEC  = '#94a3b8'
GENDER_COLORS = {'Male': ACCENT1, 'Female': ACCENT2, 'Other': ACCENT3}

card_style = {
    'backgroundColor': CARD_BG,
    'border': f'1px solid {BORDER}',
    'borderRadius': '12px',
    'padding': '20px',
    'marginBottom': '16px',
}

# ── App ───────────────────────────────────────────────────────────────────────
app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    title='India Crime Intelligence Dashboard',
    suppress_callback_exceptions=True,
)

# ── Layout ────────────────────────────────────────────────────────────────────
app.layout = html.Div(style={'backgroundColor': BG, 'minHeight': '100vh', 'fontFamily': "'Segoe UI', sans-serif", 'color': TEXT_PRIM}, children=[

    # ── HEADER ─────────────────────────────────────────────────────────────
    html.Div(style={'background': 'linear-gradient(135deg,#0b0f1a 0%,#0d1b2a 50%,#0b0f1a 100%)',
                    'borderBottom': f'2px solid {ACCENT1}', 'padding': '24px 40px', 'marginBottom': '24px'}, children=[
        html.Div(style={'display': 'flex', 'alignItems': 'center', 'gap': '16px'}, children=[
            html.Div('🔍', style={'fontSize': '36px'}),
            html.Div(children=[
                html.H1('India Crime Intelligence Dashboard',
                        style={'margin': 0, 'fontSize': '26px', 'fontWeight': '700',
                               'color': ACCENT1, 'letterSpacing': '1px'}),
                html.P(f'{len(df):,} records across {df["City"].nunique()} cities · 2020–{df["Year"].max()}',
                       style={'margin': 0, 'color': TEXT_SEC, 'fontSize': '13px'}),
            ])
        ])
    ]),

    html.Div(style={'padding': '0 32px 32px'}, children=[

        # ── KPI row ─────────────────────────────────────────────────────────
        html.Div(id='kpi-row', style={'display': 'grid', 'gridTemplateColumns': 'repeat(4,1fr)', 'gap': '16px', 'marginBottom': '20px'}),

        # ── Filter bar ──────────────────────────────────────────────────────
        html.Div(style={**card_style, 'marginBottom': '20px'}, children=[
            html.Div(style={'display': 'flex', 'flexWrap': 'wrap', 'gap': '20px', 'alignItems': 'flex-end'}, children=[
                html.Div(children=[
                    html.Label('Filter by Crime', style={'color': TEXT_SEC, 'fontSize': '12px', 'marginBottom': '6px', 'display': 'block'}),
                    dcc.Dropdown(
                        id='crime-filter',
                        options=[{'label': '— All Crimes —', 'value': 'ALL'}] + [{'label': c, 'value': c} for c in CRIMES],
                        value='ALL', clearable=False,
                        style={'width': '240px', 'backgroundColor': '#1a2332', 'color': TEXT_PRIM, 'border': f'1px solid {BORDER}'},
                    )
                ]),
                html.Div(children=[
                    html.Label('Filter by City', style={'color': TEXT_SEC, 'fontSize': '12px', 'marginBottom': '6px', 'display': 'block'}),
                    dcc.Dropdown(
                        id='city-filter',
                        options=[{'label': '— All Cities —', 'value': 'ALL'}] + [{'label': c, 'value': c} for c in CITIES],
                        value='ALL', clearable=False,
                        style={'width': '200px', 'backgroundColor': '#1a2332', 'color': TEXT_PRIM, 'border': f'1px solid {BORDER}'},
                    )
                ]),
                html.Div(children=[
                    html.Label('Age Group', style={'color': TEXT_SEC, 'fontSize': '12px', 'marginBottom': '6px', 'display': 'block'}),
                    dcc.Dropdown(
                        id='age-filter',
                        options=[
                            {'label': 'All Ages', 'value': 'ALL'},
                            {'label': 'Child (< 18)', 'value': 'child'},
                            {'label': 'Young Adult (18–35)', 'value': 'young'},
                            {'label': 'Adult (36–60)', 'value': 'adult'},
                            {'label': 'Senior (> 60)', 'value': 'senior'},
                        ],
                        value='ALL', clearable=False,
                        style={'width': '210px', 'backgroundColor': '#1a2332', 'color': TEXT_PRIM, 'border': f'1px solid {BORDER}'},
                    )
                ]),
                html.Div(children=[
                    html.Label('Gender', style={'color': TEXT_SEC, 'fontSize': '12px', 'marginBottom': '6px', 'display': 'block'}),
                    dcc.Checklist(
                        id='gender-filter',
                        options=[{'label': ' Male  ', 'value': 'M'}, {'label': ' Female  ', 'value': 'F'}, {'label': ' Other', 'value': 'X'}],
                        value=['M', 'F', 'X'],
                        inline=True,
                        inputStyle={'marginRight': '4px'},
                        labelStyle={'color': TEXT_PRIM, 'marginRight': '14px', 'fontSize': '13px'},
                    )
                ]),
            ])
        ]),

        # ── Row 1: crime bar + city map ─────────────────────────────────────
        html.Div(style={'display': 'grid', 'gridTemplateColumns': '1fr 1fr', 'gap': '16px', 'marginBottom': '16px'}, children=[
            html.Div(style=card_style, children=[
                html.H3('📊 Crimes by Type  — click a bar to drill down', style={'fontSize': '14px', 'color': TEXT_SEC, 'marginBottom': '12px'}),
                dcc.Graph(id='crime-bar', config={'displayModeBar': False}),
            ]),
            html.Div(style=card_style, children=[
                html.H3('🏙️ Crime Count by City', style={'fontSize': '14px', 'color': TEXT_SEC, 'marginBottom': '12px'}),
                dcc.Graph(id='city-bar', config={'displayModeBar': False}),
            ]),
        ]),

        # ── Row 2: gender pie + age histogram ──────────────────────────────
        html.Div(style={'display': 'grid', 'gridTemplateColumns': '1fr 1fr', 'gap': '16px', 'marginBottom': '16px'}, children=[
            html.Div(style=card_style, children=[
                html.H3('⚧ Gender Distribution by State / City', style={'fontSize': '14px', 'color': TEXT_SEC, 'marginBottom': '12px'}),
                dcc.Graph(id='gender-city-chart', config={'displayModeBar': False}),
            ]),
            html.Div(style=card_style, children=[
                html.H3('👥 Victim Age Distribution', style={'fontSize': '14px', 'color': TEXT_SEC, 'marginBottom': '12px'}),
                dcc.Graph(id='age-hist', config={'displayModeBar': False}),
            ]),
        ]),

        # ── Row 3: weapon + monthly trend ──────────────────────────────────
        html.Div(style={'display': 'grid', 'gridTemplateColumns': '1fr 1fr', 'gap': '16px', 'marginBottom': '16px'}, children=[
            html.Div(style=card_style, children=[
                html.H3('🔫 Weapon Used', style={'fontSize': '14px', 'color': TEXT_SEC, 'marginBottom': '12px'}),
                dcc.Graph(id='weapon-chart', config={'displayModeBar': False}),
            ]),
            html.Div(style=card_style, children=[
                html.H3('📅 Monthly Crime Trend', style={'fontSize': '14px', 'color': TEXT_SEC, 'marginBottom': '12px'}),
                dcc.Graph(id='trend-chart', config={'displayModeBar': False}),
            ]),
        ]),

        # ── Drill-down detail table ─────────────────────────────────────────
        html.Div(id='detail-section', style={'display': 'none'}, children=[
            html.Div(style={**card_style, 'borderColor': ACCENT1}, children=[
                html.Div(style={'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center', 'marginBottom': '14px'}, children=[
                    html.H2(id='detail-title', style={'margin': 0, 'fontSize': '18px', 'color': ACCENT1}),
                    html.Button('✕ Close', id='close-detail', n_clicks=0,
                                style={'backgroundColor': 'transparent', 'border': f'1px solid {ACCENT2}',
                                       'color': ACCENT2, 'padding': '6px 16px', 'borderRadius': '6px', 'cursor': 'pointer'}),
                ]),
                html.Div(id='detail-kpis', style={'display': 'flex', 'gap': '20px', 'marginBottom': '16px', 'flexWrap': 'wrap'}),
                html.Div(style={'display': 'grid', 'gridTemplateColumns': '1fr 1fr', 'gap': '16px', 'marginBottom': '16px'}, children=[
                    dcc.Graph(id='detail-gender-pie', config={'displayModeBar': False}),
                    dcc.Graph(id='detail-city-bar', config={'displayModeBar': False}),
                ]),
                html.H4('Full Records', style={'color': TEXT_SEC, 'fontSize': '13px', 'marginBottom': '8px'}),
                dash_table.DataTable(
                    id='detail-table',
                    page_size=15,
                    sort_action='native',
                    filter_action='native',
                    style_table={'overflowX': 'auto'},
                    style_header={'backgroundColor': '#1a2d3d', 'color': ACCENT1, 'fontWeight': '600', 'border': f'1px solid {BORDER}'},
                    style_cell={'backgroundColor': '#0f1d2b', 'color': TEXT_PRIM, 'border': f'1px solid {BORDER}', 'fontSize': '12px', 'padding': '8px 12px'},
                    style_filter={'backgroundColor': '#0d1b2a', 'color': TEXT_PRIM},
                    style_data_conditional=[{'if': {'row_index': 'odd'}, 'backgroundColor': '#0b1523'}],
                )
            ])
        ]),

    ]),  # end padding div
])  # end root div


# ── Helpers ───────────────────────────────────────────────────────────────────
def apply_filters(crime, city, age_group, genders):
    d = df.copy()
    if crime != 'ALL':
        d = d[d['Crime Description'] == crime]
    if city != 'ALL':
        d = d[d['City'] == city]
    if genders:
        d = d[d['Victim Gender'].isin(genders)]
    if age_group == 'child':
        d = d[d['Victim Age'] < 18]
    elif age_group == 'young':
        d = d[(d['Victim Age'] >= 18) & (d['Victim Age'] <= 35)]
    elif age_group == 'adult':
        d = d[(d['Victim Age'] > 35) & (d['Victim Age'] <= 60)]
    elif age_group == 'senior':
        d = d[d['Victim Age'] > 60]
    return d


def dark_fig(fig):
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color=TEXT_PRIM, size=11),
        margin=dict(l=10, r=10, t=30, b=10),
        legend=dict(bgcolor='rgba(0,0,0,0)', bordercolor=BORDER),
        xaxis=dict(gridcolor=BORDER, linecolor=BORDER, zerolinecolor=BORDER),
        yaxis=dict(gridcolor=BORDER, linecolor=BORDER, zerolinecolor=BORDER),
    )
    return fig


def kpi_card(label, value, color=ACCENT1, icon='📌'):
    return html.Div(style={'backgroundColor': CARD_BG, 'border': f'1px solid {BORDER}',
                            'borderRadius': '12px', 'padding': '18px', 'textAlign': 'center'}, children=[
        html.Div(icon, style={'fontSize': '24px'}),
        html.Div(str(value), style={'fontSize': '28px', 'fontWeight': '700', 'color': color}),
        html.Div(label, style={'fontSize': '12px', 'color': TEXT_SEC, 'marginTop': '4px'}),
    ])


# ── KPI row callback ──────────────────────────────────────────────────────────
@app.callback(Output('kpi-row', 'children'),
              [Input('crime-filter', 'value'), Input('city-filter', 'value'),
               Input('age-filter', 'value'), Input('gender-filter', 'value')])
def update_kpis(crime, city, age_group, genders):
    d = apply_filters(crime, city, age_group, genders)
    total     = len(d)
    closed    = (d['Case Closed'] == 'Yes').sum()
    rate      = f"{closed/total*100:.1f}%" if total else '—'
    top_crime = d['Crime Description'].mode()[0] if total else '—'
    top_city  = d['City'].mode()[0] if total else '—'
    return [
        kpi_card('Total Incidents', f'{total:,}', ACCENT1, '📋'),
        kpi_card('Cases Closed', f'{closed:,}', ACCENT4, '✅'),
        kpi_card('Case-Closure Rate', rate, ACCENT3, '📈'),
        kpi_card('Top Crime / City', f'{top_crime}', ACCENT2, '🏆'),
    ]


# ── Crime bar ─────────────────────────────────────────────────────────────────
@app.callback(Output('crime-bar', 'figure'),
              [Input('crime-filter', 'value'), Input('city-filter', 'value'),
               Input('age-filter', 'value'), Input('gender-filter', 'value')])
def update_crime_bar(crime, city, age_group, genders):
    d = apply_filters(crime, city, age_group, genders)
    counts = d['Crime Description'].value_counts().reset_index()
    counts.columns = ['Crime', 'Count']
    fig = go.Figure(go.Bar(
        x=counts['Count'], y=counts['Crime'], orientation='h',
        marker=dict(color=counts['Count'], colorscale=[[0, '#1a3a5c'], [1, ACCENT1]],
                    line=dict(color=BORDER, width=0.5)),
        hovertemplate='<b>%{y}</b><br>Count: %{x:,}<extra></extra>',
        customdata=counts['Crime'],
    ))
    fig.update_layout(height=380, yaxis={'categoryorder': 'total ascending'})
    return dark_fig(fig)


# ── City bar ──────────────────────────────────────────────────────────────────
@app.callback(Output('city-bar', 'figure'),
              [Input('crime-filter', 'value'), Input('city-filter', 'value'),
               Input('age-filter', 'value'), Input('gender-filter', 'value')])
def update_city_bar(crime, city, age_group, genders):
    d = apply_filters(crime, city, age_group, genders)
    counts = d['City'].value_counts().head(15).reset_index()
    counts.columns = ['City', 'Count']
    fig = go.Figure(go.Bar(
        x=counts['City'], y=counts['Count'],
        marker=dict(color=counts['Count'], colorscale=[[0, '#1a3a5c'], [1, ACCENT2]],
                    line=dict(color=BORDER, width=0.5)),
        hovertemplate='<b>%{x}</b><br>Count: %{y:,}<extra></extra>',
    ))
    fig.update_layout(height=380)
    return dark_fig(fig)


# ── Gender by city ────────────────────────────────────────────────────────────
@app.callback(Output('gender-city-chart', 'figure'),
              [Input('crime-filter', 'value'), Input('city-filter', 'value'),
               Input('age-filter', 'value'), Input('gender-filter', 'value')])
def update_gender_city(crime, city, age_group, genders):
    d = apply_filters(crime, city, age_group, genders)
    grp = d.groupby(['City', 'Gender Label']).size().reset_index(name='Count')
    top_cities = d['City'].value_counts().head(12).index.tolist()
    grp = grp[grp['City'].isin(top_cities)]

    fig = go.Figure()
    for gender, color in GENDER_COLORS.items():
        sub = grp[grp['Gender Label'] == gender]
        fig.add_trace(go.Bar(
            x=sub['City'], y=sub['Count'], name=gender,
            marker_color=color,
            hovertemplate=f'<b>%{{x}}</b><br>{gender}: %{{y:,}}<extra></extra>',
        ))
    fig.update_layout(barmode='group', height=380, legend=dict(orientation='h', y=1.08))
    return dark_fig(fig)


# ── Age histogram ─────────────────────────────────────────────────────────────
@app.callback(Output('age-hist', 'figure'),
              [Input('crime-filter', 'value'), Input('city-filter', 'value'),
               Input('age-filter', 'value'), Input('gender-filter', 'value')])
def update_age_hist(crime, city, age_group, genders):
    d = apply_filters(crime, city, age_group, genders)
    fig = go.Figure()
    for gender, color in GENDER_COLORS.items():
        sub = d[d['Gender Label'] == gender]
        fig.add_trace(go.Histogram(
            x=sub['Victim Age'], name=gender, nbinsx=20,
            marker_color=color, opacity=0.75,
            hovertemplate=f'{gender}<br>Age: %{{x}}<br>Count: %{{y:,}}<extra></extra>',
        ))
    fig.update_layout(barmode='overlay', height=380, legend=dict(orientation='h', y=1.08))
    return dark_fig(fig)


# ── Weapon ────────────────────────────────────────────────────────────────────
@app.callback(Output('weapon-chart', 'figure'),
              [Input('crime-filter', 'value'), Input('city-filter', 'value'),
               Input('age-filter', 'value'), Input('gender-filter', 'value')])
def update_weapon(crime, city, age_group, genders):
    d = apply_filters(crime, city, age_group, genders)
    counts = d['Weapon Used'].value_counts().reset_index()
    counts.columns = ['Weapon', 'Count']
    colors = [ACCENT1, ACCENT2, ACCENT3, ACCENT4, '#a855f7', '#f97316', '#ec4899']
    fig = go.Figure(go.Pie(
        labels=counts['Weapon'], values=counts['Count'],
        hole=0.4,
        marker=dict(colors=colors[:len(counts)], line=dict(color=BG, width=2)),
        hovertemplate='<b>%{label}</b><br>Count: %{value:,}<br>%{percent}<extra></extra>',
    ))
    fig.update_layout(height=380)
    return dark_fig(fig)


# ── Monthly trend ─────────────────────────────────────────────────────────────
@app.callback(Output('trend-chart', 'figure'),
              [Input('crime-filter', 'value'), Input('city-filter', 'value'),
               Input('age-filter', 'value'), Input('gender-filter', 'value')])
def update_trend(crime, city, age_group, genders):
    d = apply_filters(crime, city, age_group, genders)
    d2 = d.dropna(subset=['Date of Occurrence'])
    monthly = d2.groupby(d2['Date of Occurrence'].dt.to_period('M')).size().reset_index(name='Count')
    monthly['Month'] = monthly['Date of Occurrence'].astype(str)
    fig = go.Figure(go.Scatter(
        x=monthly['Month'], y=monthly['Count'],
        mode='lines+markers',
        line=dict(color=ACCENT1, width=2),
        marker=dict(color=ACCENT1, size=5),
        fill='tozeroy', fillcolor='rgba(0,212,255,0.08)',
        hovertemplate='<b>%{x}</b><br>Incidents: %{y:,}<extra></extra>',
    ))
    fig.update_layout(height=380)
    return dark_fig(fig)


# ── Drill-down: click crime bar ───────────────────────────────────────────────
@app.callback(
    [Output('detail-section', 'style'),
     Output('detail-title', 'children'),
     Output('detail-kpis', 'children'),
     Output('detail-gender-pie', 'figure'),
     Output('detail-city-bar', 'figure'),
     Output('detail-table', 'data'),
     Output('detail-table', 'columns')],
    [Input('crime-bar', 'clickData'), Input('close-detail', 'n_clicks')],
    [State('city-filter', 'value'), State('age-filter', 'value'), State('gender-filter', 'value')],
    prevent_initial_call=True,
)
def drill_down(click_data, close_clicks, city, age_group, genders):
    from dash import ctx
    hidden = {'display': 'none'}
    visible = {'display': 'block'}
    empty_fig = go.Figure()
    dark_fig(empty_fig)

    if ctx.triggered_id == 'close-detail' or click_data is None:
        return hidden, '', [], empty_fig, empty_fig, [], []

    crime_name = click_data['points'][0]['y']
    d = apply_filters(crime_name, city, age_group, genders)
    total     = len(d)
    closed    = (d['Case Closed'] == 'Yes').sum()
    avg_age   = d['Victim Age'].mean()
    avg_police= d['Police Deployed'].mean()

    # KPI mini cards
    mini_kpis = [
        html.Div(style={'backgroundColor': '#0d1b2a', 'border': f'1px solid {BORDER}',
                        'borderRadius': '8px', 'padding': '12px 20px', 'textAlign': 'center', 'minWidth': '120px'}, children=[
            html.Div(icon, style={'fontSize': '20px'}),
            html.Div(val, style={'fontSize': '22px', 'fontWeight': '700', 'color': color}),
            html.Div(lbl, style={'fontSize': '11px', 'color': TEXT_SEC}),
        ])
        for icon, val, color, lbl in [
            ('📋', f'{total:,}', ACCENT1, 'Total Incidents'),
            ('✅', f'{closed:,}', ACCENT4, 'Cases Closed'),
            ('📈', f"{closed/total*100:.1f}%" if total else '—', ACCENT3, 'Closure Rate'),
            ('🎂', f"{avg_age:.1f} yrs" if not pd.isna(avg_age) else '—', ACCENT2, 'Avg Victim Age'),
            ('👮', f"{avg_police:.1f}" if not pd.isna(avg_police) else '—', '#a855f7', 'Avg Police Deployed'),
        ]
    ]

    # Gender pie
    gender_counts = d['Gender Label'].value_counts().reset_index()
    gender_counts.columns = ['Gender', 'Count']
    pie_colors = [GENDER_COLORS.get(g, '#888') for g in gender_counts['Gender']]
    pie_fig = go.Figure(go.Pie(
        labels=gender_counts['Gender'], values=gender_counts['Count'],
        hole=0.45,
        marker=dict(colors=pie_colors, line=dict(color=BG, width=2)),
        hovertemplate='<b>%{label}</b><br>%{value:,} (%{percent})<extra></extra>',
    ))
    pie_fig.update_layout(title=dict(text='Gender Split', font=dict(color=TEXT_SEC, size=13)), height=300)
    dark_fig(pie_fig)

    # City breakdown bar
    city_counts = d['City'].value_counts().reset_index()
    city_counts.columns = ['City', 'Count']
    bar_fig = go.Figure(go.Bar(
        x=city_counts['City'], y=city_counts['Count'],
        marker=dict(color=city_counts['Count'], colorscale=[[0,'#1a3a5c'],[1,ACCENT2]]),
        hovertemplate='<b>%{x}</b><br>%{y:,}<extra></extra>',
    ))
    bar_fig.update_layout(title=dict(text='City Breakdown', font=dict(color=TEXT_SEC, size=13)), height=300)
    dark_fig(bar_fig)

    # Table
    show_cols = ['Report Number', 'Date of Occurrence', 'City', 'Crime Description',
                 'Victim Age', 'Victim Gender', 'Weapon Used', 'Crime Domain',
                 'Police Deployed', 'Case Closed']
    table_df = d[show_cols].copy()
    table_df['Date of Occurrence'] = table_df['Date of Occurrence'].astype(str)
    columns = [{'name': c, 'id': c, 'type': 'text'} for c in show_cols]
    data = table_df.to_dict('records')

    return (
        visible,
        f'🔎  Deep Dive — {crime_name}  ({total:,} incidents)',
        mini_kpis,
        pie_fig,
        bar_fig,
        data,
        columns,
    )


if __name__ == '__main__':
    print('\n🚀  Dashboard starting → http://127.0.0.1:8050\n')
    app.run(debug=False, port=8050, host='0.0.0.0')