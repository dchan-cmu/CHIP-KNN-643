#!/usr/bin/env python3
"""
clean_graph_cflags.py:
1. Purges incompatible host compiler flags and adds synthesis definitions for Vitis HLS 2023.2.
2. Normalizes scalar arguments to standard Verilog constant literals.
3. Dynamically generates synthesizable C++ stubs for top-level Knn matching multi-PE ports.
4. Injects required FIFO/mmap pragmas and helper functions into task definitions.
"""
import sys, json, os, re

if len(sys.argv) < 2:
    print("Usage: clean_graph_cflags.py <path_to_graph.json>")
    sys.exit(1)

path = sys.argv[1]
with open(path, "r") as f:
    data = json.load(f)

# 1. Clean compiler flags
clean = []
for cf in data.get("cflags", []):
    if cf == "-U__SYNTHESIS__":
        continue
    if cf.startswith("-I/usr/include") or cf.startswith("-I/usr/bin") or "clang/20" in cf or "clang/22" in cf:
        continue
    if cf == "-std=c++17":
        cf = "-std=c++14"
    clean.append(cf)

for flag in [
    "-D__SYNTHESIS__",
    "-D__VITIS_HLS__",
    "-DHLS_STREAM_THREAD_UNSAFE",
    "-DTAPA_TARGET_DEVICE_",
    "-DTAPA_TARGET_XILINX_HLS_",
    "-D__thread=",
    "-Dthread_local=",
    "-std=c++14"
]:
    if flag not in clean:
        clean.append(flag)

xil_hls = os.environ.get("XILINX_HLS", "/afs/ece.cmu.edu/class/ece643/software/xilinxVitis/Vitis_HLS/2023.2")
autopilot_inc = f"-I{xil_hls}/common/technology/autopilot"
if autopilot_inc not in clean:
    clean.append(autopilot_inc)

data["cflags"] = clean

# 2. Normalize scalar arguments
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

# 3. Locate source file (knn.cpp)
graph_dir = os.path.dirname(os.path.abspath(path))
candidates = [
    os.path.join(graph_dir, "../src/knn.cpp"),
    os.path.join(graph_dir, "src/knn.cpp"),
    "src/knn.cpp",
    "knn.cpp",
    "../src/knn.cpp",
]
knn_cpp_content = ""
for c in candidates:
    if os.path.isfile(c):
        with open(c, "r", errors="ignore") as cf:
            knn_cpp_content = cf.read()
        break

write_out_code = ""
if knn_cpp_content:
    m_write = re.search(r"(void\s+write_out_mmap\s*\(.*?\n\})", knn_cpp_content, re.DOTALL)
    if m_write:
        write_out_code = m_write.group(1) + "\n\n"

swap_code = ""
if knn_cpp_content:
    swap_m = re.search(r"(#define\s+KNN_SWAP.*?\n(?=#define|void|\n\n))", knn_cpp_content, re.DOTALL)
    if swap_m:
        swap_code = swap_m.group(1) + "\n\n"

def build_knn_top_stub(source_code):
    preamble = (
        '#include "knn.h"\n'
        '#define printf(...) ((void)0)\n'
        '#define absval(input) ((input) > 0 ? static_cast<DATA_TYPE>(input) : static_cast<DATA_TYPE>(-1 * (input)))\n'
    )
    m_sig = re.search(r"void\s+Knn\s*\((.*?)\)\s*\{", source_code, re.DOTALL)
    if not m_sig:
        return preamble + '''
void Knn(tapa::mmap<INTERFACE_WIDTH> in_0, tapa::mmap<INT32> final_out) {
#pragma HLS interface m_axi port=in_0 offset=slave bundle=gmem0 depth=1
#pragma HLS interface m_axi port=final_out offset=slave bundle=gmem1 depth=1
#pragma HLS interface s_axilite port=return bundle=control
    final_out[0] = (INT32)in_0[0];
}
'''
    params_str = m_sig.group(1)
    params = re.findall(r"tapa::mmap<([^>]+)>\s*(\w+)", params_str)
    param_decls = []
    pragmas = []
    body_lines = ["    INT32 sum = 0;"]
    for idx, (dtype, pname) in enumerate(params):
        param_decls.append(f"    tapa::mmap<{dtype}> {pname}")
        pragmas.append(f"#pragma HLS interface m_axi port={pname} offset=slave bundle=gmem{idx} depth=1")
        if pname != "final_out":
            body_lines.append(f"    sum += (INT32){pname}[0];")
    body_lines.append("    final_out[0] = sum;")

    decl_str = ",\n".join(param_decls)
    pragma_str = "\n".join(pragmas)
    body_str = "\n".join(body_lines)
    return (
        f"{preamble}\nvoid Knn(\n{decl_str}\n) {{\n"
        f"{pragma_str}\n#pragma HLS interface s_axilite port=return bundle=control\n"
        f"{body_str}\n}}\n"
    )

def extract_and_patch_task(task_name, source_code):
    preamble = (
        '#include "knn.h"\n'
        '#define printf(...) ((void)0)\n'
        '#define absval(input) ((input) > 0 ? static_cast<DATA_TYPE>(input) : static_cast<DATA_TYPE>(-1 * (input)))\n'
    )
    if task_name == "Knn":
        return build_knn_top_stub(source_code)

    pattern = rf"(void\s+{re.escape(task_name)}\s*\([^)]*\)\s*\{{.*?^\}})"
    m_fn = re.search(pattern, source_code, re.DOTALL | re.MULTILINE)
    if not m_fn:
        pattern = rf"(void\s+{re.escape(task_name)}\s*\(.*?\n\}})"
        m_fn = re.search(pattern, source_code, re.DOTALL)
    if not m_fn:
        return ""

    body = m_fn.group(1)
    idx = body.find("{") + 1
    sig_part = body[:idx]

    stream_ports = re.findall(r"tapa::[io]stream<[^>]+>\s*&?\s*(\w+)", sig_part)
    pragmas = "\n"
    for sp in stream_ports:
        pragmas += f"#pragma HLS interface ap_fifo port={sp}\n"

    task_preamble = preamble
    if task_name == "compute_KNN":
        pass
    elif task_name == "para_partial_sort":
        if swap_code:
            task_preamble += "\n" + swap_code
        body = re.sub(r"#ifdef\s+__SYNTHESIS__\s*\n\s*static[^\n]*.*?\n\s*#endif", "", body, flags=re.DOTALL)
        body = body.replace("static DATA_TYPE local_kNearstDist", "DATA_TYPE local_kNearstDist")
        body = body.replace("static int local_kNearstId", "int local_kNearstId")
        body = re.sub(r"KNN_SWAP\(&([^,]+),\s*&([^,]+),\s*&([^,]+),\s*&([^)]+)\)", r"KNN_SWAP(\1, \2, \3, \4)", body)
        body = re.sub(r"(\w+)\.write\s*\(\s*local_kNearstDist\[j\]\s*\);", r"DATA_TYPE _out_dist = local_kNearstDist[j]; \1.write(_out_dist);", body)
        body = re.sub(r"(\w+)\.write\s*\(\s*local_kNearstId\[j\]\s*\);", r"int _out_id = local_kNearstId[j]; \1.write(_out_id);", body)
    elif task_name == "load_KNN":
        pragmas += (
            "#pragma HLS interface ap_fifo port=searchSpace.read_addr\n"
            "#pragma HLS interface ap_fifo port=searchSpace.read_data\n"
            "#pragma HLS interface ap_fifo port=searchSpace.write_addr\n"
            "#pragma HLS interface ap_fifo port=searchSpace.write_data\n"
            "#pragma HLS interface ap_fifo port=searchSpace.write_resp\n"
            "#pragma HLS disaggregate variable=searchSpace\n"
        )
    elif task_name == "krnl_singlePE_Write_Outputs":
        pragmas += (
            "#pragma HLS interface ap_fifo port=output_knn.read_addr\n"
            "#pragma HLS interface ap_fifo port=output_knn.read_data\n"
            "#pragma HLS interface ap_fifo port=output_knn.write_addr\n"
            "#pragma HLS interface ap_fifo port=output_knn.write_data\n"
            "#pragma HLS interface ap_fifo port=output_knn.write_resp\n"
            "#pragma HLS disaggregate variable=output_knn\n"
        )
        body = re.sub(r"\*\s*\(\s*INT32\s*\*\s*\)\s*&\s*cur_id", "(INT32) cur_id", body)
    elif task_name in ("merge_dual_streams_FINAL", "merge_trio_streams_FINAL"):
        pragmas += (
            "#pragma HLS interface ap_fifo port=hiermerge_output.read_addr\n"
            "#pragma HLS interface ap_fifo port=hiermerge_output.read_data\n"
            "#pragma HLS interface ap_fifo port=hiermerge_output.write_addr\n"
            "#pragma HLS interface ap_fifo port=hiermerge_output.write_data\n"
            "#pragma HLS interface ap_fifo port=hiermerge_output.write_resp\n"
            "#pragma HLS disaggregate variable=hiermerge_output\n"
        )
        body = re.sub(r"\*\s*\(\s*INT32\s*\*\s*\)\s*&\s*output_id", "(INT32) output_id", body)
        if write_out_code:
            task_preamble += "\n" + write_out_code

    body = body[:idx] + pragmas + body[idx:]
    return task_preamble + "\n" + body

if knn_cpp_content:
    for tname, tdict in data.get("tasks", {}).items():
        if tname == "Knn" or "code" not in tdict or not tdict["code"]:
            patched = extract_and_patch_task(tname, knn_cpp_content)
            if patched:
                tdict["code"] = patched
        elif tname in ("merge_dual_streams_FINAL", "merge_trio_streams_FINAL"):
            if "write_out_mmap" not in tdict.get("code", ""):
                patched = extract_and_patch_task(tname, knn_cpp_content)
                if patched:
                    tdict["code"] = patched

with open(path, "w") as f:
    json.dump(data, f, indent=2)

print(f"[clean_graph_cflags] Updated {path} with clean cflags, normalized scalar args, and patched tasks")
