"""Certidão de Débitos Tributários de MG no CDT (modo "navegador do servidor", RN-09).

O CDT exige login gov.br, que o programa não automatiza (RNF-03): o servidor entra com o próprio gov.br,
escolhe "Empresa" e informa o CNPJ. Em 19/11/2026, o login do servidor emitiu para CNPJ de terceiro, sem
captcha depois do login (issue #8).

O PDF ("cdt_<CNPJ>_<dd-mm-aaaa>.pdf") é reconhecido pelo texto e pela raiz do CNPJ, porque a certidão vale
para todos os estabelecimentos da empresa.
"""
from certidoes.leitura import cnpj_confere, normalizar
from certidoes.pdf import texto_do_pdf
from certidoes.portais.navegador_servidor import obter_pelo_navegador

URL = "https://cdt.fazenda.mg.gov.br/"
INSTRUCAO = (
    'No seu navegador, entre com o seu gov.br, clique em "Empresa", cole o CNPJ {cnpj} (Ctrl+V) e emita a '
    "certidão, salvando o PDF na pasta Downloads. Se o portal não emitir, cole a mensagem dele aqui e clique em "
    '"O portal não emitiu".'
)


def e_certidao_do_cnpj(dados: bytes, cnpj: str) -> bool:
    texto = texto_do_pdf(dados)
    t = normalizar(texto)
    return ("SECRETARIA DE ESTADO DE FAZENDA DE MINAS GERAIS" in t and "CERTIDAO DE DEBITOS TRIBUTARIOS" in t
            and cnpj_confere(texto, cnpj))


def obter_certidao(cnpj, ao_aguardar=None, sinal=None, **opcoes):
    return obter_pelo_navegador(
        cnpj,
        url=URL,
        padrao="*.pdf",
        prefixo="cnd-estadual-mg",
        nome_portal="do CDT (MG)",
        ao_aguardar=ao_aguardar,
        sinal=sinal,
        aceitar=lambda dados: e_certidao_do_cnpj(dados, cnpj),
        **opcoes,
    )
