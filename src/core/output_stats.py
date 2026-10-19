"""Measures what a finished run actually produced.

Most engines only report output paths, so the result screen had nothing to say
beyond elapsed time. Sizes are read from disk here, once, for every tool, which
keeps the numbers honest and engines free of UI concerns.
"""

import os
from typing import Any, Dict, Iterable, List, Optional


def _total_size(paths: Iterable[Any]) -> int:
    total = 0
    for path in paths:
        if isinstance(path, str) and os.path.isfile(path):
            total += os.path.getsize(path)
    return total


def with_file_sizes(stats: Optional[Dict[str, Any]], input_files: List[str], outputs: Any) -> Dict[str, Any]:
    merged = dict(stats or {})
    output_list = outputs if isinstance(outputs, list) else [outputs]
    input_bytes = _total_size(input_files)
    output_bytes = _total_size(output_list)
    if input_bytes:
        merged.setdefault("input_bytes", input_bytes)
    if output_bytes:
        merged.setdefault("output_bytes", output_bytes)
    merged.setdefault("output_count", len([p for p in output_list if p]))
    return merged
