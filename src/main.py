import time
import calendar

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from sqlalchemy.orm import sessionmaker

from database import DiarioItem, Base, engine

from datetime import datetime

from urllib.parse import urlparse, parse_qs


# Seleção do ano de exercício
MES_INICIO = int(input('Digite o mês de início: '))
ANO = int(input('Digite o ano de exercício: '))
PAGINA = int(input('Digite a primeira página a ser lida: '))


# Configuração para modo headless
chrome_options = Options()
chrome_options.add_argument('--headless')

# Inicialização do WebDriver do Chrome
driver = webdriver.Chrome()

# Criando sessão do SQLAlchemy
Session = sessionmaker(bind=engine)
session = Session()

# Percorrendo os 12 meses do ano
for MES in range(MES_INICIO, 13):

    # Descobrir o último dia do mês
    ULTIMO_DIA = calendar.monthrange(ANO, MES)[1]

    # Determinar data inicial e final
    DATA_INICIO = f'{ANO}-{MES:02d}-01'
    DATA_FIM = f'{ANO}-{MES:02d}-{ULTIMO_DIA:02d}'

    # Imprimir datas
    print(f'Data Início: {DATA_INICIO}')
    print(f'Data Fim: {DATA_FIM}')

    while True:

        # URL da página inicial
        BASE_URL = (f'https://www.diariooficial.rs.gov.br/resultado?'
                    f'td=DOE&pc=&tmi=90&tmd=Recursos%20Humanos&at=Dispensa&di={DATA_INICIO}&df={DATA_FIM}&pg={PAGINA}')

        # Acessando a página inicial
        driver.get(BASE_URL)

        # Aguardar alguns segundos para garantir que a página seja carregada completamente
        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.CLASS_NAME, 'conteudo')),
        )

        # Analisar a URL
        url_atual = driver.current_url

        parsed_url_base = urlparse(BASE_URL)
        parsed_url_atual = urlparse(url_atual)

        parametros_base = parse_qs(parsed_url_base.query)
        parametros_atual = parse_qs(parsed_url_atual.query)

        # Obter o valor associado ao parâmetro 'pg' (página)
        numero_pagina_base = parametros_base.get('pg', [])[0]
        numero_pagina_atual = parametros_atual.get('pg', [])[0]

        print(f'URL Base: {numero_pagina_base} | URL Atual: {numero_pagina_atual}')
        print('-' * 50)

        if numero_pagina_base != numero_pagina_atual:
            PAGINA = 1
            break

        # Armazenar ID da janela original
        original_window = driver.current_window_handle

        # Obter o HTML da página
        html_lista = driver.page_source

        # Parseando o conteúdo da página com o BeautifulSoup
        soup_lista = BeautifulSoup(html_lista, 'html.parser')

        # Encontrar todas as tags <div> com a classe "itens"
        div_itens_list = soup_lista.find_all('div', class_='itens')

        # Iterando sobre as tags <div> encontradas
        for div_itens in div_itens_list:
            # Encontrando a tag <p> com a classe "item-titulo" dentro de cada tag <div>
            titulo_tag = div_itens.find('p', class_='item-titulo')

            # Verificando se a tag foi encontrada antes de acessar seu texto
            if titulo_tag:
                # Extraindo número e data da matéria e nome do servidor
                link = titulo_tag.find('a')
                if link:
                    numero_materia = link['href'].split('=')[-1]
                    nome_servidor = div_itens.find('p', class_='conteudo')

                    try:
                        nome_servidor = nome_servidor.text.split('Nome: ')[1].split('Id')[0]
                    except IndexError:
                        continue

                    data_materia = link.text.split('-')[-1].strip()
                    data_obj = datetime.strptime(data_materia, "%d/%m/%Y")
                    data_formatada = data_obj.strftime("%Y-%m-%d")

                    # Verificar se o item já existe no banco de dados
                    existing_item = session.query(DiarioItem).filter_by(materia=numero_materia).first()

                    if not existing_item:
                        # Imprimir os resultados
                        print(f'Número da Matéria: {numero_materia}')
                        print(f'Número da Matéria: {data_formatada}')
                        print(f'Nome do Servidor: {nome_servidor}')

                        url_materia = f'https://www.diariooficial.rs.gov.br/materia?id={numero_materia}'

                        # Abrir uma nova guia do navegador
                        driver.execute_script("window.open('');")

                        # Mudar o foco para a nova guia
                        driver.switch_to.window(driver.window_handles[1])

                        # Carregar a URL da matéria na nova guia
                        driver.get(url_materia)

                        # Espera até que a tag <div> com a classe "conteudo" seja visível
                        WebDriverWait(driver, 10).until(
                            EC.visibility_of_element_located((By.CLASS_NAME, 'conteudo'))
                        )

                        html_materia = driver.page_source
                        soup_materia = BeautifulSoup(html_materia, 'html.parser')

                        # Encontrar todas as tags <div> com a classe "conteudo"
                        p_materia_conteudo = soup_materia.find('p', class_='conteudo')

                        # Inicializar variáveis para armazenar as informações
                        id_func_vinculo = None
                        nome = None
                        tipo_vinculo = None
                        cargo_funcao = None

                        # Verificando se a tag foi encontrada antes de acessar seu texto
                        if p_materia_conteudo:

                            lista_span = p_materia_conteudo.find_all('span')

                            # Itere sobre as tags <span> dentro da tag <p>
                            if lista_span:
                                for span_tag in lista_span:
                                    # Obtenha o texto da tag <span>
                                    span_text = span_tag.text.strip()

                                    # Verifique os padrões conhecidos e extraia as informações
                                    if 'Id.Func./Vínculo' in span_text:
                                        id_func_vinculo = span_text.split(':')[-1].strip()
                                    elif 'Nome' in span_text:
                                        nome = span_text.split(':')[-1].strip()
                                    elif 'Tipo Vínculo' in span_text:
                                        tipo_vinculo = span_text.split(':')[-1].strip().upper()
                                    elif 'Cargo/Função' in span_text:
                                        cargo_funcao = span_text.split(':')[-1].strip()
                            else:
                                lista_for = p_materia_conteudo.find_all('p')

                                for for_tag in lista_for:
                                    # Obtenha o texto da tag <span>
                                    for_text = for_tag.text.strip()

                                    # Verifique os padrões conhecidos e extraia as informações
                                    if 'Matricula' in for_text:
                                        id_func_vinculo = for_text.split(':')[-1].strip()
                                    elif 'Nome' in for_text:
                                        nome = for_text.split(':')[-1].strip()
                                    elif 'Tipo do Vinculo' in for_text:
                                        tipo_vinculo = for_text.split(':')[-1].strip().upper()
                                    elif 'Cargo/Função' in for_text:
                                        cargo_funcao = for_text.split(':')[-1].strip()

                        # Imprimir os resultados
                        print(f'ID Func./Vínculo: {id_func_vinculo}')
                        print(f'Nome: {nome}')
                        print(f'Tipo Vínculo: {tipo_vinculo}')
                        print(f'Cargo/Função: {cargo_funcao}')
                        print('-' * 50)  # Linha separadora para melhorar a legibilidade

                        # Armazenar os dados no banco de dados
                        diario_item_db = DiarioItem(
                            id_func=id_func_vinculo,
                            nome=nome,
                            materia=numero_materia,
                            data=data_formatada,
                            tipo_vinculo=tipo_vinculo,
                            cargo_funcao=cargo_funcao
                        )
                        session.add(diario_item_db)

                        # Commit das alterações no banco de dados
                        session.commit()

                        # Fecha a nova guia após o término
                        driver.close()

                        # Muda o foco de volta para a guia original
                        driver.switch_to.window(driver.window_handles[0])
        PAGINA += 1


# Fecha a nova guia após o término
driver.close()

# Fechar a sessão
session.close()

# Feche o WebDriver
driver.quit()
time.sleep(2)  # Ajuste conforme necessário
