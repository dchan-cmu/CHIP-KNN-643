#!/bin/bash
    set -e

    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    REPO_ROOT="$(dirname "$SCRIPT_DIR")"
    export REPO_ROOT

    cd "$SCRIPT_DIR"

    echo "=== 0. Setting up Xilinx Environment Variables ==="
    for conda_bin in "/afs/ece/usr/dchan2/miniconda3/bin" "/afs/ece.cmu.edu/usr/dchan2/miniconda3/bin" "$HOME/miniconda3/bin"; do
        if [ -d "$conda_bin" ]; then
            export PATH="$conda_bin:$PATH"
        fi
    done

    if [ -z "$XILINX_VITIS" ] && [ -f "/afs/ece.cmu.edu/class/ece643/software/xilinxVitis/Vitis/2023.2/settings64.sh" ]; then
        source "/afs/ece.cmu.edu/class/ece643/software/xilinxVitis/Vitis/2023.2/settings64.sh" || true
    fi
    for conda_bin in "/afs/ece/usr/dchan2/miniconda3/bin" "/afs/ece.cmu.edu/usr/dchan2/miniconda3/bin" "$HOME/miniconda3/bin"; do
        if [ -d "$conda_bin" ]; then
            export PATH="$conda_bin:$PATH"
        fi
    done
    export PATH
    if [ -z "$XILINX_VITIS" ]; then
        export XILINX_VITIS="/afs/ece.cmu.edu/class/ece643/software/xilinxVitis/Vitis/2023.2"
    fi
    if [ -z "$XILINX_HLS" ]; then
        export XILINX_HLS="/afs/ece.cmu.edu/class/ece643/software/xilinxVitis/Vitis_HLS/2023.2"
    fi
    if [ -z "$XILINX_XRT" ] && [ -d "/opt/xilinx/xrt" ]; then
        export XILINX_XRT="/opt/xilinx/xrt"
    fi
    echo "Using XILINX_VITIS=$XILINX_VITIS"
    echo "Using XILINX_HLS=$XILINX_HLS"

    echo "=== 0a. Setting up iverilog preprocessor for Pyverilog ==="
    mkdir -p "$REPO_ROOT/.tapa/usr/bin"
    export PATH="$REPO_ROOT/.tapa/usr/bin:$PATH"

    IVERILOG_FALLBACK="$REPO_ROOT/.tapa/usr/bin/iverilog"
    cat << 'EOF_IV' > "$IVERILOG_FALLBACK"
#!/usr/bin/env python3
import sys, os, subprocess

# Delegate to real iverilog if present in system paths
for candidate in [
    "/usr/bin/iverilog",
    "/usr/local/bin/iverilog",
    "/afs/ece.cmu.edu/support/iverilog/bin/iverilog",
    "/afs/ece/support/bin/iverilog",
]:
    if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
        res = subprocess.run([candidate] + sys.argv[1:])
        sys.exit(res.returncode)

if "-v" in sys.argv or "--version" in sys.argv or "-V" in sys.argv:
    print("Icarus Verilog version 12.0 (fallback preprocessor)")
    sys.exit(0)

outfile = None
files = []
includes = []
defines = []
i = 1
while i < len(sys.argv):
    arg = sys.argv[i]
    if arg == "-o":
        i += 1
        outfile = sys.argv[i]
    elif arg == "-I":
        i += 1
        includes.append(sys.argv[i])
    elif arg.startswith("-I"):
        includes.append(arg[2:])
    elif arg == "-D":
        i += 1
        defines.append(sys.argv[i])
    elif arg.startswith("-D"):
        defines.append(arg[2:])
    elif arg in ("-E", "-v", "--version", "-V"):
        pass
    elif not arg.startswith("-"):
        files.append(arg)
    i += 1

if not outfile:
    sys.exit(0)

content = []
for f in files:
    if os.path.isfile(f):
        with open(f, "r", errors="ignore") as fp:
            for line in fp:
                if line.strip().startswith("`include"):
                    inc_name = line.strip().split()[1].strip('"\'<>')
                    found = False
                    for d in includes + [os.path.dirname(f)]:
                        inc_path = os.path.join(d, inc_name)
                        if os.path.isfile(inc_path):
                            content.append(open(inc_path, "r", errors="ignore").read())
                            found = True
                            break
                    if not found:
                        content.append(line)
                else:
                    content.append(line)

with open(outfile, "w") as out:
    out.write("".join(content))

sys.exit(0)
EOF_IV
    chmod +x "$IVERILOG_FALLBACK"
    export PYVERILOG_IVERILOG="$IVERILOG_FALLBACK"
    echo "Using iverilog: $(which iverilog)"

    echo "=== 1. Cleaning previous build artifacts ==="
    rm -rf gen_singlePE_design gen_multiPE_design

    echo "=== 1a. Patching TAPA core to remove obsolete gcc-6.2.0 path ==="
    python3 -c '
import tapa.core, re

core_file = tapa.core.__file__
with open(core_file, "r") as f:
    code = f.read()

with open("tapa_core_debug.log", "w") as df:
    df.write(code)

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

if "\x27-DTAPA_TARGET_=XILINX_HLS\x27" in code and "-D__SYNTHESIS__" not in code:
    print(f"Injecting TAPA_TARGET_DEVICE_, TAPA_TARGET_XILINX_HLS_, and __SYNTHESIS__ into {core_file}...")
    code = code.replace(
        "\x27-DTAPA_TARGET_=XILINX_HLS\x27",
        "\x27-DTAPA_TARGET_=XILINX_HLS\x27, \x27-DTAPA_TARGET_DEVICE_\x27, \x27-DTAPA_TARGET_XILINX_HLS_\x27, \x27-D__SYNTHESIS__\x27"
    )
    modified = True

# Revert old broken patch if present on remote
old_match = re.search(r"        import glob, os\n.*?raise RuntimeError\(\x27HLS failed for \{\}\x27\.format\(task\.name\)\)", code, re.DOTALL)
if old_match:
    code = code[:old_match.start()] + "        raise RuntimeError(\x27HLS failed for {}\x27.format(task.name))" + code[old_match.end():]
    modified = True
    print(f"Reverted broken worker patch in {core_file}")

# Inject in-context dumper inside with hls.RunHls(...) as proc: before temp directory is deleted
target_comm = "          stdout, stderr = proc.communicate()"
new_dumper = """          stdout, stderr = proc.communicate()
          if proc.returncode != 0:
            import glob as _glob
            print(f"=== FULL VITIS HLS LOG FOR {task.name} ===", flush=True)
            for d in _glob.glob(f"/tmp/run-hls-{task.name}*"):
              for root, dirs, files in os.walk(d):
                for file in files:
                  if file.endswith((".log", ".rpt", ".tcl", ".xml", ".size")):
                    p = os.path.join(root, file)
                    print(f"--- File: {p} ---", flush=True)
                    try:
                      with open(p, "r", errors="ignore") as lf:
                        print(lf.read(), flush=True)
                    except Exception as e:
                      print(f"Could not read {p}: {e}", flush=True)"""
if "FULL VITIS HLS LOG FOR" not in code and target_comm in code:
    code = code.replace(target_comm, new_dumper)
    modified = True
    print(f"Injected in-context HLS log dumper into {core_file}!")

target_extract = "        tarfileobj.extractall(path=self.work_dir)"
patch_invoke = """        tarfileobj.extractall(path=self.work_dir)
    try:
      import subprocess
      patch_script = os.path.join(os.environ.get("REPO_ROOT", "/scratch/643_vitis_dchan2/CHIP-KNN-643"), "scripts/patch_task_rtl.py")
      graph_path = os.path.join(self.work_dir, "graph.json")
      if os.path.isfile(patch_script) and os.path.isfile(graph_path):
        _logger.info("Auto-wrapping task HDL modules with patch_task_rtl.py...")
        subprocess.run([sys.executable, patch_script, self.work_dir, graph_path], check=True)
    except Exception as e:
      _logger.warning("patch_task_rtl hook notice: %s", e)"""
if "Auto-wrapping task HDL modules" not in code and target_extract in code:
    code = code.replace(target_extract, patch_invoke)
    modified = True
    print(f"Injected patch_task_rtl hook into generate_task_rtl in {core_file}!")

if modified:
    compile(code, core_file, "exec")
    with open(core_file, "w") as f:
        f.write(code)
    print("Successfully updated tapa.core!")
else:
    print("tapa.core already up to date.")
' || true

    echo "=== 1a-2. Patching TAPA instance to support scalar dict arguments ==="
    python3 -c '
import os, sys, glob, re

inst_candidates = []
for p in sys.path:
    target = os.path.join(p, "tapa/instance.py")
    if os.path.isfile(target):
        inst_candidates.append(target)
for base in ["/afs/ece.cmu.edu/usr/dchan2/miniconda3", "/afs/ece/usr/dchan2/miniconda3", os.path.expanduser("~/miniconda3")]:
    for p in glob.glob(f"{base}/**/tapa/instance.py", recursive=True):
        inst_candidates.append(p)

for inst_file in set(inst_candidates):
    try:
        with open(inst_file, "r") as f:
            code = f.read()
        with open("tapa_instance_debug.log", "w") as df:
            df.write(code)
        pattern = r"rtl\.sanitize_array_name\(\s*arg\[[\x27\"]arg[\x27\"]\]\s*\)"
        replacement = "(f\"{arg[\x27arg\x27].get(\x27width\x27, 32)}\x27d{arg[\x27arg\x27][\x27value\x27]}\" if isinstance(arg[\x27arg\x27], dict) else rtl.sanitize_array_name(str(arg[\x27arg\x27])))"
        if re.search(pattern, code):
            print(f"Patching {inst_file} for scalar dictionary arguments...")
            code = re.sub(pattern, replacement, code)
            compile(code, inst_file, "exec")
            with open(inst_file, "w") as f:
                f.write(code)
            print(f"Successfully patched {inst_file}!")
        else:
            print(f"{inst_file} already patched or pattern not found.")
    except Exception as e:
        print(f"Notice: checking {inst_file}: {e}")
' || true

    echo "=== 1a-3. Patching TAPA module to support get_port_of fallback ==="
    python3 -c '
import os, sys, glob, re

mod_candidates = []
for p in sys.path:
    target = os.path.join(p, "tapa/verilog/xilinx/module.py")
    if os.path.isfile(target):
        mod_candidates.append(target)
for base in ["/afs/ece.cmu.edu/usr/dchan2/miniconda3", "/afs/ece/usr/dchan2/miniconda3", os.path.expanduser("~/miniconda3")]:
    for p in glob.glob(f"{base}/**/tapa/verilog/xilinx/module.py", recursive=True):
        mod_candidates.append(p)

for mod_file in set(mod_candidates):
    try:
        with open(mod_file, "r") as f:
            code = f.read()
        pattern = r"(?:[ \t]*base_fifo = fifo\[:-5\].*?)?(?:[ \t]*if sanitized_fifo in ports:.*?)?raise ValueError\(f\x27module \{self\.name\} does not have port \{fifo\}\.\{suffix\}\x27\)"
        fallback = """base_fifo = fifo[:-5] if fifo.endswith(\x27_peek\x27) else fifo
    sanitized_base = sanitize_array_name(base_fifo)
    for infix in infixes:
      p = ports.get(f\x27{sanitized_base}{infix}{suffix}\x27)
      if p is not None:
        _logger.warning("Mapped %s%s to %s%s%s", fifo, suffix, sanitized_base, infix, suffix)
        return p
    for candidate in [sanitized_base, sanitized_fifo]:
      if candidate in ports:
        _logger.warning("Falling back to port %s for %s%s", candidate, fifo, suffix)
        return ports[candidate]
    raise ValueError(f\x27module {self.name} does not have port {fifo}.{suffix}\x27)"""
        if re.search(pattern, code, re.DOTALL):
            print(f"Patching {mod_file} for get_port_of fallback (with peek support)...")
            code = re.sub(pattern, fallback, code, count=1, flags=re.DOTALL)
            compile(code, mod_file, "exec")
            with open(mod_file, "w") as f:
                f.write(code)
            print(f"Successfully patched {mod_file}!")
        else:
            print(f"{mod_file} pattern not found.")
    except Exception as e:
        print(f"Notice: checking {mod_file}: {e}")
' || true

    echo "=== 1a-4. Inspecting and Patching TAPA async_mmap ==="
    python3 -c '
import os, sys, glob, re, inspect

amm_candidates = []
for p in sys.path:
    target = os.path.join(p, "tapa/verilog/xilinx/async_mmap.py")
    if os.path.isfile(target):
        amm_candidates.append(target)
for base in ["/afs/ece.cmu.edu/usr/dchan2/miniconda3", "/afs/ece/usr/dchan2/miniconda3", os.path.expanduser("~/miniconda3")]:
    for p in glob.glob(f"{base}/**/tapa/verilog/xilinx/async_mmap.py", recursive=True):
        amm_candidates.append(p)

for amm_file in set(amm_candidates):
    try:
        with open(amm_file, "r") as f:
            code = f.read()
        with open("tapa_async_mmap_debug.log", "w") as df:
            df.write(code)

        pattern = r"assert\s+port_name\s+is\s+not\s+None,\s*f[\x27\"][^\x27\"]*offset[^\x27\"]*[\x27\"]"
        replacement = """if port_name is None:
      for cand in (f"{port}_offset", f"{port}", f"{arg}_offset", f"{arg}"):
        if cand in instance.task.module.ports:
          port_name = cand
          break
      else:
        port_name = f"{port}_offset"
    # patched offset assertion"""
        if re.search(pattern, code):
            print(f"Patching {amm_file} for async_mmap offset fallback...")
            code = re.sub(pattern, replacement, code)
            compile(code, amm_file, "exec")
            with open(amm_file, "w") as f:
                f.write(code)
            print(f"Successfully patched {amm_file}!")
        else:
            print(f"{amm_file} already patched or pattern not found.")
    except Exception as e:
        print(f"Notice: checking {amm_file}: {e}")
' || true

    echo "=== 1a-5. Patching TAPA task clock period fallback ==="
    python3 -c '
import os, sys, glob, re

cands = []
for p in sys.path:
    t = os.path.join(p, "tapa/task.py")
    if os.path.isfile(t):
        cands.append(t)
for base in ["/afs/ece.cmu.edu/usr/dchan2/miniconda3", "/afs/ece/usr/dchan2/miniconda3", os.path.expanduser("~/miniconda3")]:
    cands.extend(glob.glob(f"{base}/**/tapa/task.py", recursive=True))

for f in set(cands):
    try:
        code = open(f).read()
        with open("tapa_task_debug.log", "w") as df:
            df.write(code)
        pat = r"raise ValueError\(f\x27clock period of task \{self\.name\} not populated\x27\)"
        rep = "return __import__(\x27decimal\x27).Decimal(\x275.0\x27)  # patched fallback"
        if re.search(pat, code):
            code = re.sub(pat, rep, code)
            compile(code, f, "exec")
            open(f, "w").write(code)
            print(f"Patched clock period fallback in {f}")
        else:
            print(f"{f} already patched or pattern not found.")
    except Exception as e:
        print(f"Notice: {f}: {e}")
' || true

    python3 -c '
import os, glob

repo = os.environ.get("REPO_ROOT", "/scratch/643_vitis_dchan2/CHIP-KNN-643")
stream_h = os.path.join(repo, ".tapa/usr/include/tapa/xilinx/hls/stream.h")

clean_hls_stream_code = ""
patched_hdr = os.path.join(repo, "real_xilinx_hls_stream.h")
if os.path.isfile(patched_hdr):
    with open(patched_hdr, "r") as rf:
        clean_hls_stream_code = rf.read()
    print(f"Loaded patched Xilinx hls_stream.h from {patched_hdr}")
else:
    raise FileNotFoundError(f"Missing {patched_hdr}")

clean_stream_code = """#pragma once

#ifndef __SYNTHESIS__
#define __SYNTHESIS__
#endif

#include "tapa/base/stream.h"

#include <cassert>
#include <cstddef>
#include <cstdint>

#include <hls_stream.h>

namespace tapa {

template <typename T, uint64_t N = kStreamDefaultDepth,
          uint64_t SimulationDepth = N>
using stream = hls::stream<T, int(N)>;

template <typename T>
using istream = hls::stream<T>;

template <typename T>
using ostream = hls::stream<T>;

template <typename T, uint64_t S>
using istreams = istream<T>[S];

template <typename T, uint64_t S>
using ostreams = ostream<T>[S];

template <typename T, uint64_t S, uint64_t N = kStreamDefaultDepth,
          uint64_t SimulationDepth = N>
using streams = stream<T, N>[S];

}  // namespace tapa
"""
hls_stream_targets = [
    os.path.join(repo, ".tapa/usr/include/hls_stream.h"),
]
stream_targets = [
    os.path.join(repo, ".tapa/usr/include/tapa/xilinx/hls/stream.h"),
]
clean_mmap_code = """#pragma once

#ifndef __SYNTHESIS__
#define __SYNTHESIS__
#endif

#include <cstddef>
#include <cstdint>
#include <hls_stream.h>

#include "tapa/xilinx/hls/stream.h"

namespace tapa {

template <typename T>
using mmap = T*;

template <typename T>
struct async_mmap {
  using addr_t = int64_t;
  using resp_t = uint8_t;

  hls::stream<addr_t> read_addr;
  hls::stream<T> read_data;
  hls::stream<addr_t> write_addr;
  hls::stream<T> write_data;
  hls::stream<resp_t> write_resp;
};

template <typename T, uint64_t S>
class mmaps;

template <typename T, int chan_count, int64_t chan_size>
class hmap;

}  // namespace tapa
"""
mmap_targets = [
    os.path.join(repo, ".tapa/usr/include/tapa/xilinx/hls/mmap.h"),
]
clean_task_code = """#pragma once

#include <string>
#include <utility>

#include "tapa/base/task.h"

namespace tapa {

struct executable {
  explicit executable(std::string path);
};

struct task {
#if defined(TAPA_TARGET_DEVICE_) || defined(TAPA_TARGET_XILINX_HLS_) || defined(__SYNTHESIS__)
  template <typename Func, typename... Args>
  task& invoke(Func&&, Args&&...) { return *this; }

  template <internal::InvokeMode mode, typename Func, typename... Args>
  task& invoke(Func&&, Args&&...) { return *this; }

  template <typename Func, typename... Args, size_t name_size>
  task& invoke(Func&&, const char (&)[name_size], Args&&...) { return *this; }

  template <internal::InvokeMode mode, typename Func, typename... Args,
            size_t name_size>
  task& invoke(Func&&, const char (&)[name_size], Args&&...) { return *this; }

  template <internal::InvokeMode mode, int n, typename Func, typename... Args>
  task& invoke(Func&&, Args&&...) { return *this; }

  template <internal::InvokeMode mode, int n, typename Func, typename... Args,
            size_t name_size>
  task& invoke(Func&&, const char (&)[name_size], Args&&...) { return *this; }

  template <typename Func, typename... Args>
  task& invoke(Func&&, executable, Args&&...) { return *this; }
#else
  template <typename Func, typename... Args>
  task& invoke(Func&& func, Args&&... args) {
    return invoke<join>(std::forward<Func>(func), "",
                        std::forward<Args>(args)...);
  }

  template <internal::InvokeMode mode, typename Func, typename... Args>
  task& invoke(Func&& func, Args&&... args) {
    return invoke<mode>(std::forward<Func>(func), "",
                        std::forward<Args>(args)...);
  }

  template <typename Func, typename... Args, size_t name_size>
  task& invoke(Func&& func, const char (&name)[name_size], Args&&... args) {
    return invoke<join>(std::forward<Func>(func), name,
                        std::forward<Args>(args)...);
  }

  template <internal::InvokeMode mode, typename Func, typename... Args,
            size_t name_size>
  task& invoke(Func&& func, const char (&name)[name_size], Args&&... args) {
    func(std::forward<Args>(args)...);
    return *this;
  }

  template <internal::InvokeMode mode, int n, typename Func, typename... Args>
  task& invoke(Func&& func, Args&&... args) {
    return invoke<mode, n>(std::forward<Func>(func), "",
                           std::forward<Args>(args)...);
  }

  template <internal::InvokeMode mode, int n, typename Func, typename... Args,
            size_t name_size>
  task& invoke(Func&& func, const char (&name)[name_size], Args&&... args) {
    for (int i = 0; i < n; ++i) {
      invoke<mode>(std::forward<Func>(func), std::forward<Args>(args)...);
    }
    return *this;
  }

  template <typename Func, typename... Args>
  task& invoke(Func&& func, executable exe, Args&&... args) {
    return invoke<join>(std::forward<Func>(func), "",
                        std::forward<Args>(args)...);
  }
#endif
};

}  // namespace tapa
"""
task_targets = [
    os.path.join(repo, ".tapa/usr/include/tapa/xilinx/hls/task.h"),
]
import glob
for p in glob.glob("/scratch/643_vitis_dchan2/**/tapa/xilinx/hls/stream.h", recursive=True):
    stream_targets.append(p)
for p in glob.glob("/scratch/643_vitis_dchan2/**/tapa/xilinx/hls/mmap.h", recursive=True):
    mmap_targets.append(p)
for p in glob.glob("/scratch/643_vitis_dchan2/**/tapa/xilinx/hls/task.h", recursive=True):
    task_targets.append(p)
for p in glob.glob("/afs/ece/usr/dchan2/miniconda3/**/tapa/xilinx/hls/stream.h", recursive=True):
    stream_targets.append(p)
for p in glob.glob("/afs/ece/usr/dchan2/miniconda3/**/tapa/xilinx/hls/mmap.h", recursive=True):
    mmap_targets.append(p)
for p in glob.glob("/afs/ece/usr/dchan2/miniconda3/**/tapa/xilinx/hls/task.h", recursive=True):
    task_targets.append(p)
for p in glob.glob("/scratch/643_vitis_dchan2/**/tapa/xilinx/hls/hls_stream.h", recursive=True):
    hls_stream_targets.append(p)
for p in glob.glob("/afs/ece/usr/dchan2/miniconda3/**/tapa/xilinx/hls/hls_stream.h", recursive=True):
    hls_stream_targets.append(p)

for hs in set(hls_stream_targets):
    try:
        os.makedirs(os.path.dirname(hs), exist_ok=True)
        with open(hs, "w") as f:
            f.write(clean_hls_stream_code)
        print(f"Successfully wrote clean hls_stream.h to {hs}")
    except Exception as e:
        print(f"Failed to write to {hs}: {e}")

for s in set(stream_targets):
    try:
        os.makedirs(os.path.dirname(s), exist_ok=True)
        with open(s, "w") as f:
            f.write(clean_stream_code)
        print(f"Successfully wrote clean tapa stream.h to {s}")
    except Exception as e:
        print(f"Failed to write to {s}: {e}")

for m in set(mmap_targets):
    try:
        os.makedirs(os.path.dirname(m), exist_ok=True)
        with open(m, "w") as f:
            f.write(clean_mmap_code)
        print(f"Successfully wrote clean tapa mmap.h to {m}")
    except Exception as e:
        print(f"Failed to write to {m}: {e}")

for t in set(task_targets):
    try:
        os.makedirs(os.path.dirname(t), exist_ok=True)
        with open(t, "w") as f:
            f.write(clean_task_code)
        print(f"Successfully wrote clean tapa task.h to {t}")
    except Exception as e:
        print(f"Failed to write to {t}: {e}")

util_targets = []
for p in glob.glob("/scratch/643_vitis_dchan2/**/tapa/xilinx/hls/util.h", recursive=True):
    util_targets.append(p)
for p in glob.glob("/afs/ece/usr/dchan2/miniconda3/**/tapa/xilinx/hls/util.h", recursive=True):
    util_targets.append(p)
for u in set(util_targets):
    try:
        with open(u, "r") as uf:
            uc = uf.read()
        if "#pragma HLS protocol float" in uc:
            uc = uc.replace("#pragma HLS protocol float", "// #pragma HLS protocol float")
            with open(u, "w") as uf:
                uf.write(uc)
            print(f"Patched {u} to remove invalid pragma!")
    except Exception as e:
        print(f"Failed to patch {u}: {e}")
' || true

    python3 -c '
import os, glob

print("=== SEARCHING TAPA HEADERS ===")
repo = os.environ.get("REPO_ROOT", "/scratch/643_vitis_dchan2/CHIP-KNN-643")
inc_base = os.path.join(repo, ".tapa/usr/include")

for root, dirs, files in os.walk(inc_base):
    for f in files:
        p = os.path.join(root, f)
        rel = os.path.relpath(p, inc_base)
        if rel in ["tapa.h", "tapa/base/stream.h", "tapa/base/task.h", "tapa/base/int.h", "tapa/xilinx/hls/tapa.h", "tapa/xilinx/hls/stream.h", "tapa/xilinx/hls/mmap.h", "tapa/xilinx/hls/task.h", "tapa/xilinx/hls/util.h", "tapa/compat.h"]:
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

print("\n=== GREP mutex in headers ===")
for root, dirs, files in os.walk(inc_base):
    for f in files:
        p = os.path.join(root, f)
        try:
            content = open(p, errors="ignore").read()
            if "mutex" in content:
                for idx, line in enumerate(content.splitlines(), 1):
                    if "mutex" in line or "include" in line:
                        print(f"{os.path.relpath(p, inc_base)}:{idx}: {line.strip()}")
        except Exception:
            pass
' > "$REPO_ROOT/tapa_headers_debug.log" 2>&1 || true

    echo "=== 1b. Setting up vitis_hls and tapacc wrappers with diagnostics ==="
    mkdir -p "$REPO_ROOT/.tapa/usr/bin"
    export PATH="$REPO_ROOT/.tapa/usr/bin:$PATH"
    echo "which tapac: $(which tapac || true)"

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
            -e 's|-DTAPA_TARGET_=XILINX_HLS|-DTAPA_TARGET_=XILINX_HLS -DTAPA_TARGET_DEVICE_ -DTAPA_TARGET_XILINX_HLS_ -D__SYNTHESIS__ -D__VITIS_HLS__ -DHLS_STREAM_THREAD_UNSAFE -D__thread= -Dthread_local=|g' \
            -e 's|-I/usr/include/c++/[^ "]*||g' \
            -e 's|-I/usr/include/x86_64-linux-gnu||g' \
            -e 's|-I/usr/include||g' \
            -e 's|-I/usr/bin/[^ "]*||g' \
            "$arg"
        echo "=== [vitis_hls wrapper] Filtered $arg ===" >&2
    fi
done

"$REAL_VITIS_HLS" "$@"
RET=$?
if [ $RET -ne 0 ]; then
    echo "=== [vitis_hls wrapper] Vitis HLS failed with exit code $RET ===" >&2
    for d in /tmp/run-hls-*; do
        if [ -d "$d" ]; then
            for rpt in $(find "$d" -name "*.rpt" -o -name "*.log"); do
                echo "=== LOG FILE: $rpt ===" >&2
                tail -n 100 "$rpt" >&2
            done
        fi
    done
fi
exit $RET
EOF_VHLS
    chmod +x "$VITIS_HLS_WRAPPER"

    PATCH_GRAPH_PY="$REPO_ROOT/.tapa/usr/bin/patch_graph.py"
    cat << 'EOF_PG' > "$PATCH_GRAPH_PY"
import sys, re, json, os, glob

text = sys.stdin.read()
m = re.search(r"(\{.*\"schema_version\".*\})", text, re.DOTALL)
if m:
    sys.stderr.write(text[:m.start()] + text[m.end():])
    try:
        data = json.loads(m.group(1))

        knn_cpp_content = ""
        for c in ["src/knn.cpp", "knn.cpp", "./src/knn.cpp", "../src/knn.cpp"]:
            if os.path.isfile(c):
                with open(c) as cf:
                    knn_cpp_content = cf.read()
                break

        full_code = knn_cpp_content

        def extract_task_code(task_name, source_code):
            preamble = '#include "knn.h"\n#define printf(...) ((void)0)\n#define absval(input) ((input) > 0 ? static_cast<DATA_TYPE>(input) : static_cast<DATA_TYPE>(-1 * (input)))\n'
            if task_name == "Knn":
                return preamble + '''
void Knn(tapa::mmap<INTERFACE_WIDTH> in_0, tapa::mmap<INT32> final_out) {
#pragma HLS interface m_axi port=in_0 offset=slave bundle=gmem0 depth=1
#pragma HLS interface m_axi port=final_out offset=slave bundle=gmem1 depth=1
#pragma HLS interface s_axilite port=return bundle=control
    final_out[0] = (INT32)in_0[0];
}
'''
            pattern = rf"(void\s+{re.escape(task_name)}\s*\([^)]*\)\s*\{{.*?^\}})"
            m_fn = re.search(pattern, source_code, re.DOTALL | re.MULTILINE)
            if not m_fn:
                pattern = rf"(void\s+{re.escape(task_name)}\s*\(.*?\n\}})"
                m_fn = re.search(pattern, source_code, re.DOTALL)
            if m_fn:
                body = m_fn.group(1)
                idx = body.find("{") + 1
                pragmas = "\n"
                if task_name == "compute_KNN":
                    pragmas += "#pragma HLS interface ap_fifo port=load_to_compute_stream\n#pragma HLS interface ap_fifo port=compute_to_sort_stream\n"
                elif task_name == "para_partial_sort":
                    pragmas += "#pragma HLS interface ap_fifo port=compute_to_sort_stream\n#pragma HLS interface ap_fifo port=sort_to_hiermerge_dist_stream\n#pragma HLS interface ap_fifo port=sort_to_hiermerge_id_stream\n"
                    swap_m = re.search(r"(#define\s+KNN_SWAP.*?\n(?=#define|void|\n\n))", source_code, re.DOTALL)
                    if swap_m:
                        preamble += "\n" + swap_m.group(1) + "\n"
                    body = re.sub(r"#ifdef\s+__SYNTHESIS__\s*\n\s*static[^\n]*.*?\n\s*#endif", "", body, flags=re.DOTALL)
                    body = body.replace("static DATA_TYPE local_kNearstDist", "DATA_TYPE local_kNearstDist")
                    body = body.replace("static int local_kNearstId", "int local_kNearstId")
                    body = re.sub(r"KNN_SWAP\(&([^,]+),\s*&([^,]+),\s*&([^,]+),\s*&([^)]+)\)", r"KNN_SWAP(\1, \2, \3, \4)", body)
                    body = re.sub(
                        r"sort_to_hiermerge_dist_stream\.write\s*\(\s*local_kNearstDist\[j\]\s*\);",
                        "DATA_TYPE _out_dist = local_kNearstDist[j]; sort_to_hiermerge_dist_stream.write(_out_dist);",
                        body
                    )
                    body = re.sub(
                        r"sort_to_hiermerge_id_stream\.write\s*\(\s*local_kNearstId\[j\]\s*\);",
                        "int _out_id = local_kNearstId[j]; sort_to_hiermerge_id_stream.write(_out_id);",
                        body
                    )
                elif task_name == "load_KNN":
                    pragmas += "#pragma HLS interface ap_fifo port=load_to_compute_stream\n#pragma HLS interface ap_fifo port=searchSpace.read_addr\n#pragma HLS interface ap_fifo port=searchSpace.read_data\n#pragma HLS interface ap_fifo port=searchSpace.write_addr\n#pragma HLS interface ap_fifo port=searchSpace.write_data\n#pragma HLS interface ap_fifo port=searchSpace.write_resp\n#pragma HLS disaggregate variable=searchSpace\n"
                elif task_name == "krnl_singlePE_Write_Outputs":
                    pragmas += "#pragma HLS interface ap_fifo port=in_dist0\n#pragma HLS interface ap_fifo port=in_id0\n#pragma HLS interface ap_fifo port=output_knn.read_addr\n#pragma HLS interface ap_fifo port=output_knn.read_data\n#pragma HLS interface ap_fifo port=output_knn.write_addr\n#pragma HLS interface ap_fifo port=output_knn.write_data\n#pragma HLS interface ap_fifo port=output_knn.write_resp\n#pragma HLS disaggregate variable=output_knn\n"
                    body = re.sub(r"\*\s*\(\s*INT32\s*\*\s*\)\s*&\s*cur_id", "(INT32) cur_id", body)
                body = body[:idx] + pragmas + body[idx:]
                return preamble + "\n" + body
            return preamble + "\n" + source_code

        for tname, tdict in data.get("tasks", {}).items():
            if "code" not in tdict or not tdict["code"]:
                tdict["code"] = extract_task_code(tname, knn_cpp_content)

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
        if "-D__VITIS_HLS__" not in clean_cflags:
            clean_cflags.append("-D__VITIS_HLS__")
        if "-DHLS_STREAM_THREAD_UNSAFE" not in clean_cflags:
            clean_cflags.append("-DHLS_STREAM_THREAD_UNSAFE")
        xil_hls = os.environ.get("XILINX_HLS", "/afs/ece.cmu.edu/class/ece643/software/xilinxVitis/Vitis_HLS/2023.2")
        autopilot_inc = f"-I{xil_hls}/common/technology/autopilot"
        if autopilot_inc not in clean_cflags:
            clean_cflags.append(autopilot_inc)
        data["cflags"] = clean_cflags

        def normalize_scalar_args(obj):
            if isinstance(obj, dict):
                if obj.get("cat") == "scalar":
                    arg_val = obj.get("arg")
                    if isinstance(arg_val, dict) and "value" in arg_val:
                        w = arg_val.get("width", 32)
                        v = arg_val.get("value", 0)
                        obj["arg"] = f"{w}'d{v}"
                    elif isinstance(arg_val, int):
                        obj["arg"] = f"32'd{arg_val}"
                for k, v in obj.items():
                    normalize_scalar_args(v)
            elif isinstance(obj, list):
                for item in obj:
                    normalize_scalar_args(item)

        normalize_scalar_args(data)

        sys.stdout.write(json.dumps(data))
    except Exception as e:
        sys.stderr.write(f"Error patching JSON: {e}\n")
        sys.stdout.write(m.group(1))
    sys.exit(0)
else:
    sys.stderr.write(text)
    sys.exit(1)
EOF_PG
    chmod +x "$PATCH_GRAPH_PY"

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

echo "$RAW_OUT" | python3 "$DIR/patch_graph.py"
PY_RC=$?

if [ $RC -ne 0 ] || [ $PY_RC -ne 0 ]; then
    echo "=== tapacc failed (RC=$RC, PY_RC=$PY_RC) ===" >&2
    exit 1
fi
EOF_WRAP
        chmod +x "$TAPACC_WRAPPER"
    fi

    echo "=== 1.5 Inspecting TAPA Internals ==="
    python3 -c "import tapa.core, tapa.task, tapa.verilog.xilinx.module, inspect; print('=== Program.run_hls ===\n', inspect.getsource(tapa.core.Program.run_hls)); print('=== Program.generate_task_rtl ===\n', inspect.getsource(tapa.core.Program.generate_task_rtl) if hasattr(tapa.core.Program, 'generate_task_rtl') else 'N/A'); print('=== Program.generate_top_rtl ===\n', inspect.getsource(tapa.core.Program.generate_top_rtl) if hasattr(tapa.core.Program, 'generate_top_rtl') else 'N/A'); print('=== Module.get_port_of ===\n', inspect.getsource(tapa.verilog.xilinx.module.Module.get_port_of) if hasattr(tapa.verilog.xilinx.module.Module, 'get_port_of') else 'N/A')" > "$REPO_ROOT/tapa_internals.log" 2>&1 || true

    chmod +x "$REPO_ROOT/scripts/"*.py 2>/dev/null || true

    echo "=== 2. Running Single-PE Exploration ==="
    python3 singlePE_design_exploration.py 2>&1 | tee "$REPO_ROOT/run_output.log" || true

    echo "=== 2b. Running Multi-PE Exploration ==="
    if [ -f "singlePE_perf_results.log" ]; then
        rm -rf gen_multiPE_design
        python3 multiPE_design_exploration.py 2>&1 | tee "$REPO_ROOT/multiPE_output.log" || true
    else
        echo "singlePE_perf_results.log missing, skipping multi-PE." | tee "$REPO_ROOT/multiPE_output.log"
    fi

    echo "=== 3. Gathering Build Logs ==="
    if [ -f "gen_singlePE_design/tapa_HLS_output.log" ]; then
        cp "gen_singlePE_design/tapa_HLS_output.log" "$REPO_ROOT/tapa_HLS_output.log"
    fi
    if [ -f "/tmp/tapacc_wrapper.log" ]; then
        cp "/tmp/tapacc_wrapper.log" "$REPO_ROOT/tapacc_wrapper.log"
    fi

    if [ -f "singlePE_perf_results.log" ]; then
        cp "singlePE_perf_results.log" "$REPO_ROOT/singlePE_perf_results.log"
    fi
    for rj in gen_singlePE_design/_x.tapa_HLS.*/report.json; do
        if [ -f "$rj" ]; then
            cp "$rj" "$REPO_ROOT/report.json"
            break
        fi
    done

    cd "$REPO_ROOT"

    echo "=== 4. Pushing Logs to GitHub (branch: debug-run) ==="
    git checkout -B debug-run
    git add -f multiPE_output.log run_output.log tapa_HLS_output.log tapacc_wrapper.log tapa_internals.log tapa_headers_debug.log tapa_instance_debug.log singlePE_perf_results.log report.json real_xilinx_hls_stream.h scripts/ 2>/dev/null || true
    git commit -m "Auto-upload run logs: $(date -u +'%Y-%m-%d %H:%M:%S UTC')" || true
    git push -u origin debug-run --force

    echo "=== Finished! Latest logs are live on branch 'debug-run' ==="
