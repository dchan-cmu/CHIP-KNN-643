#!/usr/bin/env python3
"""
sanitize_top_rtl.py: Inspect top-level Verilog RTL (Knn.v) and packaged .xo archives,
and remove any duplicate port connections within module instantiations.
This ensures Vivado synthesis never encounters 'Synth 8-344: instance has duplicate port connection'.
"""

import os
import sys
import re
import zipfile
import shutil

def deduplicate_instance_ports(verilog_text):
    """
    Find module instantiations of the form:
        module_name instance_name (
            .port1(sig1),
            .port2(sig2),
            ...
        );
    and deduplicate port connections by port name.
    """
    pattern = re.compile(r"(\b\w+\s+\w+\s*\()([^;]+?)(\);)", re.DOTALL)

    def fix_inst(match):
        prefix = match.group(1)
        body = match.group(2)
        suffix = match.group(3)

        port_pattern = re.compile(r"\.(\w+)\s*\(([^)]*)\)")
        seen = set()

        # Split port arguments by comma at parentheses depth 0
        parts = []
        cur = []
        depth = 0
        for char in body:
            if char == "(":
                depth += 1
                cur.append(char)
            elif char == ")":
                depth -= 1
                cur.append(char)
            elif char == "," and depth == 0:
                parts.append("".join(cur))
                cur = []
            else:
                cur.append(char)
        if cur:
            parts.append("".join(cur))

        new_parts = []
        removed_count = 0
        for part in parts:
            pm = port_pattern.search(part)
            if pm:
                pname = pm.group(1)
                if pname in seen:
                    removed_count += 1
                    continue
                seen.add(pname)
            new_parts.append(part)

        if removed_count > 0:
            print(f"[sanitize_top_rtl] Removed {removed_count} duplicate port connection(s) in instance.")

        return prefix + ",".join(new_parts) + suffix

    return pattern.sub(fix_inst, verilog_text)

def sanitize_file(file_path):
    if not os.path.isfile(file_path):
        return False
    with open(file_path, "r") as f:
        content = f.read()
    cleaned = deduplicate_instance_ports(content)
    if cleaned != content:
        with open(file_path, "w") as f:
            f.write(cleaned)
        print(f"[sanitize_top_rtl] Cleaned duplicate ports in {file_path}")
        return True
    return False

def sanitize_xo(xo_path):
    if not os.path.isfile(xo_path):
        return False
    if not zipfile.is_zipfile(xo_path):
        print(f"[sanitize_top_rtl] {xo_path} is not a valid zip archive.")
        return False

    tmp_dir = xo_path + "_tmp_unpack"
    if os.path.exists(tmp_dir):
        shutil.rmtree(tmp_dir, ignore_errors=True)
    os.makedirs(tmp_dir, exist_ok=True)

    with zipfile.ZipFile(xo_path, "r") as z:
        z.extractall(tmp_dir)

    modified = False
    for root, dirs, files in os.walk(tmp_dir):
        for file in files:
            if file.endswith(".v"):
                vpath = os.path.join(root, file)
                if sanitize_file(vpath):
                    modified = True

    if modified:
        # Re-pack the archive
        backup_path = xo_path + ".bak"
        shutil.move(xo_path, backup_path)
        with zipfile.ZipFile(xo_path, "w", zipfile.ZIP_DEFLATED) as z:
            for root, dirs, files in os.walk(tmp_dir):
                for file in files:
                    full_p = os.path.join(root, file)
                    rel_p = os.path.relpath(full_p, tmp_dir)
                    z.write(full_p, rel_p)
        if os.path.exists(backup_path):
            os.remove(backup_path)
        print(f"[sanitize_top_rtl] Successfully updated {xo_path} with sanitized Verilog!")

    shutil.rmtree(tmp_dir, ignore_errors=True)
    return modified

def sanitize_work_dir(work_dir):
    print(f"[sanitize_top_rtl] Scanning {work_dir} for Verilog and XO files...")
    # 1. Sanitize standalone Verilog files in work_dir
    for root, dirs, files in os.walk(work_dir):
        for file in files:
            if file.endswith(".v"):
                sanitize_file(os.path.join(root, file))

    # 2. Sanitize any .xo files
    for root, dirs, files in os.walk(work_dir):
        for file in files:
            if file.endswith(".xo"):
                sanitize_xo(os.path.join(root, file))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: sanitize_top_rtl.py <work_dir_or_file>")
        sys.exit(1)

    target = sys.argv[1]
    if os.path.isdir(target):
        sanitize_work_dir(target)
    elif os.path.isfile(target):
        if target.endswith(".xo"):
            sanitize_xo(target)
        else:
            sanitize_file(target)
