/*
 * "Open with Boltools" in the Windows 11 top-level right-click menu.
 *
 * Explorer loads this DLL through the sparse package in AppxManifest.xml. It never
 * hard-codes tools: the app writes %USERPROFILE%\.boltools\explorer-menu.txt from
 * the tools list, and every hover re-reads it. A photo therefore only ever sees
 * photo tools, and a new tool appears without rebuilding this DLL.
 *
 * Menu file format (UTF-8):
 *   line 1  command prefix that launches Boltools
 *   line 2  working folder for that command
 *   line 3  icon path ("C:\...\Boltools.ico" or "...exe,0")
 *   then    tool_id|Menu label|min_files|ext,ext,...   ("*" = any file)
 */
#include "menu_config.h"
#include <shlobj.h>
#include <shlwapi.h>

/* {B01700E5-6C1A-4F3E-9B7D-3A5E2F1C8D40}; must match AppxManifest.xml. */
static const CLSID CLSID_BoltoolsMenu = {0xb01700e5, 0x6c1a, 0x4f3e, {0x9b, 0x7d, 0x3a, 0x5e, 0x2f, 0x1c, 0x8d, 0x40}};

static LONG g_objects;
static LONG g_locks;

/* ---------- IExplorerCommand: root (-1) and one per tool (index) ---------- */

typedef struct {
    IExplorerCommand iface;
    LONG refs;
    int toolIndex;
} Command;

typedef struct {
    IEnumExplorerCommand iface;
    LONG refs;
    int pos;
    int count;
} CommandEnum;

static HRESULT CreateCommand(int toolIndex, REFIID riid, void **out);
static HRESULT CreateEnum(int count, int pos, IEnumExplorerCommand **out);

static HRESULT STDMETHODCALLTYPE Cmd_QueryInterface(IExplorerCommand *This, REFIID riid, void **out) {
    if (IsEqualIID(riid, &IID_IUnknown) || IsEqualIID(riid, &IID_IExplorerCommand)) {
        *out = This;
        IExplorerCommand_AddRef(This);
        return S_OK;
    }
    *out = NULL;
    return E_NOINTERFACE;
}

static ULONG STDMETHODCALLTYPE Cmd_AddRef(IExplorerCommand *This) {
    return InterlockedIncrement(&((Command *)This)->refs);
}

static ULONG STDMETHODCALLTYPE Cmd_Release(IExplorerCommand *This) {
    Command *self = (Command *)This;
    LONG left = InterlockedDecrement(&self->refs);
    if (left == 0) {
        HeapFree(GetProcessHeap(), 0, self);
        InterlockedDecrement(&g_objects);
    }
    return left;
}

static MenuConfig g_cfg; /* Explorer calls menu objects on one STA thread. */

static HRESULT STDMETHODCALLTYPE Cmd_GetTitle(IExplorerCommand *This, IShellItemArray *items, LPWSTR *name) {
    Command *self = (Command *)This;
    if (self->toolIndex < 0) return SHStrDupW(L"Open with Boltools", name);
    if (!LoadConfig(&g_cfg) || self->toolIndex >= g_cfg.count) return E_FAIL;
    return SHStrDupW(g_cfg.tools[self->toolIndex].label, name);
}

static HRESULT STDMETHODCALLTYPE Cmd_GetIcon(IExplorerCommand *This, IShellItemArray *items, LPWSTR *icon) {
    Command *self = (Command *)This;
    if (self->toolIndex >= 0 || !LoadConfig(&g_cfg) || !g_cfg.icon[0]) { *icon = NULL; return E_NOTIMPL; }
    return SHStrDupW(g_cfg.icon, icon);
}

static HRESULT STDMETHODCALLTYPE Cmd_GetToolTip(IExplorerCommand *This, IShellItemArray *items, LPWSTR *tip) {
    *tip = NULL;
    return E_NOTIMPL;
}

static HRESULT STDMETHODCALLTYPE Cmd_GetCanonicalName(IExplorerCommand *This, GUID *guid) {
    *guid = GUID_NULL;
    return E_NOTIMPL;
}

static HRESULT STDMETHODCALLTYPE Cmd_GetState(IExplorerCommand *This, IShellItemArray *items, BOOL slowOk, EXPCMDSTATE *state) {
    Command *self = (Command *)This;
    *state = ECS_HIDDEN;
    if (!LoadConfig(&g_cfg)) return S_OK;
    if (self->toolIndex >= 0) {
        if (self->toolIndex < g_cfg.count && ToolFits(&g_cfg.tools[self->toolIndex], items)) *state = ECS_ENABLED;
        return S_OK;
    }
    for (int i = 0; i < g_cfg.count; i++) {
        if (ToolFits(&g_cfg.tools[i], items)) { *state = ECS_ENABLED; break; }
    }
    return S_OK;
}

static HRESULT STDMETHODCALLTYPE Cmd_Invoke(IExplorerCommand *This, IShellItemArray *items, IBindCtx *ctx) {
    Command *self = (Command *)This;
    if (self->toolIndex < 0 || !items) return S_OK;
    if (!LoadConfig(&g_cfg) || self->toolIndex >= g_cfg.count) return E_FAIL;
    return LaunchTool(&g_cfg, &g_cfg.tools[self->toolIndex], items);
}

static HRESULT STDMETHODCALLTYPE Cmd_GetFlags(IExplorerCommand *This, EXPCMDFLAGS *flags) {
    *flags = ((Command *)This)->toolIndex < 0 ? ECF_HASSUBCOMMANDS : ECF_DEFAULT;
    return S_OK;
}

static HRESULT STDMETHODCALLTYPE Cmd_EnumSubCommands(IExplorerCommand *This, IEnumExplorerCommand **out) {
    *out = NULL;
    if (((Command *)This)->toolIndex >= 0) return E_NOTIMPL;
    if (!LoadConfig(&g_cfg)) return E_FAIL;
    return CreateEnum(g_cfg.count, 0, out);
}

static IExplorerCommandVtbl g_cmdVtbl = {
    Cmd_QueryInterface, Cmd_AddRef, Cmd_Release, Cmd_GetTitle, Cmd_GetIcon, Cmd_GetToolTip,
    Cmd_GetCanonicalName, Cmd_GetState, Cmd_Invoke, Cmd_GetFlags, Cmd_EnumSubCommands};

static HRESULT CreateCommand(int toolIndex, REFIID riid, void **out) {
    Command *self = (Command *)HeapAlloc(GetProcessHeap(), HEAP_ZERO_MEMORY, sizeof(Command));
    if (!self) return E_OUTOFMEMORY;
    self->iface.lpVtbl = &g_cmdVtbl;
    self->refs = 1;
    self->toolIndex = toolIndex;
    InterlockedIncrement(&g_objects);
    HRESULT hr = Cmd_QueryInterface(&self->iface, riid, out);
    Cmd_Release(&self->iface);
    return hr;
}

/* ---------- IEnumExplorerCommand ---------- */

static HRESULT STDMETHODCALLTYPE Enum_QueryInterface(IEnumExplorerCommand *This, REFIID riid, void **out) {
    if (IsEqualIID(riid, &IID_IUnknown) || IsEqualIID(riid, &IID_IEnumExplorerCommand)) {
        *out = This;
        IEnumExplorerCommand_AddRef(This);
        return S_OK;
    }
    *out = NULL;
    return E_NOINTERFACE;
}

static ULONG STDMETHODCALLTYPE Enum_AddRef(IEnumExplorerCommand *This) {
    return InterlockedIncrement(&((CommandEnum *)This)->refs);
}

static ULONG STDMETHODCALLTYPE Enum_Release(IEnumExplorerCommand *This) {
    CommandEnum *self = (CommandEnum *)This;
    LONG left = InterlockedDecrement(&self->refs);
    if (left == 0) {
        HeapFree(GetProcessHeap(), 0, self);
        InterlockedDecrement(&g_objects);
    }
    return left;
}

static HRESULT STDMETHODCALLTYPE Enum_Next(IEnumExplorerCommand *This, ULONG want, IExplorerCommand **items, ULONG *got) {
    CommandEnum *self = (CommandEnum *)This;
    ULONG n = 0;
    while (n < want && self->pos < self->count) {
        if (FAILED(CreateCommand(self->pos, &IID_IExplorerCommand, (void **)&items[n]))) break;
        self->pos++;
        n++;
    }
    if (got) *got = n;
    return n == want ? S_OK : S_FALSE;
}

static HRESULT STDMETHODCALLTYPE Enum_Skip(IEnumExplorerCommand *This, ULONG skip) {
    CommandEnum *self = (CommandEnum *)This;
    self->pos = min(self->count, self->pos + (int)skip);
    return self->pos < self->count ? S_OK : S_FALSE;
}

static HRESULT STDMETHODCALLTYPE Enum_Reset(IEnumExplorerCommand *This) {
    ((CommandEnum *)This)->pos = 0;
    return S_OK;
}

static HRESULT STDMETHODCALLTYPE Enum_Clone(IEnumExplorerCommand *This, IEnumExplorerCommand **out) {
    CommandEnum *self = (CommandEnum *)This;
    return CreateEnum(self->count, self->pos, out);
}

static IEnumExplorerCommandVtbl g_enumVtbl = {
    Enum_QueryInterface, Enum_AddRef, Enum_Release, Enum_Next, Enum_Skip, Enum_Reset, Enum_Clone};

static HRESULT CreateEnum(int count, int pos, IEnumExplorerCommand **out) {
    CommandEnum *self = (CommandEnum *)HeapAlloc(GetProcessHeap(), HEAP_ZERO_MEMORY, sizeof(CommandEnum));
    if (!self) return E_OUTOFMEMORY;
    self->iface.lpVtbl = &g_enumVtbl;
    self->refs = 1;
    self->count = count;
    self->pos = pos;
    InterlockedIncrement(&g_objects);
    *out = &self->iface;
    return S_OK;
}

/* ---------- class factory and exports ---------- */

static HRESULT STDMETHODCALLTYPE Factory_QueryInterface(IClassFactory *This, REFIID riid, void **out) {
    if (IsEqualIID(riid, &IID_IUnknown) || IsEqualIID(riid, &IID_IClassFactory)) {
        *out = This;
        return S_OK;
    }
    *out = NULL;
    return E_NOINTERFACE;
}

static ULONG STDMETHODCALLTYPE Factory_AddRef(IClassFactory *This) { return 2; }
static ULONG STDMETHODCALLTYPE Factory_Release(IClassFactory *This) { return 1; }

static HRESULT STDMETHODCALLTYPE Factory_CreateInstance(IClassFactory *This, IUnknown *outer, REFIID riid, void **out) {
    *out = NULL;
    if (outer) return CLASS_E_NOAGGREGATION;
    return CreateCommand(-1, riid, out);
}

static HRESULT STDMETHODCALLTYPE Factory_LockServer(IClassFactory *This, BOOL lock) {
    if (lock) InterlockedIncrement(&g_locks);
    else InterlockedDecrement(&g_locks);
    return S_OK;
}

static IClassFactoryVtbl g_factoryVtbl = {
    Factory_QueryInterface, Factory_AddRef, Factory_Release, Factory_CreateInstance, Factory_LockServer};
static IClassFactory g_factory = {&g_factoryVtbl};

HRESULT STDAPICALLTYPE DllGetClassObject(REFCLSID clsid, REFIID riid, void **out) {
    if (!IsEqualCLSID(clsid, &CLSID_BoltoolsMenu)) { *out = NULL; return CLASS_E_CLASSNOTAVAILABLE; }
    return Factory_QueryInterface(&g_factory, riid, out);
}

HRESULT STDAPICALLTYPE DllCanUnloadNow(void) {
    return (g_objects == 0 && g_locks == 0) ? S_OK : S_FALSE;
}

BOOL WINAPI DllMain(HINSTANCE instance, DWORD reason, LPVOID reserved) {
    if (reason == DLL_PROCESS_ATTACH) DisableThreadLibraryCalls(instance);
    return TRUE;
}
