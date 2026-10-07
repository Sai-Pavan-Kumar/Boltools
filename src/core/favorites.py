"""Favorites & Pinned Tools Management Service for Boltools."""

import os
import json
from typing import List, Set


class FavoritesService:
    """Manages user pinned and favorited tools in local app state."""

    def __init__(self):
        self.state_dir = os.path.join(os.path.expanduser("~"), ".boltools")
        os.makedirs(self.state_dir, exist_ok=True)
        self.file_path = os.path.join(self.state_dir, "favorites.json")
        self._favorites: Set[str] = self._load()

    def _load(self) -> Set[str]:
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        return set(data)
            except Exception:
                return set()
        return set()

    def _save(self):
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(list(self._favorites), f, indent=2)
        except Exception:
            pass

    def get_all(self) -> List[str]:
        return list(self._favorites)

    def is_favorite(self, tool_id: str) -> bool:
        return tool_id in self._favorites

    def toggle_favorite(self, tool_id: str) -> bool:
        if tool_id in self._favorites:
            self._favorites.remove(tool_id)
            is_fav = False
        else:
            self._favorites.add(tool_id)
            is_fav = True
        self._save()
        return is_fav

    def add_favorite(self, tool_id: str):
        self._favorites.add(tool_id)
        self._save()

    def remove_favorite(self, tool_id: str):
        if tool_id in self._favorites:
            self._favorites.remove(tool_id)
            self._save()


# Global Singleton
favorites_service = FavoritesService()
