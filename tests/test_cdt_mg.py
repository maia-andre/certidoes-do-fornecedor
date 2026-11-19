import datetime as dt
import threading

import pytest

from certidoes.portais import cdt_mg
from certidoes.portais.comum import PortalErro
from tests.conftest import CDT_MG_NEGATIVA, pdf_com_texto

CNPJ = "11222333000181"
AGORA = dt.datetime(2026, 11, 19, 15, 48, 49)


def certidao(cnpj="11.222.333/0001-81"):
    return pdf_com_texto(*(linha.replace("11.222.333/0001-81", cnpj) for linha in CDT_MG_NEGATIVA))


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


def obter(pastas, navegador, cnpj=CNPJ, **kw):
    downloads, certidoes = pastas
    opcoes = dict(pasta_base=certidoes, pasta=downloads, abrir_url=navegador, copiar=lambda t: True,
                  tempo_limite_s=3, intervalo_s=0.05, agora=AGORA)
    opcoes.update(kw)
    return cdt_mg.obter_certidao(cnpj, **opcoes)


def test_copia_o_cnpj_abre_o_cdt_e_guarda_a_certidao_na_pasta_do_cnpj(pastas):
    downloads, certidoes = pastas
    copiados = []
    navegador = Navegador(downloads, [("cdt_11222333000181_19-11-2026.pdf", certidao())])
    arquivo = obter(pastas, navegador, copiar=lambda t: copiados.append(t) or True)
    assert (navegador.urls, copiados) == ([cdt_mg.URL], [CNPJ])
    assert arquivo == certidoes / CNPJ / "cnd-estadual-mg-20261119-154849.pdf"
    assert arquivo.read_bytes() == certidao()
    assert list(downloads.iterdir()) == []


def test_filial_aceita_a_certidao_da_mesma_raiz(pastas):
    downloads, _ = pastas
    arquivo = obter(pastas, Navegador(downloads, [("cdt.pdf", certidao())]), cnpj="11222333000262")
    assert arquivo.read_bytes() == certidao()


def test_ignora_pdf_que_nao_e_a_certidao_e_certidao_de_outra_empresa(pastas):
    downloads, _ = pastas
    outros = [("boleto.pdf", pdf_com_texto("Boleto bancario", "11.222.333/0001-81")),
              ("cdt_99888777000166_19-11-2026.pdf", certidao("99.888.777/0001-66"))]
    arquivo = obter(pastas, Navegador(downloads, outros + [("cdt_11222333000181_19-11-2026.pdf", certidao())]))
    assert arquivo.read_bytes() == certidao()
    assert {p.name for p in downloads.iterdir()} == {n for n, _ in outros}


def test_navegador_que_nao_abre_gera_erro_claro(pastas):
    with pytest.raises(PortalErro, match=r"Não foi possível abrir o portal do CDT \(MG\)"):
        obter(pastas, lambda url: False)


def test_e_certidao_do_cnpj():
    assert cdt_mg.e_certidao_do_cnpj(certidao(), CNPJ)
    assert not cdt_mg.e_certidao_do_cnpj(certidao("99.888.777/0001-66"), CNPJ)
    assert not cdt_mg.e_certidao_do_cnpj(pdf_com_texto("Outro documento 11.222.333/0001-81"), CNPJ)
    assert not cdt_mg.e_certidao_do_cnpj(b"%PDF-quebrado", CNPJ)
