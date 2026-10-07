"""Verification of Install and Uninstall Lifecycle in Boltools Desktop Suite."""

import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.desktop_bridge import desktop_bridge
from src.core.community import community_service


def test_lifecycle():
    tool_id = "media_audio_extractor"

    # Step 1: Install tool
    desktop_bridge.install_tool(tool_id)
    data = desktop_bridge.get_initial_data()
    tool = next((t for t in data["tools"] if t["id"] == tool_id), None)
    assert tool is not None, "Tool should be in tools list"
    assert tool["status"] == "installed", f"Expected 'installed', got {tool['status']}"
    print(f"  [PASS] Tool {tool_id} installed successfully (status={tool['status']})")

    # Step 2: Uninstall tool
    desktop_bridge.uninstall_tool(tool_id, purge_data=False)
    data = desktop_bridge.get_initial_data()
    tool = next((t for t in data["tools"] if t["id"] == tool_id), None)
    assert tool is not None, "Tool should still exist in catalog after uninstall"
    assert tool["status"] == "available", f"Expected 'available', got {tool['status']}"
    print(f"  [PASS] Tool {tool_id} uninstalled successfully (status={tool['status']})")

    # Step 3: Re-install tool
    desktop_bridge.install_tool(tool_id)
    data = desktop_bridge.get_initial_data()
    tool = next((t for t in data["tools"] if t["id"] == tool_id), None)
    assert tool["status"] == "installed", f"Expected 'installed', got {tool['status']}"
    print(f"  [PASS] Tool {tool_id} re-installed successfully (status={tool['status']})")

    print("\n>>> ALL LIFECYCLE TESTS PASSED <<<")
    return True


if __name__ == "__main__":
    test_lifecycle()
