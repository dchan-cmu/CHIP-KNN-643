#!/usr/bin/env python3
"""
golden_model.py: Standalone Pure-Python Golden Reference Model for CHIP-KNN.
Uses standard library only (no external dependencies like numpy) so it runs
seamlessly on development hosts, build servers, and Ultra96 embedded Linux.
"""

import os
import sys
import json
import math
import random
import struct

def float_to_fixed32(val, int_bits=12, fract_bits=20):
    """Convert float to signed fixed point 32-bit integer."""
    scale = 1 << fract_bits
    int_val = int(round(val * scale))
    max_val = (1 << (int_bits + fract_bits - 1)) - 1
    min_val = -(1 << (int_bits + fract_bits - 1))
    clamped = max(min(int_val, max_val), min_val)
    return clamped & 0xFFFFFFFF

def fixed32_to_float(fixed_val, int_bits=12, fract_bits=20):
    """Convert signed fixed point 32-bit integer back to float."""
    scale = float(1 << fract_bits)
    if fixed_val & (1 << 31):
        signed_val = fixed_val - (1 << 32)
    else:
        signed_val = fixed_val
    return float(signed_val) / scale

def quantize_12_20(val):
    """Quantize a float to signed fixed-point 12.20 representation."""
    scale = float(1 << 20)
    int_val = int(round(val * scale))
    max_val = (1 << 31) - 1
    min_val = -(1 << 31)
    clamped = max(min(int_val, max_val), min_val)
    return float(clamped) / scale

def generate_golden_dataset(n_points=131072, dim=16, k=10, dist_metric=0, num_pes=1, seed=42):
    """
    Generate query, search space, and top-K ground truth using standard library.
    
    Args:
        n_points: Total search space points across all PEs.
        dim: Dimensionality of each point.
        k: Top-K neighbors to retain.
        dist_metric: 0 for Manhattan, 1 for Euclidean.
        num_pes: Number of processing elements (for partitioning).
        seed: Random seed for reproducibility.
        
    Returns:
        dict containing query, search_space, topk results, and metadata.
    """
    rnd = random.Random(seed)
    
    # Scale components to prevent fixed-point overflow during distance summation
    max_val = 2047.0  # 12 integer bits (signed)
    max_comp = (max_val * 0.8) / dim
    
    # Generate quantized query
    query = [quantize_12_20(rnd.uniform(0.1, max_comp)) for _ in range(dim)]
    
    # Generate search space and compute distances
    search_space = []
    distances_and_ids = []
    
    for i in range(n_points):
        pt = [quantize_12_20(rnd.uniform(0.0, max_comp)) for _ in range(dim)]
        search_space.append(pt)
        
        # Calculate distance matching hardware
        if dist_metric == 0:
            # Manhattan distance: sum(|x_d - q_d|)
            dist = sum(abs(pt[d] - query[d]) for d in range(dim))
        else:
            # Euclidean distance: sum((x_d - q_d)^2)
            dist = sum((pt[d] - query[d]) ** 2 for d in range(dim))
            
        quantized_dist = quantize_12_20(dist)
        distances_and_ids.append((quantized_dist, i))
        
    # Sort by distance ascending, tie-break by ID ascending
    distances_and_ids.sort(key=lambda item: (item[0], item[1]))
    
    topk_list = []
    for rank in range(min(k, len(distances_and_ids))):
        dist, pt_id = distances_and_ids[rank]
        topk_list.append({
            "rank": int(rank),
            "id": int(pt_id),
            "distance": float(dist),
            "distance_fixed_hex": hex(float_to_fixed32(float(dist)))
        })
        
    return {
        "metadata": {
            "n_points": int(n_points),
            "dim": int(dim),
            "k": int(k),
            "dist_metric": "manhattan" if dist_metric == 0 else "euclidean",
            "num_pes": int(num_pes),
            "seed": int(seed),
            "fixed_point": {"int_bits": 12, "fract_bits": 20, "total_bits": 32}
        },
        "query": query,
        "search_space": search_space,
        "topk": topk_list
    }

def export_golden_files(dataset, output_dir):
    """
    Export golden dataset files into the specified directory.
    """
    os.makedirs(output_dir, exist_ok=True)
    meta = dataset["metadata"]
    dim = meta["dim"]
    num_pes = meta["num_pes"]
    n_points = meta["n_points"]
    query = dataset["query"]
    search_space = dataset["search_space"]
    topk = dataset["topk"]
    
    # 1. Metadata & Query JSON
    with open(os.path.join(output_dir, "metadata.json"), "w") as f:
        json.dump(meta, f, indent=2)
        
    with open(os.path.join(output_dir, "query.json"), "w") as f:
        json.dump(query, f, indent=2)
        
    with open(os.path.join(output_dir, "query.txt"), "w") as f:
        for val in query:
            f.write(f"{val:.8f}\n")
            
    # 2. Expected Top-K Ground Truth
    with open(os.path.join(output_dir, "expected_topk.json"), "w") as f:
        json.dump(topk, f, indent=2)
        
    with open(os.path.join(output_dir, "expected_topk.txt"), "w") as f:
        f.write("# Rank  Point_ID  Distance  Fixed_Hex\n")
        for item in topk:
            f.write(f"{item['rank']:<6} {item['id']:<10} {item['distance']:<14.6f} {item['distance_fixed_hex']}\n")
            
    # 3. Partitioned Search Space for Hardware / Emulation
    pts_per_pe = n_points // num_pes
    partitions_meta = []
    
    for pe_idx in range(num_pes):
        start_pt = pe_idx * pts_per_pe
        end_pt = (pe_idx + 1) * pts_per_pe if pe_idx < num_pes - 1 else n_points
        pe_pts = search_space[start_pt:end_pt]
        
        bin_path = os.path.join(output_dir, f"search_space_pe{pe_idx}.bin")
        txt_path = os.path.join(output_dir, f"search_space_pe{pe_idx}.txt")
        
        with open(bin_path, "wb") as bf, open(txt_path, "w") as tf:
            for pt_idx, pt in enumerate(pe_pts):
                global_id = start_pt + pt_idx
                tf.write(f"# ID {global_id}\n")
                for comp in pt:
                    fixed_val = float_to_fixed32(float(comp))
                    bf.write(struct.pack("<I", fixed_val))
                    tf.write(f"{comp:.8f} ")
                tf.write("\n")
                
        partitions_meta.append({
            "pe_idx": pe_idx,
            "start_pt": start_pt,
            "end_pt": end_pt,
            "count": int(end_pt - start_pt),
            "bin_file": os.path.basename(bin_path),
            "txt_file": os.path.basename(txt_path)
        })
        
    with open(os.path.join(output_dir, "partitions_meta.json"), "w") as f:
        json.dump(partitions_meta, f, indent=2)
        
    # 4. Write self-contained Ultra96 verification script
    verify_script_content = '''#!/usr/bin/env python3
"""
verify_results.py: Compare Ultra96 hardware / emulation output with expected top-K.
Usage:
  python3 verify_results.py [output_file]
"""
import sys, os, json

def verify(output_path="hw_output.txt", expected_path="expected_topk.json"):
    if not os.path.isfile(expected_path):
        expected_path = os.path.join(os.path.dirname(__file__), "expected_topk.json")
    if not os.path.isfile(expected_path):
        print(f"Error: {expected_path} not found.")
        sys.exit(1)
        
    with open(expected_path, "r") as f:
        expected = json.load(f)
        
    if not os.path.isfile(output_path):
        print(f"Notice: output file {output_path} not found.")
        print("Expected Top-K is:")
        for item in expected:
            print(f"  Rank {item['rank']}: ID={item['id']}, Dist={item['distance']:.4f}")
        return False
        
    actual = []
    with open(output_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) >= 2:
                try:
                    actual.append({"id": int(parts[0]), "dist": float(parts[1])})
                except ValueError:
                    pass
                    
    print(f"Comparing {len(actual)} hardware results against {len(expected)} expected...")
    matches = 0
    for idx, exp in enumerate(expected):
        if idx < len(actual):
            act = actual[idx]
            id_match = (act["id"] == exp["id"])
            dist_diff = abs(act["dist"] - exp["distance"])
            dist_ok = (dist_diff < 1e-3)
            status = "PASS" if (id_match and dist_ok) else "FAIL"
            if id_match:
                matches += 1
            print(f"Rank {idx}: Exp(ID={exp['id']}, D={exp['distance']:.4f}) | Act(ID={act['id']}, D={act['dist']:.4f}) -> {status}")
            
    print(f"Result: {matches}/{len(expected)} matches.")
    if matches == len(expected):
        print(">>> ALL TOP-K RESULTS MATCH! VERIFICATION SUCCESSFUL. <<<")
        return True
    else:
        print(">>> MISMATCH DETECTED IN TOP-K RESULTS. <<<")
        return False

if __name__ == "__main__":
    out_file = sys.argv[1] if len(sys.argv) > 1 else "hw_output.txt"
    ok = verify(out_file)
    sys.exit(0 if ok else 1)
'''
    with open(os.path.join(output_dir, "verify_results.py"), "w") as f:
        f.write(verify_script_content)
    os.chmod(os.path.join(output_dir, "verify_results.py"), 0o755)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Generate golden KNN reference dataset")
    parser.add_argument("--n-points", type=int, default=1000, help="Number of search space points")
    parser.add_argument("--dim", type=int, default=16, help="Feature dimension")
    parser.add_argument("--k", type=int, default=10, help="Top-K count")
    parser.add_argument("--dist", type=int, default=0, help="0: Manhattan, 1: Euclidean")
    parser.add_argument("--pes", type=int, default=1, help="Number of PEs")
    parser.add_argument("--out-dir", type=str, default="golden_ref", help="Output directory")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()
    
    ds = generate_golden_dataset(args.n_points, args.dim, args.k, args.dist, args.pes, args.seed)
    export_golden_files(ds, args.out_dir)
    print(f"[golden_model] Generated {args.n_points} points in {args.dim}D for {args.pes} PEs in {args.out_dir}")
