import datetime as dt
import threading

import pytest

from certidoes.portais import sideb
from certidoes.portais.comum import PortalErro
from tests.conftest import SIDEB_NEGATIVA, pdf_com_texto

CNPJ = "11222333000262"  # filial: o SIDEB pede só a raiz
QUINTA = dt.datetime(2026, 11, 19, 14, 7, 46)


def certidao(raiz="11.222.333"):
    return pdf_com_texto(*(linha.replace("11.222.333", raiz) for linha in SIDEB_NEGATIVA))


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
                  tempo_limite_s=3, intervalo_s=0.05, agora=QUINTA)
    opcoes.update(kw)
    return sideb.obter_certidao(CNPJ, **opcoes)


def test_copia_a_raiz_abre_o_sideb_e_guarda_a_certidao_na_pasta_do_cnpj(pastas):
    downloads, certidoes = pastas
    copiados = []
    navegador = Navegador(downloads, [("CertidaoNegativa_11222333_20261119140722.pdf", certidao())])
    arquivo = obter(pastas, navegador, copiar=lambda t: copiados.append(t) or True)
    assert (navegador.urls, copiados) == ([sideb.URL], ["11222333"])
    assert arquivo == certidoes / CNPJ / "certidao-unica-sp-20261119-140746.pdf"
    assert arquivo.read_bytes() == certidao()
    assert list(downloads.iterdir()) == []


def test_ignora_pdf_que_nao_e_a_certidao_e_certidao_de_outra_raiz(pastas):
    downloads, _ = pastas
    outros = [("boleto.pdf", pdf_com_texto("Boleto bancario", "CNPJ: 11.222.333")),
              ("CertidaoNegativa_99888777_20261119140722.pdf", certidao("99.888.777"))]
    arquivo = obter(pastas, Navegador(downloads, outros + [("CertidaoNegativa_11222333.pdf", certidao())]))
    assert arquivo.read_bytes() == certidao()
    assert {p.name for p in downloads.iterdir()} == {n for n, _ in outros}


@pytest.mark.parametrize("agora", [
    dt.datetime(2026, 11, 21, 10, 0),  # sábado
    dt.datetime(2026, 11, 22, 10, 0),  # domingo
    dt.datetime(2026, 11, 19, 5, 59),
    dt.datetime(2026, 11, 19, 21, 0),
])
def test_fora_do_horario_do_sideb_e_falha_tecnica_sem_abrir_o_portal(pastas, agora):
    navegador = Navegador(pastas[0], [])
    with pytest.raises(PortalErro, match="dias úteis, das 6h às 21h"):
        obter(pastas, navegador, agora=agora)
    assert navegador.urls == []


def test_horario_do_sideb():
    assert sideb.no_horario(dt.datetime(2026, 11, 16, 6, 0))  # segunda
    assert sideb.no_horario(dt.datetime(2026, 11, 20, 20, 59))  # sexta
    assert not sideb.no_horario(dt.datetime(2026, 11, 20, 21, 0))


def test_e_certidao_da_raiz():
    assert sideb.e_certidao_da_raiz(certidao(), CNPJ)
    assert not sideb.e_certidao_da_raiz(certidao("99.888.777"), CNPJ)
    assert not sideb.e_certidao_da_raiz(pdf_com_texto("Outro documento", "CNPJ: 11.222.333"), CNPJ)
    assert not sideb.e_certidao_da_raiz(b"%PDF-quebrado", CNPJ)
