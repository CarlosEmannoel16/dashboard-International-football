import kagglehub
import streamlit as st
import pandas as pd
import plotly.express as px

path = kagglehub.dataset_download("martj42/international-football-results-from-1872-to-2017")

df = pd.read_csv(f"{path}/results.csv")
df2 = pd.read_csv(f"{path}/goalscorers.csv")

st.title('Análise de Resultados de Futebol Internacional')
st.markdown('Este aplicativo permite explorar dados de resultados de futebol internacional e artilheiros.')

st.header('Dados dos Jogos')
st.dataframe(df)
st.header('Artilheiros')
st.dataframe(df2)

st.sidebar.title('Filtros')
country = st.sidebar.selectbox('Selecione o país', df['home_team'].unique(), key='country_selectbox')
selected_city = st.sidebar.selectbox('Selecione a cidade', df['city'].unique(), key='city_selectbox')
selected_scorer = st.sidebar.selectbox('Selecione o artilheiro', df2['scorer'].unique(), key='scorer_selectbox')
num_countries = st.sidebar.slider('Quantidade de Países', min_value=1, max_value=50, value=10, key='countries_slider')

# Filtra os jogos em que o país é o time da casa ou o time visitante e ganhou o jogo
country_wins = df[((df['home_team'] == country) & (df['home_score'] > df['away_score'])) |
                  ((df['away_team'] == country) & (df['away_score'] > df['home_score']))]

competitions = df[(df['home_team'] == country) | (df['away_team'] == country)]['tournament'].unique()
selected_competition = st.sidebar.selectbox('Selecione a competição', competitions, key='competition_selectbox')

df_competition = df[(df['tournament'] == selected_competition) & 
                    ((df['home_team'] == country) | (df['away_team'] == country))]

merged_df = pd.merge(country_wins, df2, left_on=['date', 'home_team', 'away_team'], right_on=['date', 'home_team', 'away_team'])

# Conta o Número de ocorrências de cada jogador na coluna scorer agrupado por date, home_team e away_team
merged_df['scores'] = merged_df.groupby(['date', 'home_team', 'away_team'])['scorer'].transform('count')

# Cria uma nova coluna goalscorers no DataFrame merged_df, que combina o nome do jogador 
# e o número de gols 
merged_df['goalscorers'] = merged_df.groupby(['date', 'home_team', 'away_team'])['scorer'].transform(lambda x: ', '.join(x + ' (1 gol)'))

final_table = merged_df[['date', 'home_team', 'away_team', 'city', 'home_score', 'away_score', 'goalscorers']].drop_duplicates()

final_table.columns = ['Data', 'Time da Casa', 'Time Visitante', 'Local do Confronto', 'Gols da Casa', 'Gols do Visitante', 'Artilheiros']

st.header('Jogos e Artilheiros')
st.dataframe(final_table)

# Conta o número de vitórias por cidade
win_counts = country_wins['city'].value_counts().reset_index()
win_counts.columns = ['city', 'win_count']

top_scorers = merged_df.groupby('city')['scorer'].agg(lambda x: x.value_counts().idxmax()).reset_index()
top_scorers.columns = ['city', 'top_scorer']

final_win_data = pd.merge(win_counts, top_scorers, on='city').head(20)

st.header('Vitórias por Cidade e Artilheiro Principal')
fig = px.bar(final_win_data, x='city', y='win_count', text='top_scorer', title='Vitórias por Cidade e Artilheiro Principal',
             labels={'city': 'Cidade', 'win_count': 'Número de Vitórias'}, 
             color='win_count', color_continuous_scale='Viridis')
fig.update_traces(textposition='outside')
st.plotly_chart(fig)

# Os maiores artilheiros por país
top_scorers_by_country = merged_df.groupby(['home_team', 'scorer']).size().reset_index(name='goals')
top_scorers_by_country = top_scorers_by_country.sort_values(['home_team', 'goals'], ascending=[True, False])
top_scorers_by_country = top_scorers_by_country.groupby('home_team').head(1).reset_index(drop=True)

top_scorers_by_country.columns = ['País', 'Artilheiro', 'Gols']

st.header('Maiores Artilheiros por País')
fig_top_scorers = px.bar(top_scorers_by_country.head(num_countries), x='País', y='Gols', text='Artilheiro', title='Maiores Artilheiros por País',
              labels={'País': 'País', 'Gols': 'Número de Gols'}, 
              color='Gols', color_continuous_scale='Viridis')
fig_top_scorers.update_traces(textposition='outside')
st.plotly_chart(fig_top_scorers)

# Média dos minutos dos gols para cada equipe 
average_goal_time = df2.groupby('team')['minute'].mean().reset_index()

top_average_goal_time = average_goal_time.nsmallest(num_countries, 'minute')

top_average_goal_time.columns = ['Equipe', 'Média de Minutos']

st.header(f'Ranking das {num_countries} Equipes com a Média de Gols Mais Rápidos')
st.dataframe(top_average_goal_time)

fig3 = px.bar(top_average_goal_time, x='Equipe', y='Média de Minutos', title=f'Ranking das {num_countries} Equipes com a Média de Gols Mais Rápidos',
              labels={'Equipe': 'Equipe', 'Média de Minutos': 'Média de Minutos dos Gols'}, 
              color='Média de Minutos', color_continuous_scale='Viridis')
fig3.update_traces(textposition='outside')
st.plotly_chart(fig3)

# Vitórias por Ano
st.header('Vitórias por Ano')
wins_per_year = df[((df['home_team'] == country) & (df['home_score'] > df['away_score'])) |
                   ((df['away_team'] == country) & (df['away_score'] > df['home_score']))].groupby(df['date'].str[:4]).size().reset_index(name='Vitórias')
wins_per_year.columns = ['Ano', 'Vitórias']
fig4 = px.line(wins_per_year, x='Ano', y='Vitórias', title='Vitórias por Ano')
st.plotly_chart(fig4)


# Artilheiros por Ano --------------------
st.header('Artilheiros por Ano')
scorers_per_year = df2[df2['team'] == country].groupby([df2['date'].str[:4], 'scorer']).size().reset_index(name='gols')
scorers_per_year.columns = ['Ano', 'Artilheiro', 'Gols']

top_scorers_per_year = scorers_per_year.loc[scorers_per_year.groupby('Ano')['Gols'].idxmax()].reset_index(drop=True)

fig5 = px.bar(top_scorers_per_year, x='Ano', y='Gols', text='Artilheiro', title='Artilheiros por Ano',
              labels={'Ano': 'Ano', 'Gols': 'Número de Gols', 'Artilheiro': 'Artilheiro'},
              color='Gols', color_continuous_scale='Viridis')
fig5.update_traces(textposition='outside')
st.plotly_chart(fig5)

# Gols por Competição ---------------------
st.header('Gols por Competição')
goals_per_competition = df[df['home_team'] == country].groupby('tournament')[['home_score', 'away_score']].sum().reset_index()
goals_per_competition['total_goals'] = goals_per_competition['home_score'] + goals_per_competition['away_score']
fig6 = px.bar(goals_per_competition.head(num_countries), x='tournament', y='total_goals', title='Gols por Competição')
st.plotly_chart(fig6)

# Porcentagem de Vitórias, Empates e Derrotas por Competição
st.header('Porcentagem de Vitórias, Empates e Derrotas por Competição')
results_by_competition = df[((df['home_team'] == country) | (df['away_team'] == country))].groupby('tournament').apply(
    lambda x: pd.Series({
        'Vitórias': ((x['home_team'] == country) & (x['home_score'] > x['away_score'])).sum() +
                    ((x['away_team'] == country) & (x['away_score'] > x['home_score'])).sum(),
        'Empates': (x['home_score'] == x['away_score']).sum(),
        'Derrotas': ((x['home_team'] == country) & (x['home_score'] < x['away_score'])).sum() +
                    ((x['away_team'] == country) & (x['away_score'] < x['home_score'])).sum()
    })
).reset_index()

results_by_competition['Total'] = results_by_competition[['Vitórias', 'Empates', 'Derrotas']].sum(axis=1)
results_by_competition['Vitórias (%)'] = results_by_competition['Vitórias'] / results_by_competition['Total'] * 100
results_by_competition['Empates (%)'] = results_by_competition['Empates'] / results_by_competition['Total'] * 100
results_by_competition['Derrotas (%)'] = results_by_competition['Derrotas'] / results_by_competition['Total'] * 100

results_melted = results_by_competition.melt(id_vars='tournament', value_vars=['Vitórias', 'Empates', 'Derrotas'],
                                             var_name='Resultado', value_name='Quantidade')
results_melted['Porcentagem'] = results_melted.apply(
    lambda row: results_by_competition.loc[results_by_competition['tournament'] == row['tournament'], f"{row['Resultado']} (%)"].values[0],
    axis=1
)

fig7 = px.pie(results_melted, names='Resultado', values='Quantidade', title='Porcentagem de Vitórias, Empates e Derrotas por Competição',
              hover_data=['Porcentagem'], labels={'Quantidade': 'Quantidade', 'Porcentagem': 'Porcentagem (%)'})
fig7.update_traces(textposition='inside', textinfo='label+percent+value')
st.plotly_chart(fig7)


# Tabela com a quantidade de gols, vitórias, empates, derrotas, gols de pênalti e gols contra do país selecionado
st.header('Estatísticas do País Selecionado')
total_goals = df2[df2['team'] == country].shape[0]
total_wins = ((df['home_team'] == country) & (df['home_score'] > df['away_score'])).sum() + ((df['away_team'] == country) & (df['away_score'] > df['home_score'])).sum()
total_draws = ((df['home_team'] == country) & (df['home_score'] == df['away_score'])).sum() + ((df['away_team'] == country) & (df['home_score'] == df['away_score'])).sum()
total_losses = ((df['home_team'] == country) & (df['home_score'] < df['away_score'])).sum() + ((df['away_team'] == country) & (df['away_score'] < df['home_score'])).sum()
total_penalty_goals = df2[(df2['team'] == country) & (df2['penalty'] == 1)].shape[0]
total_own_goals = df2[(df2['team'] == country) & (df2['own_goal'] == 1)].shape[0]
total_goals_conceded = df[(df['home_team'] == country)]['away_score'].sum() + df[(df['away_team'] == country)]['home_score'].sum()

stats_data = {
    'Estatística': ['Gols', 'Vitórias', 'Empates', 'Derrotas', 'Gols de Pênalti', 'Gols Contra', 'Gols Sofridos'],
    'Quantidade': [total_goals, total_wins, total_draws, total_losses, total_penalty_goals, total_own_goals, total_goals_conceded]
}
stats_df = pd.DataFrame(stats_data)

st.dataframe(stats_df)

# Ranking dos jogadores que fizeram mais gols
st.header('Ranking dos Jogadores que Fizeram Mais Gols')
top_scorers_overall = df2[df2['team'] == country].groupby('scorer').size().reset_index(name='gols').sort_values(by='gols', ascending=False).head(num_countries)
top_scorers_overall.columns = ['Jogador', 'Gols']
st.dataframe(top_scorers_overall)

if st.sidebar.button('Recarregar Dados'):
    st.experimental_rerun()