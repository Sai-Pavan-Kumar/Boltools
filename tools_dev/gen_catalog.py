"""Synthetic Tool Catalog Generator for Boltools Development & Benchmarking.

Generates N synthetic tools (default 10,000) with mixed English, Telugu, and Hindi titles,
diverse categories, mixed statuses, and long descriptions.
Used only when BOLTOOLS_DEV_CATALOG is set.
"""

import sys
import json
import random
import unicodedata
from typing import List, Dict, Any

CATEGORIES = [
    {"id": "video", "name": "Media & Video", "icon": "video", "accent": "#2563EB"},
    {"id": "pdf", "name": "PDF Studio", "icon": "file-text", "accent": "#DC2626"},
    {"id": "image", "name": "Image Studio", "icon": "image", "accent": "#059669"},
    {"id": "system", "name": "System & Files", "icon": "sliders", "accent": "#475569"},
    {"id": "audio", "name": "Audio Engineering", "icon": "music", "accent": "#8B5CF6"},
    {"id": "document", "name": "Documents & Office", "icon": "file", "accent": "#F59E0B"}
]

ENGLISH_PREFIXES = ["Ultra", "Fast", "Smart", "Batch", "Lossless", "Clean", "Offline", "Instant", "Quick", "Pro", "Silent", "Secure"]
ENGLISH_ACTIONS = ["Compressor", "Converter", "Extractor", "Merger", "Splitter", "Optimizer", "Watermarker", "Renamer", "Generator", "Validator"]
ENGLISH_SUBJECTS = ["Video", "PDF", "Audio", "WebP", "Image", "Subtitles", "Metadata", "Archive", "Font", "Cache", "Document", "Stream"]

TELUGU_WORDS = [
    "వీడియో కంప్రెసర్", "పిడిఎఫ్ కన్వర్టర్", "ఆడియో ఎక్స్ట్రాక్టర్", "ఫోటో రీసైజర్",
    "సబ్‌టైటిల్స్ ఎడిటర్", "ఫైల్ రీనేమర్", "త్వరిత ఆప్టిమైజర్", "డాక్యుమెంట్ స్కానర్",
    "క్లీన్ ఆర్కైవర్", "ఆఫ్‌లైన్ టూల్ బాక్స్"
]

HINDI_WORDS = [
    "वीडियो कंप्रेसर", "पीडीएफ कन्वर्टर", "ऑडियो एक्सट्रैक्टर", "फोटो रिसाइज़र",
    "सबटाइटल एडिटर", "फ़ाइल रीनेमर", "त्वरित ऑप्टिमाइज़र", "दस्तावेज़ स्कैनर",
    "स्वच्छ संग्रहकर्ता", "ऑफ़लाइन टूलकिट"
]

DESCRIPTIONS = [
    "High-speed 100% offline local processing with zero memory spikes, private local sandboxing, and ultra-fast hardware acceleration.",
    "Comprehensive batch automation designed specifically for creators, editors, power users, and enterprise document workflows.",
    "Eliminates subscriptions and cloud security risks by processing gigabytes directly on this PC using native OS pipelines.",
    "పూర్తిగా ఆఫ్‌లైన్ మరియు సురక్షితమైన టూల్. మీ డేటా ఎక్కడికీ వెళ్లదు, మీ కంప్యూటర్‌లోనే ప్రాసెస్ అవుతుంది.",
    "पूरी तरह से ऑफ़लाइन और सुरक्षित टूल। आपका डेटा पूरी तरह से निजी रहता है और पीसी पर प्रोसेस होता है।"
]

STATUSES = ["installed", "available", "update_available"]
STATUS_WEIGHTS = [0.25, 0.65, 0.10]
ICONS = ["video", "music", "file-text", "image", "sliders", "type", "archive", "folder", "download", "cpu"]


def generate_tools(count: int = 10000) -> List[Dict[str, Any]]:
    random.seed(42)  # Deterministic for repeatable benchmarking
    tools = []

    for i in range(1, count + 1):
        cat = CATEGORIES[i % len(CATEGORIES)]
        lang_choice = i % 10

        if lang_choice < 6:
            # English (60%)
            pre = random.choice(ENGLISH_PREFIXES)
            sub = random.choice(ENGLISH_SUBJECTS)
            act = random.choice(ENGLISH_ACTIONS)
            name = f"{pre} {sub} {act} #{i}"
        elif lang_choice < 8:
            # Telugu (20%)
            t_term = random.choice(TELUGU_WORDS)
            name = f"{t_term} (టూల్ #{i})"
        else:
            # Hindi (20%)
            h_term = random.choice(HINDI_WORDS)
            name = f"{h_term} (टूल #{i})"

        name = unicodedata.normalize("NFC", name)
        status = random.choices(STATUSES, weights=STATUS_WEIGHTS, k=1)[0]
        desc = unicodedata.normalize("NFC", random.choice(DESCRIPTIONS))

        tools.append({
            "id": f"tool_synth_{i:05d}",
            "num": f"{(i // 1000) + 1}.{(i % 1000) + 1}",
            "name": name,
            "category_id": cat["id"],
            "category_name": cat["name"],
            "icon": random.choice(ICONS),
            "description": desc,
            "status": status,
            "version": f"1.{random.randint(0, 5)}.{random.randint(0, 9)}",
            "remote_version": "2.0.0" if status == "update_available" else None,
            "update_available": (status == "update_available"),
            "size_mb": random.randint(5, 80),
            "is_offline": True,
            "engine": "Native Subprocess Engine"
        })

    return tools


def main():
    count = 10000
    if len(sys.argv) > 1:
        try:
            count = int(sys.argv[1])
        except ValueError:
            pass

    out_file = "tools_dev/catalog_synth.json"
    if len(sys.argv) > 2:
        out_file = sys.argv[2]

    print(f"Generating {count} synthetic tools...")
    tools = generate_tools(count)
    data = {
        "schema_version": "1.0.0",
        "total_tools": len(tools),
        "tools": tools
    }

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Successfully generated {len(tools)} tools to {out_file}")


if __name__ == "__main__":
    main()
