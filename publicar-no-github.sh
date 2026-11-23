#!/usr/bin/env bash
# Publica o COMEL no GitHub (github.com/aragonxpd154/COMEL) e liga o GitHub Pages.
#
# Uso, dentro da pasta extraída:
#   bash publicar-no-github.sh                 # repositório COMEL
#   bash publicar-no-github.sh comel-computer  # outro nome
#
# Se o repositório no GitHub já tiver arquivos (README, LICENSE criados pelo site, ou um envio
# anterior), o script junta o histórico de lá com o daqui. Nos arquivos que existirem dos dois
# lados vale a versão desta pasta; nada do GitHub é apagado.
#
# Com o GitHub CLI logado (sudo apt install gh && gh auth login), o script cria o repositório,
# envia tudo e liga o Pages. Sem ele, crie o repositório vazio em github.com/new e rode de novo.
set -euo pipefail
cd "$(dirname "$0")"

USUARIO="aragonxpd154"
REPO="${1:-COMEL}"
URL="https://github.com/$USUARIO/$REPO.git"

command -v git >/dev/null || { echo "Instale o git: sudo apt install git"; exit 1; }

echo "▶ preparando o repositório local"
if [ ! -d .git ]; then
  git init -q -b main
fi
git add -A
if git diff --cached --quiet; then
  echo "  nada novo para registrar"
else
  git -c user.name="${GIT_AUTHOR_NAME:-Marcos Santos}" -c user.email="${GIT_AUTHOR_EMAIL:-$USUARIO@users.noreply.github.com}" \
    commit -q -m "COMEL: placa única (KiCad 7), 2 USB, carcaça a laser com tela inclinada, firmware do C64 e visualizador 3D"
  echo "  commit criado"
fi

if command -v gh >/dev/null && gh auth status >/dev/null 2>&1; then
  if ! gh repo view "$USUARIO/$REPO" >/dev/null 2>&1; then
    echo "▶ criando $USUARIO/$REPO no GitHub"
    gh repo create "$USUARIO/$REPO" --public \
      --description "Commodore 64 em Pico 2 ligado à rede pela TSDA 4011R1 — KiCad, carcaça a laser e 3D" >/dev/null
  fi
fi

if git remote get-url origin >/dev/null 2>&1; then
  URL="$(git remote get-url origin)"
else
  git remote add origin "$URL"
fi
echo "▶ enviando para $URL"
if ! git push -u origin main; then
  echo "▶ o GitHub já tem arquivos neste repositório — juntando com os daqui"
  if ! git fetch origin main; then
    echo
    echo "Não achei o repositório. Crie em https://github.com/new (pode ser vazio) e rode este script de novo."
    exit 1
  fi
  git -c user.name="${GIT_AUTHOR_NAME:-Marcos Santos}" -c user.email="${GIT_AUTHOR_EMAIL:-$USUARIO@users.noreply.github.com}" \
    merge --no-edit --allow-unrelated-histories -X ours -m "Junta o que já estava no GitHub" origin/main
  git push -u origin main
fi

if command -v gh >/dev/null && gh auth status >/dev/null 2>&1; then
  echo "▶ ligando o GitHub Pages (branch main, pasta raiz)"
  gh api -X POST "repos/$USUARIO/$REPO/pages" -f "source[branch]=main" -f "source[path]=/" >/dev/null 2>&1 || \
  gh api -X PUT "repos/$USUARIO/$REPO/pages" -f "source[branch]=main" -f "source[path]=/" >/dev/null 2>&1 || true
fi

echo
echo "✓ pronto: https://github.com/$USUARIO/$REPO"
echo "  Visualizador 3D (1 a 2 minutos depois): https://$USUARIO.github.io/$REPO/"
echo "  Se o Pages não ligou sozinho: Settings → Pages → Branch: main, pasta / (root) → Save."
