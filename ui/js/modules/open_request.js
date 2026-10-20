// Right-click "Open with Boltools > <action>" lands here: the tool opens on its
// Ready state with the files already in the tray.
const OpenRequest = (() => {
  function open(request) {
    // A notification click opens the store.
    if (request && request.view === 'tool_hub') {
      navigateTo('tool_hub');
      return;
    }
    if (!request || !request.tool_id || !Array.isArray(request.files) || !request.files.length) return;
    if (state.isToolRunning) return; // never swap files under a running job
    openToolWithFiles(request.tool_id, request.files);
  }

  // Called once the catalog is loaded, for the request this window started with.
  async function takeInitial() {
    open(await callBridge('get_launch_request'));
  }

  return { open, takeInitial };
})();

// A second right-click while Boltools is open arrives through the UI dispatcher.
window.handleOpenRequest = (request) => OpenRequest.open(request);
