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
