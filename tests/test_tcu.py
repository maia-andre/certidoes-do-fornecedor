"""Consulta Consolidada do TCU no modo "navegador do servidor" (RNF-06): Downloads simulada, sem o portal real."""
import datetime as dt
import threading

import pytest

from certidoes import leitura
from certidoes.pdf import texto_do_pdf
from certidoes.portais import tcu
from certidoes.portais.comum import PortalErro, Pulada, SinalServidor
from tests.conftest import TCU_CONSULTA, pdf_com_texto

CNPJ = "11222333000181"
AGORA = dt.datetime(2026, 11, 17, 11, 28, 12)


def consulta(cnpj="11.222.333/0001-81"):
    return pdf_com_texto(*(linha.replace("11.222.333/0001-81", cnpj) for linha in TCU_CONSULTA))


class Navegador:
    """Simula o servidor salvando arquivos em Downloads depois de abrir o portal."""

    def __init__(self, pasta, arquivos, atraso=0.15):
        self.pasta, self.arquivos, self.atraso = pasta, arquivos, atraso
        self.urls = []

    def __call__(self, url):
        self.urls.append(url)

        def salvar():
            for nome, dados in self.arquivos:
                (self.pasta / nome).write_bytes(dados)

        if self.arquivos:
            threading.Timer(self.atraso, salvar).start()
        return True


@pytest.fixture
def pastas(tmp_path):
    downloads = tmp_path / "Downloads"
    downloads.mkdir()
    return downloads, tmp_path / "Certidoes"


def obter(pastas, navegador, **kw):
    downloads, certidoes = pastas
    opcoes = dict(pasta_base=certidoes, pasta=downloads, abrir_url=navegador, copiar=lambda t: True,
                  tempo_limite_s=3, intervalo_s=0.05, agora=AGORA)
    opcoes.update(kw)
    return tcu.obter_consulta(CNPJ, **opcoes)


def test_abre_a_consulta_do_tcu_e_guarda_o_pdf_na_pasta_do_cnpj(pastas):
    downloads, certidoes = pastas
    navegador = Navegador(downloads, [("consulta.pdf", consulta())])
    arquivo = obter(pastas, navegador)
    assert navegador.urls == [tcu.URL]
    assert arquivo == certidoes / CNPJ / "sancoes-tcu-20261117-112812.pdf"
    assert leitura.ler(leitura.ler_sancoes_tcu, texto_do_pdf(arquivo.read_bytes()), CNPJ).situacao == leitura.NADA_CONSTA
    assert list(downloads.iterdir()) == []


def test_copia_o_cnpj_e_avisa_que_aguarda_o_servidor(pastas):
    downloads, _ = pastas
    copiados, avisos = [], []
    obter(pastas, Navegador(downloads, [("consulta.pdf", consulta())]),
          copiar=lambda t: copiados.append(t) or True, ao_aguardar=lambda: avisos.append("aguardando"))
    assert (copiados, avisos) == ([CNPJ], ["aguardando"])


def test_ignora_pdf_novo_que_nao_e_a_consulta_e_consulta_de_outro_cnpj(pastas):
    downloads, _ = pastas
    outros = [("boleto.pdf", pdf_com_texto("Boleto bancario", "11.222.333/0001-81")),
              ("outra.pdf", consulta("99.999.999/0001-91"))]
    arquivo = obter(pastas, Navegador(downloads, outros + [("consulta (1).pdf", consulta())]))
    assert arquivo.read_bytes() == consulta()
    assert {p.name for p in downloads.iterdir()} == {n for n, _ in outros}


def test_sem_a_consulta_termina_em_tempo_esgotado(pastas):
    downloads, _ = pastas
    with pytest.raises(PortalErro, match="Tempo esgotado"):
        obter(pastas, Navegador(downloads, [("boleto.pdf", pdf_com_texto("Boleto bancario"))]), tempo_limite_s=0.6)


def test_navegador_que_nao_abre_gera_erro_claro(pastas):
    with pytest.raises(PortalErro, match="Não foi possível abrir o portal do TCU"):
        obter(pastas, lambda url: False)


def test_servidor_pula_o_item_enquanto_o_programa_espera(pastas):
    sinal = SinalServidor()

    def abrir(url):
        threading.Timer(0.1, sinal.pular).start()
        return True

    with pytest.raises(Pulada):
        obter(pastas, abrir, sinal=sinal)


def test_e_consulta_do_cnpj():
    assert tcu.e_consulta_do_cnpj(consulta(), CNPJ)
    assert not tcu.e_consulta_do_cnpj(consulta("99.999.999/0001-91"), CNPJ)
    assert not tcu.e_consulta_do_cnpj(pdf_com_texto("Outro documento 11.222.333/0001-81"), CNPJ)
    assert not tcu.e_consulta_do_cnpj(b"%PDF-quebrado", CNPJ)
