import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
import streamlit as st
import warnings
warnings.filterwarnings('ignore')

# ── Configuración de la página ────────────────────────────────────────────────
st.set_page_config(
    page_title="La Anatomía de un Gol de Messi",
    page_icon="⚽",
    layout="wide"
)

# ── Estilos ───────────────────────────────────────────────────────────────────
DARK_BG   = '#0e1117'
GOLD      = '#f5c518'
BLUE      = '#4a90d9'
RED       = '#e05252'
GREEN     = '#5cb85c'

def set_style():
    plt.rcParams['figure.facecolor']  = DARK_BG
    plt.rcParams['axes.facecolor']    = DARK_BG
    plt.rcParams['axes.edgecolor']    = '#333333'
    plt.rcParams['axes.labelcolor']   = '#cccccc'
    plt.rcParams['xtick.color']       = '#cccccc'
    plt.rcParams['ytick.color']       = '#cccccc'
    plt.rcParams['text.color']        = '#ffffff'
    plt.rcParams['grid.color']        = '#222222'
    plt.rcParams['grid.linestyle']    = '--'
    plt.rcParams['grid.alpha']        = 0.5
    plt.rcParams['font.family']       = 'sans-serif'

set_style()

# ── Carga de datos ────────────────────────────────────────────────────────────
SHEET_ID = '1-MQcfFuBED9VTE1vsruclxFfYNlSkQmf422NaY7Xb84'

@st.cache_data(ttl=3600)
def cargar_datos():
    url = f'https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv'
    df = pd.read_csv(url)

    df['Fecha'] = pd.to_datetime(df['Fecha'], dayfirst=True, errors='coerce')
    df['Año']   = df['Fecha'].dt.year
    df['Mes']   = df['Fecha'].dt.month

    df['Temporada'] = df['Fecha'].apply(
        lambda d: f"{d.year}/{str(d.year+1)[-2:]}" if pd.notnull(d) and d.month >= 8
        else (f"{d.year-1}/{str(d.year)[-2:]}" if pd.notnull(d) else None)
    )

    def parse_minuto(m):
        m = str(m).replace(' ', '')
        if '+' in m:
            parts = m.split('+')
            try: return int(parts[0]) + int(parts[1])
            except: return None
        try: return int(m)
        except: return None

    df['Minuto_num'] = df['Minuto'].apply(parse_minuto)
    df['Mitad'] = df['Minuto_num'].apply(
        lambda m: 'Primer tiempo' if m is not None and m <= 45
        else ('Segundo tiempo' if m is not None else 'Desconocido')
    )

    def era(equipo):
        equipo = str(equipo)
        if 'Barcelona' in equipo: return 'FC Barcelona'
        if 'Paris' in equipo or 'PSG' in equipo: return 'PSG'
        if 'Miami' in equipo: return 'Inter Miami'
        if 'Argentina' in equipo: return 'Selección Argentina'
        return 'Otro'

    df['Era'] = df['Equipo Local'].apply(era)
    df.loc[df['Era'] == 'Otro', 'Era'] = df.loc[df['Era'] == 'Otro', 'Equipo Visitante'].apply(era)

    def tipo_simple(t):
        if pd.isna(t): return 'Gol de campo'
        t = str(t).strip()
        if t in ['Penal', 'Tiro libre']: return t
        return 'Gol de campo'

    df['Tipo_simple'] = df['Tipo'].apply(tipo_simple)
    df['Pie'] = df['Cómo'].str.strip().str.title().replace({
        'Pie Izquierdo': 'Pie izquierdo',
        'Pie Derecho':   'Pie derecho',
    })

    def simplificar_comp(c):
        c = str(c)
        if 'Champions' in c: return 'Champions League'
        if 'La Liga' in c or ('Liga' in c and 'Major' not in c): return 'La Liga'
        if 'Copa del Rey' in c: return 'Copa del Rey'
        if 'World Cup' in c and 'WCQ' not in c and 'Qualif' not in c and 'WCT' not in c: return 'Copa del Mundo'
        if 'Copa América' in c or 'CPA' in c: return 'Copa América'
        if 'Eliminatorias' in c or 'WCQ' in c: return 'Eliminatorias'
        if 'Major League' in c or 'MLS' in c: return 'MLS'
        if 'Amistoso' in c: return 'Amistosos'
        if 'Club World Cup' in c or 'WCT' in c: return 'Club World Cup'
        return 'Otros'

    df['Competicion_simple'] = df['Competición'].apply(simplificar_comp)

    return df

# ── Carga ─────────────────────────────────────────────────────────────────────
with st.spinner('Cargando datos desde Google Sheets...'):
    df_full = cargar_datos()

# ── Header ────────────────────────────────────────────────────────────────────
st.title('⚽ La Anatomía de un Gol de Messi')
st.markdown('Análisis exploratorio de **{}** goles — desde 2005 hasta hoy.'.format(len(df_full)))
st.divider()

# ── Sidebar con filtros ───────────────────────────────────────────────────────
st.sidebar.header('Filtros')

eras_disponibles = ['Todas'] + sorted([e for e in df_full['Era'].unique() if e != 'Otro'])
era_sel = st.sidebar.selectbox('Era / Club', eras_disponibles)

comps_disponibles = ['Todas'] + sorted(df_full['Competicion_simple'].unique().tolist())
comp_sel = st.sidebar.selectbox('Competición', comps_disponibles)

tipos_disponibles = ['Todos'] + sorted(df_full['Tipo_simple'].unique().tolist())
tipo_sel = st.sidebar.selectbox('Tipo de gol', tipos_disponibles)

st.sidebar.divider()
st.sidebar.markdown('📊 Datos actualizados automáticamente desde [Google Sheets](https://docs.google.com/spreadsheets/d/{}).'.format(SHEET_ID))

# ── Aplicar filtros ───────────────────────────────────────────────────────────
df = df_full.copy()
if era_sel  != 'Todas': df = df[df['Era'] == era_sel]
if comp_sel != 'Todas': df = df[df['Competicion_simple'] == comp_sel]
if tipo_sel != 'Todos': df = df[df['Tipo_simple'] == tipo_sel]

# ── Métricas rápidas ──────────────────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
col1.metric('Total de goles', len(df))
col2.metric('Temporadas', df['Temporada'].nunique())
col3.metric('Competiciones', df['Competicion_simple'].nunique())
col4.metric('% de zurda', f"{(df['Pie'] == 'Pie izquierdo').mean()*100:.1f}%")

st.divider()

# ── Gráfico 1: Goles por temporada ───────────────────────────────────────────
st.subheader('Goles por temporada')

goles_temp = df.groupby('Temporada').size().reset_index(name='Goles')
era_por_temp = df.groupby('Temporada')['Era'].agg(lambda x: x.value_counts().index[0]).reset_index()
era_por_temp.columns = ['Temporada', 'Era_principal']
goles_temp = goles_temp.merge(era_por_temp, on='Temporada')

color_map = {
    'FC Barcelona':       GOLD,
    'PSG':                '#0069b4',
    'Inter Miami':        '#f7b5cd',
    'Selección Argentina':'#74acdf',
    'Otro':               '#888'
}
colores = goles_temp['Era_principal'].map(color_map).fillna('#888')

fig1, ax1 = plt.subplots(figsize=(14, 5))
ax1.bar(goles_temp['Temporada'], goles_temp['Goles'], color=colores, width=0.7, zorder=3)
media = goles_temp['Goles'].mean()
ax1.axhline(media, color='#ffffff', linewidth=1, linestyle='--', alpha=0.4, label=f'Media: {media:.0f} goles/temporada')
ax1.set_xlabel('Temporada', fontsize=11)
ax1.set_ylabel('Goles', fontsize=11)
ax1.tick_params(axis='x', rotation=45)
ax1.grid(axis='y', zorder=0)

eras_legend = [mpatches.Patch(color=v, label=k) for k, v in color_map.items() if k != 'Otro']
ax1.legend(handles=eras_legend, loc='upper left', fontsize=9, framealpha=0.2)

plt.tight_layout()
st.pyplot(fig1)
plt.close()

st.divider()

# ── Gráficos 2 y 3 en columnas ────────────────────────────────────────────────
col_izq, col_der = st.columns(2)

# Gráfico 2: Minutos
with col_izq:
    st.subheader('¿En qué minuto mete más goles?')
    df_min = df.dropna(subset=['Minuto_num']).copy()
    df_min['Franja'] = pd.cut(df_min['Minuto_num'],
                               bins=[0,15,30,45,60,75,90,120],
                               labels=['1-15','16-30','31-45','46-60','61-75','76-90','90+'])
    conteo = df_min['Franja'].value_counts().sort_index()
    pct    = (conteo / conteo.sum() * 100).round(1)

    fig2, ax2 = plt.subplots(figsize=(7, 5))
    bar_colors = [GOLD if v == conteo.max() else BLUE for v in conteo.values]
    bars = ax2.bar(conteo.index.astype(str), conteo.values, color=bar_colors, edgecolor='#1a1a2e', linewidth=0.5, zorder=3)
    for bar, p in zip(bars, pct.values):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                 f'{p}%', ha='center', va='bottom', fontsize=8, color='#cccccc')
    ax2.axvline(x=2.5, color='#ffffff', linewidth=1.5, linestyle='--', alpha=0.3)
    ax2.text(2.6, conteo.max() * 0.92, 'Descanso', fontsize=8, color='#aaaaaa')
    ax2.set_xlabel('Franja de minutos', fontsize=10)
    ax2.set_ylabel('Cantidad de goles', fontsize=10)
    ax2.grid(axis='y', zorder=0)
    plt.tight_layout()
    st.pyplot(fig2)
    plt.close()

# Gráfico 3: Pie
with col_der:
    st.subheader('¿Con qué pie mete los goles?')
    conteo_pie = df['Pie'].value_counts()

    fig3, ax3 = plt.subplots(figsize=(7, 5))
    pie_colors = [GOLD, BLUE, RED, GREEN, '#888']
    wedges, texts, autotexts = ax3.pie(
        conteo_pie.values, labels=conteo_pie.index,
        autopct='%1.1f%%', colors=pie_colors[:len(conteo_pie)],
        startangle=90, pctdistance=0.8,
        wedgeprops={'edgecolor': DARK_BG, 'linewidth': 2}
    )
    for text in texts: text.set_color('white'); text.set_fontsize(10)
    for at in autotexts: at.set_color(DARK_BG); at.set_fontweight('bold')
    plt.tight_layout()
    st.pyplot(fig3)
    plt.close()

st.divider()

# ── Gráfico 4: Tipo de gol por era ───────────────────────────────────────────
st.subheader('Tipo de gol por club/era')

era_order = ['FC Barcelona', 'PSG', 'Inter Miami']
df_club = df[df['Era'].isin(era_order)]

if len(df_club) > 0:
    pivot_tipo = df_club.groupby(['Era', 'Tipo_simple']).size().unstack(fill_value=0)
    pivot_pct  = pivot_tipo.div(pivot_tipo.sum(axis=1), axis=0) * 100
    pivot_pct  = pivot_pct.reindex([e for e in era_order if e in pivot_pct.index])

    fig4, ax4 = plt.subplots(figsize=(10, 5))
    tipo_colors = {'Gol de campo': GOLD, 'Penal': BLUE, 'Tiro libre': RED}
    bottom = np.zeros(len(pivot_pct))

    for tipo, color in tipo_colors.items():
        if tipo in pivot_pct.columns:
            vals = pivot_pct[tipo].values
            bars = ax4.bar(pivot_pct.index, vals, bottom=bottom, label=tipo,
                           color=color, edgecolor=DARK_BG, linewidth=0.5)
            for i, (bar, v) in enumerate(zip(bars, vals)):
                if v > 5:
                    ax4.text(bar.get_x() + bar.get_width()/2,
                             bottom[i] + v/2, f'{v:.0f}%',
                             ha='center', va='center', fontsize=11,
                             color=DARK_BG, fontweight='bold')
            bottom += vals

    ax4.set_ylabel('% de goles', fontsize=11)
    ax4.legend(fontsize=10, loc='lower right')
    ax4.set_ylim(0, 110)
    ax4.grid(axis='y', zorder=0)
    plt.tight_layout()
    st.pyplot(fig4)
    plt.close()
else:
    st.info('No hay datos para mostrar con los filtros seleccionados.')

st.divider()

# ── Gráfico 5: Competiciones ──────────────────────────────────────────────────
st.subheader('Goles por competición')

top_comp = df.groupby('Competicion_simple').size().sort_values(ascending=True).tail(10)

fig5, ax5 = plt.subplots(figsize=(10, 6))
bar_colors5 = [GOLD if v == top_comp.max() else BLUE for v in top_comp.values]
bars5 = ax5.barh(top_comp.index, top_comp.values, color=bar_colors5,
                  edgecolor=DARK_BG, linewidth=0.5)
for bar in bars5:
    ax5.text(bar.get_width() + 2, bar.get_y() + bar.get_height()/2,
             f'{int(bar.get_width())}', va='center', ha='left', fontsize=10)
ax5.set_xlabel('Cantidad de goles', fontsize=11)
ax5.set_xlim(0, top_comp.max() * 1.15)
ax5.grid(axis='x', zorder=0)
plt.tight_layout()
st.pyplot(fig5)
plt.close()

st.divider()

# ── Gráfico 6: Heatmap mensual ────────────────────────────────────────────────
st.subheader('Patrón estacional — goles por mes y año')

df_hm = df[(df['Año'] >= 2007) & df['Mes'].notna() & df['Año'].notna()].copy()
pivot_hm = df_hm.groupby(['Año', 'Mes']).size().unstack(fill_value=0)
meses = ['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic']
pivot_hm.columns = [meses[i-1] for i in pivot_hm.columns]

if len(pivot_hm) > 0:
    fig6, ax6 = plt.subplots(figsize=(14, max(6, len(pivot_hm) * 0.45)))
    sns.heatmap(
        pivot_hm, cmap='YlOrRd', linewidths=0.3, linecolor=DARK_BG,
        annot=True, fmt='d', ax=ax6,
        cbar_kws={'label': 'Cantidad de goles'},
        annot_kws={'size': 8}
    )
    ax6.set_xlabel('Mes', fontsize=11)
    ax6.set_ylabel('Año', fontsize=11)
    ax6.tick_params(axis='x', rotation=0)
    plt.tight_layout()
    st.pyplot(fig6)
    plt.close()
else:
    st.info('No hay suficientes datos para el heatmap con los filtros seleccionados.')

st.divider()
st.caption('Datos obtenidos desde Google Sheets · Análisis por Leandro Corvalan · Estudiante de Ciencia de Datos, UBA')
