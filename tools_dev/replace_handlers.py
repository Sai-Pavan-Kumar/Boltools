import re

with open('software/ui/js/app.js', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Breadcrumb buttons (lines ~265-280)
old_bc = 'html += `<button onclick="${onclickStr}" class="text-xs font-medium text-[var(--brand-primary)] hover:underline cursor-pointer">${crumb}</button>`;'
new_bc = '''let actionAttr = '';
      if (crumb === 'Home') actionAttr = 'data-action="nav" data-view="home"';
      else if (crumb === 'Tool Hub') actionAttr = 'data-action="nav" data-view="tool_hub"';
      else if (crumb === 'Favorites') actionAttr = 'data-action="nav" data-view="favorites"';
      else if (crumb === 'Settings') actionAttr = 'data-action="nav" data-view="settings"';
      else {
        const cat = state.categories.find(c => c.name.toLowerCase() === crumb.toLowerCase());
        if (cat) actionAttr = `data-action="nav-category" data-cat="${escapeAttr(cat.id)}"`;
      }
      html += `<button ${actionAttr} class="text-xs font-medium text-[var(--brand-primary)] hover:underline cursor-pointer">${escapeHtml(crumb)}</button>`;'''
assert old_bc in code, "old_bc not found"
code = code.replace(old_bc, new_bc)

# 2. Home recentRows & bentoGrid
old_recent = '<div onclick="navigateTo(\'tool_studio\', \'${t.id}\')"'
new_recent = '<div data-action="open-tool" data-tool-id="${escapeAttr(t.id)}"'
code = code.replace(old_recent, new_recent)

# Home buttons:
code = code.replace(
  '<button onclick="navigateTo(\'tool_hub\')" class="btn-primary px-3.5 py-1.5 text-xs font-medium rounded-lg bg-[var(--brand-primary)] hover:bg-[var(--brand-hover)] text-white inline-flex items-center gap-1.5">',
  '<button data-action="nav" data-view="tool_hub" class="btn-primary px-3.5 py-1.5 text-xs font-medium rounded-lg bg-[var(--brand-primary)] hover:bg-[var(--brand-hover)] text-white inline-flex items-center gap-1.5 cursor-pointer">'
)

code = code.replace(
  '<button onclick="setHubTab(\'Updates\'); navigateTo(\'tool_hub\');" class="px-3.5 py-1.5 text-xs font-semibold rounded-lg bg-amber-500 hover:bg-amber-600 text-white transition-all shrink-0 cursor-pointer shadow-sm">',
  '<button data-action="open-updates-hub" class="px-3.5 py-1.5 text-xs font-semibold rounded-lg bg-amber-500 hover:bg-amber-600 text-white transition-all shrink-0 cursor-pointer shadow-sm">'
)

code = code.replace(
  '<button onclick="navigateTo(\'tool_hub\')" class="text-xs font-medium text-[var(--brand-primary)] hover:underline flex items-center gap-1">',
  '<button data-action="nav" data-view="tool_hub" class="text-xs font-medium text-[var(--brand-primary)] hover:underline flex items-center gap-1 cursor-pointer">'
)

# 3. Category View
code = code.replace(
  '<button onclick="event.stopPropagation(); openUninstallModal(\'${t.id}\', \'${t.name}\')"',
  '<button data-action="uninstall-tool" data-tool-id="${escapeAttr(t.id)}" data-tool-name="${escapeAttr(t.name)}"'
)
code = code.replace(
  '<button onclick="event.stopPropagation(); installTool(\'${t.id}\')"',
  '<button data-action="install-tool" data-tool-id="${escapeAttr(t.id)}"'
)
code = code.replace(
  '<button onclick="navigateTo(\'tool_hub\')" class="text-xs text-[var(--brand-primary)] hover:underline">Browse all in Tool Hub &rarr;</button>',
  '<button data-action="nav" data-view="tool_hub" class="text-xs text-[var(--brand-primary)] hover:underline cursor-pointer">Browse all in Tool Hub &rarr;</button>'
)

# 4. Tool Hub Card
code = code.replace(
  '<button id="btn-action-${t.id}" onclick="handleInstallOrUpdateTool(\'${t.id}\', true)"',
  '<button id="btn-action-${escapeAttr(t.id)}" data-action="update-tool" data-tool-id="${escapeAttr(t.id)}"'
)
code = code.replace(
  '<button onclick="navigateTo(\'tool_studio\', \'${t.id}\')" class="px-2 py-1 text-xs font-medium rounded-lg text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--surface-inset)] transition-colors cursor-pointer">',
  '<button data-action="open-tool" data-tool-id="${escapeAttr(t.id)}" class="px-2 py-1 text-xs font-medium rounded-lg text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--surface-inset)] transition-colors cursor-pointer">'
)
code = code.replace(
  '<button onclick="navigateTo(\'tool_studio\', \'${t.id}\')" class="btn-primary px-3 py-1 text-xs font-medium rounded-lg bg-[var(--brand-primary)] hover:bg-[var(--brand-hover)] text-white transition-all flex items-center gap-1.5 cursor-pointer">',
  '<button data-action="open-tool" data-tool-id="${escapeAttr(t.id)}" class="btn-primary px-3 py-1 text-xs font-medium rounded-lg bg-[var(--brand-primary)] hover:bg-[var(--brand-hover)] text-white transition-all flex items-center gap-1.5 cursor-pointer">'
)
code = code.replace(
  '<button onclick="openUninstallModal(\'${t.id}\', \'${t.name}\')"',
  '<button data-action="uninstall-tool" data-tool-id="${escapeAttr(t.id)}" data-tool-name="${escapeAttr(t.name)}"'
)
code = code.replace(
  '<button id="btn-action-${t.id}" onclick="handleInstallOrUpdateTool(\'${t.id}\', false)"',
  '<button id="btn-action-${escapeAttr(t.id)}" data-action="install-tool" data-tool-id="${escapeAttr(t.id)}"'
)

# Hub Tabs & Search Input:
code = code.replace(
  '<button onclick="setHubTab(\'${tab.id}\')"',
  '<button data-action="set-hub-tab" data-tab="${escapeAttr(tab.id)}"'
)
code = code.replace(
  'oninput="handleHubSearch(this.value)"',
  'data-action="hub-search-input"'
)

# 5. Favorites
code = code.replace(
  '<button onclick="navigateTo(\'tool_hub\')" class="btn-primary px-4 py-2 text-xs font-medium rounded-lg bg-[var(--brand-primary)] hover:bg-[var(--brand-hover)] text-white shadow-sm transition-all inline-flex items-center gap-1.5">',
  '<button data-action="nav" data-view="tool_hub" class="btn-primary px-4 py-2 text-xs font-medium rounded-lg bg-[var(--brand-primary)] hover:bg-[var(--brand-hover)] text-white shadow-sm transition-all inline-flex items-center gap-1.5 cursor-pointer">'
)
code = code.replace(
  '<button onclick="handleToggleFavorite(\'${t.id}\')"',
  '<button data-action="toggle-fav" data-tool-id="${escapeAttr(t.id)}"'
)
code = code.replace(
  '<button onclick="navigateTo(\'tool_studio\', \'${t.id}\')" class="btn-primary px-3.5 py-1.5 text-xs font-medium rounded-lg bg-[var(--brand-primary)] hover:bg-[var(--brand-hover)] text-white transition-all flex items-center gap-1.5 shadow-sm">',
  '<button data-action="open-tool" data-tool-id="${escapeAttr(t.id)}" class="btn-primary px-3.5 py-1.5 text-xs font-medium rounded-lg bg-[var(--brand-primary)] hover:bg-[var(--brand-hover)] text-white transition-all flex items-center gap-1.5 shadow-sm cursor-pointer">'
)

# 6. Settings
code = code.replace(
  '<button onclick="applyTheme(\'${m}\')"',
  '<button data-action="set-theme" data-theme="${escapeAttr(m)}"'
)
code = code.replace(
  '<button onclick="handleBrowseDefaultFolder()" class="px-3.5 py-2 text-xs font-medium rounded-lg bg-[var(--surface-inset)] hover:bg-[var(--surface-card-hover)] border border-[var(--border-subtle)] text-[var(--text-primary)] shrink-0 transition-colors">',
  '<button data-action="browse-default-folder" class="px-3.5 py-2 text-xs font-medium rounded-lg bg-[var(--surface-inset)] hover:bg-[var(--surface-card-hover)] border border-[var(--border-subtle)] text-[var(--text-primary)] shrink-0 transition-colors cursor-pointer">'
)
code = code.replace(
  '<button onclick="handleCleanCache(this)" class="px-3.5 py-2 text-xs font-medium rounded-lg bg-[var(--surface-inset)] hover:bg-[var(--surface-card-hover)] border border-[var(--border-subtle)] text-[var(--text-primary)] transition-colors">',
  '<button data-action="clean-cache" class="px-3.5 py-2 text-xs font-medium rounded-lg bg-[var(--surface-inset)] hover:bg-[var(--surface-card-hover)] border border-[var(--border-subtle)] text-[var(--text-primary)] transition-colors cursor-pointer">'
)

# 7. Studio Header & Dropzone
code = code.replace(
  '<button onclick="navigateBack()" class="w-8 h-8 rounded-lg flex items-center justify-center bg-[var(--surface-card)] hover:bg-[var(--surface-card-hover)] border border-[var(--border-subtle)] text-[var(--text-primary)] transition-colors">',
  '<button data-action="navigate-back" class="w-8 h-8 rounded-lg flex items-center justify-center bg-[var(--surface-card)] hover:bg-[var(--surface-card-hover)] border border-[var(--border-subtle)] text-[var(--text-primary)] transition-colors cursor-pointer">'
)
code = code.replace(
  '<button onclick="handleStudioToggleFavorite(\'${tool.id}\', this)"',
  '<button data-action="studio-toggle-fav" data-tool-id="${escapeAttr(tool.id)}"'
)
code = code.replace(
  'onclick="handleStudioBrowseFiles(\'${tool.id}\')"',
  'data-action="studio-browse-files" data-tool-id="${escapeAttr(tool.id)}"'
)
code = code.replace(
  '<button onclick="clearStudioFiles()" class="text-red-500 hover:underline">Clear all</button>',
  '<button data-action="clear-studio-files" class="text-red-500 hover:underline cursor-pointer">Clear all</button>'
)
code = code.replace(
  'oninput="state.customOutputDir = this.value"',
  'data-action="studio-out-folder-input"'
)
code = code.replace(
  '<button onclick="handleStudioBrowseOutFolder()" class="px-3 py-1.5 text-xs font-medium rounded-lg bg-[var(--surface-inset)] hover:bg-[var(--surface-card-hover)] border border-[var(--border-subtle)] text-[var(--text-primary)] shrink-0 transition-colors">',
  '<button data-action="studio-browse-out-folder" class="px-3 py-1.5 text-xs font-medium rounded-lg bg-[var(--surface-inset)] hover:bg-[var(--surface-card-hover)] border border-[var(--border-subtle)] text-[var(--text-primary)] shrink-0 transition-colors cursor-pointer">'
)
code = code.replace(
  'onclick="handleExecuteTool(\'${tool.id}\')"',
  'data-action="studio-execute" data-tool-id="${escapeAttr(tool.id)}"'
)

# 8. Subtitle Animator Player & Cues
code = code.replace(
  '<button id="sub-btn-playpause" onclick="toggleSubtitleVideoPlay()"',
  '<button id="sub-btn-playpause" data-action="sub-toggle-play"'
)
code = code.replace(
  'oninput="handleSubtitleScrub(this.value)"',
  'data-action="sub-scrubber-input"'
)
code = code.replace(
  '<button onclick="addSubtitleCue()"',
  '<button data-action="sub-add-cue"'
)
code = code.replace(
  '<button onclick="handleCancelTool()"',
  '<button data-action="cancel-tool"'
)

# 9. Tool Specific Options
code = code.replace(
  'onclick="setStudioMode(\'${m}\')"',
  'data-action="set-studio-mode" data-mode="${escapeAttr(m)}"'
)
code = code.replace(
  'oninput="document.getElementById(\'qual-val-lbl\').innerText = this.value + \'%\'; state.activeToolOptions.quality = this.value;"',
  'data-action="webp-qual-input"'
)
code = code.replace(
  'oninput="state.activeToolOptions.text1 = this.value"',
  'data-action="renamer-text-input"'
)
code = code.replace(
  'onclick="handleSelectSubtitleStyle(\'${p.id}\')"',
  'data-action="sub-select-style" data-style="${escapeAttr(p.id)}"'
)
code = code.replace(
  'onclick="handleBrowseCustomFont()"',
  'data-action="sub-browse-font"'
)
code = code.replace(
  'onchange="setSubtitleColor(\'primary_color\', this.value)"',
  'data-action="sub-color-change" data-color-prop="primary_color"'
)
code = code.replace(
  'onchange="setSubtitleColor(\'outline_color\', this.value)"',
  'data-action="sub-color-change" data-color-prop="outline_color"'
)
code = code.replace(
  'onchange="setSubtitleColor(\'highlight_color\', this.value)"',
  'data-action="sub-color-change" data-color-prop="highlight_color"'
)
code = code.replace(
  'oninput="document.getElementById(\'sub-fontsize-val\').innerText = this.value + \'px\'; setSubtitleFontSize(this.value);"',
  'data-action="sub-fontsize-input"'
)
code = code.replace(
  'onclick="setSubtitlePosition(\'${pKey}\')"',
  'data-action="sub-set-position" data-pos="${escapeAttr(pKey)}"'
)
code = code.replace(
  'onchange="setSubtitleAllCaps(this.checked)"',
  'data-action="sub-all-caps-change"'
)
code = code.replace(
  'onclick="loadDemoSubtitleSample()"',
  'data-action="sub-load-demo"'
)

# 10. Dropdowns
code = code.replace(
  'onclick="selectCustomDropdownOption(\'${id}\', \'${safeVal}\', \'${safeLbl}\', \'${onSelect}\')"',
  'data-action="select-dropdown-option" data-dd-id="${escapeAttr(id)}" data-dd-val="${escapeAttr(val)}" data-dd-lbl="${escapeAttr(lbl)}" data-dd-callback="${escapeAttr(onSelect)}"'
)
code = code.replace(
  'onclick="toggleCustomDropdown(\'${id}\', event)"',
  'data-action="toggle-dropdown" data-dd-id="${escapeAttr(id)}"'
)

# 11. Completion card
code = code.replace(
  '<button onclick="handleOpenOutputFile()"',
  '<button data-action="open-output-file"'
)
code = code.replace(
  '<button onclick="handleRevealOutputFolder()"',
  '<button data-action="reveal-output-folder"'
)

# 12. Subtitle Cues
code = code.replace(
  '<button onclick="seekSubtitlePreview(${cue.start})"',
  '<button data-action="sub-seek-cue" data-cue-start="${cue.start}"'
)
code = code.replace(
  '<button onclick="nudgeCueTime(${cue.id}, -0.1)"',
  '<button data-action="sub-nudge-cue" data-cue-id="${cue.id}" data-nudge="-0.1"'
)
code = code.replace(
  '<button onclick="nudgeCueTime(${cue.id}, 0.1)"',
  '<button data-action="sub-nudge-cue" data-cue-id="${cue.id}" data-nudge="0.1"'
)
code = code.replace(
  '<button onclick="deleteSubtitleCue(${cue.id})"',
  '<button data-action="sub-delete-cue" data-cue-id="${cue.id}"'
)
code = code.replace(
  'oninput="updateSubtitleCueText(${cue.id}, this.value)"',
  'data-action="sub-cue-text-input" data-cue-id="${cue.id}"'
)

# 13. Command Palette
code = code.replace(
  '<div onclick="closeCommandPalette(); navigateTo(\'tool_studio\', \'${t.id}\')"',
  '<div data-action="cmd-select-tool" data-tool-id="${escapeAttr(t.id)}"'
)

# 14. Announcements CTA
code = code.replace(
  '<button onclick="handleAnnouncementAction(\'${a.cta_action}\', \'${a.cta_target || \'\'}\')"',
  '<button data-action="announcement-cta" data-cta-action="${escapeAttr(a.cta_action)}" data-cta-target="${escapeAttr(a.cta_target || \'\')}"'
)

# 15. Escape dynamic catalog / manifest values in tool cards and titles:
# Replace unescaped t.name, t.description, t.category_name, tool.name, tool.description in templates:
code = re.sub(r'<h4 class="text-sm font-semibold text-\[var\(--text-primary\)\] truncate">\$\{t\.name\}</h4>',
              '<h4 class="text-sm font-semibold text-[var(--text-primary)] truncate">${escapeHtml(t.name)}</h4>', code)
code = re.sub(r'<p class="text-xs text-\[var\(--text-secondary\)\] mt-1 line-clamp-2 leading-relaxed">\$\{t\.description\}</p>',
              '<p class="text-xs text-[var(--text-secondary)] mt-1 line-clamp-2 leading-relaxed">${escapeHtml(t.description)}</p>', code)
code = re.sub(r'<h3 class="text-base font-bold font-display text-\[var\(--text-primary\)\]">\$\{tool\.name\}</h3>',
              '<h3 class="text-base font-bold font-display text-[var(--text-primary)]">${escapeHtml(tool.name)}</h3>', code)
code = re.sub(r'<p class="text-xs text-\[var\(--text-secondary\)\] line-clamp-1">\$\{tool\.description\}</p>',
              '<p class="text-xs text-[var(--text-secondary)] line-clamp-1">${escapeHtml(tool.description)}</p>', code)
code = re.sub(r'<h4 class="text-xs font-semibold text-\[var\(--text-primary\)\]">\$\{a\.title\}</h4>',
              '<h4 class="text-xs font-semibold text-[var(--text-primary)]">${escapeHtml(a.title)}</h4>', code)
code = re.sub(r'<p class="text-\[11px\] text-\[var\(--text-secondary\)\] leading-relaxed">\$\{a\.description\}</p>',
              '<p class="text-[11px] text-[var(--text-secondary)] leading-relaxed">${escapeHtml(a.description)}</p>', code)

with open('software/ui/js/app.js', 'w', encoding='utf-8') as f:
    f.write(code)

print("Batch replacement complete.")
