"""Lists every library source the media pack build used, from BtbN's pinned build scripts.

Usage: python tools_dev/list_media_sources.py <btbn-build-scripts.tar.gz> <out.txt>

Each scripts.d file pins its source with SCRIPT_REPO/SCRIPT_COMMIT (or a tag or
tarball URL). The GPL asks for the complete source of what we ship; this list,
next to the build scripts, says exactly which sources those are.
"""

import re
import sys
import tarfile

PIN = re.compile(r'^(SCRIPT_(?:REPO|COMMIT|TAG|URL|BRANCH|SHA512|SHA256)\d*)="?([^"\n]+)"?', re.M)


def main() -> None:
    archive, out_path = sys.argv[1:3]
    rows = []
    with tarfile.open(archive) as tar:
        for member in sorted(tar.getmembers(), key=lambda m: m.name):
            if "/scripts.d/" not in member.name or not member.isfile():
                continue
            text = tar.extractfile(member).read().decode("utf-8", "replace")
            pins = PIN.findall(text)
            if pins:
                script = member.name.split("/scripts.d/", 1)[1]
                rows.append(script + "\n" + "\n".join(f"  {k} = {v}" for k, v in pins))
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        f.write("Library sources pinned by BtbN/FFmpeg-Builds commit 937868360a21d711ec94a33f5591d345ad9b7754\n")
        f.write("(the scripts that built the FFmpeg in this media pack)\n\n")
        f.write("\n\n".join(rows) + "\n")
    print(f"{len(rows)} build scripts with pinned sources -> {out_path}")


if __name__ == "__main__":
    main()
