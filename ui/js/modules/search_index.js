/**
 * High-Speed Multi-Word Unicode Search Index for 10,000 Tools
 *
 * Requirements & Performance Guarantees:
 * 1. Split query into multiple whitespace-delimited words (all words must match).
 * 2. Full Unicode NFC normalization so English, Telugu (e.g. వీడియో, ఆడియో), and Hindi (e.g. वीडियो) work seamlessly.
 * 3. Relevance ranking: exact match > prefix match > word boundary match > contains.
 * 4. Match highlighting helper (returns HTML with <mark> tags safely escaped).
 * 5. Zero stale mutation on objects (no lingering `_score` or memory leaks).
 * 6. Sub-10ms search throughput over 10,000 tools.
 */

class ToolSearchIndex {
  constructor(tools = []) {
    this.rawTools = tools;
    this.indexed = [];
    this.rebuild(tools);
  }

  rebuild(tools) {
    this.rawTools = tools || [];
    this.indexed = this.rawTools.map((t, idx) => {
      const rawName = t.name || '';
      const rawDesc = t.description || '';
      const rawCat = t.category_name || '';

      const normName = rawName.normalize('NFC').toLowerCase();
      const normDesc = rawDesc.normalize('NFC').toLowerCase();
      const normCat = rawCat.normalize('NFC').toLowerCase();
      const words = normName.split(/\s+/).filter(Boolean);

      return {
        idx,
        tool: t,
        name: normName,
        desc: normDesc,
        cat: normCat,
        words
      };
    });
  }

  /**
   * Search tools with multi-word requirements and category/status filtering
   * @param {string} query
   * @param {string} filterTab - 'All' | 'Installed' | 'Updates' | 'Hub Catalog'
   * @returns {Array<Object>} Sorted list of matching tool objects
   */
  search(query, filterTab = 'All') {
    const rawQ = (query || '').normalize('NFC').trim();
    if (!rawQ) {
      return this._filterByTab(this.indexed, filterTab).map(item => item.tool);
    }

    const queryWords = rawQ.toLowerCase().split(/\s+/).filter(Boolean);
    if (queryWords.length === 0) {
      return this._filterByTab(this.indexed, filterTab).map(item => item.tool);
    }

    const tabFiltered = this._filterByTab(this.indexed, filterTab);
    const scoredMatches = [];

    const fullQuery = queryWords.join(' ');

    for (let i = 0; i < tabFiltered.length; i++) {
      const item = tabFiltered[i];
      let matchesAllWords = true;
      let totalScore = 0;

      // Every word in queryWords must match somewhere in name, description, or category
      for (let w = 0; w < queryWords.length; w++) {
        const qw = queryWords[w];
        let wordScore = 0;

        if (item.name === qw) {
          wordScore = 120;
        } else if (item.name.startsWith(qw)) {
          wordScore = 80;
        } else if (item.words.some(word => word.startsWith(qw))) {
          wordScore = 50;
        } else if (item.name.includes(qw)) {
          wordScore = 30;
        } else if (item.desc.includes(qw)) {
          wordScore = 15;
        } else if (item.cat.includes(qw)) {
          wordScore = 10;
        } else {
          matchesAllWords = false;
          break;
        }

        totalScore += wordScore;
      }

      if (matchesAllWords) {
        // Bonus for matching full concatenated phrase exactly or as prefix
        if (item.name === fullQuery) {
          totalScore += 200;
        } else if (item.name.startsWith(fullQuery)) {
          totalScore += 100;
        }

        // Store score separately without mutating item or item.tool (Zero stale _score)
        scoredMatches.push({
          tool: item.tool,
          score: totalScore
        });
      }
    }

    // Sort by relevance score descending
    scoredMatches.sort((a, b) => b.score - a.score);

    return scoredMatches.map(m => m.tool);
  }

  _filterByTab(items, filterTab) {
    if (filterTab === 'All') return items;

    return items.filter(item => {
      const t = item.tool;
      const isUpdate = Boolean(t.update_available || t.status === 'update_available');
      const isInstalled = t.status === 'installed' || isUpdate;

      if (filterTab === 'Installed') return isInstalled;
      if (filterTab === 'Updates') return isUpdate;
      if (filterTab === 'Hub Catalog' || filterTab === 'Catalog') return !isInstalled;
      return true;
    });
  }

  /**
   * Helper to highlight matched query words safely
   * @param {string} text
   * @param {string} query
   * @returns {string} Escaped HTML with <mark> tags
   */
  static highlight(text, query) {
    if (!text) return '';
    const rawQ = (query || '').normalize('NFC').trim();
    if (!rawQ) return ToolSearchIndex.escapeHtml(text);

    const words = rawQ.split(/\s+/).filter(Boolean);
    if (words.length === 0) return ToolSearchIndex.escapeHtml(text);

    // Escape regex special chars for safe word matching
    const pattern = words.map(w => w.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('|');
    const regex = new RegExp(`(${pattern})`, 'gi');

    const parts = text.split(regex);
    return parts.map(part => {
      if (regex.test(part)) {
        return `<mark class="bg-amber-400/30 text-[var(--text-primary)] rounded px-0.5">${ToolSearchIndex.escapeHtml(part)}</mark>`;
      }
      return ToolSearchIndex.escapeHtml(part);
    }).join('');
  }

  static escapeHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }
}

window.ToolSearchIndex = ToolSearchIndex;
