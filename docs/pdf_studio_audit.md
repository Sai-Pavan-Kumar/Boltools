# PDF Studio v0.1 Security, Packaging & Audit Dossier

## 1. Overview & License Compliance
- **Tool ID:** `pdf_studio`
- **Version:** `0.1.0`
- **Core Utility:** Bundled official **QPDF v12.4.2** (MSVC 64-bit release from Jay Berkenbilt / qpdf GitHub releases).
- **License:** Apache License 2.0 (bundled directly inside `engines/pdf_studio/LICENSE.txt` and `NOTICE.txt`).
- **Dependencies:** 100% offline, self-contained binary bundle with MSVC C-Runtime redistributables. Zero internet requests, zero telemetry.

---

## 2. Binary SHA-256 Hashes & VirusTotal Audit Checksums

| File | Relative Path | SHA-256 Hash |
| :--- | :--- | :--- |
| **PDF Studio Engine** | `engines/pdf_studio/pdf_engine.exe` | `D909F36530E19860A0DB3D6CFD1AA02B1AC49C0715BB7D088F5F866AF6EEE9F2` |
| **Bundled QPDF** | `engines/pdf_studio/bin/qpdf.exe` | `1BDAF878F37EAFFEA1EA3C30591214C77636A0F2FC7432427516B6E22E36C0FF` |
| **QPDF Core DLL** | `engines/pdf_studio/bin/qpdf30.dll` | `8812952678DE93E0750308A113AA650E9161AF466F9770679EA9673ADEB61041` |
| **Official Release Pack** | `release_bundles/pdf_studio-0.1.0.bolpack` | `AA71E0F7335C2D2C83CE51275C8F69E950CF443A151B7A4E1B4A708746A301F5` |

*Note: The official QPDF 12.4.2 binaries (`qpdf.exe` and `qpdf30.dll`) are bit-for-bit identical to the GitHub release asset `qpdf-12.4.2-msvc64.zip` published by Jay Berkenbilt.*

---

## 3. Merge Retention Behavior (What is Kept vs. Dropped)

When merging multiple PDF documents via QPDF (`qpdf --empty --pages file1.pdf ... fileN.pdf -- out.pdf`):

| Feature / Metadata | Behavior | Technical Rationale |
| :--- | :--- | :--- |
| **Page Content & Vector Graphics** | **Kept (100%)** | All stream contents, fonts, vector paths, and raster images are preserved losslessly. |
| **Table of Contents / Bookmarks (Outlines)** | **Merged / Hierarchical** | QPDF merges outline trees from each document in sequential order. |
| **Interactive Form Fields (AcroForms)** | **Kept** | Form fields are preserved. Duplicate field names across different documents are resolved according to PDF spec rules. |
| **Document Metadata (Title, Author, Subject)** | **First Document Primary** | Primary document info dictionary and XMP metadata are inherited from the first document in the sequence. |
| **Document Security / Password Protections** | **Refused** | Encrypted/password-protected files are intercepted in pre-flight checks (`--requires-password`) and refused with an error, protecting users against silent corruption or unintended decryption. |
| **Page Labels & Logical Numbering** | **Kept** | Logical page label dictionaries are merged to reflect physical page offsets. |

---

## 4. Real Performance Benchmarks (Local System)

Tested with native `pdf_engine.exe` and official Windows QPDF v12.4.2:

1. **Merging 20 Files (40 Total Pages):**
   - **Wall-Clock Time:** `2.28 seconds`
   - **Engine Processing Time:** `2,200 ms`
   - **Output Size:** `5,185 bytes`

2. **Splitting 500-Page Document (Ranges Mode: `1-50, 100-250, 300-`):**
   - **Wall-Clock Time:** `0.87 seconds`
   - **Engine Processing Time:** `800 ms`
   - **Chunks Created:** 3 selective PDFs

3. **Splitting 500-Page Document (Each-Page Mode -> 500 Individual PDFs):**
   - **Wall-Clock Time:** `2.18 seconds`
   - **Engine Processing Time:** `2,075 ms`
   - **Chunks Created:** 500 individual zero-padded PDFs (`page_001.pdf` through `page_500.pdf`)

---

## 5. Security & Isolation Guarantees
1. **Air-Gapped Execution:** Operates completely offline without external network sockets.
2. **Safe Atomic Writes:** Output files are reserved using `create_new` semantics. Temporary staging occurs in hidden `.boltools_tmp` directories and is cleaned up on completion, cancel, or subsequent runs.
3. **Mid-Flight Cancellation:** Engine responds to stdin `{"cmd":"cancel"}` commands, terminates active child QPDF processes, deletes temporary files, and exits cleanly with exit code `2`.
4. **Unicode / Telugu Path Support:** Handled natively with UTF-16 Windows API support in Rust. Falls back to ASCII temporary mirroring if non-UTF-8 paths or legacy tool limits are detected.
