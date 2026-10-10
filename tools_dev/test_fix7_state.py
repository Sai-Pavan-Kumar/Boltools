import os
import sys
import json

sys.path.insert(0, os.path.abspath("."))
sys.path.insert(0, os.path.abspath("software"))
from src.core.tool_store import tool_store_service
from src.core.community import community_service
from src.core.announcements import announcement_service

def test_fix7_state_and_announcements():
    print("Testing Fix 7: State persistence, single-writer tool_states.json, and announcements deferral...")

    # 1. Single writer check: tool_store_service owns tool_states.json
    assert os.path.basename(tool_store_service.tool_states_file) == "tool_states.json"
    assert os.path.basename(community_service.tool_states_file) != "tool_states.json"
    assert os.path.basename(community_service.tool_states_file) == "community_install_counts.json"
    print("[OK] Single-writer invariant verified: community_service no longer writes to tool_states.json")

    # 2. Storage path check in main.py
    with open("main.py", "r", encoding="utf-8") as f:
        main_content = f.read()
    assert "private_mode=False" in main_content, "private_mode=False missing in main.py"
    assert "storage_path=" in main_content, "storage_path missing in main.py"
    print("[OK] WebView2 persistent session parameters verified in main.py (private_mode=False, storage_path)")

    # 3. Announcements deferred fetch check
    with open("src/core/announcements.py", "r", encoding="utf-8") as f:
        ann_content = f.read()
    assert "threading.Timer(10.0, self.fetch_async).start()" in ann_content, "Announcements fetch is not deferred by 10s"
    print("[OK] Remote announcements 10s deferral verified in announcements.py")

    print("\nFix 7 Verification PASSED!")

if __name__ == "__main__":
    test_fix7_state_and_announcements()
