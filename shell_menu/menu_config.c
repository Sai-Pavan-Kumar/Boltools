#include "menu_config.h"
#include <shlobj.h>
#include <shlwapi.h>

/* ---------- menu file ---------- */

static void CopyField(WCHAR *dst, size_t cap, const WCHAR *src) {
    lstrcpynW(dst, src ? src : L"", (int)cap);
}

static void ParseTool(MenuConfig *cfg, WCHAR *line) {
    WCHAR *parts[4] = {0};
    int n = 0;
    WCHAR *cursor = line;
    while (n < 4) {
        parts[n++] = cursor;
        WCHAR *bar = wcschr(cursor, L'|');
        if (!bar) break;
        *bar = 0;
        cursor = bar + 1;
    }
    if (n < 4 || cfg->count >= MAX_TOOLS) return;
    ToolEntry *t = &cfg->tools[cfg->count++];
    CopyField(t->id, ARRAYSIZE(t->id), parts[0]);
    CopyField(t->label, ARRAYSIZE(t->label), parts[1]);
    t->minFiles = _wtoi(parts[2]) > 0 ? _wtoi(parts[2]) : 1;
    CopyField(t->exts, ARRAYSIZE(t->exts), parts[3]);
}

/* Returns FALSE when the app has not written the file yet: the menu then stays hidden. */
BOOL LoadConfig(MenuConfig *cfg) {
    WCHAR path[MAX_PATH];
    ZeroMemory(cfg, sizeof(*cfg));
    if (!GetEnvironmentVariableW(L"USERPROFILE", path, MAX_PATH)) return FALSE;
    PathAppendW(path, L".boltools\\explorer-menu.txt");

    HANDLE file = CreateFileW(path, GENERIC_READ, FILE_SHARE_READ | FILE_SHARE_WRITE, NULL, OPEN_EXISTING, 0, NULL);
    if (file == INVALID_HANDLE_VALUE) return FALSE;
    static char raw[MENU_FILE_LIMIT];
    DWORD got = 0;
    BOOL ok = ReadFile(file, raw, MENU_FILE_LIMIT - 1, &got, NULL);
    CloseHandle(file);
    if (!ok || got == 0) return FALSE;

    static WCHAR text[MENU_FILE_LIMIT];
    int len = MultiByteToWideChar(CP_UTF8, 0, raw, (int)got, text, MENU_FILE_LIMIT - 1);
    text[len] = 0;

    int lineNo = 0;
    WCHAR *line = text;
    while (line && *line) {
        WCHAR *next = wcschr(line, L'\n');
        if (next) *next++ = 0;
        size_t l = wcslen(line);
        if (l && line[l - 1] == L'\r') line[l - 1] = 0;
        if (lineNo == 0) CopyField(cfg->command, ARRAYSIZE(cfg->command), line);
        else if (lineNo == 1) CopyField(cfg->workDir, ARRAYSIZE(cfg->workDir), line);
        else if (lineNo == 2) CopyField(cfg->icon, ARRAYSIZE(cfg->icon), line);
        else if (*line) ParseTool(cfg, line);
        lineNo++;
        line = next;
    }
    return cfg->command[0] != 0 && cfg->count > 0;
}

/* ---------- matching ---------- */

static BOOL ExtensionAllowed(const WCHAR *exts, const WCHAR *path) {
    if (lstrcmpW(exts, L"*") == 0) return TRUE;
    const WCHAR *dot = PathFindExtensionW(path);
    if (!dot || !*dot) return FALSE;
    WCHAR ext[32];
    lstrcpynW(ext, dot + 1, ARRAYSIZE(ext));
    CharLowerW(ext);

    const WCHAR *p = exts;
    size_t extLen = wcslen(ext);
    while (*p) {
        const WCHAR *comma = wcschr(p, L',');
        size_t tokenLen = comma ? (size_t)(comma - p) : wcslen(p);
        if (tokenLen == extLen && _wcsnicmp(p, ext, extLen) == 0) return TRUE;
        if (!comma) break;
        p = comma + 1;
    }
    return FALSE;
}

/* Every selected item must be a real file (not inside a ZIP or a phone) the tool can take. */
BOOL ToolFits(const ToolEntry *tool, IShellItemArray *items) {
    DWORD count = 0;
    if (!items || FAILED(IShellItemArray_GetCount(items, &count))) return FALSE;
    if ((int)count < tool->minFiles) return FALSE;
    for (DWORD i = 0; i < count; i++) {
        IShellItem *item = NULL;
        LPWSTR path = NULL;
        BOOL fits = FALSE;
        if (SUCCEEDED(IShellItemArray_GetItemAt(items, i, &item))) {
            SFGAOF attrs = 0;
            IShellItem_GetAttributes(item, SFGAO_FOLDER, &attrs);
            if (!(attrs & SFGAO_FOLDER) && SUCCEEDED(IShellItem_GetDisplayName(item, SIGDN_FILESYSPATH, &path))) {
                fits = ExtensionAllowed(tool->exts, path);
                CoTaskMemFree(path);
            }
            IShellItem_Release(item);
        }
        if (!fits) return FALSE;
    }
    return TRUE;
}

/* ---------- launching ---------- */

static BOOL Append(WCHAR *buf, size_t cap, const WCHAR *text) {
    if (wcslen(buf) + wcslen(text) + 1 >= cap) return FALSE;
    lstrcatW(buf, text);
    return TRUE;
}

HRESULT LaunchTool(const MenuConfig *cfg, const ToolEntry *tool, IShellItemArray *items) {
    WCHAR *cmd = (WCHAR *)HeapAlloc(GetProcessHeap(), HEAP_ZERO_MEMORY, COMMAND_LINE_LIMIT * sizeof(WCHAR));
    if (!cmd) return E_OUTOFMEMORY;
    Append(cmd, COMMAND_LINE_LIMIT, cfg->command);
    Append(cmd, COMMAND_LINE_LIMIT, L" --open-tool ");
    Append(cmd, COMMAND_LINE_LIMIT, tool->id);

    DWORD count = 0;
    IShellItemArray_GetCount(items, &count);
    for (DWORD i = 0; i < count; i++) {
        IShellItem *item = NULL;
        LPWSTR path = NULL;
        if (FAILED(IShellItemArray_GetItemAt(items, i, &item))) continue;
        if (SUCCEEDED(IShellItem_GetDisplayName(item, SIGDN_FILESYSPATH, &path))) {
            /* Too many files for one command line: open with the ones that fit. */
            BOOL fitted = Append(cmd, COMMAND_LINE_LIMIT, L" \"") && Append(cmd, COMMAND_LINE_LIMIT, path) &&
                          Append(cmd, COMMAND_LINE_LIMIT, L"\"");
            CoTaskMemFree(path);
            if (!fitted) { IShellItem_Release(item); break; }
        }
        IShellItem_Release(item);
    }

    STARTUPINFOW si = {sizeof(si)};
    PROCESS_INFORMATION pi;
    BOOL ok = CreateProcessW(NULL, cmd, NULL, NULL, FALSE, CREATE_NO_WINDOW, NULL,
                             cfg->workDir[0] ? cfg->workDir : NULL, &si, &pi);
    HeapFree(GetProcessHeap(), 0, cmd);
    if (!ok) return HRESULT_FROM_WIN32(GetLastError());
    AllowSetForegroundWindow(pi.dwProcessId);
    CloseHandle(pi.hThread);
    CloseHandle(pi.hProcess);
    return S_OK;
}

