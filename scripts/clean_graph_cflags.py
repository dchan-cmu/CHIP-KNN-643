#!/usr/bin/env python3
import sys, json

if len(sys.argv) < 2:
    print("Usage: clean_graph_cflags.py <path_to_graph.json>")
    sys.exit(1)

path = sys.argv[1]
with open(path, "r") as f:
    data = json.load(f)

clean = []
for cf in data.get("cflags", []):
    if cf == "-U__SYNTHESIS__":
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
if "-std=c++14" not in clean:
    clean.append("-std=c++14")

data["cflags"] = clean

with open(path, "w") as f:
    json.dump(data, f, indent=2)

print(f"[clean_graph_cflags] Updated {path} with clean cflags: {clean}")
