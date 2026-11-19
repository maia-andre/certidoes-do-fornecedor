"""Certidão Única estadual de SP no SIDEB (modo "navegador do servidor", RN-09).

"Emitir eCND" exige login gov.br, que o programa não automatiza (RNF-03): o servidor entra com o próprio
gov.br e emite. Em 19/11/2026, o login do servidor emitiu para CNPJ de terceiro, e o portal pede só a raiz
(8 dígitos), porque a certidão vale para a matriz e as filiais (RN-08).

O PDF ("CertidaoNegativa_<raiz>_<data e hora>.pdf") é reconhecido pelo texto e pela raiz do CNPJ, para não
depender do nome.

O SIDEB só funciona em dias úteis, das 6h às 21h, horário de Brasília (CE-07). Fora disso, o portal nem é aberto.
"""
import datetime as dt
import re

from certidoes.leitura import normalizar
from certidoes.pdf import texto_do_pdf
from certidoes.portais.comum import PortalErro
from certidoes.portais.navegador_servidor import obter_pelo_navegador

URL = "https://www4.fazenda.sp.gov.br/SIDEB/CertidaoNegativaDebitos"
TITULO = "TRIBUTOS ESTADUAIS E A DIVIDA ATIVA DO ESTADO DE SAO PAULO"
INSTRUCAO = (
    'No seu navegador, clique em "Emitir eCND", entre com o seu gov.br e cole a raiz do CNPJ {raiz} (Ctrl+V). '
    'Se a certidão for emitida, clique em "Clique aqui para ver mais informações" e em "Baixar eCND", '
    'salvando na pasta Downloads. Se o portal não emitir, cole a mensagem dele aqui e clique em '
    '"O portal não emitiu".'
)
FORA_DO_HORARIO = ("O SIDEB só funciona em dias úteis, das 6h às 21h (horário de Brasília). "
                   "Repita o item dentro desse horário.")
_HORA_INICIO, _HORA_FIM = 6, 21


def no_horario(agora: dt.datetime) -> bool:
    """Dia útil (segunda a sexta), das 6h às 21h (CE-07). Feriados não são conferidos."""
    return agora.weekday() < 5 and _HORA_INICIO <= agora.hour < _HORA_FIM


def e_certidao_da_raiz(dados: bytes, cnpj: str) -> bool:
    texto = normalizar(texto_do_pdf(dados))
    raizes = {"".join(m.groups()) for m in re.finditer(r"CNPJ: (\d{2})\.?(\d{3})\.?(\d{3})\b", texto)}
    return TITULO in texto and raizes == {cnpj[:8]}


def obter_certidao(cnpj, ao_aguardar=None, sinal=None, agora=None, **opcoes):
    agora = agora or dt.datetime.now()
    if not no_horario(agora):
        raise PortalErro(FORA_DO_HORARIO)
    return obter_pelo_navegador(
        cnpj,
        url=URL,
        padrao="*.pdf",
        cnpj_portal=cnpj[:8],
        prefixo="certidao-unica-sp",
        nome_portal="do SIDEB",
        ao_aguardar=ao_aguardar,
        sinal=sinal,
        aceitar=lambda dados: e_certidao_da_raiz(dados, cnpj),
        agora=agora,
        **opcoes,
    )
