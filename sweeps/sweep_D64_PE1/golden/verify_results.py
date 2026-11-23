#!/usr/bin/env python3
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
