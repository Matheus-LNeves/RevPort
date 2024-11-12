from datetime import datetime, timedelta
import pandas as pd
import streamlit as st
from streamlit_calendar import calendar
import json
import locale

# Configura a localidade para português do Brasil
try:
    # Tente configurar para pt_BR.UTF-8 ou pt_BR
    locale.setlocale(locale.LC_TIME, "pt_BR.UTF-8")
except locale.Error:
    try:
        locale.setlocale(locale.LC_TIME, "pt_BR")
    except locale.Error:
        # Se não estiver disponível, deixe no padrão do sistema
        pass

# Caminho para os arquivos JSON
eventos_file = "eventos.json"
cancelados_file = "clientes_cancelados.json"

# Carregar lista de clientes
def carregar_clientes():
    #caminho no PC Faz Capital: "C:/Users/FAZCAPITAL/OneDrive/lista de contatos.xlsx"
    #caminho no meu PC: "C:/Users/USER/OneDrive/lista de contatos.xlsx"
    file_path = "C:/Users/USER/OneDrive/lista de contatos.xlsx"
    xls = pd.ExcelFile(file_path)
    planilha2 = pd.read_excel(xls, 'Planilha2')
    nomes_encontrados = list(set(planilha2['a'].dropna().loc[planilha2['a.3'] != "Não encontrado"]))
    lista_clientes = sorted(nomes_encontrados)
    return lista_clientes

# Funções para manipulação de eventos
def carregar_eventos():
    try:
        with open(eventos_file, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def salvar_eventos(eventos):
    with open(eventos_file, 'w') as f:
        json.dump(eventos, f)

def carregar_cancelados():
    try:
        with open(cancelados_file, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def salvar_cancelados(cancelados):
    with open(cancelados_file, 'w') as f:
        json.dump(cancelados, f)

# Função para gerar próximos 3 eventos do cliente com intervalos de 3 meses
def gerar_proximos_eventos(cliente, data_inicial):
    novos_eventos = []
    for i in range(1, 4):
        # Calcula a data do próximo evento (a cada 3 meses)
        data_evento = data_inicial + timedelta(days=i * 90)
        
        # Ajusta a data para o próximo dia útil se cair em um final de semana
        if data_evento.weekday() >= 5:  # 5 = Sábado, 6 = Domingo
            data_evento += timedelta(days=(7 - data_evento.weekday()))

        # Adiciona o evento à lista de novos eventos
        novos_eventos.append({
            "cliente": cliente,
            "data": data_evento.strftime('%Y-%m-%d'),
            "observacao": ""  # Campo de observação vazio
        })
    return novos_eventos

# Principal função da aplicação Streamlit
def main():
    st.title("Gerenciamento de Revisões")
    
    # Carregar dados
    clientes = carregar_clientes()
    eventos = carregar_eventos()
    cancelados = carregar_cancelados()

    # Seleção de Cliente e Data para Agendamento
    st.header("Agendar Revisão")
    cliente_selecionado = st.selectbox("Selecionar Cliente para Agendar", clientes)
    data_reuniao = st.date_input("Escolha a Data da Reunião", datetime.now())
    if st.button("Agendar Revisão"):
        # Cria o evento principal
        novo_evento = {
            "cliente": cliente_selecionado,
            "data": data_reuniao.strftime('%Y-%m-%d'),
            "observacao": ""  # Campo de observação vazio
        }
        eventos.append(novo_evento)
        
        # Gera e adiciona os próximos 3 eventos para o mesmo cliente
        proximos_eventos = gerar_proximos_eventos(cliente_selecionado, data_reuniao)
        eventos.extend(proximos_eventos)
        
        # Salva todos os eventos no arquivo JSON
        salvar_eventos(eventos)
        st.experimental_rerun()

    # Seção do calendário de eventos agendados
    st.header("Calendário de Eventos Agendados")
    
    # Preparar os eventos para o calendário
    eventos_calendario = []
    for evento in eventos:
        eventos_calendario.append({
            "title": evento['cliente'],
            "start": evento['data']
        })
    
    # Exibir o calendário com eventos agendados
    calendar(events=eventos_calendario)

    # Seção para exibir e gerenciar eventos agendados com expander
    with st.expander("Lista de Eventos Agendados"):
        cliente_agendado_selecionado = st.selectbox("Filtrar por Cliente na Lista de Agendados", ["Selecione um Cliente"] + clientes, key="agendados")
        
        if cliente_agendado_selecionado != "Selecione um Cliente":
            # Filtrar eventos agendados pelo cliente selecionado
            agendados_filtrados = [e for e in eventos if e['cliente'] == cliente_agendado_selecionado]
            
            if agendados_filtrados:
                for index, evento in enumerate(agendados_filtrados):
                    st.write(f"Cliente: {evento['cliente']}, Data: {evento['data']}")
                    
                    # Campo de entrada para observação
                    observacao = st.text_area("Observações", value=evento.get("observacao", ""), key=f"obs_{index}_{evento['cliente']}")
                    
                    # Botão para salvar observação
                    if st.button("Salvar Observação", key=f"salvar_obs_{index}_{evento['cliente']}"):
                        evento['observacao'] = observacao  # Atualiza a observação no evento
                        salvar_eventos(eventos)  # Salva os eventos atualizados no arquivo JSON
                        st.success("Observação salva com sucesso!")
                    
                    # Botão para cancelar o evento
                    if st.button(f"Cancelar evento de {evento['cliente']}", key=f"cancelar_{index}_{evento['cliente']}"):
                        cancelados.append(evento)
                        salvar_cancelados(cancelados)
                        eventos = [e for e in eventos if e != evento]
                        salvar_eventos(eventos)
                        st.experimental_rerun()
            else:
                st.write("Não há reuniões para este cliente.")

    # Seção para gerenciar eventos cancelados com expander
    with st.expander("Eventos Cancelados"):
        cliente_cancelado_selecionado = st.selectbox("Filtrar por Cliente na Lista de Cancelados", ["Selecione um Cliente"] + clientes, key="cancelado")
        
        if cliente_cancelado_selecionado != "Selecione um Cliente":
            # Filtrar eventos cancelados pelo cliente selecionado
            cancelados_filtrados = [e for e in cancelados if e['cliente'] == cliente_cancelado_selecionado]
            
            if cancelados_filtrados:
                for index, evento in enumerate(cancelados_filtrados):
                    st.write(f"Cliente: {evento['cliente']}")
                    st.write(f"Data Cancelada: {evento['data']}")
                    
                    col1, col2 = st.columns(2)
                    
                    # Opção para remover o cliente da lista de cancelados
                    if col1.button(f"Remover {evento['cliente']} da lista cancelada", key=f"remover_{index}_{evento['cliente']}"):
                        cancelados = [e for e in cancelados if e != evento]
                        salvar_cancelados(cancelados)
                        st.experimental_rerun()

                    # Opção para reagendar o cliente e movê-lo de volta para os eventos agendados
                    nova_data = col2.date_input(f"Nova Data para {evento['cliente']}", datetime.now(), key=f"data_{index}_{evento['cliente']}")
                    if col2.button(f"Reagendar {evento['cliente']}", key=f"reagendar_{index}_{evento['cliente']}"):
                        novo_evento = {
                            "cliente": evento['cliente'],
                            "data": nova_data.strftime('%Y-%m-%d'),
                            "observacao": evento.get("observacao", "")  # Mantém a observação se existente
                        }
                        eventos.append(novo_evento)
                        salvar_eventos(eventos)
                        
                        # Remove o evento da lista de cancelados ao reagendar
                        cancelados = [e for e in cancelados if e != evento]
                        salvar_cancelados(cancelados)
                        st.experimental_rerun()
            else:
                st.write("Não há reuniões para este cliente.")

if __name__ == "__main__":
    main()
