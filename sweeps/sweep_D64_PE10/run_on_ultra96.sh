#!/bin/bash
# Ultra96 Kernel Runner for Configuration: D=64, PE=10
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

BITSTREAM="${1:-build_dir.hw.u96v2_sbc_base_2023_2-vitis-platform/knn.xclbin}"
if [ ! -f "$BITSTREAM" ]; then
    echo "Notice: Bitstream $BITSTREAM not found."
    echo "Usage: ./run_on_ultra96.sh [path_to_xclbin]"
    exit 1
fi

echo "=== Running CHIP-KNN on Ultra96 (D=64, PE=10) ==="
./knn "$BITSTREAM" 2>&1 | tee ultra96_run.log

echo "=== Verifying Hardware Output Against Golden Reference ==="
python3 golden/verify_results.py hw_output.txt
