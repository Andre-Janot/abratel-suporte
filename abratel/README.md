# Abratel Suporte: cliente RustDesk da Abratel Tecnologia

Fork de marca do [RustDesk](https://github.com/rustdesk/rustdesk) usado pela Abratel Tecnologia no suporte remoto aos clientes.
O branch `abratel` é a árvore de uma tag oficial do `rustdesk/rustdesk` (commit raiz) mais um único commit, que só acrescenta
esta pasta e `.github/workflows/abratel-windows.yml`.

- `aplicar-marca.py`: no build, troca o nome (AbratelSuporte), o servidor e a chave fixos, as propriedades do .exe e os
  ícones, e esconde a aba Rede das configurações.
- `marca/`: ícones e logos da Abratel Tecnologia (marca da empresa; não fazem parte da licença do código).
- O workflow "Abratel Suporte (Windows x64)" roda a cada push neste branch, ou manualmente, e gera o artifact
  `abratel-suporte-windows-x86_64`. Servidor e chave vêm dos secrets `HALLO_HOST` e `HALLO_KEY`.

Código sob AGPL-3.0, como o RustDesk original (veja `LICENCE` na raiz).
