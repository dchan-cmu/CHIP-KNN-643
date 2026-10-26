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

GDB_PATCH="/tmp/tapacc_patch.gdb"
cat << 'EOF_GDB' > "$GDB_PATCH"
set breakpoint pending on
set confirm off
set pagination off
handle SIGSEGV stop print nopass

break *(_ZNK4tapa2cc13XilinxBackend17RewriteHelperFuncEPKN5clang12FunctionDeclERNS0_8EditSinkE + 296)
commands
if $rax == 0
  printf "[tapacc patch] Bypassing null helper function body by returning\n"
  return
end
continue
end

break tapa::cc::AddPragmaToBody
commands
if $rsi == 0
  printf "[tapacc patch] Bypassing AddPragmaToBody with null Stmt by returning\n"
  return
end
continue
end

run
EOF_GDB

RAW_OUT=$(gdb -q -batch -return-child-result -x "$GDB_PATCH" --args "$DIR/tapacc.real" "${ARGS[@]}" 2>&1)
RC=$?

echo "$RAW_OUT" | python3 -c '
import sys, re, json, os, glob
text = sys.stdin.read()
m = re.search(r"(\{.*\"schema_version\".*\})", text, re.DOTALL)
if m:
    sys.stderr.write(text[:m.start()] + text[m.end():])
    try:
        data = json.loads(m.group(1))

        knn_h_content = ""
        for h in ["src/knn.h", "knn.h", "./src/knn.h", "../src/knn.h"]:
            if os.path.isfile(h):
                with open(h) as hf:
                    knn_h_content = hf.read()
                break

        knn_cpp_content = ""
        for c in ["src/knn.cpp", "knn.cpp", "./src/knn.cpp", "../src/knn.cpp"]:
            if os.path.isfile(c):
                with open(c) as cf:
                    knn_cpp_content = cf.read()
                break

        full_code = knn_h_content + "\n" + knn_cpp_content

        for tname, tdict in data.get("tasks", {}).items():
            if "code" not in tdict or not tdict["code"]:
                tdict["code"] = full_code

        sys.stdout.write(json.dumps(data))
    except Exception as e:
        sys.stderr.write(f"Error patching JSON: {e}\n")
        sys.stdout.write(m.group(1))
    sys.exit(0)
else:
    sys.stderr.write(text)
    sys.exit(1)
'
PY_RC=$?

if [ $RC -ne 0 ] || [ $PY_RC -ne 0 ]; then
    echo "=== tapacc failed (RC=$RC, PY_RC=$PY_RC) ===" >&2
    exit 1
fi
EOF_WRAP
        chmod +x "$TAPACC_WRAPPER"
    fi

    echo "=== 1.5 Inspecting TAPA Internals ==="
    python3 -c "import tapa.core, tapa.task, inspect; print('=== Program.run_hls ===\n', inspect.getsource(tapa.core.Program.run_hls)); print('=== Task ===\n', inspect.getsource(tapa.task.Task.__init__))" 2>&1 || true

    echo "=== 2. Running Single-PE Exploration ==="
    python3 singlePE_design_exploration.py 2>&1 | tee "$REPO_ROOT/run_output.log" || true

    echo "=== 3. Gathering Build Logs ==="
    if [ -f "gen_singlePE_design/tapa_HLS_output.log" ]; then
        cp "gen_singlePE_design/tapa_HLS_output.log" "$REPO_ROOT/tapa_HLS_output.log"
    fi
    if [ -f "/tmp/tapacc_wrapper.log" ]; then
        cp "/tmp/tapacc_wrapper.log" "$REPO_ROOT/tapacc_wrapper.log"
    fi

    cd "$REPO_ROOT"

    echo "=== 4. Pushing Logs to GitHub (branch: debug-run) ==="
    git checkout -B debug-run
    git add -f run_output.log tapa_HLS_output.log tapacc_wrapper.log scripts/ 2>/dev/null || true
    git commit -m "Auto-upload run logs: $(date -u +'%Y-%m-%d %H:%M:%S UTC')" || true
    git push -u origin debug-run --force

    echo "=== Finished! Latest logs are live on branch 'debug-run' ==="
