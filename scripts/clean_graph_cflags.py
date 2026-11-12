#!/usr/bin/env python3
import sys, json, os

if len(sys.argv) < 2:
    print("Usage: clean_graph_cflags.py <path_to_graph.json>")
    sys.exit(1)

path = sys.argv[1]
with open(path, "r") as f:
    data = json.load(f)

clean = []
for cf in data.get("cflags", []):
    if cf in ("-U__SYNTHESIS__", "-D__VITIS_HLS__"):
        continue
    if cf.startswith("-I/usr/include") or cf.startswith("-I/usr/bin") or "clang/20" in cf or "clang/22" in cf:
        continue
    if cf == "-std=c++17":
        cf = "-std=c++14"
    clean.append(cf)

if "-D__SYNTHESIS__" not in clean:
    clean.append("-D__SYNTHESIS__")
if "-DTAPA_TARGET_DEVICE_" not in clean:
    clean.append("-DTAPA_TARGET_DEVICE_")
if "-DTAPA_TARGET_XILINX_HLS_" not in clean:
    clean.append("-DTAPA_TARGET_XILINX_HLS_")
if "-D__thread=" not in clean:
    clean.append("-D__thread=")
if "-Dthread_local=" not in clean:
    clean.append("-Dthread_local=")
if "-std=c++14" not in clean:
    clean.append("-std=c++14")

xil_hls = os.environ.get("XILINX_HLS", "/afs/ece.cmu.edu/class/ece643/software/xilinxVitis/Vitis_HLS/2023.2")
autopilot_inc = f"-I{xil_hls}/common/technology/autopilot"
if autopilot_inc not in clean:
    clean.append(autopilot_inc)

data["cflags"] = clean

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

with open(path, "w") as f:
    json.dump(data, f, indent=2)

print(f"[clean_graph_cflags] Updated {path} with clean cflags and normalized scalar args")

