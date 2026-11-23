#!/usr/bin/env python3
import subprocess
import sys
import os

def main():
    repo_root = os.path.dirname(os.path.abspath(__file__))
    os.chdir(repo_root)
    print(f"Working in repository: {repo_root}")

    # 1. Clean zero-byte corrupt objects
    subprocess.run(["find", ".git/objects/", "-type", "f", "-empty", "-delete"], check=False)

    # 2. Restore blob for scripts/singlePE_design_exploration.py
    target_file = "scripts/singlePE_design_exploration.py"
    if os.path.isfile(target_file):
        res = subprocess.run(["git", "hash-object", "-w", target_file], capture_output=True, text=True, check=True)
        print(f"Restored blob for {target_file}: {res.stdout.strip()}")

    # 3. Restore the 3 missing historical trees
    trees = [
        "100644 blob 1be3f18e5327060c67375c05a74f07ffe0fadf1e\t.gitignore\n"
        "100644 blob de7ba011a049f7e91654561afd184bb7727e34ba\tLICENSE\n"
        "100644 blob a599259990d42f2ad4d29311b741e9cb85510353\tREADME.md\n"
        "040000 tree def017e008735cc0695130e680a8af88046f2b4a\tcommon\n"
        "040000 tree ae07a96815ad21f6de575c5b3ccf947587d65965\tscripts\n"
        "100644 blob 31d10198063735c2b527d11a381a18740c156a5d\tutils.mk\n",

        "100644 blob 1be3f18e5327060c67375c05a74f07ffe0fadf1e\t.gitignore\n"
        "100644 blob de7ba011a049f7e91654561afd184bb7727e34ba\tLICENSE\n"
        "100644 blob a599259990d42f2ad4d29311b741e9cb85510353\tREADME.md\n"
        "040000 tree def017e008735cc0695130e680a8af88046f2b4a\tcommon\n"
        "040000 tree 99527ab5b9e47bf9147fd229948103f54ed58655\tscripts\n"
        "100644 blob 31d10198063735c2b527d11a381a18740c156a5d\tutils.mk\n",

        "100644 blob 1be3f18e5327060c67375c05a74f07ffe0fadf1e\t.gitignore\n"
        "100644 blob de7ba011a049f7e91654561afd184bb7727e34ba\tLICENSE\n"
        "100644 blob a599259990d42f2ad4d29311b741e9cb85510353\tREADME.md\n"
        "040000 tree def017e008735cc0695130e680a8af88046f2b4a\tcommon\n"
        "040000 tree b7e0c57513a98dc8abfa60dc3a3196e4605835c9\tscripts\n"
        "100644 blob 31d10198063735c2b527d11a381a18740c156a5d\tutils.mk\n"
    ]

    for t in trees:
        res = subprocess.run(["git", "mktree", "--missing"], input=t, text=True, capture_output=True, check=True)
        print(f"Repaired tree: {res.stdout.strip()}")

    # 4. Refresh index
    subprocess.run(["git", "update-index", "--refresh"], check=False)
    print("Git database repair finished successfully!")

if __name__ == "__main__":
    main()
