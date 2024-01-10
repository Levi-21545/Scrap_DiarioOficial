import pandas as pd

from database import engine


def exportar_para_csv(query, nome_arquivo):

    # Execute a consulta e salve o resultado em um DataFrame do Pandas
    df = pd.read_sql(query, engine)

    # Renomeie as colunas conforme necessário
    df = df.rename(columns={
        'ID': 'ID',
        'id_func': 'ID Func./Vínculo',
        'data': 'Data',
        'materia': 'Materia',
        'nome': 'Nome',
        'tipo_vinculo': 'Tipo Vínculo',
        'cargo_funcao': 'Cargo/Função'
    })

    # Salve o DataFrame como um arquivo CSV
    df.to_csv(nome_arquivo, index=False)


# MAIN
if __name__ == "__main__":

    # Substitua 'sua_query_sql' pela consulta que retorna os dados desejados
    query_sql = 'SELECT * FROM servidores'

    exportar_para_csv(query_sql, '../data/22 23.csv')

