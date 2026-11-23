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

# Add scripts directory to path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

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

def build_sweep_point(point_dir, dim, num_pe, args):
    """
    Run HLS synthesis and TAPA XO packaging for one design point.
    """
    build_log_path = os.path.join(point_dir, "build.log")
    curr_dir = os.getcwd()
    os.chdir(point_dir)
    
    build_status = "PENDING"
    start_time = time.time()
    
    # Verify toolchain availability
    has_tapac = shutil.which("tapac") is not None
    has_vitis = shutil.which("vitis_hls") is not None or "XILINX_HLS" in os.environ
    
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
    if has_xo and args.build_bitstream:
        print(f"[{dim}D-{num_pe}PE] Launching Vivado bitstream generation (.xclbin)...", flush=True)
        build_dir = os.path.join(point_dir, f"build_dir.hw.{FPGA_target_name}")
        xclbin_target = os.path.join(build_dir, "knn.xclbin")
        cmd_link = ["make", "build", f"DEVICE={FPGA_target_name}"]
        
        with open(build_log_path, "a") as log_file:
            log_file.write("\n=== STARTING BITSTREAM LINKING ===\n")
            proc_link = subprocess.run(cmd_link, stdout=log_file, stderr=subprocess.STDOUT, text=True, env=env)
            
        if os.path.isfile(xclbin_target):
            has_xclbin = True
            build_status = "BITSTREAM_SUCCESS"
            shutil.copy2(xclbin_target, os.path.join(point_dir, "knn.xclbin"))
            
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
        "report_path": report_path if os.path.isfile(report_path) else None
    }

def run_sweep(args):
    """
    Main execution loop across all (dimension, processing elements) configurations.
    """
    os.makedirs(args.output_dir, exist_ok=True)
    
    if args.clean:
        # Selectively clean only the configurations being executed in this run
        for dim in args.dims:
            for num_pe in args.pes:
                target_point = os.path.join(args.output_dir, f"sweep_D{dim}_PE{num_pe}")
                if os.path.exists(target_point):
                    print(f"Cleaning configuration directory: {target_point}")
                    shutil.rmtree(target_point)
        
    sweep_results = []
    total_points = len(args.dims) * len(args.pes)
    clock_period_ns = 1000.0 / args.frequency
    
    print("=" * 78)
    print(f"CHIP-KNN ULTRA96 DESIGN SPACE SWEEP")
    print(f"Dimensions: {args.dims} | PEs: {args.pes} | Total Configurations: {total_points}")
    print(f"Points (N): {args.n_points} | K: {args.k} | Clock: {args.frequency} MHz ({clock_period_ns:.2f} ns)")
    print(f"Output Directory: {args.output_dir}")
    print(f"Mode: {args.mode} | Build Bitstream: {args.build_bitstream}")
    print("=" * 78)
    
    point_idx = 0
    for dim in args.dims:
        for num_pe in args.pes:
            point_idx += 1
            config_name = f"sweep_D{dim}_PE{num_pe}"
            point_dir = os.path.join(args.output_dir, config_name)
            
            print(f"\n[{point_idx}/{total_points}] Configuring: D={dim}, PE={num_pe} -> {config_name}")
            
            # 1. Scaffold and generate golden dataset
            if args.mode in ("generate-only", "all") or not os.path.exists(point_dir):
                setup_sweep_point(point_dir, dim, num_pe, args)
                
            # 2. Run build if requested
            build_info = {
                "status": "SCAFFOLDED",
                "build_time_sec": 0.0,
                "has_xo": False,
                "has_xclbin": False,
                "resources": None
            }
            if args.mode in ("build", "all"):
                build_info = build_sweep_point(point_dir, dim, num_pe, args)
                
            # 3. Compute analytical and empirical performance
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
                "resources": build_info["resources"]
            }
            
            # Save metrics.json in point directory
            with open(os.path.join(point_dir, "metrics.json"), "w") as mf:
                json.dump(metrics, mf, indent=2)
                
            sweep_results.append(metrics)
            
            # Update summary reports after each configuration finishes
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
            capture_output=True, text=True, check=True
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
            print(f"[auto-push] Pushing {config_name} to origin/{branch}...")
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
        "Config", "Dim", "PE", "Status", "Clock_ns", "Cycles",
        "Runtime_ms", "Throughput_Mfeat_s", "Queries_s",
        "BRAM", "DSP", "FF", "LUT", "URAM", "Build_Time_s"
    ]
    with open(csv_path, "w", newline="") as cf:
        writer = csv.writer(cf)
        writer.writerow(headers)
        for res in sweep_results:
            perf = res["performance"]
            res_util = res["resources"] or {}
            writer.writerow([
                res["config_name"],
                res["dimension"],
                res["num_pe"],
                res["status"],
                f"{res['clock_period_ns']:.2f}",
                perf["estimated_cycles"],
                f"{perf['estimated_runtime_sec'] * 1e3:.3f}",
                f"{perf['throughput_features_sec'] / 1e6:.3f}",
                f"{perf['throughput_queries_sec']:.1f}",
                res_util.get("BRAM", "-"),
                res_util.get("DSP", "-"),
                res_util.get("FF", "-"),
                res_util.get("LUT", "-"),
                res_util.get("URAM", "-"),
                res["build_time_sec"]
            ])
            
    # Print formatted console report
    print("\n" + "=" * 98)
    print("DESIGN SPACE SWEEP SUMMARY (RANKED BY FEATURE THROUGHPUT)")
    print("=" * 98)
    
    # Sort descending by feature throughput
    sorted_results = sorted(
        sweep_results,
        key=lambda r: r["performance"]["throughput_features_sec"],
        reverse=True
    )
    
    row_fmt = "{:<16} {:>4} {:>4} {:>10} {:>10} {:>12} {:>16} {:>12} {:>10}"
    print(row_fmt.format(
        "Config", "Dim", "PE", "Status", "Clock(ns)", "Cycles", "Runtime(ms)", "Throughput(M/s)", "LUTs"
    ))
    print("-" * 98)
    
    for rank, res in enumerate(sorted_results):
        perf = res["performance"]
        res_util = res["resources"] or {}
        lut_str = str(res_util.get("LUT", "-"))
        
        star = " ★ BEST" if rank == 0 else ""
        print(row_fmt.format(
            res["config_name"],
            res["dimension"],
            res["num_pe"],
            res["status"],
            f"{res['clock_period_ns']:.2f}",
            perf["estimated_cycles"],
            f"{perf['estimated_runtime_sec'] * 1e3:.2f}",
            f"{perf['throughput_features_sec'] / 1e6:.2f}",
            lut_str
        ) + star)
        
    print("-" * 98)
    best = sorted_results[0]
    print(f"Optimal Configuration: {best['config_name']} (Dim={best['dimension']}, PE={best['num_pe']})")
    print(f"Peak Feature Throughput: {best['performance']['throughput_features_sec'] / 1e6:.2f} Million Features/sec")
    print(f"Full results saved to:\n  - {json_path}\n  - {csv_path}")
    print("=" * 98 + "\n")

if __name__ == "__main__":
    cli_args = parse_args()
    run_sweep(cli_args)
