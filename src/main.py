import time
import calendar

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from sqlalchemy.orm import sessionmaker

from database import DiarioItem, Base, engine

from datetime import datetime

# CONTADOR LAÇO PARA PERCORRER TODAS AS PÁGINAS DO FILTRO
PAGINA = 1

# CONTADOR LAÇO PARA ITERAR TODOS OS MESES
MES = 1
ANO = 2022

# Configuração para modo headless
chrome_options = Options()
chrome_options.add_argument('--headless')

# Inicialize o WebDriver do Chrome
driver = webdriver.Chrome(options=chrome_options)

# Criar uma sessão do SQLAlchemy
Session = sessionmaker(bind=engine)
session = Session()

for MES in range(1, 13):

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

        # Acesse a página inicial
        driver.get(BASE_URL)

        # Aguarde alguns segundos para garantir que a página seja carregada completamente
        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.CLASS_NAME, 'conteudo'))
        )

        # Armazenar ID da janela original
        original_window = driver.current_window_handle

        # Obtenha o HTML da página
        html_lista = driver.page_source

        # Parseie o conteúdo da página com o BeautifulSoup
        soup_lista = BeautifulSoup(html_lista, 'html.parser')

        # Encontre todas as tags <div> com a classe "itens"
        div_itens_list = soup_lista.find_all('div', class_='itens')

        # Itere sobre as tags <div> encontradas
        for div_itens in div_itens_list:
            # Encontre a tag <p> com a classe "item-titulo" dentro de cada tag <div>
            titulo_tag = div_itens.find('p', class_='item-titulo')

            # Verifique se a tag foi encontrada antes de acessar seu texto
            if titulo_tag:
                # Extraia o número da matéria e o nome do servidor
                link = titulo_tag.find('a')
                if link:
                    numero_materia = link['href'].split('=')[-1]
                    nome_servidor = div_itens.find('p', class_='conteudo').text.split('Nome: ')[1].split('Id')[0]
                    data_materia = link.text.split('-')[-1].strip()
                    data_obj = datetime.strptime(data_materia, "%d/%m/%Y")
                    data_formatada = data_obj.strftime("%Y-%m-%d")

                    # Verificar se o item já existe no banco de dados
                    existing_item = session.query(DiarioItem).filter_by(materia=numero_materia).first()

                    if not existing_item:
                        # Imprima os resultados
                        print(f'Número da Matéria: {numero_materia}')
                        print(f'Número da Matéria: {data_formatada}')
                        print(f'Nome do Servidor: {nome_servidor}')
                        print('-' * 50)  # Linha separadora para melhorar a legibilidade

                        url_materia = f'https://www.diariooficial.rs.gov.br/materia?id={numero_materia}'

                        # Abre uma nova guia do navegador
                        driver.execute_script("window.open('');")

                        # Muda o foco para a nova guia
                        driver.switch_to.window(driver.window_handles[1])

                        # Carrega a URL da matéria na nova guia
                        driver.get(url_materia)

                        # Espera até que a tag <div> com a classe "conteudo" seja visível
                        WebDriverWait(driver, 10).until(
                            EC.visibility_of_element_located((By.CLASS_NAME, 'conteudo'))
                        )

                        html_materia = driver.page_source
                        soup_materia = BeautifulSoup(html_materia, 'html.parser')

                        # Encontre todas as tags <div> com a classe "conteudo"
                        p_materia_conteudo = soup_materia.find('p', class_='conteudo')

                        # Inicialize variáveis para armazenar as informações
                        id_func_vinculo = None
                        nome = None
                        tipo_vinculo = None
                        cargo_funcao = None

                        # Verifique se a tag foi encontrada antes de acessar seu texto
                        if p_materia_conteudo:
                            # Itere sobre as tags <span> dentro da tag <p>
                            for span_tag in p_materia_conteudo.find_all('span'):
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

                        # Imprima os resultados
                        print(f'ID Func./Vínculo: {id_func_vinculo}')
                        print(f'Nome: {nome}')
                        print(f'Tipo Vínculo: {tipo_vinculo}')
                        print(f'Cargo/Função: {cargo_funcao}')

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

        if PAGINA > 7:
            break

# Fecha a nova guia após o término
driver.close()

# Fechar a sessão
session.close()

# Feche o WebDriver
driver.quit()
time.sleep(2)  # Ajuste conforme necessário
