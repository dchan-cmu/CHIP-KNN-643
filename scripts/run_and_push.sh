#!/bin/bash
    set -e

    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    REPO_ROOT="$(dirname "$SCRIPT_DIR")"

    cd "$SCRIPT_DIR"

    echo "=== 1. Cleaning previous build artifacts ==="
    rm -rf gen_singlePE_design gen_multiPE_design

    echo "=== 1b. Setting up tapacc wrapper with diagnostics ==="
    TAPACC_WRAPPER="$REPO_ROOT/.tapa/usr/bin/tapacc"
    if [ -f "$TAPACC_WRAPPER.real" ]; then
        cat << 'EOF_WRAP' > "$TAPACC_WRAPPER"
#!/bin/bash
DIR="$(dirname "$(readlink -f "$0")")"

if [ "$1" = "--version" ] || [ "$1" = "-version" ] || [ "$1" = "-v" ] || [ "$1" = "--help" ] || [ "$1" = "-help" ]; then
    exec "$DIR/tapacc.real" "$@"
fi

EMIT_DIR="/tmp/tapa_emit"
mkdir -p "$EMIT_DIR"

ARGS=()
INSERTED=0
for arg in "$@"; do
    if [ "$arg" = "--" ] && [ $INSERTED -eq 0 ]; then
        ARGS+=("--emit-dir" "$EMIT_DIR")
        INSERTED=1
    fi
    ARGS+=("$arg")
done
if [ $INSERTED -eq 0 ]; then
    ARGS+=("--emit-dir" "$EMIT_DIR")
fi

if command -v gdb >/dev/null 2>&1; then
    echo "=== Running tapacc.real under GDB ===" >&2
    gdb -batch -return-child-result -ex "run" -ex "bt 50" --args "$DIR/tapacc.real" "${ARGS[@]}"
else
    exec "$DIR/tapacc.real" "${ARGS[@]}"
fi
EOF_WRAP
        chmod +x "$TAPACC_WRAPPER"
    fi

    echo "=== 2. Running Single-PE Exploration ==="
    python3 singlePE_design_exploration.py 2>&1 | tee "$REPO_ROOT/run_output.log" || true

    echo "=== 3. Gathering Build Logs ==="
    if [ -f "gen_singlePE_design/tapa_HLS_output.log" ]; then
        cp "gen_singlePE_design/tapa_HLS_output.log" "$REPO_ROOT/tapa_HLS_output.log"
    fi

    cd "$REPO_ROOT"

    echo "=== 4. Pushing Logs to GitHub (branch: debug-run) ==="
    git checkout -B debug-run
    git add -f run_output.log tapa_HLS_output.log scripts/ 2>/dev/null || true
    git commit -m "Auto-upload run logs: $(date -u +'%Y-%m-%d %H:%M:%S UTC')" || true
    git push -u origin debug-run --force

    echo "=== Finished! Latest logs are live on branch 'debug-run' ==="
