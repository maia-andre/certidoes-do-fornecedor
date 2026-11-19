## O que muda

<!-- Em poucas linhas: o que o PR faz e por quê. -->

## Issue

<!-- "Closes #N" fecha a issue no merge. Para portal novo, cite também a issue de mapeamento (#6 municipal, #7 estadual). -->
Closes #
Refs #

## Como foi testado

- [ ] Suíte automatizada: `.venv\Scripts\python -m pytest -q`
- [ ] Teste assistido no portal real (portal novo ou correção de portal): quantos CNPJs e o que cada um mostrou, sem identificar as empresas

<!-- Resultado do teste assistido, se houver. -->

## Regras do projeto

- [ ] Não contorna captcha nem esconde a automação; se o portal recusa navegador automatizado, usa o modo navegador do servidor (RN-05, RN-09)
- [ ] Não guarda senhas, tokens nem sessões, inclusive do gov.br (RNF-03)
- [ ] Na dúvida, a leitura mostra "Conferir no PDF" e não presume situação nem validade (RN-03, RN-04)
- [ ] Os testes não acessam portais reais e usam textos de certidão com CNPJ e razão social fictícios (RNF-06)
- [ ] Nenhum dado real de empresa, senha ou dado pessoal no código, nos testes ou neste PR
- [ ] Spec, plano e README atualizados, quando o PR muda o comportamento
