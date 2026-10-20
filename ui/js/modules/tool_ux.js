/**
 * Tool UX copy: the one place that says how each tool talks to people.
 * Start-button verbs, what files are accepted, and which tool makes sense
 * next for a given output. namesOutput: false hides the file-name field (each file
 * keeps its own name); 'single' shows it only when exactly one file is added. Adding a tool = adding an entry here.
 */
(function () {
  const TOOLS = {
    pdf_merge: { verb: 'Merge', noun: 'PDF', minFiles: 2, minReason: 'Add at least 2 PDFs to merge.', limits: 'PDF only · as many files as you like', before: 'Many PDFs become one' },
    pdf_split: { verb: 'Split', noun: 'PDF', minFiles: 1, limits: 'One PDF at a time', before: 'One PDF becomes several' },
    pdf_compress: { verb: 'Compress', noun: 'PDF', minFiles: 1, limits: 'PDF only · many files at once', before: 'Big PDFs become small ones' },
    pdf_converter: { namesOutput: false, verb: 'Convert', noun: 'file', minFiles: 1, limits: 'PDF, PNG or JPG', before: 'PDF pages become images' },
    image_webp_compress: { namesOutput: 'single', verb: 'Compress', noun: 'image', minFiles: 1, limits: 'PNG, JPG, BMP or WEBP · many at once', before: 'Big photos become small ones' },
    video_compressor: { namesOutput: 'single', verb: 'Compress', noun: 'video', minFiles: 1, maxFiles: 1, maxReason: 'One video at a time for now.', limits: 'MP4, MOV, MKV, WEBM and more', before: 'Big videos become small ones' },
    media_audio_extractor: { namesOutput: 'single', verb: 'Extract audio from', noun: 'file', minFiles: 1, limits: 'Any video or audio file', before: 'Video or audio becomes MP3, WAV, AAC or FLAC' },
    system_batch_rename: { namesOutput: false, verb: 'Rename', noun: 'file', minFiles: 1, limits: 'Any file type · many at once', before: 'Messy names become tidy' },
    subtitle_animator: { namesOutput: false, verb: 'Add captions to', noun: 'video', minFiles: 1, limits: 'A video plus an SRT or VTT file', before: 'Plain video gets animated captions' }
  };

  const FALLBACK = { verb: 'Process', noun: 'file', minFiles: 1, limits: '', before: '' };

  // Suggestions follow the output's type, so the user keeps going with the file they just made.
  const NEXT_BY_KIND = {
    pdf: [
      { toolId: 'pdf_compress', title: 'Compress this PDF', why: 'Smaller for email and upload portals' },
      { toolId: 'pdf_converter', title: 'Turn pages into images', why: 'For WhatsApp, slides or posts' },
      { toolId: 'pdf_split', title: 'Split this PDF', why: 'Take some pages back out' }
    ],
    image: [
      { toolId: 'image_webp_compress', title: 'Compress these images', why: 'Much smaller, same look' }
    ],
    video: [
      { toolId: 'video_compressor', title: 'Compress this video', why: 'Easier to share and store' },
      { toolId: 'media_audio_extractor', title: 'Pull the audio out', why: 'Save it as MP3' },
      { toolId: 'subtitle_animator', title: 'Add captions', why: 'Animated subtitles for reels' }
    ]
  };

  const KIND_BY_EXT = {
    pdf: 'pdf',
    png: 'image', jpg: 'image', jpeg: 'image', bmp: 'image',
    mp4: 'video', mov: 'video', mkv: 'video', webm: 'video', avi: 'video', m4v: 'video'
  };

  function get(toolId) {
    return TOOLS[toolId] || { ...FALLBACK, ...(ToolSettings.ux(toolId) || {}) };
  }

  function startLabel(toolId, fileCount) {
    const tool = get(toolId);
    const count = Math.max(fileCount, 1);
    return `${tool.verb} ${count} ${tool.noun}${count === 1 ? '' : 's'}`;
  }

  function blockedReason(toolId, fileCount) {
    const tool = get(toolId);
    if (tool.maxFiles && fileCount > tool.maxFiles) return tool.maxReason || '';
    return fileCount > 0 && fileCount < tool.minFiles ? tool.minReason || '' : '';
  }

  function nextSteps(outputs, currentToolId, isAvailable) {
    const first = String(outputs[0] || '');
    const kind = KIND_BY_EXT[(first.split('.').pop() || '').toLowerCase()];
    const usable = outputs.filter(path => KIND_BY_EXT[(String(path).split('.').pop() || '').toLowerCase()] === kind);
    return (NEXT_BY_KIND[kind] || [])
      .filter(step => step.toolId !== currentToolId && isAvailable(step.toolId))
      .map(step => ({ ...step, files: usable }));
  }

  window.ToolUX = { get, startLabel, blockedReason, nextSteps };
})();
