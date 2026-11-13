"""Aplica a marca Abratel e o servidor fixo no código-fonte oficial do RustDesk.

Roda no GitHub Actions, na raiz de um checkout de github.com/rustdesk/rustdesk (com o
submódulo libs/hbb_common), antes do build:

    python abratel/aplicar-marca.py --host <servidor hbbs> --key <chave pública do hbbs>

Cada substituição precisa casar exatamente uma vez; se uma versão nova do RustDesk mudar
algum desses trechos, o script para com erro (em vez de gerar um cliente sem marca).
"""
import argparse
import re
import shutil
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
MARCA = AQUI / "marca"

# Nome interno: vira pasta de instalação, nome do serviço do Windows, nome do .exe instalado
# e o esquema de link (abratelsuporte://). Por isso sem espaço nem acento.
APP_NAME = "AbratelSuporte"
# Nome de exibição (propriedades do .exe, Painel de Controle).
PRODUTO = "Abratel Suporte"
DESCRICAO = "Abratel Suporte - Acesso Remoto"
EMPRESA = "Abratel Tecnologia"
# Opções da tela de configurações escondidas (chaves de flutter/lib/consts.dart).
OCULTAR = ("hide-network-settings", "hide-server-settings", "hide-proxy-settings", "hide-websocket-settings")


def trocar(arquivo: str, padrao: str, novo: str, vezes: int = 1):
    p = Path(arquivo)
    texto = p.read_bytes().decode("utf-8")  # bytes: preserva CRLF/LF do arquivo original
    texto_novo, n = re.subn(padrao, lambda _m: novo, texto, flags=re.M)
    if n != vezes:
        sys.exit(f"ERRO: {arquivo}: esperava {vezes} ocorrência(s) de /{padrao}/, achei {n}")
    p.write_bytes(texto_novo.encode("utf-8"))
    print(f"  {arquivo}: {padrao!r} -> {novo!r}")


def copiar(origem: str, destino: str):
    shutil.copyfile(MARCA / origem, destino)
    print(f"  {destino} <- marca/{origem}")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", required=True, help="servidor hbbs (ID server)")
    ap.add_argument("--key", required=True, help="chave pública do hbbs (id_ed25519.pub)")
    ap.add_argument("--portal", required=True, help="portal da empresa, ex.: https://suporte.exemplo.com.br/abratel")
    a = ap.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9+/]{43}=", a.key):
        sys.exit("ERRO: --key não parece uma chave ed25519 em base64")
    if not re.fullmatch(r"[A-Za-z0-9.\-:]+", a.host):
        sys.exit("ERRO: --host inválido")

    print("==> Servidor e nome (libs/hbb_common/src/config.rs)")
    cfg = "libs/hbb_common/src/config.rs"
    trocar(cfg, r'^pub const RENDEZVOUS_SERVERS: &\[&str\] = &\[[^\]]*\];',
           f'pub const RENDEZVOUS_SERVERS: &[&str] = &["{a.host}"];')
    trocar(cfg, r'^pub const RS_PUB_KEY: &str = "[^"]*";', f'pub const RS_PUB_KEY: &str = "{a.key}";')
    trocar(cfg, r'APP_NAME: RwLock<String> = RwLock::new\("RustDesk"\.to_owned\(\)\)',
           f'APP_NAME: RwLock<String> = RwLock::new("{APP_NAME}".to_owned())')
    # Esconde a aba Rede (servidor de ID/relay, proxy, websocket): o cliente não vê nem troca o servidor.
    # São as mesmas opções "builtin" que o gerador de cliente personalizado do RustDesk usa (valor "Y").
    ocultar = ", ".join(f'"{k}"' for k in OCULTAR)
    trocar(cfg, r'pub static ref BUILTIN_SETTINGS: RwLock<HashMap<String, String>> = Default::default\(\);',
           'pub static ref BUILTIN_SETTINGS: RwLock<HashMap<String, String>> = RwLock::new(\n'
           f'        [{ocultar}].iter().map(|k| (k.to_string(), "Y".to_owned())).collect());')

    print("==> Propriedades dos .exe")
    for toml in ("Cargo.toml", "libs/portable/Cargo.toml"):
        # O runner Windows faz checkout com CRLF, então o fim de linha aceita CR opcional.
        trocar(toml, r'^ProductName = "RustDesk"(?=\r?$)', f'ProductName = "{PRODUTO}"')
        trocar(toml, r'^FileDescription = "RustDesk Remote Desktop"(?=\r?$)', f'FileDescription = "{DESCRICAO}"')
    rc = "flutter/windows/runner/Runner.rc"
    trocar(rc, r'VALUE "CompanyName", "[^"]*"', f'VALUE "CompanyName", "{EMPRESA}"')
    trocar(rc, r'VALUE "FileDescription", "RustDesk Remote Desktop"', f'VALUE "FileDescription", "{DESCRICAO}"')
    trocar(rc, r'VALUE "ProductName", "RustDesk"', f'VALUE "ProductName", "{PRODUTO}"')
    # Fallback do título da janela, se a DLL não responder o nome.
    trocar("flutter/windows/runner/main.cpp", r'std::wstring app_name = L"RustDesk";',
           f'std::wstring app_name = L"{APP_NAME}";')

    print("==> Ícones e logos")
    copiar("icon.ico", "res/icon.ico")                       # rustdesk.exe e o pacote portátil
    copiar("tray-icon.ico", "res/tray-icon.ico")             # bandeja
    copiar("icon.ico", "flutter/windows/runner/resources/app_icon.ico")  # janela Flutter
    for png in ("icon.png", "32x32.png", "64x64.png", "128x128.png", "128x128@2x.png"):
        copiar(png, f"res/{png}")
    # A interface procura assets/icon.png e assets/logo*.png (máx. 300x60 na tela).
    for png in ("icon.png", "logo.png", "logo_light.png", "logo_dark.png"):
        copiar(png, f"flutter/assets/{png}")
    print("==> Lista de atendentes na tela inicial")
    if not re.fullmatch(r"https://[A-Za-z0-9.\-]+(:[0-9]+)?(/[A-Za-z0-9_\-]+)*", a.portal):
        sys.exit("ERRO: --portal precisa ser https://host/caminho, sem barra no fim")
    widget = (AQUI / "app" / "abratel_atendentes.dart").read_text(encoding="utf-8")
    if widget.count("__HALLO_PORTAL__") != 1:
        sys.exit("ERRO: abratel_atendentes.dart sem o marcador __HALLO_PORTAL__")
    Path("flutter/lib/desktop/widgets/abratel_atendentes.dart").write_bytes(
        widget.replace("__HALLO_PORTAL__", a.portal).encode("utf-8"))
    print("  flutter/lib/desktop/widgets/abratel_atendentes.dart <- app/abratel_atendentes.dart")
    home = "flutter/lib/desktop/pages/desktop_home_page.dart"
    trocar(home, r"^import '\.\./widgets/button\.dart';",
           "import '../widgets/button.dart';\nimport '../widgets/abratel_atendentes.dart';")
    trocar(home, r"^      if \(!isOutgoingOnly\) buildPasswordBoard\(context\),",
           "      if (!isOutgoingOnly) buildPasswordBoard(context),\n      if (!isOutgoingOnly) const AbratelAtendentes(),")
    print("==> Marca aplicada")


if __name__ == "__main__":
    main()
