#!/usr/bin/env python3
"""
sweep_design_space.py: Design Space Exploration Framework for CHIP-KNN on Ultra96.
Sweeps throughput across:
  - Feature dimensions (low=2, medium=16, high=64)
  - Processing elements (PEs: 1, 2, 3, 4)

Produces per-point directories containing:
  - build.log: Build and synthesis log
  - knn.xo / knn.xclbin: Resulting FPGA kernel and image
  - report.json: HLS resource and timing report
  - golden/: Ground truth query, search space, expected top-K results, and verify_results.py
  - run_on_ultra96.sh: Shell script to run kernel on physical Ultra96 board
  - metrics.json: Latency, resource utilization, and feature throughput
"""

import os
import sys
import shutil
import json
import csv
import time
import math
import subprocess
import argparse
import re

# Add scripts directory to path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

# Auto-add local TAPA binary directory to PATH
TAPA_BIN_DIR = os.path.join(REPO_ROOT, ".tapa", "usr", "bin")
if os.path.isdir(TAPA_BIN_DIR):
    cur_p = os.environ.get("PATH", "")
    if TAPA_BIN_DIR not in cur_p:
        os.environ["PATH"] = f"{TAPA_BIN_DIR}:{cur_p}"

# Auto-detect CMU ECE AFS Vitis toolchain if not in PATH
VITIS_HLS_AFS = "/afs/ece.cmu.edu/class/ece643/software/xilinxVitis/Vitis_HLS/2023.2/bin"
VITIS_AFS = "/afs/ece.cmu.edu/class/ece643/software/xilinxVitis/Vitis/2023.2/bin"
if os.path.isdir(VITIS_HLS_AFS):
    cur_p = os.environ.get("PATH", "")
    if VITIS_HLS_AFS not in cur_p:
        os.environ["PATH"] = f"{VITIS_HLS_AFS}:{VITIS_AFS}:{cur_p}"
    if "XILINX_HLS" not in os.environ:
        os.environ["XILINX_HLS"] = "/afs/ece.cmu.edu/class/ece643/software/xilinxVitis/Vitis_HLS/2023.2"
    if "XILINX_VITIS" not in os.environ:
        os.environ["XILINX_VITIS"] = "/afs/ece.cmu.edu/class/ece643/software/xilinxVitis/Vitis/2023.2"

from config import (
    SLR_resource, SLR_resource_ZU3EG, FPGA_target_name, FPGA_part_name,
    memory_type, max_port_width, data_type_to_use, data_type_int_bits,
    data_type_fract_bits, kernel_frequency
)
import knn_code_generation as knngen
from multiPE_design_generate import Generate_MultiPE_Design
import supporting_code_generation as suppcodegen
import golden_model

# Ultra96 Total FPGA Resources for percentage calculations
ULTRA96_TOTAL_RESOURCES = SLR_resource_ZU3EG[0]

# Ultra96 Vitis Platform Repository Path on CMU ECE AFS
U96_PLATFORM_REPO = "/afs/ece.cmu.edu/class/ece643/software/xilinxVitis/platforms/2023.2/u96v2_sbc_base_2023_2/export"
if os.path.isdir(U96_PLATFORM_REPO):
    existing_repo = os.environ.get("PLATFORM_REPO_PATHS", "")
    if U96_PLATFORM_REPO not in existing_repo:
        os.environ["PLATFORM_REPO_PATHS"] = f"{U96_PLATFORM_REPO}:{existing_repo}" if existing_repo else U96_PLATFORM_REPO

def parse_args():
    parser = argparse.ArgumentParser(
        description="CHIP-KNN Design Space Sweep for Ultra96 (Dimension x Processing Elements)"
    )
    parser.add_argument(
        "--dims", type=int, nargs="+", default=[2, 16, 64],
        help="Feature dimensions to sweep (default: 2 16 64)"
    )
    parser.add_argument(
        "--pes", type=int, nargs="+", default=[1, 2, 3, 4],
        help="PE counts to sweep (default: 1 2 3 4)"
    )
    parser.add_argument(
        "--n-points", type=int, default=131072,
        help="Search space points count (default: 131072)"
    )
    parser.add_argument(
        "--k", type=int, default=10,
        help="Top-K nearest neighbors (default: 10)"
    )
    parser.add_argument(
        "--dist", type=int, default=0, choices=[0, 1],
        help="Distance metric (0: Manhattan, 1: Euclidean, default: 0)"
    )
    parser.add_argument(
        "--output-dir", type=str, default=os.path.join(REPO_ROOT, "sweeps"),
        help="Base directory for sweep outputs (default: <repo>/sweeps)"
    )
    parser.add_argument(
        "--mode", type=str, choices=["generate-only", "build", "all"], default="all",
        help="Sweep execution mode: 'generate-only' (scaffold + golden ref), 'build' (compile existing), 'all' (default)"
    )
    parser.add_argument(
        "--build-bitstream", action="store_true",
        help="Also compile full Vivado bitstream (.xclbin) via v++ linker"
    )
    parser.add_argument(
        "--jobs", type=int, default=12,
        help="Parallel HLS synthesis workers (default: 12)"
    )
    parser.add_argument(
        "--frequency", type=int, default=kernel_frequency,
        help=f"Target kernel frequency in MHz (default: {kernel_frequency})"
    )
    parser.add_argument(
        "--clean", action="store_true",
        help="Clean existing sweep output directory before starting"
    )
    parser.add_argument(
        "--auto-push", action="store_true",
        help="Commit and push sweep results to GitHub after each configuration finishes"
    )
    # Adaptive PE Search Arguments
    parser.add_argument(
        "--adaptive-pe", action="store_true",
        help="Adaptively increment PE count per dimension until build/bitstream failure or resource exhaustion"
    )
    parser.add_argument(
        "--start-pe", type=int, default=1,
        help="Starting PE count for adaptive sweep (default: 1)"
    )
    parser.add_argument(
        "--max-pe", type=int, default=16,
        help="Maximum PE count ceiling for adaptive sweep (default: 16)"
    )
    parser.add_argument(
        "--pe-step", type=int, default=1,
        help="PE increment step for adaptive sweep (default: 1)"
    )
    parser.add_argument(
        "--max-failures", type=int, default=1,
        help="Consecutive build failures per dimension before stopping (default: 1)"
    )
    # Simulation Arguments
    parser.add_argument(
        "--run-simulation", action="store_true",
        help="Execute simulation verification and benchmark runtime"
    )
    parser.add_argument(
        "--sim-mode", type=str, choices=["sw_emu", "hw_emu"], default="sw_emu",
        help="Simulation target: 'sw_emu' (TAPA C-sim) or 'hw_emu' (Vivado cycle-accurate RTL sim)"
    )
    return parser.parse_args()

def calculate_analytical_performance(dim, num_pe, n_points, k, clock_period_ns):
    """
    Compute analytical pipeline latency, execution time, and throughput.
    Throughput = (# points * dimension) / execution_time (features / sec).
    """
    pts_per_pe = math.ceil(n_points / num_pe)
    packing_factor = max_port_width // (data_type_int_bits + data_type_fract_bits)
    cycles_per_vector = math.ceil(dim / packing_factor)
    
    # II=1 pipelined compute latency per PE
    compute_cycles = pts_per_pe * cycles_per_vector
    
    # Parallel partial sort insertion pipeline
    sort_cycles = pts_per_pe + k
    
    # Hierarchical merge reduction tree latency
    if num_pe > 1:
        merge_levels = math.ceil(math.log2(num_pe))
        merge_cycles = merge_levels * k * 2
    else:
        merge_cycles = k
        
    total_pipeline_cycles = max(compute_cycles, sort_cycles) + merge_cycles + 50
    runtime_sec = total_pipeline_cycles * (clock_period_ns * 1e-9)
    throughput_features_sec = (n_points * dim) / runtime_sec if runtime_sec > 0 else 0.0
    throughput_queries_sec = n_points / runtime_sec if runtime_sec > 0 else 0.0
    
    return {
        "cycles_per_vector": cycles_per_vector,
        "pts_per_pe": pts_per_pe,
        "estimated_cycles": total_pipeline_cycles,
        "estimated_clock_period_ns": clock_period_ns,
        "estimated_runtime_sec": runtime_sec,
        "throughput_features_sec": throughput_features_sec,
        "throughput_queries_sec": throughput_queries_sec
    }

def setup_sweep_point(point_dir, dim, num_pe, args):
    """
    Generate complete source code, makefiles, and golden dataset for one sweep point.
    """
    os.makedirs(point_dir, exist_ok=True)
    src_dir = os.path.join(point_dir, "src")
    golden_dir = os.path.join(point_dir, "golden")
    os.makedirs(src_dir, exist_ok=True)
    os.makedirs(golden_dir, exist_ok=True)
    
    # 1. Symlink required common framework files
    common_src = os.path.relpath(os.path.join(REPO_ROOT, "common"), point_dir)
    utils_mk_src = os.path.relpath(os.path.join(REPO_ROOT, "utils.mk"), point_dir)
    
    common_dst = os.path.join(point_dir, "common")
    utils_mk_dst = os.path.join(point_dir, "utils.mk")
    
    if not os.path.exists(common_dst) and not os.path.islink(common_dst):
        os.symlink(common_src, common_dst)
    if not os.path.exists(utils_mk_dst) and not os.path.islink(utils_mk_dst):
        os.symlink(utils_mk_src, utils_mk_dst)
        
    # 2. Generate C++ kernel and host code inside src/
    curr_dir = os.getcwd()
    os.chdir(src_dir)
    try:
        knn_config = Generate_MultiPE_Design(
            args.n_points, dim, args.dist, args.k, max_port_width, memory_type, num_pe
        )
        suppcodegen.Generate_Host_Code(num_pe, knn_config)
        suppcodegen.Generate_Connectivity_Map(memory_type, num_pe, max_port_width)
    finally:
        os.chdir(curr_dir)
        
    # 3. Generate Makefile inside point_dir
    os.chdir(point_dir)
    try:
        suppcodegen.Generate_MakeFile(args.frequency, _fpga_part_name=FPGA_part_name)
    finally:
        os.chdir(curr_dir)
        
    # 4. Generate golden simulation data
    dataset = golden_model.generate_golden_dataset(
        n_points=args.n_points,
        dim=dim,
        k=args.k,
        dist_metric=args.dist,
        num_pes=num_pe,
        seed=42 + dim * 10 + num_pe
    )
    golden_model.export_golden_files(dataset, golden_dir)
    
    # Also write top-level expected results directly in sweep directory for convenience
    with open(os.path.join(point_dir, "expected_topk.json"), "w") as f:
        json.dump(dataset["topk"], f, indent=2)
        
    # 5. Create Ultra96 execution script
    u96_script_path = os.path.join(point_dir, "run_on_ultra96.sh")
    with open(u96_script_path, "w") as f:
        f.write(f"""#!/bin/bash
# Ultra96 Kernel Runner for Configuration: D={dim}, PE={num_pe}
set -e

DIR="$(cd "$(dirname "${{BASH_SOURCE[0]}}")" && pwd)"
cd "$DIR"

BITSTREAM="${{1:-build_dir.hw.{FPGA_target_name}/knn.xclbin}}"
if [ ! -f "$BITSTREAM" ]; then
    echo "Notice: Bitstream $BITSTREAM not found."
    echo "Usage: ./run_on_ultra96.sh [path_to_xclbin]"
    exit 1
fi

echo "=== Running CHIP-KNN on Ultra96 (D={dim}, PE={num_pe}) ==="
./knn "$BITSTREAM" 2>&1 | tee ultra96_run.log

echo "=== Verifying Hardware Output Against Golden Reference ==="
python3 golden/verify_results.py hw_output.txt
""")
    os.chmod(u96_script_path, 0o755)

def parse_implementation_reports(point_dir, FPGA_target_name):
    """
    Search for Vivado routed implementation reports (utilization and timing)
    in build_dir.hw.<platform>/reports/link/ and point_dir/reports/.
    Copy reports to point_dir/reports/ for git tracking and return parsed metrics.
    """
    reports_dst = os.path.join(point_dir, "reports")
    os.makedirs(reports_dst, exist_ok=True)

    src_link_reports = os.path.join(point_dir, f"build_dir.hw.{FPGA_target_name}", "reports", "link")
    if os.path.isdir(src_link_reports):
        for root, dirs, files in os.walk(src_link_reports):
            for file in files:
                if file.endswith((".rpt", ".xtxt", ".html", ".log")):
                    full_p = os.path.join(root, file)
                    try:
                        shutil.copy2(full_p, reports_dst)
                    except Exception:
                        pass

    impl_resources = None
    impl_timing = None

    util_file = None
    timing_file = None
    for root, dirs, files in os.walk(reports_dst):
        for f in files:
            if "util_routed" in f or "utilization_routed" in f:
                util_file = os.path.join(root, f)
            elif "timing_summary_routed" in f:
                timing_file = os.path.join(root, f)

    if util_file and os.path.isfile(util_file):
        try:
            with open(util_file, "r", errors="ignore") as f:
                content = f.read()
            m_lut = re.search(r"\|\s*(?:CLB|Slice)\s*LUTs\s*\|\s*(\d+)", content)
            m_ff = re.search(r"\|\s*(?:CLB|Slice)\s*Registers\s*\|\s*(\d+)", content)
            m_bram = re.search(r"\|\s*Block RAM Tile\s*\|\s*([\d\.]+)", content)
            m_dsp = re.search(r"\|\s*DSPs\s*\|\s*(\d+)", content)
            m_uram = re.search(r"\|\s*URAM\s*\|\s*(\d+)", content)
            impl_resources = {
                "LUT": int(m_lut.group(1)) if m_lut else None,
                "FF": int(m_ff.group(1)) if m_ff else None,
                "BRAM": float(m_bram.group(1)) if m_bram else None,
                "DSP": int(m_dsp.group(1)) if m_dsp else None,
                "URAM": int(m_uram.group(1)) if m_uram else 0
            }
        except Exception as e:
            print(f"[reports] Error parsing utilization: {e}")

    # Fallback to system_estimate_knn.xtxt
    if not impl_resources:
        sys_est = os.path.join(reports_dst, "system_estimate_knn.xtxt")
        if os.path.isfile(sys_est):
            try:
                with open(sys_est, "r", errors="ignore") as f:
                    for line in f:
                        if "Knn_1" in line:
                            parts = line.split()
                            if len(parts) >= 7:
                                impl_resources = {
                                    "BRAM": int(parts[2]),
                                    "DSP": int(parts[3]),
                                    "FF": int(parts[4]),
                                    "LUT": int(parts[5]),
                                    "URAM": int(parts[6])
                                }
            except Exception:
                pass

    if timing_file and os.path.isfile(timing_file):
        try:
            with open(timing_file, "r", errors="ignore") as f:
                content = f.read()
            m_timing_table = re.search(r"WNS\(ns\)\s+TNS\(ns\)[^\n]*\n[^\n]*\n\s*([-\d\.]+)\s+([-\d\.]+)", content)
            m_wns = re.search(r"Worst Negative Slack \(WNS\):\s*([-\d\.]+)", content)
            if m_timing_table:
                wns = float(m_timing_table.group(1))
                tns = float(m_timing_table.group(2))
            elif m_wns:
                wns = float(m_wns.group(1))
                m_tns = re.search(r"Total Negative Slack \(TNS\):\s*([-\d\.]+)", content)
                tns = float(m_tns.group(1)) if m_tns else 0.0
            else:
                wns = None

            if wns is not None:
                target_clk = 5.0
                achieved_period = target_clk - min(0.0, wns)
                fmax = 1000.0 / (target_clk - wns) if (target_clk - wns) > 0 else 0.0
                impl_timing = {
                    "wns_ns": wns,
                    "tns_ns": tns,
                    "target_clock_ns": target_clk,
                    "achieved_clock_ns": round(achieved_period, 3),
                    "fmax_mhz": round(fmax, 1)
                }
        except Exception as e:
            print(f"[reports] Error parsing timing: {e}")

    return impl_resources, impl_timing

def run_simulation(point_dir, dim, num_pe, sim_mode, args, env):
    """
    Run software emulation (sw_emu) or hardware emulation (hw_emu) for one design point.
    """
    sim_log_path = os.path.join(point_dir, "sim.log")
    curr_dir = os.getcwd()
    os.chdir(point_dir)
    sim_result = {
        "mode": sim_mode,
        "status": "NOT_RUN",
        "passed": False,
        "kernel_time_sec": None,
        "total_time_sec": None,
        "throughput_mfeat_sec": None
    }
    try:
        if sim_mode == "sw_emu":
            print(f"[{dim}D-{num_pe}PE] Compiling host executable for software emulation...", flush=True)
            cmd_build = ["make", "exe"]
            proc_b = subprocess.run(cmd_build, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=env)
            with open(sim_log_path, "w") as sf:
                sf.write("=== COMPILING HOST FOR SIMULATION ===\n")
                sf.write(proc_b.stdout)

            exe_path = os.path.join(point_dir, "knn")
            if not os.path.isfile(exe_path):
                print(f"[{dim}D-{num_pe}PE] Notice: Host compilation failed; skipping simulation.")
                sim_result["status"] = "BUILD_FAILED"
                return sim_result

            print(f"[{dim}D-{num_pe}PE] Executing software simulation (./knn)...", flush=True)
            cmd_run = ["./knn"]
            proc_r = subprocess.run(cmd_run, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=300, env=env)
            with open(sim_log_path, "a") as sf:
                sf.write("\n=== SIMULATION EXECUTION OUTPUT ===\n")
                sf.write(proc_r.stdout)

            output = proc_r.stdout
            passed = "PASSED" in output
            sim_result["passed"] = passed
            sim_result["status"] = "PASSED" if passed else "FAILED"

            m_ktime = re.search(r"KERNEL time:\s*([\d\.]+(?:e[+-]?\d+)?)\s*s", output)
            if m_ktime:
                ktime = float(m_ktime.group(1))
                sim_result["kernel_time_sec"] = ktime
                if ktime > 0:
                    sim_result["throughput_mfeat_sec"] = (args.n_points * dim) / (ktime * 1e6)

            m_ttime = re.search(r"Total elapsed time:\s*([\d\.]+(?:e[+-]?\d+)?)\s*s", output)
            if m_ttime:
                sim_result["total_time_sec"] = float(m_ttime.group(1))

            print(f"[{dim}D-{num_pe}PE] Simulation status: {sim_result['status']} | Kernel time: {sim_result.get('kernel_time_sec', 'N/A')} s")

        elif sim_mode == "hw_emu":
            print(f"[{dim}D-{num_pe}PE] Executing hardware emulation (make check TARGET=hw_emu)...", flush=True)
            cmd_hw = ["make", "check", "TARGET=hw_emu", f"DEVICE={FPGA_target_name}"]
            proc_h = subprocess.run(cmd_hw, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=1800, env=env)
            with open(sim_log_path, "w") as sf:
                sf.write(proc_h.stdout)
            passed = "PASSED" in proc_h.stdout
            sim_result["passed"] = passed
            sim_result["status"] = "PASSED" if passed else "FAILED"
            print(f"[{dim}D-{num_pe}PE] Hardware emulation status: {sim_result['status']}")

    except subprocess.TimeoutExpired:
        print(f"[{dim}D-{num_pe}PE] Notice: Simulation execution timed out.")
        sim_result["status"] = "TIMEOUT"
    except Exception as e:
        print(f"[{dim}D-{num_pe}PE] Notice: Error during simulation: {e}")
        sim_result["status"] = f"ERROR"
    finally:
        os.chdir(curr_dir)

    return sim_result

def load_hls_report(point_dir, report_path=None):
    resources = None
    target_rep = os.path.join(point_dir, "report.json")
    rep = report_path if (report_path and os.path.isfile(report_path)) else target_rep
    if os.path.isfile(rep):
        try:
            with open(rep, "r") as rf:
                rdata = json.load(rf)
            area_tot = rdata.get("area", {}).get("total", {})
            resources = {
                "BRAM": area_tot.get("BRAM_18K", 0),
                "DSP": area_tot.get("DSP", 0),
                "FF": area_tot.get("FF", 0),
                "LUT": area_tot.get("LUT", 0),
                "URAM": area_tot.get("URAM", 0),
                "clock_period_ns": float(rdata.get("performance", {}).get("clock_period", 5.0))
            }
        except Exception as e:
            print(f"[reports] Error reading report.json: {e}")
    return resources

def build_sweep_point(point_dir, dim, num_pe, args):
    """
    Run HLS synthesis and TAPA XO packaging for one design point.
    """
    build_log_path = os.path.join(point_dir, "build.log")
    curr_dir = os.getcwd()
    os.chdir(point_dir)
    
    build_status = "PENDING"
    start_time = time.time()

    # Check for existing generated artifacts
    temp_dir_pattern = f"_x.tapa_HLS.{FPGA_target_name}"
    xo_path = os.path.join(point_dir, temp_dir_pattern, "knn.xo")
    point_xo = os.path.join(point_dir, "knn.xo")
    report_path = os.path.join(point_dir, temp_dir_pattern, "report.json")
    has_xo = os.path.isfile(xo_path) or os.path.isfile(point_xo)

    build_dir = os.path.join(point_dir, f"build_dir.hw.{FPGA_target_name}")
    xclbin_target = os.path.join(point_dir, "knn.xclbin")
    build_xclbin = os.path.join(build_dir, "knn.xclbin")
    has_xclbin = os.path.isfile(xclbin_target) or os.path.isfile(build_xclbin)

    # If the target requested is already fully built, reuse it and parse metrics
    if args.build_bitstream and has_xclbin:
        print(f"[{dim}D-{num_pe}PE] Found existing bitstream (knn.xclbin). Skipping rebuild.", flush=True)
        build_status = "BITSTREAM_SUCCESS"
        if os.path.isfile(build_xclbin) and not os.path.isfile(xclbin_target):
            shutil.copy2(build_xclbin, xclbin_target)
        impl_resources, impl_timing = parse_implementation_reports(point_dir, FPGA_target_name)
        resources = load_hls_report(point_dir, report_path)
        os.chdir(curr_dir)
        return {
            "status": build_status,
            "build_time_sec": 0.0,
            "has_xo": True,
            "has_xclbin": True,
            "resources": resources,
            "impl_resources": impl_resources,
            "impl_timing": impl_timing,
            "report_path": report_path if os.path.isfile(report_path) else None
        }
    elif not args.build_bitstream and has_xo:
        print(f"[{dim}D-{num_pe}PE] Found existing XO (knn.xo). Skipping HLS rebuild.", flush=True)
        build_status = "XO_SUCCESS"
        resources = load_hls_report(point_dir, report_path)
        os.chdir(curr_dir)
        return {
            "status": build_status,
            "build_time_sec": 0.0,
            "has_xo": True,
            "has_xclbin": has_xclbin,
            "resources": resources,
            "impl_resources": None,
            "impl_timing": None,
            "report_path": report_path if os.path.isfile(report_path) else None
        }

    # Verify toolchain availability
    has_tapac = shutil.which("tapac") is not None or os.path.isfile(os.path.join(TAPA_BIN_DIR, "tapac"))
    has_vitis = (
        shutil.which("vitis_hls") is not None
        or shutil.which("v++") is not None
        or "XILINX_HLS" in os.environ
        or "XILINX_VITIS" in os.environ
    )
    
    if not (has_tapac and has_vitis):
        with open(build_log_path, "w") as lf:
            lf.write("[sweep_design_space] Notice: TAPA or Vitis HLS toolchain not detected in PATH.\n")
            lf.write(f"[sweep_design_space] Generated synthesizable sources, Makefiles, and golden data for D={dim}, PE={num_pe}.\n")
            lf.write("[sweep_design_space] Run 'make tapa_HLS' on the Vitis build machine to execute hardware build.\n")
        build_status = "SCAFFOLDED"
        os.chdir(curr_dir)
        return {
            "status": build_status,
            "build_time_sec": 0.0,
            "has_xo": False,
            "has_xclbin": False,
            "resources": None,
            "report_path": None
        }
        
    print(f"[{dim}D-{num_pe}PE] Starting HLS synthesis and XO packaging (log: {build_log_path})...", flush=True)
    
    env = os.environ.copy()
    env["PATH"] = f"{os.path.join(REPO_ROOT, '.tapa/usr/bin')}:{env.get('PATH', '')}"
    env["REPO_ROOT"] = REPO_ROOT
    if os.path.isdir(U96_PLATFORM_REPO):
        cur_repo = env.get("PLATFORM_REPO_PATHS", "")
        if U96_PLATFORM_REPO not in cur_repo:
            env["PLATFORM_REPO_PATHS"] = f"{U96_PLATFORM_REPO}:{cur_repo}" if cur_repo else U96_PLATFORM_REPO
    
    cmd = [
        "make", "tapa_HLS",
        f"TARGET=tapa_HLS",
        f"DEVICE={FPGA_target_name}"
    ]
    
    with open(build_log_path, "w") as log_file:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            env=env
        )
        for line in proc.stdout:
            log_file.write(line)
            log_file.flush()
        proc.wait()
        
    build_time = time.time() - start_time
    
    # Check for generated .xo
    temp_dir_pattern = f"_x.tapa_HLS.{FPGA_target_name}"
    xo_path = os.path.join(point_dir, temp_dir_pattern, "knn.xo")
    report_path = os.path.join(point_dir, temp_dir_pattern, "report.json")
    
    has_xo = os.path.isfile(xo_path) or os.path.isfile(os.path.join(point_dir, "knn.xo"))
    if has_xo:
        build_status = "XO_SUCCESS"
        if os.path.isfile(xo_path) and not os.path.isfile(os.path.join(point_dir, "knn.xo")):
            shutil.copy2(xo_path, os.path.join(point_dir, "knn.xo"))
    else:
        build_status = "HLS_FAILED" if proc.returncode != 0 else "XO_MISSING"
        
    # Check for bitstream generation if requested
    has_xclbin = False
    impl_resources = None
    impl_timing = None
    if has_xo and args.build_bitstream:
        print(f"[{dim}D-{num_pe}PE] Launching Vivado bitstream generation (.xclbin)...", flush=True)
        build_dir = os.path.join(point_dir, f"build_dir.hw.{FPGA_target_name}")
        xclbin_target = os.path.join(build_dir, "knn.xclbin")
        if not os.path.isfile(xclbin_target) and os.path.isdir(build_dir):
            print(f"[{dim}D-{num_pe}PE] Cleaning incomplete build directory before linking...", flush=True)
            shutil.rmtree(build_dir, ignore_errors=True)
        cmd_link = ["make", "build", f"DEVICE={FPGA_target_name}"]
        
        # Sanitize any XO and Verilog files in point_dir before bitstream link
        sanitize_script = os.path.join(SCRIPT_DIR, "sanitize_top_rtl.py")
        if os.path.isfile(sanitize_script):
            subprocess.run([sys.executable, sanitize_script, point_dir], check=False)

        with open(build_log_path, "a") as log_file:
            log_file.write("\n=== STARTING BITSTREAM LINKING ===\n")
            proc_link = subprocess.run(cmd_link, stdout=log_file, stderr=subprocess.STDOUT, text=True, env=env)
            
        if os.path.isfile(xclbin_target):
            has_xclbin = True
            build_status = "BITSTREAM_SUCCESS"
            shutil.copy2(xclbin_target, os.path.join(point_dir, "knn.xclbin"))
            impl_resources, impl_timing = parse_implementation_reports(point_dir, FPGA_target_name)
            
    # Parse utilization report if present
    resources = None
    if os.path.isfile(report_path):
        shutil.copy2(report_path, os.path.join(point_dir, "report.json"))
        try:
            with open(report_path, "r") as rf:
                rdata = json.load(rf)
            area_tot = rdata.get("area", {}).get("total", {})
            resources = {
                "BRAM": area_tot.get("BRAM_18K", 0),
                "DSP": area_tot.get("DSP", 0),
                "FF": area_tot.get("FF", 0),
                "LUT": area_tot.get("LUT", 0),
                "URAM": area_tot.get("URAM", 0),
                "clock_period_ns": float(rdata.get("performance", {}).get("clock_period", 5.0))
            }
        except Exception as e:
            print(f"[{dim}D-{num_pe}PE] Notice: Error reading report.json: {e}")
            
    os.chdir(curr_dir)
    return {
        "status": build_status,
        "build_time_sec": build_time,
        "has_xo": has_xo,
        "has_xclbin": has_xclbin,
        "resources": resources,
        "impl_resources": impl_resources,
        "impl_timing": impl_timing,
        "report_path": report_path if os.path.isfile(report_path) else None
    }

def process_point(dim, num_pe, point_idx, label, args, clock_period_ns):
    config_name = f"sweep_D{dim}_PE{num_pe}"
    point_dir = os.path.join(args.output_dir, config_name)
    
    print(f"\n[{label}] Configuring: D={dim}, PE={num_pe} -> {config_name}")
    
    # 1. Scaffold and generate golden dataset
    if args.mode in ("generate-only", "all") or not os.path.exists(point_dir):
        setup_sweep_point(point_dir, dim, num_pe, args)
        
    # 2. Run build if requested
    build_info = {
        "status": "SCAFFOLDED",
        "build_time_sec": 0.0,
        "has_xo": False,
        "has_xclbin": False,
        "resources": None,
        "impl_resources": None,
        "impl_timing": None
    }
    if args.mode in ("build", "all"):
        build_info = build_sweep_point(point_dir, dim, num_pe, args)
        
    # Check if implementation reports can be parsed from disk if not already parsed
    impl_resources = build_info.get("impl_resources")
    impl_timing = build_info.get("impl_timing")
    if (os.path.isfile(os.path.join(point_dir, "knn.xclbin")) or build_info.get("has_xclbin", False)) and (not impl_resources or not impl_timing):
        ir, it = parse_implementation_reports(point_dir, FPGA_target_name)
        if ir:
            impl_resources = ir
            build_info["impl_resources"] = ir
        if it:
            impl_timing = it
            build_info["impl_timing"] = it

    # 3. Run simulation if requested
    sim_info = None
    if args.run_simulation:
        env = os.environ.copy()
        env["PATH"] = f"{os.path.join(REPO_ROOT, '.tapa/usr/bin')}:{env.get('PATH', '')}"
        env["REPO_ROOT"] = REPO_ROOT
        sim_info = run_simulation(point_dir, dim, num_pe, args.sim_mode, args, env)
        
    # 4. Compute analytical and empirical performance
    effective_clk = clock_period_ns
    if build_info["resources"] and "clock_period_ns" in build_info["resources"]:
        effective_clk = build_info["resources"]["clock_period_ns"]
        
    perf = calculate_analytical_performance(dim, num_pe, args.n_points, args.k, effective_clk)
    
    # Combine metrics
    metrics = {
        "config_name": config_name,
        "dimension": dim,
        "num_pe": num_pe,
        "n_points": args.n_points,
        "k": args.k,
        "clock_frequency_mhz": args.frequency,
        "clock_period_ns": effective_clk,
        "status": build_info["status"],
        "has_xo": build_info["has_xo"],
        "has_xclbin": build_info["has_xclbin"],
        "build_time_sec": round(build_info["build_time_sec"], 2),
        "performance": perf,
        "resources": build_info["resources"],
        "impl_resources": impl_resources,
        "impl_timing": impl_timing,
        "simulation": sim_info
    }
    
    # Save metrics.json in point directory
    with open(os.path.join(point_dir, "metrics.json"), "w") as mf:
        json.dump(metrics, mf, indent=2)
        
    return metrics, build_info

def run_sweep(args):
    """
    Main execution loop across all (dimension, processing elements) configurations.
    Supports either fixed PE list or adaptive PE scaling until failure.
    """
    os.makedirs(args.output_dir, exist_ok=True)
    
    clock_period_ns = 1000.0 / args.frequency
    sweep_results = []
    
    if args.clean:
        if args.adaptive_pe:
            for dim in args.dims:
                for pe in range(args.start_pe, args.max_pe + 1, args.pe_step):
                    target_point = os.path.join(args.output_dir, f"sweep_D{dim}_PE{pe}")
                    if os.path.exists(target_point):
                        print(f"Cleaning configuration directory: {target_point}")
                        shutil.rmtree(target_point)
        else:
            for dim in args.dims:
                for num_pe in args.pes:
                    target_point = os.path.join(args.output_dir, f"sweep_D{dim}_PE{num_pe}")
                    if os.path.exists(target_point):
                        print(f"Cleaning configuration directory: {target_point}")
                        shutil.rmtree(target_point)

    print("=" * 82)
    print("CHIP-KNN ULTRA96 DESIGN SPACE SWEEP")
    print(f"Dimensions: {args.dims}")
    if args.adaptive_pe:
        print(f"Mode: ADAPTIVE PE SCALING (Start PE: {args.start_pe}, Max PE: {args.max_pe}, Step: {args.pe_step})")
    else:
        print(f"Mode: FIXED PE SWEEP (PEs: {args.pes})")
    print(f"Points (N): {args.n_points} | K: {args.k} | Clock: {args.frequency} MHz ({clock_period_ns:.2f} ns)")
    print(f"Simulation: {'Enabled (' + args.sim_mode + ')' if args.run_simulation else 'Disabled'}")
    print(f"Build Bitstream: {args.build_bitstream}")
    print(f"Output Directory: {args.output_dir}")
    print("=" * 82)

    point_idx = 0
    if args.adaptive_pe:
        for dim in args.dims:
            current_pe = args.start_pe
            consecutive_failures = 0
            print(f"\n{'='*40}\n>>> ADAPTIVE PE EXPLORATION: D={dim} (from PE={current_pe} up to PE={args.max_pe}) <<<\n{'='*40}")
            while current_pe <= args.max_pe:
                point_idx += 1
                config_name = f"sweep_D{dim}_PE{current_pe}"
                point_dir = os.path.join(args.output_dir, config_name)
                
                metrics, build_info = process_point(
                    dim, current_pe, point_idx, f"Adaptive D={dim}-PE={current_pe}", args, clock_period_ns
                )
                sweep_results.append(metrics)
                generate_summary_reports(args.output_dir, sweep_results)

                if args.auto_push:
                    git_auto_push(config_name, point_dir)

                # Determine if build failed or resource budget exceeded
                failed = False
                if build_info["status"] in ("HLS_FAILED", "XO_MISSING"):
                    print(f"[adaptive-pe] HLS synthesis failed for D={dim}, PE={current_pe}.")
                    failed = True
                elif args.build_bitstream and build_info["status"] != "BITSTREAM_SUCCESS":
                    print(f"[adaptive-pe] Bitstream generation failed for D={dim}, PE={current_pe}.")
                    failed = True
                elif build_info.get("resources") and build_info["resources"].get("LUT", 0) > ULTRA96_TOTAL_RESOURCES["LUT"]:
                    print(f"[adaptive-pe] HLS LUT estimate ({build_info['resources']['LUT']}) exceeds device limit ({ULTRA96_TOTAL_RESOURCES['LUT']}).")
                    failed = True

                if failed:
                    consecutive_failures += 1
                    if consecutive_failures >= args.max_failures:
                        print(f"\n[adaptive-pe] Reached failure limit for D={dim} at PE={current_pe}. Halting exploration for D={dim}.\n")
                        break
                else:
                    consecutive_failures = 0

                current_pe += args.pe_step
    else:
        total_points = len(args.dims) * len(args.pes)
        for dim in args.dims:
            for num_pe in args.pes:
                point_idx += 1
                config_name = f"sweep_D{dim}_PE{num_pe}"
                point_dir = os.path.join(args.output_dir, config_name)

                metrics, build_info = process_point(
                    dim, num_pe, point_idx, f"{point_idx}/{total_points}", args, clock_period_ns
                )
                sweep_results.append(metrics)
                generate_summary_reports(args.output_dir, sweep_results)

                if args.auto_push:
                    git_auto_push(config_name, point_dir)

    return sweep_results

def git_auto_push(config_name, point_dir):
    """
    Commit and push newly generated sweep results to the current git branch.
    """
    try:
        res_branch = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, check=True
        )
        branch = res_branch.stdout.strip()
        if not branch or branch == "HEAD":
            print(f"[auto-push] Detached HEAD detected; skipping git push for {config_name}.")
            return

        subprocess.run(["git", "add", "sweeps/"], check=True)
        status_proc = subprocess.run(["git", "diff", "--cached", "--quiet"])
        if status_proc.returncode != 0:
            commit_msg = f"Auto-push: complete build for {config_name}"
            subprocess.run(["git", "commit", "-m", commit_msg], check=True)
            print(f"[auto-push] Rebasing on origin/{branch} before push...")
            subprocess.run(["git", "pull", "--rebase", "origin", branch], check=False)
            print(f"[auto-push] Pushing {config_name} to origin/{branch}...")
            res_push = subprocess.run(["git", "push", "origin", branch])
            if res_push.returncode != 0:
                print(f"[auto-push] Push failed, retrying after rebase...")
                subprocess.run(["git", "pull", "--rebase", "origin", branch], check=False)
                subprocess.run(["git", "push", "origin", branch], check=True)
            print(f"[auto-push] Successfully pushed {config_name} to origin/{branch}.")
        else:
            print(f"[auto-push] No new changes to commit for {config_name}.")
    except subprocess.CalledProcessError as e:
        print(f"[auto-push] Notice: git operation exited with code {e.returncode}: {e}")
    except Exception as e:
        print(f"[auto-push] Notice: unexpected git error: {e}")

def generate_summary_reports(output_dir, sweep_results):
    """
    Produce JSON and CSV summary tables, then print the leaderboard to stdout.
    """
    # Merge with existing metrics.json files across output_dir to retain sweep history
    all_results = {r["config_name"]: r for r in sweep_results}
    if os.path.isdir(output_dir):
        for entry in sorted(os.listdir(output_dir)):
            sub_dir = os.path.join(output_dir, entry)
            metric_file = os.path.join(sub_dir, "metrics.json")
            if os.path.isdir(sub_dir) and os.path.isfile(metric_file) and entry not in all_results:
                try:
                    with open(metric_file, "r") as mf:
                        all_results[entry] = json.load(mf)
                except Exception:
                    pass

    # Sort merged results by dimension then PE
    sweep_results = sorted(all_results.values(), key=lambda r: (r.get("dimension", 0), r.get("num_pe", 0)))

    json_path = os.path.join(output_dir, "sweep_summary.json")
    csv_path = os.path.join(output_dir, "sweep_summary.csv")
    
    with open(json_path, "w") as jf:
        json.dump(sweep_results, jf, indent=2)
        
    # Write CSV table
    headers = [
        "Config", "Dim", "PE", "Status", "Clock_ns",
        "Est_Cycles", "Est_Runtime_ms", "Est_Throughput_Mfeat_s",
        "Sim_Status", "Sim_Kernel_ms", "Sim_Throughput_Mfeat_s",
        "HLS_LUT", "HLS_FF", "HLS_BRAM", "HLS_DSP",
        "Impl_LUT", "Impl_FF", "Impl_BRAM", "Impl_DSP", "WNS_ns", "Fmax_MHz",
        "Build_Time_s"
    ]
    with open(csv_path, "w", newline="") as cf:
        writer = csv.writer(cf)
        writer.writerow(headers)
        for res in sweep_results:
            perf = res.get("performance", {})
            hls_res = res.get("resources") or {}
            impl_res = res.get("impl_resources") or {}
            impl_tim = res.get("impl_timing") or {}
            sim = res.get("simulation") or {}

            sim_kernel_ms = f"{sim['kernel_time_sec'] * 1e3:.2f}" if sim.get("kernel_time_sec") is not None else "-"
            sim_thr = f"{sim['throughput_mfeat_sec']:.2f}" if sim.get("throughput_mfeat_sec") is not None else "-"
            wns_val = f"{impl_tim['wns_ns']:.3f}" if impl_tim.get("wns_ns") is not None else "-"
            fmax_val = f"{impl_tim['fmax_mhz']:.1f}" if impl_tim.get("fmax_mhz") is not None else "-"

            writer.writerow([
                res["config_name"],
                res["dimension"],
                res["num_pe"],
                res["status"],
                f"{res.get('clock_period_ns', 5.0):.2f}",
                perf.get("estimated_cycles", "-"),
                f"{perf.get('estimated_runtime_sec', 0) * 1e3:.3f}" if "estimated_runtime_sec" in perf else "-",
                f"{perf.get('throughput_features_sec', 0) / 1e6:.3f}" if "throughput_features_sec" in perf else "-",
                sim.get("status", "-"),
                sim_kernel_ms,
                sim_thr,
                hls_res.get("LUT", "-"),
                hls_res.get("FF", "-"),
                hls_res.get("BRAM", "-"),
                hls_res.get("DSP", "-"),
                impl_res.get("LUT", "-"),
                impl_res.get("FF", "-"),
                impl_res.get("BRAM", "-"),
                impl_res.get("DSP", "-"),
                wns_val,
                fmax_val,
                res.get("build_time_sec", 0.0)
            ])
            
    # Print formatted console report
    print("\n" + "=" * 118)
    print("DESIGN SPACE SWEEP SUMMARY (RANKED BY FEATURE THROUGHPUT)")
    print("=" * 118)
    
    # Sort descending by feature throughput
    sorted_results = sorted(
        sweep_results,
        key=lambda r: r.get("performance", {}).get("throughput_features_sec", 0.0),
        reverse=True
    )
    
    row_fmt = "{:<15} {:>3} {:>3} {:>17} {:>11} {:>10} {:>11} {:>9} {:>9} {:>7} {:>7}"
    print(row_fmt.format(
        "Config", "Dim", "PE", "Status", "Est(Mfeat/s)", "Sim Status", "Sim(Mfeat/s)", "HLS_LUT%", "Imp_LUT%", "WNS(ns)", "Fmax(M)"
    ))
    print("-" * 118)
    
    for rank, res in enumerate(sorted_results):
        perf = res.get("performance", {})
        hls_res = res.get("resources") or {}
        impl_res = res.get("impl_resources") or {}
        impl_tim = res.get("impl_timing") or {}
        sim = res.get("simulation") or {}

        hls_lut = hls_res.get("LUT")
        hls_pct = f"{hls_lut * 100 // ULTRA96_TOTAL_RESOURCES['LUT']}%" if hls_lut else "-"

        impl_lut = impl_res.get("LUT")
        impl_pct = f"{impl_lut * 100 // ULTRA96_TOTAL_RESOURCES['LUT']}%" if impl_lut else "-"

        sim_st = sim.get("status", "-")
        sim_thr = f"{sim.get('throughput_mfeat_sec', 0.0):.1f}" if sim.get("throughput_mfeat_sec") else "-"
        wns_s = f"{impl_tim.get('wns_ns', 0.0):.2f}" if "wns_ns" in impl_tim else "-"
        fmax_s = f"{impl_tim.get('fmax_mhz', 0.0):.0f}" if "fmax_mhz" in impl_tim else "-"

        star = " ★ BEST" if rank == 0 else ""
        print(row_fmt.format(
            res["config_name"],
            res["dimension"],
            res["num_pe"],
            res["status"],
            f"{perf.get('throughput_features_sec', 0.0) / 1e6:.1f}",
            sim_st,
            sim_thr,
            hls_pct,
            impl_pct,
            wns_s,
            fmax_s
        ) + star)
        
    print("-" * 118)
    best = sorted_results[0]
    print(f"Optimal Configuration: {best['config_name']} (Dim={best['dimension']}, PE={best['num_pe']})")
    print(f"Peak Feature Throughput: {best.get('performance', {}).get('throughput_features_sec', 0.0) / 1e6:.2f} Million Features/sec")
    print(f"Full results saved to:\n  - {json_path}\n  - {csv_path}")
    print("=" * 118 + "\n")

if __name__ == "__main__":
    cli_args = parse_args()
    run_sweep(cli_args)
