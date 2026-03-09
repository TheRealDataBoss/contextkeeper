#!/usr/bin/env sh
# workbench-ai installer — POSIX shell
# Usage: curl -fsSL https://raw.githubusercontent.com/TheRealDataBoss/workbench/main/installer/install.sh | sh

set -eu

WORKBENCH_HOME="${HOME}/.workbench"
WORKBENCH_BIN="${WORKBENCH_HOME}/bin"
REPO_URL="https://github.com/TheRealDataBoss/workbench.git"
VERSION="0.1.0"

# --- Helpers ---

info()  { printf "\033[36m[workbench]\033[0m %s\n" "$1"; }
ok()    { printf "\033[32m[workbench]\033[0m %s\n" "$1"; }
warn()  { printf "\033[33m[workbench]\033[0m %s\n" "$1"; }
fail()  { printf "\033[31m[workbench]\033[0m %s\n" "$1" >&2; exit 1; }

command_exists() { command -v "$1" >/dev/null 2>&1; }

# --- Detect OS ---

detect_os() {
    case "$(uname -s)" in
        Linux*)   OS="linux" ;;
        Darwin*)  OS="macos" ;;
        CYGWIN*|MINGW*|MSYS*) OS="windows-wsl" ;;
        *)        OS="unknown" ;;
    esac
    info "Detected OS: ${OS}"
}

# --- Check prerequisites ---

check_prerequisites() {
    if ! command_exists git; then
        fail "git is required but not found. Install git and retry."
    fi
    info "git: $(git --version)"

    if command_exists node; then
        info "node: $(node --version)"
    else
        warn "node not found. npm CLI will not be available. Install Node.js 18+ for full functionality."
    fi

    if command_exists python3; then
        info "python3: $(python3 --version)"
    elif command_exists python; then
        info "python: $(python --version)"
    else
        warn "python not found. Python CLI will not be available. Install Python 3.10+ for full functionality."
    fi
}

# --- Install ---

install_workbench() {
    info "Installing workbench-ai v${VERSION} to ${WORKBENCH_HOME}"

    if [ -d "${WORKBENCH_HOME}" ]; then
        info "Existing installation found. Updating..."
        cd "${WORKBENCH_HOME}/src"
        git pull --ff-only origin main || fail "Failed to update workbench-ai. Check your network connection."
        cd - >/dev/null
    else
        mkdir -p "${WORKBENCH_HOME}"
        mkdir -p "${WORKBENCH_BIN}"
        info "Cloning workbench-ai repository..."
        git clone --depth 1 "${REPO_URL}" "${WORKBENCH_HOME}/src" || fail "Failed to clone repository. Check your network connection."
    fi

    # Create bin wrapper that delegates to npm or python CLI
    cat > "${WORKBENCH_BIN}/workbench" << 'WRAPPER'
#!/usr/bin/env sh
set -eu
WORKBENCH_SRC="${HOME}/.workbench/src"

if command -v node >/dev/null 2>&1; then
    exec node "${WORKBENCH_SRC}/packages/npm/bin/workbench.js" "$@"
elif command -v python3 >/dev/null 2>&1; then
    exec python3 -m workbench_ai.cli "$@"
elif command -v python >/dev/null 2>&1; then
    exec python -m workbench_ai.cli "$@"
else
    echo "Error: workbench-ai requires Node.js 18+ or Python 3.10+" >&2
    exit 1
fi
WRAPPER
    chmod +x "${WORKBENCH_BIN}/workbench"

    ok "Binary installed to ${WORKBENCH_BIN}/workbench"
}

# --- Update PATH ---

update_path() {
    SHELL_NAME="$(basename "${SHELL:-/bin/sh}")"
    PATH_LINE="export PATH=\"${WORKBENCH_BIN}:\$PATH\""

    case "${SHELL_NAME}" in
        zsh)  RC_FILE="${HOME}/.zshrc" ;;
        bash) RC_FILE="${HOME}/.bashrc" ;;
        fish)
            RC_FILE="${HOME}/.config/fish/config.fish"
            PATH_LINE="set -gx PATH ${WORKBENCH_BIN} \$PATH"
            ;;
        *)    RC_FILE="${HOME}/.profile" ;;
    esac

    if [ -f "${RC_FILE}" ] && grep -qF "${WORKBENCH_BIN}" "${RC_FILE}" 2>/dev/null; then
        info "PATH already configured in ${RC_FILE}"
    else
        printf "\n# workbench-ai\n%s\n" "${PATH_LINE}" >> "${RC_FILE}"
        ok "Added ${WORKBENCH_BIN} to PATH in ${RC_FILE}"
    fi

    # Make it available in current session
    export PATH="${WORKBENCH_BIN}:${PATH}"
}

# --- Verify ---

verify_installation() {
    if command_exists workbench; then
        ok "Installation verified: workbench is on PATH"
    else
        warn "workbench is installed but not yet on PATH. Restart your shell or run:"
        info "  export PATH=\"${WORKBENCH_BIN}:\$PATH\""
    fi
}

# --- Main ---

main() {
    info "workbench-ai installer v${VERSION}"
    info "================================="
    detect_os
    check_prerequisites
    install_workbench
    update_path
    verify_installation

    echo ""
    ok "workbench-ai v${VERSION} installed successfully!"
    echo ""
    info "Next steps:"
    info "  1. cd into your project directory"
    info "  2. Run: workbench init"
    info "  3. Run: workbench sync"
    echo ""
    info "Documentation: https://github.com/TheRealDataBoss/workbench"
}

main
