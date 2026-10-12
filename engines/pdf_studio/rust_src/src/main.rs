//! PDF Studio Engine v0.1 (Rust)
//! JSON-lines CLI wrapping bundled QPDF with cancel support, atomic outputs, and Telugu path fallback.

use serde::{Deserialize, Serialize};
use std::fs::{self, File, OpenOptions};
use std::io::{self, BufRead, BufReader, Write};
use std::path::{Path, PathBuf};
use std::process::{Child, Command, Stdio};
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::mpsc::{channel, Receiver};
use std::sync::Arc;
use std::thread;
use std::time::{Duration, Instant};

#[derive(Deserialize)]
struct JobRequest {
    #[serde(default)]
    subcommand: String,
    #[serde(default)]
    input_files: Vec<String>,
    #[serde(default)]
    options: serde_json::Value,
    #[serde(default)]
    output_dir: Option<String>,
}

#[derive(Serialize)]
struct ProgressMessage<'a> {
    #[serde(rename = "type")]
    msg_type: &'a str,
    percent: i32,
    #[serde(skip_serializing_if = "Option::is_none")]
    indeterminate: Option<bool>,
    message: String,
}

#[derive(Serialize)]
struct LogMessage<'a> {
    #[serde(rename = "type")]
    msg_type: &'a str,
    #[serde(skip_serializing_if = "Option::is_none")]
    level: Option<&'a str>,
    message: String,
}

#[derive(Serialize)]
struct DoneMessage<'a> {
    #[serde(rename = "type")]
    msg_type: &'a str,
    outputs: Vec<String>,
    stats: serde_json::Value,
}

#[derive(Serialize)]
struct ErrorMessage<'a> {
    #[serde(rename = "type")]
    msg_type: &'a str,
    code: String,
    message: String,
}

fn emit_json<T: Serialize>(val: &T) {
    if let Ok(serialized) = serde_json::to_string(val) {
        let stdout = io::stdout();
        let mut handle = stdout.lock();
        let _ = writeln!(handle, "{}", serialized);
        let _ = handle.flush();
    }
}

fn emit_progress(percent: i32, indeterminate: bool, msg: &str) {
    emit_json(&ProgressMessage {
        msg_type: "progress",
        percent,
        indeterminate: if indeterminate { Some(true) } else { None },
        message: msg.to_string(),
    });
}

fn emit_log(msg: &str, level: Option<&str>) {
    emit_json(&LogMessage {
        msg_type: "log",
        level,
        message: msg.to_string(),
    });
}

fn emit_done(outputs: Vec<String>, stats: serde_json::Value) {
    emit_json(&DoneMessage {
        msg_type: "done",
        outputs,
        stats,
    });
}

fn emit_error(code: &str, msg: &str) {
    emit_json(&ErrorMessage {
        msg_type: "error",
        code: code.to_string(),
        message: msg.to_string(),
    });
}

/// Locates bundled `qpdf.exe` strictly relative to this executable. Never touches PATH.
fn get_qpdf_binary_path() -> io::Result<PathBuf> {
    let cur_exe = std::env::current_exe()?;
    let exe_dir = cur_exe.parent().ok_or_else(|| {
        io::Error::new(io::ErrorKind::NotFound, "Failed to resolve executable directory")
    })?;

    let candidates = [
        exe_dir.join("bin").join("qpdf.exe"),
        exe_dir.join("qpdf.exe"),
        exe_dir.join("..").join("bin").join("qpdf.exe"),
    ];

    for c in &candidates {
        if c.is_file() {
            return Ok(c.canonicalize().unwrap_or_else(|_| c.clone()));
        }
    }

    Err(io::Error::new(
        io::ErrorKind::NotFound,
        format!("Bundled qpdf.exe not found near {:?}", exe_dir),
    ))
}

/// Starts background thread to listen for {"cmd":"cancel"} on stdin.
fn spawn_cancel_listener() -> (Arc<AtomicBool>, Receiver<()>) {
    let cancel_flag = Arc::new(AtomicBool::new(false));
    let flag_clone = cancel_flag.clone();
    let (tx, rx) = channel();

    thread::spawn(move || {
        let stdin = io::stdin();
        for line in stdin.lock().lines() {
            if let Ok(l) = line {
                let trimmed = l.trim();
                if trimmed.contains("\"cancel\"") {
                    flag_clone.store(true, Ordering::SeqCst);
                    let _ = tx.send(());
                    break;
                }
            }
        }
    });

    (cancel_flag, rx)
}

/// Runs a command with cancellation monitoring and output line streaming.
fn run_monitored_qpdf(
    mut cmd: Command,
    cancel_flag: &Arc<AtomicBool>,
    mut on_output_line: impl FnMut(&str),
) -> Result<i32, String> {
    cmd.stdout(Stdio::piped());
    cmd.stderr(Stdio::piped());

    let mut child: Child = cmd.spawn().map_err(|e| format!("Failed to spawn qpdf: {}", e))?;
    let stdout = child.stdout.take().ok_or("Failed to open child stdout")?;
    let stderr = child.stderr.take().ok_or("Failed to open child stderr")?;

    let (line_tx, line_rx) = channel();
    let tx_err = line_tx.clone();

    // Reader thread for stdout
    thread::spawn(move || {
        let reader = BufReader::new(stdout);
        for line in reader.lines().flatten() {
            if line_tx.send(line).is_err() {
                break;
            }
        }
    });

    // Reader thread for stderr
    thread::spawn(move || {
        let reader = BufReader::new(stderr);
        for line in reader.lines().flatten() {
            if tx_err.send(line).is_err() {
                break;
            }
        }
    });

    loop {
        if cancel_flag.load(Ordering::SeqCst) {
            let _ = child.kill();
            let _ = child.wait();
            return Err("CANCELLED".to_string());
        }

        match line_rx.recv_timeout(Duration::from_millis(50)) {
            Ok(line) => {
                on_output_line(&line);
            }
            Err(std::sync::mpsc::RecvTimeoutError::Timeout) => {
                // Check if child has exited
                if let Ok(Some(status)) = child.try_wait() {
                    // Drain any remaining lines
                    while let Ok(line) = line_rx.try_recv() {
                        on_output_line(&line);
                    }
                    if cancel_flag.load(Ordering::SeqCst) {
                        return Err("CANCELLED".to_string());
                    }
                    return Ok(status.code().unwrap_or(-1));
                }
            }
            Err(std::sync::mpsc::RecvTimeoutError::Disconnected) => {
                break;
            }
        }
    }

    let status = child.wait().map_err(|e| format!("Failed to wait for qpdf: {}", e))?;
    if cancel_flag.load(Ordering::SeqCst) {
        return Err("CANCELLED".to_string());
    }
    Ok(status.code().unwrap_or(-1))
}

fn parse_qpdf_progress(line: &str) -> Option<i32> {
    if line.contains("qpdf:") {
        if let Some(pct_idx) = line.find('%') {
            if let Some(open_paren) = line[..pct_idx].rfind('(') {
                if let Ok(pct) = line[open_paren + 1..pct_idx].trim().parse::<i32>() {
                    return Some(pct);
                }
            }
        }
    }
    None
}

/// Checks if a file requires a password or is valid.
fn inspect_pdf_file(qpdf_bin: &Path, file_path: &Path) -> Result<u32, (String, String)> {
    if !file_path.is_file() {
        return Err((
            "FILE_NOT_FOUND".to_string(),
            format!("File not found: {:?}", file_path.file_name().unwrap_or_default()),
        ));
    }

    if let Ok(meta) = fs::metadata(file_path) {
        if meta.len() == 0 {
            return Err((
                "EMPTY_FILE".to_string(),
                format!("File '{:?}' is 0 bytes.", file_path.file_name().unwrap_or_default()),
            ));
        }
    }

    // 1. Check if password required
    // qpdf --requires-password exit codes:
    // 0: a password, other than as supplied, is required (locked!)
    // 2: the file is not encrypted
    // 3: the file is encrypted, and empty/correct password matches
    let pw_check = Command::new(qpdf_bin)
        .arg("--requires-password")
        .arg(file_path)
        .output();

    if let Ok(out) = pw_check {
        if out.status.code() == Some(0) {
            return Err((
                "PASSWORD_PROTECTED".to_string(),
                format!(
                    "File '{}' is password-protected. Locked files cannot be processed.",
                    file_path.file_name().unwrap_or_default().to_string_lossy()
                ),
            ));
        }
    }

    // 2. Query page count via --show-npages
    let pages_check = Command::new(qpdf_bin)
        .arg("--show-npages")
        .arg(file_path)
        .output();

    match pages_check {
        Ok(out) => {
            let code = out.status.code().unwrap_or(2);
            if code == 0 || code == 3 {
                let s = String::from_utf8_lossy(&out.stdout).trim().to_string();
                if let Ok(p) = s.parse::<u32>() {
                    if p == 0 {
                        return Err((
                            "ZERO_PAGES".to_string(),
                            format!("File '{}' has 0 pages.", file_path.file_name().unwrap_or_default().to_string_lossy()),
                        ));
                    }
                    return Ok(p);
                }
            }

            // Check if failure is due to password requirement
            let err_msg = String::from_utf8_lossy(&out.stderr).to_lowercase();
            if err_msg.contains("password") {
                return Err((
                    "PASSWORD_PROTECTED".to_string(),
                    format!(
                        "File '{}' is password-protected. Locked files cannot be processed.",
                        file_path.file_name().unwrap_or_default().to_string_lossy()
                    ),
                ));
            }

            // Failed: run full --check as diagnostic fallback only after failure
            let check_diag = Command::new(qpdf_bin)
                .arg("--check")
                .arg(file_path)
                .output();
            let diag_msg = check_diag
                .map(|d| String::from_utf8_lossy(&d.stderr).trim().to_string())
                .unwrap_or_else(|_| "Corrupted PDF syntax".to_string());

            Err((
                "CORRUPT_PDF".to_string(),
                format!(
                    "File '{}' is damaged or corrupt: {}",
                    file_path.file_name().unwrap_or_default().to_string_lossy(),
                    if diag_msg.is_empty() { "Invalid PDF header/trailer." } else { &diag_msg }
                ),
            ))
        }
        Err(e) => Err((
            "EXEC_ERROR".to_string(),
            format!("Failed to execute qpdf on '{}': {}", file_path.display(), e),
        )),
    }
}

/// Helper to ensure input files can be opened by QPDF, mapping non-ASCII/Telugu paths to safe temp ASCII files if necessary.
struct SafePathMapping {
    original: PathBuf,
    active: PathBuf,
    is_temp: bool,
}

impl SafePathMapping {
    fn new(path: &Path, tmp_dir: &Path) -> io::Result<Self> {
        let path_buf = path.to_path_buf();
        let is_ascii = path.to_string_lossy().is_ascii();

        if is_ascii {
            Ok(Self {
                original: path_buf.clone(),
                active: path_buf,
                is_temp: false,
            })
        } else {
            // Copy to ASCII temp file
            fs::create_dir_all(tmp_dir)?;
            let safe_name = format!("in_{:x}.pdf", md5_simple(&path.to_string_lossy()));
            let temp_path = tmp_dir.join(safe_name);
            fs::copy(path, &temp_path)?;
            Ok(Self {
                original: path_buf,
                active: temp_path,
                is_temp: true,
            })
        }
    }

    fn cleanup(&self) {
        if self.is_temp && self.active.is_file() {
            let _ = fs::remove_file(&self.active);
        }
    }
}

fn md5_simple(s: &str) -> u64 {
    let mut hash: u64 = 0xcbf29ce484222325;
    for b in s.as_bytes() {
        hash ^= *b as u64;
        hash = hash.wrapping_mul(0x100000001b3);
    }
    hash
}

/// Reserves an output file atomically without race condition, using (1), (2) numbering if exists.
fn reserve_output_file(target_dir: &Path, base_name: &str, ext: &str) -> io::Result<(PathBuf, File)> {
    fs::create_dir_all(target_dir)?;
    let mut candidate = target_dir.join(format!("{}.{}", base_name, ext));
    let mut counter = 1;

    loop {
        match OpenOptions::new().write(true).create_new(true).open(&candidate) {
            Ok(f) => return Ok((candidate, f)),
            Err(e) if e.kind() == io::ErrorKind::AlreadyExists => {
                candidate = target_dir.join(format!("{} ({}).{}", base_name, counter, ext));
                counter += 1;
            }
            Err(e) => return Err(e),
        }
    }
}

/// Cleans up leftover .boltools_tmp directories from prior interrupted runs.
fn cleanup_leftover_tmp(dir: &Path) {
    let tmp = dir.join(".boltools_tmp");
    if tmp.is_dir() {
        let _ = fs::remove_dir_all(&tmp);
    }
}

// ── Merge Operation ──────────────────────────────────────────────────────────
fn do_merge(req: JobRequest, qpdf_bin: &Path, cancel_flag: &Arc<AtomicBool>) -> Result<(), i32> {
    if req.input_files.is_empty() {
        emit_error("NO_INPUT_FILES", "Please select at least one PDF file to merge.");
        return Err(3);
    }

    let start_time = Instant::now();
    let first_file = PathBuf::from(&req.input_files[0]);
    let out_dir = match &req.output_dir {
        Some(d) if !d.is_empty() => PathBuf::from(d),
        _ => first_file.parent().map(|p| p.to_path_buf()).unwrap_or_else(|| PathBuf::from(".")),
    };

    let tmp_dir = out_dir.join(".boltools_tmp");
    cleanup_leftover_tmp(&out_dir);
    let _ = fs::create_dir_all(&tmp_dir);

    // 1. Pre-flight checks on all files & calculate expected total pages
    emit_progress(-1, true, "Validating input PDF files...");
    let mut mappings = Vec::new();
    let mut total_expected_pages = 0u32;

    for file_str in &req.input_files {
        if cancel_flag.load(Ordering::SeqCst) {
            let _ = fs::remove_dir_all(&tmp_dir);
            return Err(2);
        }
        let p = Path::new(file_str);
        match inspect_pdf_file(qpdf_bin, p) {
            Ok(pages) => {
                total_expected_pages += pages;
                match SafePathMapping::new(p, &tmp_dir) {
                    Ok(m) => mappings.push(m),
                    Err(e) => {
                        emit_error("FILE_ACCESS_ERROR", &format!("Cannot read '{}': {}", p.display(), e));
                        let _ = fs::remove_dir_all(&tmp_dir);
                        return Err(1);
                    }
                }
            }
            Err((code, msg)) => {
                emit_error(&code, &msg);
                let _ = fs::remove_dir_all(&tmp_dir);
                return Err(1);
            }
        }
    }

    emit_log(&format!("All {} files validated successfully (Total pages: {}).", req.input_files.len(), total_expected_pages), None);

    // 2. Reserve destination file
    let custom_name = req.options.get("custom_filename")
        .or_else(|| req.options.get("output_filename"))
        .and_then(|v| v.as_str())
        .map(|s| s.trim())
        .filter(|s| !s.is_empty());

    let (base_name, ext) = if let Some(cname) = custom_name {
        let p = Path::new(cname);
        let s = p.file_stem().unwrap_or_default().to_string_lossy().to_string();
        let e = p.extension().and_then(|ext| ext.to_str()).unwrap_or("pdf");
        (if s.is_empty() { "merged".to_string() } else { s }, e.to_string())
    } else {
        ("merged".to_string(), "pdf".to_string())
    };

    let (final_path, final_file_handle) = match reserve_output_file(&out_dir, &base_name, &ext) {
        Ok(r) => r,
        Err(e) => {
            emit_error("PERMISSION_DENIED", &format!("Cannot write to destination folder '{:?}': {}", out_dir, e));
            let _ = fs::remove_dir_all(&tmp_dir);
            return Err(1);
        }
    };
    drop(final_file_handle); // Release handle so QPDF / rename can write to it

    let temp_merged_path = tmp_dir.join("temp_merge_output.pdf");

    // 3. Build QPDF merge command
    // qpdf --empty --pages input1.pdf input2.pdf ... -- temp_out.pdf
    let mut cmd = Command::new(qpdf_bin);
    cmd.arg("--empty");
    cmd.arg("--pages");
    for m in &mappings {
        cmd.arg(&m.active);
    }
    cmd.arg("--");
    cmd.arg(&temp_merged_path);
    cmd.arg("--progress");

    // 4. Run monitored with progress parser
    let res = run_monitored_qpdf(cmd, cancel_flag, |line| {
        if let Some(pct) = parse_qpdf_progress(line) {
            emit_progress(pct, false, line);
        } else if line.contains("qpdf:") {
            emit_progress(-1, true, line);
        }
    });

    for m in &mappings {
        m.cleanup();
    }

    match res {
        Ok(code) if code == 0 || code == 3 => {
            if code == 3 {
                emit_log("Merge completed with non-fatal PDF warnings.", Some("warn"));
            }
            // 5. Verify output page count
            match inspect_pdf_file(qpdf_bin, &temp_merged_path) {
                Ok(actual_pages) if actual_pages == total_expected_pages => {
                    // Atomic move to final path
                    let _ = fs::rename(&temp_merged_path, &final_path);
                    let _ = fs::remove_dir_all(&tmp_dir);

                    let elapsed_ms = start_time.elapsed().as_millis();
                    let final_size = fs::metadata(&final_path).map(|m| m.len()).unwrap_or(0);

                    emit_progress(100, false, "Merge Complete");
                    emit_done(
                        vec![final_path.to_string_lossy().to_string()],
                        serde_json::json!({
                            "total_time_ms": elapsed_ms,
                            "total_bytes": final_size,
                            "total_pages": actual_pages
                        }),
                    );
                    Ok(())
                }
                Ok(actual) => {
                    let _ = fs::remove_file(&final_path);
                    let _ = fs::remove_dir_all(&tmp_dir);
                    emit_error("PAGE_COUNT_MISMATCH", &format!("Merged PDF page count ({}) did not match expected count ({}).", actual, total_expected_pages));
                    Err(1)
                }
                Err((c, m)) => {
                    let _ = fs::remove_file(&final_path);
                    let _ = fs::remove_dir_all(&tmp_dir);
                    emit_error(&c, &format!("Output validation failed: {}", m));
                    Err(1)
                }
            }
        }
        Err(e) if e == "CANCELLED" => {
            let _ = fs::remove_file(&final_path);
            let _ = fs::remove_dir_all(&tmp_dir);
            emit_error("CANCELLED", "Operation was cancelled by user.");
            Err(2)
        }
        _ => {
            let _ = fs::remove_file(&final_path);
            let _ = fs::remove_dir_all(&tmp_dir);
            emit_error("MERGE_FAILED", "QPDF merge execution failed.");
            Err(1)
        }
    }
}

// ── Split Operation ──────────────────────────────────────────────────────────
fn do_split(req: JobRequest, qpdf_bin: &Path, cancel_flag: &Arc<AtomicBool>) -> Result<(), i32> {
    if req.input_files.is_empty() {
        emit_error("NO_INPUT_FILES", "Please select a PDF file to split.");
        return Err(3);
    }

    let start_time = Instant::now();
    let src_path = PathBuf::from(&req.input_files[0]);
    let out_base_dir = match &req.output_dir {
        Some(d) if !d.is_empty() => PathBuf::from(d),
        _ => src_path.parent().map(|p| p.to_path_buf()).unwrap_or_else(|| PathBuf::from(".")),
    };

    let custom_name = req.options.get("custom_filename")
        .or_else(|| req.options.get("output_filename"))
        .and_then(|v| v.as_str())
        .map(|s| s.trim())
        .filter(|s| !s.is_empty());

    let stem = if let Some(cname) = custom_name {
        let p = Path::new(cname);
        let s = p.file_stem().unwrap_or_default().to_string_lossy().to_string();
        if s.is_empty() { src_path.file_stem().unwrap_or_default().to_string_lossy().to_string() } else { s }
    } else {
        src_path.file_stem().unwrap_or_default().to_string_lossy().to_string()
    };
    let split_folder_name = if stem.ends_with("_split") { stem } else { format!("{}_split", stem) };
    let split_target_dir = out_base_dir.join(&split_folder_name);
    fs::create_dir_all(&split_target_dir).map_err(|e| {
        emit_error("PERMISSION_DENIED", &format!("Cannot create output folder '{:?}': {}", split_target_dir, e));
        1
    })?;

    let tmp_dir = split_target_dir.join(".boltools_tmp");
    cleanup_leftover_tmp(&split_target_dir);
    let _ = fs::create_dir_all(&tmp_dir);

    // 1. Inspect source PDF
    emit_progress(-1, true, "Inspecting document...");
    let total_pages = match inspect_pdf_file(qpdf_bin, &src_path) {
        Ok(p) => p,
        Err((code, msg)) => {
            emit_error(&code, &msg);
            let _ = fs::remove_dir_all(&tmp_dir);
            return Err(1);
        }
    };

    let mapping = SafePathMapping::new(&src_path, &tmp_dir).map_err(|e| {
        emit_error("FILE_ACCESS_ERROR", &format!("Cannot map input file: {}", e));
        1
    })?;

    // 2. Parse split options
    let mode = req.options.get("split_mode").and_then(|v| v.as_str()).unwrap_or("each_page");
    // "each_page", "every_n_pages", "ranges"

    let mut ranges_to_extract: Vec<(String, u32)> = Vec::new(); // (range_str, expected_pages)

    if mode == "each_page" || mode == "every_n" || mode == "every_n_pages" {
        let n = if mode == "each_page" {
            1
        } else {
            let val = req.options.get("every_n").and_then(|v| v.as_u64()).unwrap_or(1) as u32;
            if val == 0 { 1 } else { val }
        };

        emit_log(&format!("Splitting document using high-speed native batch engine (group size: {})...", n), None);
        let pattern = tmp_dir.join("page_%d.pdf");

        let mut cmd = Command::new(qpdf_bin);
        cmd.arg(&mapping.active);
        if n == 1 {
            cmd.arg("--split-pages=1");
        } else {
            cmd.arg(format!("--split-pages={}", n));
        }
        cmd.arg("--progress");
        cmd.arg(pattern.to_string_lossy().to_string());

        let res = run_monitored_qpdf(cmd, cancel_flag, |line| {
            if let Some(pct) = parse_qpdf_progress(line) {
                emit_progress(pct, false, "Extracting pages...");
            }
        });

        match res {
            Ok(code) if code == 0 || code == 3 => {
                // Collect generated temp chunks and move to destination
                let mut temp_files: Vec<PathBuf> = Vec::new();
                if let Ok(entries) = fs::read_dir(&tmp_dir) {
                    for entry in entries.flatten() {
                        let path = entry.path();
                        if path.is_file() && path.extension().and_then(|s| s.to_str()) == Some("pdf") {
                            let fname = path.file_name().unwrap_or_default().to_string_lossy();
                            if fname.starts_with("page_") {
                                temp_files.push(path);
                            }
                        }
                    }
                }
                temp_files.sort();

                let expected_chunks = (total_pages + n - 1) / n;
                if temp_files.len() as u32 != expected_chunks {
                    mapping.cleanup();
                    let _ = fs::remove_dir_all(&tmp_dir);
                    emit_error(
                        "SPLIT_COUNT_MISMATCH",
                        &format!("Expected {} split files, but got {}.", expected_chunks, temp_files.len()),
                    );
                    return Err(1);
                }

                let mut generated_outputs = Vec::new();
                for temp_file in temp_files {
                    let fname = temp_file.file_name().unwrap();
                    let dest_file = split_target_dir.join(fname);
                    let _ = fs::rename(&temp_file, &dest_file);
                    generated_outputs.push(dest_file.to_string_lossy().to_string());
                }

                mapping.cleanup();
                let _ = fs::remove_dir_all(&tmp_dir);

                let elapsed_ms = start_time.elapsed().as_millis();
                let mut total_bytes = 0u64;
                for out in &generated_outputs {
                    if let Ok(m) = fs::metadata(out) {
                        total_bytes += m.len();
                    }
                }

                emit_done(
                    generated_outputs,
                    serde_json::json!({
                        "total_time_ms": elapsed_ms,
                        "total_bytes": total_bytes,
                        "total_chunks": expected_chunks,
                        "output_directory": split_target_dir.to_string_lossy().to_string()
                    }),
                );
                return Ok(());
            }
            Err(e) if e == "CANCELLED" => {
                mapping.cleanup();
                let _ = fs::remove_dir_all(&tmp_dir);
                emit_error("CANCELLED", "Operation was cancelled by user.");
                return Err(2);
            }
            _ => {
                mapping.cleanup();
                let _ = fs::remove_dir_all(&tmp_dir);
                emit_error("SPLIT_FAILED", "Native batch split failed.");
                return Err(1);
            }
        }
    }

    // Otherwise, split by specific ranges (e.g. 1-3, 5, 8-)
    let raw_ranges = req.options.get("ranges").and_then(|v| v.as_str()).unwrap_or("1-");
    for part in raw_ranges.split(',') {
        let clean = part.trim();
        if clean.is_empty() {
            continue;
        }
        if let Some(dash_idx) = clean.find('-') {
            let s_str = clean[..dash_idx].trim();
            let e_str = clean[dash_idx + 1..].trim();
            let start: u32 = s_str.parse().unwrap_or(1);
            let end: u32 = if e_str.is_empty() { total_pages } else { e_str.parse().unwrap_or(total_pages) };
            if start <= end && start <= total_pages {
                let actual_end = end.min(total_pages);
                ranges_to_extract.push((format!("{}-{}", start, actual_end), actual_end - start + 1));
            }
        } else if let Ok(p) = clean.parse::<u32>() {
            if p >= 1 && p <= total_pages {
                ranges_to_extract.push((format!("{}", p), 1));
            }
        }
    }

    if ranges_to_extract.is_empty() {
        mapping.cleanup();
        let _ = fs::remove_dir_all(&tmp_dir);
        emit_error("INVALID_RANGES", "No valid pages or ranges were specified to extract.");
        return Err(3);
    }

    emit_log(&format!("Splitting document into {} chunks...", ranges_to_extract.len()), None);

    let total_chunks = ranges_to_extract.len();
    let pad_width = if total_chunks >= 100 { 3 } else if total_chunks >= 10 { 2 } else { 1 };
    let mut generated_outputs = Vec::new();

    for (idx, (range_str, exp_pages)) in ranges_to_extract.iter().enumerate() {
        if cancel_flag.load(Ordering::SeqCst) {
            mapping.cleanup();
            let _ = fs::remove_dir_all(&tmp_dir);
            emit_error("CANCELLED", "Operation was cancelled by user.");
            return Err(2);
        }

        let chunk_name = format!("page_{:0width$}", idx + 1, width = pad_width);
        let temp_chunk = tmp_dir.join(format!("{}.pdf", chunk_name));
        let dest_chunk = split_target_dir.join(format!("{}.pdf", chunk_name));

        // qpdf mapping.active --pages . range_str -- temp_chunk
        let mut cmd = Command::new(qpdf_bin);
        cmd.arg(&mapping.active);
        cmd.arg("--pages");
        cmd.arg(".");
        cmd.arg(range_str);
        cmd.arg("--");
        cmd.arg(&temp_chunk);

        let res = run_monitored_qpdf(cmd, cancel_flag, |_| {});
        match res {
            Ok(code) if code == 0 || code == 3 => {
                // Verify output page count
                if let Ok(actual) = inspect_pdf_file(qpdf_bin, &temp_chunk) {
                    if actual == *exp_pages {
                        let _ = fs::rename(&temp_chunk, &dest_chunk);
                        generated_outputs.push(dest_chunk.to_string_lossy().to_string());
                        let pct = (((idx + 1) as f32 / total_chunks as f32) * 100.0) as i32;
                        emit_progress(pct, false, &format!("Extracted chunk {} of {}", idx + 1, total_chunks));
                    } else {
                        mapping.cleanup();
                        let _ = fs::remove_dir_all(&tmp_dir);
                        emit_error("PAGE_COUNT_MISMATCH", &format!("Chunk '{}' expected {} pages, got {}", chunk_name, exp_pages, actual));
                        return Err(1);
                    }
                }
            }
            Err(e) if e == "CANCELLED" => {
                mapping.cleanup();
                let _ = fs::remove_dir_all(&tmp_dir);
                emit_error("CANCELLED", "Operation was cancelled by user.");
                return Err(2);
            }
            _ => {
                mapping.cleanup();
                let _ = fs::remove_dir_all(&tmp_dir);
                emit_error("SPLIT_FAILED", &format!("Failed to split chunk {}", chunk_name));
                return Err(1);
            }
        }
    }

    mapping.cleanup();
    let _ = fs::remove_dir_all(&tmp_dir);

    let elapsed_ms = start_time.elapsed().as_millis();
    let mut total_bytes = 0u64;
    for out in &generated_outputs {
        if let Ok(m) = fs::metadata(out) {
            total_bytes += m.len();
        }
    }

    emit_progress(100, false, "Split Complete");
    emit_done(
        generated_outputs,
        serde_json::json!({
            "total_time_ms": elapsed_ms,
            "total_bytes": total_bytes,
            "total_chunks": total_chunks,
            "output_directory": split_target_dir.to_string_lossy().to_string()
        }),
    );

    Ok(())
}

// ── Info Operation ───────────────────────────────────────────────────────────
fn do_info(req: JobRequest, qpdf_bin: &Path) -> Result<(), i32> {
    if req.input_files.is_empty() {
        emit_error("NO_INPUT_FILES", "No file provided for inspection.");
        return Err(3);
    }
    for file_str in &req.input_files {
        let p = Path::new(file_str);
        match inspect_pdf_file(qpdf_bin, p) {
            Ok(pages) => {
                let sz = fs::metadata(p).map(|m| m.len()).unwrap_or(0);
                emit_json(&serde_json::json!({
                    "type": "info",
                    "file": p.to_string_lossy().to_string(),
                    "pages": pages,
                    "size_bytes": sz,
                    "is_locked": false
                }));
            }
            Err((code, msg)) => {
                let is_locked = code == "PASSWORD_PROTECTED";
                emit_json(&serde_json::json!({
                    "type": "info",
                    "file": p.to_string_lossy().to_string(),
                    "pages": 0,
                    "size_bytes": fs::metadata(p).map(|m| m.len()).unwrap_or(0),
                    "is_locked": is_locked,
                    "error_code": code,
                    "error_message": msg
                }));
            }
        }
    }
    Ok(())
}

// ── Main Entrypoint ──────────────────────────────────────────────────────────
fn main() {
    let args: Vec<String> = std::env::args().collect();

    let qpdf_bin = match get_qpdf_binary_path() {
        Ok(p) => p,
        Err(e) => {
            emit_error("QPDF_NOT_FOUND", &format!("Bundled qpdf.exe could not be found: {}", e));
            std::process::exit(1);
        }
    };

    // Read single JSON request from stdin FIRST
    let stdin = io::stdin();
    let mut input_json = String::new();
    if let Err(e) = stdin.lock().read_line(&mut input_json) {
        emit_error("INPUT_ERROR", &format!("Failed to read request from stdin: {}", e));
        std::process::exit(3);
    }

    let mut req: JobRequest = match serde_json::from_str(&input_json) {
        Ok(r) => r,
        Err(e) => {
            // Also allow subcommand via argv[1] if payload is wrapped
            let sub = args.get(1).map(|s| s.as_str()).unwrap_or("");
            emit_error("INVALID_PAYLOAD", &format!("JSON request syntax error: {} (subcommand: {})", e, sub));
            std::process::exit(3);
        }
    };

    // If subcommand is empty, resolve from options: e.g. options.mode ("merge" or "split")
    if req.subcommand.is_empty() {
        if let Some(m) = req.options.get("mode").and_then(|v| v.as_str()) {
            req.subcommand = m.to_string();
        } else if let Some(sub) = req.options.get("subcommand").and_then(|v| v.as_str()) {
            req.subcommand = sub.to_string();
        } else if let Some(arg_sub) = args.get(1) {
            req.subcommand = arg_sub.clone();
        }
    }

    // Now spawn cancel listener for subsequent lines (e.g. {"cmd":"cancel"})
    let (cancel_flag, _) = spawn_cancel_listener();

    let result = match req.subcommand.as_str() {
        "merge" => do_merge(req, &qpdf_bin, &cancel_flag),
        "split" => do_split(req, &qpdf_bin, &cancel_flag),
        "info" => do_info(req, &qpdf_bin),
        unknown => {
            emit_error("UNKNOWN_SUBCOMMAND", &format!("Unknown subcommand: '{}'. Supported: merge, split, info", unknown));
            Err(3)
        }
    };

    match result {
        Ok(_) => std::process::exit(0),
        Err(code) => std::process::exit(code),
    }
}
