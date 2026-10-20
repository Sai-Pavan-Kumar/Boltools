/* Menu file reading, file-type matching and launching, shared by the menu objects. */
#pragma once
#define COBJMACROS
#define WIN32_LEAN_AND_MEAN
#ifndef _WIN32_WINNT
#define _WIN32_WINNT 0x0A00
#endif
#include <windows.h>
#include <shobjidl.h>

#define MAX_TOOLS 48
#define MENU_FILE_LIMIT 65536
#define COMMAND_LINE_LIMIT 32767

typedef struct {
    WCHAR id[64];
    WCHAR label[128];
    int minFiles;
    WCHAR exts[512];
} ToolEntry;

typedef struct {
    WCHAR command[1024];
    WCHAR workDir[MAX_PATH];
    WCHAR icon[MAX_PATH + 8];
    int count;
    ToolEntry tools[MAX_TOOLS];
} MenuConfig;

BOOL LoadConfig(MenuConfig *cfg);
BOOL ToolFits(const ToolEntry *tool, IShellItemArray *items);
HRESULT LaunchTool(const MenuConfig *cfg, const ToolEntry *tool, IShellItemArray *items);
