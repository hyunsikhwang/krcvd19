import requests
import bs4
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st


st.set_page_config(
    page_title="COVID-19 in Korea",
    page_icon=":shark:",
    layout="wide",
    initial_sidebar_state="expanded"
    )

st.title("COVID-19 in Korea")

def get_bs(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
    return bs4.BeautifulSoup(requests.get(url, headers=headers).text, "lxml")


def get_covid19_xlsx():
    url = 'http://ncov.mohw.go.kr'
    response = get_bs(url)

    # 질병관리청 매일 오전 10시 발표 코로나 환자 현황 Excel File 링크
    #for a in response.findAll('div', {"class":"liveNum_today_new"}):
    for a in response.findAll('div', {"class":"occur_num"}):   
        for b in a.findAll('a'):                                         
            path = url + b.get('href')
    
    return path


@st.experimental_memo
def init(path):
    try:

        # File Download (COVID-19.xlsx)
        r = requests.get(path, allow_redirects=True)
        open('./COVID-19.xlsx', 'wb').write(r.content)

        xls = pd.ExcelFile('COVID-19.xlsx')

        df1 = pd.read_excel(xls, '발생별(국내발생+해외유입), 사망', skiprows=3, header=1)
        df2 = pd.read_excel(xls, '성별(남+여)', skiprows=3, header=1)
        df3 = pd.read_excel(xls, '연령별(10세단위)', skiprows=3, header=1)

        df1 = df1.iloc[1:]
        df2 = df2.iloc[1:]
        df3 = df3.iloc[1:]

        df1 = df1.drop(['국내발생(명)', '해외유입(명)'], axis='columns')
        #df1 = df1.melt(id_vars='일자', value_vars=['계(명)', '사망(명)'])

        df3 = df3.drop(['계(명)'], axis='columns')
        df3 = df3.melt(id_vars='일자', value_vars=['0-9세', '10-19세', '20-29세', '30-39세', '40-49세', '50-59세', '60-69세', '70-79세', '80세이상'])
        df3 = df3.rename(columns={'variable':'연령대', 'value':'확진환자수'})

        #display(df3)

    except Exception as e:
        print(e)
        st.write(e)
        pass

    df_pop = pd.read_excel('./성_및_연령별_추계인구_1세별__5세별____전국.xlsx')

    return df1, df2, df3, df_pop

path = get_covid19_xlsx()

df1_org, df2_org, df3_org, df_pop_org = init(path)

df1 = df1_org.copy()
df2 = df2_org.copy()
df3 = df3_org.copy()
df_pop = df_pop_org.copy()

df_pop = df_pop[['성별', '연령별', '2021']]
df_pop.loc[1:17, '성별'] = '전체'
df_pop.loc[19:35, '성별'] = '남자'
df_pop.loc[37:53, '성별'] = '여자'


df_pop.loc[len(df_pop)] = ['전체', '0-9세', df_pop.iloc[1:3]['2021'].sum()]
df_pop.loc[len(df_pop)] = ['전체', '10-19세', df_pop.iloc[3:5]['2021'].sum()]
df_pop.loc[len(df_pop)] = ['전체', '20-29세', df_pop.iloc[5:7]['2021'].sum()]
df_pop.loc[len(df_pop)] = ['전체', '30-39세', df_pop.iloc[7:9]['2021'].sum()]
df_pop.loc[len(df_pop)] = ['전체', '40-49세', df_pop.iloc[9:11]['2021'].sum()]
df_pop.loc[len(df_pop)] = ['전체', '50-59세', df_pop.iloc[11:13]['2021'].sum()]
df_pop.loc[len(df_pop)] = ['전체', '60-69세', df_pop.iloc[13:15]['2021'].sum()]
df_pop.loc[len(df_pop)] = ['전체', '70-79세', df_pop.iloc[15:17]['2021'].sum()]
#df_pop.loc[len(df_pop)] = ['전체', '80세이상', df_pop.iloc[17:18]['2021'].sum()]

# 확진자 통계에 2021 추계인구 merge
df4 = df3.merge(df_pop[(df_pop['성별']=='전체')], how='left', left_on=['연령대'], right_on=['연령별'])

# 발생률(백만명당 발생자수) 계산
df4['확진환자수'] = df4['확진환자수'].replace('-', '0').astype(float)
df4['발생률'] = df4['확진환자수'] / df4['2021'] * 1000000
df4['일자별발생률합'] = df4.groupby(['일자'])['발생률'].transform('sum')
df4['발생률비중'] = df4['발생률'] / df4['일자별발생률합'] * 100


df4['확진환자수MA'] = df4['확진환자수'].rolling(window=7).mean()
df4['발생률MA'] = df4['확진환자수MA'] / df4['2021'] * 1000000
df4['일자별발생률합MA'] = df4.groupby(['일자'])['발생률MA'].transform('sum')
df4['발생률비중MA'] = df4['발생률MA'] / df4['일자별발생률합MA'] * 100

df4 = df4.fillna(0)

fig4 = px.area(df4, x="일자", y="발생률비중MA", color="연령대")
fig4.update_xaxes(dtick='M1')
#fig4.show()
st.plotly_chart(fig4, use_container_width=True)

fig5 = px.line(df4, x='일자', y='발생률MA', line_group='연령대', color='연령대')
#fig5.show()
st.plotly_chart(fig5, use_container_width=True)

#display(df4)
#fig4.write_html("file.html")




mvAvg = 7

df1['확진환자수MA'] = df1['계(명)'].rolling(window=mvAvg).mean()

df1['사망(명)'] = df1['사망(명)'].replace('-', '0').astype(float)
df1['사망자수MA'] = df1['사망(명)'].rolling(window=mvAvg).mean()

#df4 = df1.merge(df_pop[(df_pop['성별']=='전체')], how='left', left_on=['연령대'], right_on=['연령별'])
df1['총인구수'] = df_pop.iloc[0, 2]
df1['Cases per mil'] = df1['확진환자수MA'] / df1['총인구수'] * 1000000
df1['Deaths per mil'] = df1['사망자수MA'] / df1['총인구수'] * 1000000
df1 = df1.fillna(0)


fig1 = make_subplots(specs=[[{"secondary_y": True}]])

fig1.add_trace(go.Scatter(x=df1['일자'],
                    y=df1['Cases per mil'],
                    name='Cases',
                    mode='lines',
                    yaxis='y1')
)

fig1.add_trace(go.Scatter(x=df1['일자'],
                    y=df1['Deaths per mil'],
                    name='Deaths',
                    mode='lines',
                    yaxis='y2')
)

fig1.update_layout(
    title_text="<b>코로나-19 확진환자 일자별 발생 및 사망 현황(백만명당)</b>"
)
fig1.update_xaxes(dtick='M1')

df1['date'] = df1['일자'].dt.strftime('%Y%m%d')

#display(df1[(df1['date'].str[6:8]=='01')])

#fig1.show()

# Todo: 이 부분을 Cases 또는 Deaths 의 max 값 대비 일정 비율로 autoscaling 되도록 변경
#x_max = 250
#y_max = 2

scale = st.selectbox('Scale', ['Max', 'Current'], key='Max')

if scale=='Current':
    x_max = df1.tail(1)['Cases per mil'].values[0] * 1.5
    y_max = df1.tail(1)['Deaths per mil'].values[0] * 1.5
else:
    x_max = df1['Cases per mil'].max() * 1.1
    y_max = df1['Deaths per mil'].max() * 1.1


fig2 = px.scatter(df1[(df1['date'].str[6:8].isin(['01', '15']))]
                  , x="Cases per mil"
                  , y="Deaths per mil"
                  , animation_frame="date"
                  , size='확진환자수MA'
                  , range_x=[0,x_max]
                  , range_y=[0,y_max])
#fig2.show()

df2 = pd.concat([df1[(df1['date'].str[6:8].isin(['01', '06', '11', '16', '21', '26']))], df1.tail(1)])
df2 = pd.concat([df1.iloc[::5], df1.tail(15)]).drop_duplicates('date').sort_values('date')
#df2 = df1

N = len(df2['Cases per mil'].tolist())


fig = go.Figure(
    data=[go.Scatter(x=df2['Cases per mil'], y=df2['Deaths per mil'],
                     mode="lines+markers",
                     customdata=df2['date'],
                     hovertemplate='<b>Date: %{customdata}</b><br><br>Cases: %{x:.2f}<br>Death: %{y:.2f}',
                     line_shape='spline',
                     name='Scatter',
                     line=dict(width=2, color="blue")),
          go.Scatter(x=df2['Cases per mil'], y=df2['Deaths per mil'],
                     mode="lines+markers",
                     customdata=df2['date'],
                     hovertemplate='<b>Date: %{customdata}</b><br><br>Cases: %{x:.2f}<br>Death: %{y:.2f}',
                     line_shape='spline',
                     name='Line',
                     line=dict(width=2, color="blue"))],
    layout=go.Layout(
        xaxis=dict(range=[0, x_max], autorange=False, zeroline=False, title_text='Cases per 1M pop'),
        yaxis=dict(range=[0, y_max], autorange=False, zeroline=False, title_text='Deaths per 1M pop'),
        autosize=False,
        width=1200,
        height=700,
        title_text=f"COVID-19 confirmed cases and deaths in Korea ({mvAvg} days moving average)", hovermode="closest",
        updatemenus=[dict(type="buttons",
                          buttons=[
                                   dict(label="Play",
                                        method="animate",
                                        args=[None, {"frame": {"duration": 50, "redraw": True},}]),
                                   dict(label="Pause",
                                        method="animate",
                                        args=[[None], {"frame": {"duration": 0, "redraw": False},"mode":"immediate", "transition": {"duration": 0}}]),
                                  ])],
        ),
    frames=[go.Frame(
        data=[go.Scatter(
            x=[df2['Cases per mil'].tolist()[k]],
            y=[df2['Deaths per mil'].tolist()[k]],
            mode="markers+text",
            text=[df2['date'].tolist()[k]],
            textposition="top center",
            marker=dict(color="red", size=15))],
        
        )
        for k in range(N)],
    
)

#x_adj = 100 / x_max
#y_adj = 1 / y_max

#fig.add_shape(type="rect", xref="paper", yref="paper", x0=0, y0=0, x1=0.2*x_adj, y1=1, line=dict(color="Green", width=0,), fillcolor="Green", opacity=0.4,)
#fig.add_shape(type="rect", xref="paper", yref="paper", x0=0.2*x_adj, y0=0, x1=0.8*x_adj, y1=0.4*y_adj, line=dict(color="Green", width=0,), fillcolor="Green", opacity=0.4,)
#fig.add_shape(type="rect", xref="paper", yref="paper", x0=0.2*x_adj, y0=0.4*y_adj, x1=0.8*x_adj, y1=1, line=dict(color="Yellow", width=0,), fillcolor="Yellow", opacity=0.4,)
#fig.add_shape(type="rect", xref="paper", yref="paper", x0=0.8*x_adj, y0=0.4*y_adj, x1=1, y1=1, line=dict(color="Red", width=0,), fillcolor="Red", opacity=0.4,)
#fig.add_shape(type="rect", xref="paper", yref="paper", x0=0.8*x_adj, y0=0, x1=1, y1=0.4*y_adj, line=dict(color="Yellow", width=0,), fillcolor="Yellow", opacity=0.4,)

# Add shapes
fig.add_shape(type="rect", x0=0,   y0=0,   x1=100,     y1=5.0,   line=dict(color="Green",  width=0,), fillcolor="Green",  opacity=0.4,)
fig.add_shape(type="rect", x0=0,   y0=5.0, x1=100,     y1=y_max, line=dict(color="Green",  width=0,), fillcolor="Yellow", opacity=0.4,)
fig.add_shape(type="rect", x0=100, y0=0,   x1=800,     y1=2.0,   line=dict(color="Green",  width=0,), fillcolor="Green",  opacity=0.4,)
fig.add_shape(type="rect", x0=100, y0=2.0, x1=800,     y1=5.0,   line=dict(color="Yellow", width=0,), fillcolor="Yellow", opacity=0.4,)
fig.add_shape(type="rect", x0=100, y0=5.0, x1=800,     y1=y_max, line=dict(color="Yellow", width=0,), fillcolor="Red",    opacity=0.4,)
fig.add_shape(type="rect", x0=800, y0=0,   x1=x_max,   y1=2.0,   line=dict(color="Yellow", width=0,), fillcolor="Yellow", opacity=0.4,)
fig.add_shape(type="rect", x0=800, y0=2.0, x1=x_max,   y1=y_max, line=dict(color="Red",    width=0,), fillcolor="Red",    opacity=0.4,)


fig.update_xaxes(showspikes=True, spikecolor="green", spikesnap="cursor", spikemode="across")
fig.update_yaxes(showspikes=True, spikecolor="orange", spikethickness=2)
fig.update_layout(height=800, spikedistance=1000, hoverdistance=100)


#fig.show()
st.plotly_chart(fig, use_container_width=True)
#fig.write_html('COVID-19_Korea.html')
