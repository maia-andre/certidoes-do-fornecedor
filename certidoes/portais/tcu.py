"""Consulta Consolidada de Pessoa Jurídica do TCU (REQ-16, RN-11): Licitantes Inidôneos (TCU), CNIA (CNJ), CEIS e CNEP.

Modo "navegador do servidor" (RN-09): em 17/11/2026, o firewall de aplicações do TCU passou a recusar a consulta
direta pela API pública ("Requisição rejeitada", suporte ID extB), enquanto a página abria normalmente no navegador
do servidor. O servidor faz a consulta no próprio navegador e o programa recolhe o PDF da pasta Downloads,
reconhecido pelo texto e pelo CNPJ, para não depender do nome do arquivo.
"""
from certidoes.leitura import normalizar
from certidoes.pdf import contem_cnpj, texto_do_pdf
from certidoes.portais.navegador_servidor import obter_pelo_navegador

URL = "https://certidoes-apf.apps.tcu.gov.br/"
INSTRUCAO = (
    "No seu navegador, cole o CNPJ {cnpj} (Ctrl+V) na consulta de pessoa jurídica, faça a consulta "
    "e salve o PDF na pasta Downloads."
)


def e_consulta_do_cnpj(dados: bytes, cnpj: str) -> bool:
    texto = texto_do_pdf(dados)
    return "CONSULTA CONSOLIDADA DE PESSOA JURIDICA" in normalizar(texto) and contem_cnpj(texto, cnpj)


def obter_consulta(cnpj, ao_aguardar=None, sinal=None, **opcoes):
    return obter_pelo_navegador(
        cnpj,
        url=URL,
        padrao="*.pdf",
        prefixo="sancoes-tcu",
        nome_portal="do TCU",
        ao_aguardar=ao_aguardar,
        sinal=sinal,
        aceitar=lambda dados: e_consulta_do_cnpj(dados, cnpj),
        **opcoes,
    )
