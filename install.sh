#!/usr/bin/env bash
# SpeedTerm - Installateur Debian/Ubuntu
# Usage: curl -sSL https://raw.githubusercontent.com/YOUR_USERNAME/speedterm/main/install.sh | bash

set -e

GITHUB_REPO="YOUR_USERNAME/speedterm"

# Couleurs
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${CYAN}╔═══════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║   Installation de SpeedTerm               ║${NC}"
echo -e "${CYAN}╚═══════════════════════════════════════════╝${NC}"
echo

# Vérifie sudo
if [ "$EUID" -ne 0 ]; then
    SUDO="sudo"
else
    SUDO=""
fi

# Détection de l'OS
if [ -f /etc/debian_version ]; then
    echo -e "${GREEN}✓${NC} Système Debian/Ubuntu détecté"
else
    echo -e "${YELLOW}⚠${NC} Système non-Debian détecté, l'installation peut échouer"
fi

# Installation Python3 et pip
echo -e "${CYAN}➜${NC} Installation de Python3 et pip..."
$SUDO apt-get update -qq
$SUDO apt-get install -y -qq python3 python3-pip python3-venv

# Détection de PEP 668 (externally-managed-environment) sur les distributions récentes
PIP_FLAGS=""
if python3 -m pip install --help 2>&1 | grep -q "break-system-packages"; then
    PIP_FLAGS="--break-system-packages"
fi

# Installation de speedterm depuis GitHub
echo -e "${CYAN}➜${NC} Installation de speedterm depuis GitHub..."
python3 -m pip install --upgrade $PIP_FLAGS "git+https://github.com/${GITHUB_REPO}.git"

# Vérification
if command -v speedterm &> /dev/null; then
    echo
    echo -e "${GREEN}╔═══════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║   ✓ Installation réussie !                ║${NC}"
    echo -e "${GREEN}╚═══════════════════════════════════════════╝${NC}"
    echo
    echo -e "Lancez la commande : ${CYAN}speedterm${NC}"
else
    # speedterm peut avoir été installé dans ~/.local/bin
    if [ -f "$HOME/.local/bin/speedterm" ]; then
        echo
        echo -e "${YELLOW}⚠${NC} speedterm a été installé dans ${CYAN}\$HOME/.local/bin${NC}"
        echo -e "Ajoutez ce répertoire à votre PATH avec :"
        echo -e "  ${CYAN}echo 'export PATH=\"\$HOME/.local/bin:\$PATH\"' >> ~/.bashrc && source ~/.bashrc${NC}"
        echo
        echo -e "Ou lancez directement : ${CYAN}\$HOME/.local/bin/speedterm${NC}"
    else
        echo -e "${RED}✗ L'installation semble avoir échoué.${NC}"
        exit 1
    fi
fi
