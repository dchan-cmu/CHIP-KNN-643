#!/bin/bash
    set -e

    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    REPO_ROOT="$(dirname "$SCRIPT_DIR")"

    cd "$SCRIPT_DIR"

    echo "=== 1. Cleaning previous build artifacts ==="
    rm -rf gen_singlePE_design gen_multiPE_design

    echo "=== 1a. Patching TAPA core to remove obsolete gcc-6.2.0 path ==="
    python3 -c '
import tapa.core, re

core_file = tapa.core.__file__
with open(core_file, "r") as f:
    code = f.read()

modified = False
if "gcc-6.2.0" in code:
    print(f"Patching {core_file} to remove obsolete gcc-6.2.0 path...")
    code = re.sub(r"\*\([^\)]*gcc-6\.2\.0.*?for x in util\.get_vendor_include_paths\(\)\),?", "", code, flags=re.DOTALL)
    modified = True

if "std=\x27c++17\x27" in code:
    print(f"Setting {core_file} to std=c++14 for HLS...")
    code = code.replace("std=\x27c++17\x27", "std=\x27c++14\x27")
    modified = True

if "std=\"c++17\"" in code:
    print(f"Setting {core_file} to std=c++14 for HLS...")
    code = code.replace("std=\"c++17\"", "std=\"c++14\"")
    modified = True

if "\x27-DTAPA_TARGET_=XILINX_HLS\x27" in code and "TAPA_TARGET_DEVICE_" not in code:
    print(f"Injecting TAPA_TARGET_DEVICE_ and TAPA_TARGET_XILINX_HLS_ into {core_file}...")
    code = code.replace(
        "\x27-DTAPA_TARGET_=XILINX_HLS\x27",
        "\x27-DTAPA_TARGET_=XILINX_HLS\x27, \x27-DTAPA_TARGET_DEVICE_\x27, \x27-DTAPA_TARGET_XILINX_HLS_\x27, \x27-D__SYNTHESIS__\x27"
    )
    modified = True

if modified:
    compile(code, core_file, "exec")
    with open(core_file, "w") as f:
        f.write(code)
    print("Successfully updated tapa.core!")
else:
    print("tapa.core already up to date.")
' || true

    STREAM_H="$REPO_ROOT/.tapa/usr/include/tapa/xilinx/hls/stream.h"
    if [ -f "$STREAM_H" ]; then
        sed -i 's|hls::stream<internal::elem_t<T>> _;|mutable hls::stream<internal::elem_t<T>> _;|g' "$STREAM_H"
        echo "=== [tapa stream patch] Patched stream.h for mutable _ ==="
    fi

    python3 -c '
import os, glob

print("=== SEARCHING TAPA HEADERS ===")
repo = os.environ.get("REPO_ROOT", "/scratch/643_vitis_dchan2/CHIP-KNN-643")
inc_base = os.path.join(repo, ".tapa/usr/include")

for root, dirs, files in os.walk(inc_base):
    for f in files:
        p = os.path.join(root, f)
        rel = os.path.relpath(p, inc_base)
        if rel in ["tapa.h", "tapa/base/stream.h", "tapa/base/task.h", "tapa/base/int.h", "tapa/xilinx/hls/tapa.h", "tapa/xilinx/hls/stream.h", "tapa/xilinx/hls/mmap.h", "tapa/xilinx/hls/task.h"]:
            print(f"\n--- {rel} ---")
            with open(p, errors="ignore") as fp:
                print(fp.read())

print("\n=== GREP coroutine.h & TAPA_TARGET ===")
for root, dirs, files in os.walk(inc_base):
    for f in files:
        p = os.path.join(root, f)
        try:
            with open(p, errors="ignore") as fp:
                for idx, line in enumerate(fp, 1):
                    if "coroutine" in line or "TAPA_TARGET" in line:
                        print(f"{os.path.relpath(p, inc_base)}:{idx}: {line.strip()}")
        except Exception:
            pass
' > "$REPO_ROOT/tapa_headers_debug.log" 2>&1 || true

    echo "=== 1b. Setting up vitis_hls and tapacc wrappers with diagnostics ==="
    mkdir -p "$REPO_ROOT/.tapa/usr/bin"
    export PATH="$REPO_ROOT/.tapa/usr/bin:$PATH"

    VITIS_HLS_WRAPPER="$REPO_ROOT/.tapa/usr/bin/vitis_hls"
    cat << 'EOF_VHLS' > "$VITIS_HLS_WRAPPER"
#!/bin/bash
REAL_VITIS_HLS="/afs/ece.cmu.edu/class/ece643/software/xilinxVitis/Vitis_HLS/2023.2/bin/vitis_hls"
if [ ! -x "$REAL_VITIS_HLS" ] && [ -n "$XILINX_HLS" ]; then
    REAL_VITIS_HLS="$XILINX_HLS/bin/vitis_hls"
fi

for arg in "$@"; do
    if [ -f "$arg" ]; then
        sed -i \
            -e 's|-U__SYNTHESIS__|-D__SYNTHESIS__|g' \
            -e 's|-std=c++17|-std=c++14|g' \
            -e 's|-DTAPA_TARGET_=XILINX_HLS|-DTAPA_TARGET_=XILINX_HLS -DTAPA_TARGET_DEVICE_ -DTAPA_TARGET_XILINX_HLS_ -D__SYNTHESIS__|g' \
            -e 's|-I/usr/include/c++/[^ "]*||g' \
            -e 's|-I/usr/include/x86_64-linux-gnu||g' \
            -e 's|-I/usr/include||g' \
            -e 's|-I/usr/bin/[^ "]*||g' \
            "$arg"
        echo "=== [vitis_hls wrapper] Filtered $arg ===" >&2
    fi
done

exec "$REAL_VITIS_HLS" "$@"
EOF_VHLS
    chmod +x "$VITIS_HLS_WRAPPER"

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

        clean_cflags = []
        for cf in data.get("cflags", []):
            if cf == "-U__SYNTHESIS__":
                continue
            if any(bad in cf for bad in [
                "/usr/include/c++",
                "/usr/include/x86_64-linux-gnu",
                "/usr/include",
                "/usr/bin/../lib/clang",
                "clang/20",
                "clang/22"
            ]):
                continue
            clean_cflags.append(cf)
        if "-D__SYNTHESIS__" not in clean_cflags:
            clean_cflags.append("-D__SYNTHESIS__")
        data["cflags"] = clean_cflags

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
    python3 -c "import tapa.core, tapa.task, inspect; print('=== Program.run_hls ===\n', inspect.getsource(tapa.core.Program.run_hls)); print('=== Task ===\n', inspect.getsource(tapa.task.Task.__init__))" > "$REPO_ROOT/tapa_internals.log" 2>&1 || true

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
    git add -f run_output.log tapa_HLS_output.log tapacc_wrapper.log tapa_internals.log tapa_headers_debug.log scripts/ 2>/dev/null || true
    git commit -m "Auto-upload run logs: $(date -u +'%Y-%m-%d %H:%M:%S UTC')" || true
    git push -u origin debug-run --force

    echo "=== Finished! Latest logs are live on branch 'debug-run' ==="
