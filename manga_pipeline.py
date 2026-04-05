#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════╗
║           MANGA PDF PIPELINE  //  v1.0                  ║
║  ─────────────────────────────────────────────────────  ║
║  Stage 1 · Convert   — Image folders  →  flat PDFs      ║
║  Stage 2 · Organize  — Flat PDFs      →  batch folders  ║
║  Stage 3 · Merge     — Batch folders  →  combined PDFs  ║
║  ─────────────────────────────────────────────────────  ║
║  Universal: works for any project, any chapter format   ║
╚══════════════════════════════════════════════════════════╝

Requirements:
    pip install customtkinter img2pdf pypdf
"""

import os
import shutil
import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

# ── Dependency guards ─────────────────────────────────────────────────────────
try:
    import img2pdf
    HAS_IMG2PDF = True
except ImportError:
    HAS_IMG2PDF = False

try:
    from pypdf import PdfWriter, PdfReader
    HAS_PYPDF = True
except ImportError:
    try:
        from PyPDF2 import PdfWriter, PdfReader   # legacy fallback
        HAS_PYPDF = True
    except ImportError:
        HAS_PYPDF = False

# ── Theme ─────────────────────────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

C = {
    "bg":       "#0A0A0A",
    "panel":    "#111111",
    "card":     "#161616",
    "border":   "#252525",
    "accent":   "#5E5CE6",
    "accent_h": "#7B79FF",
    "ok":       "#30D158",
    "warn":     "#FFD60A",
    "err":      "#FF453A",
    "fg":       "#F0F0F2",
    "sub":      "#6B6B72",
    "log_bg":   "#080808",
    "stage1":   "#5E5CE6",
    "stage2":   "#30A0FF",
    "stage3":   "#30D158",
}

MONO = ("Consolas", 10)
MONO_B = ("Consolas", 10, "bold")
HEAD = ("Segoe UI", 18, "bold")
LABEL = ("Segoe UI", 11)
LABEL_B = ("Segoe UI", 11, "bold")
SMALL = ("Segoe UI", 9)
BTN = ("Segoe UI", 12, "bold")

# ═══════════════════════════════════════════════════════════════════════════════
#  PIPELINE CORE  (exact algorithms from original scripts — no changes)
# ═══════════════════════════════════════════════════════════════════════════════

def get_chapter_number(folder_name: str):
    """Extract integer chapter number from a folder name."""
    parts = folder_name.upper().replace("CHAPTER", "").strip()
    try:
        return int(parts)
    except ValueError:
        return None


def collect_images(chapter_path: Path, image_exts: tuple):
    """Collect all image files from a chapter folder, deduped and sorted."""
    images = []
    for ext in image_exts:
        images.extend(chapter_path.glob("*" + ext))
        images.extend(chapter_path.glob("*" + ext.upper()))
    return sorted(set(images), key=lambda p: p.name.lower())


# ── Stage 1: Image → PDF ──────────────────────────────────────────────────────

def stage1_convert(source_dir: str, output_dir: str,
                   skip_chapters: set, image_exts: tuple,
                   log_fn, progress_fn) -> bool:
    source = Path(source_dir)
    output = Path(output_dir)

    if not source.exists():
        log_fn(f"[ERROR] Source directory not found: {source}", "err")
        return False

    output.mkdir(parents=True, exist_ok=True)

    chapter_folders = sorted(
        [d for d in source.iterdir() if d.is_dir()],
        key=lambda d: d.name.upper()
    )

    if not chapter_folders:
        log_fn(f"[ERROR] No chapter folders found in: {source}", "err")
        return False

    total = len(chapter_folders)
    done = skipped = errors = 0

    log_fn(f"  Source   : {source}", "sub")
    log_fn(f"  Output   : {output}", "sub")
    log_fn(f"  Folders  : {total} total", "sub")
    log_fn(f"  Skip set : {sorted(skip_chapters) if skip_chapters else 'None'}", "sub")
    log_fn("", "fg")

    for idx, chapter_dir in enumerate(chapter_folders, 1):
        progress_fn(idx / total)
        chapter_num = get_chapter_number(chapter_dir.name)

        if chapter_num is None:
            log_fn(f"  [WARN]  Unrecognised folder : {chapter_dir.name}", "warn")
            continue

        if chapter_num in skip_chapters:
            skipped += 1
            continue

        images = collect_images(chapter_dir, image_exts)

        if not images:
            log_fn(f"  [SKIP]  No images found     : {chapter_dir.name}", "warn")
            errors += 1
            continue

        output_pdf = output / (chapter_dir.name.upper() + ".PDF")

        if output_pdf.exists():
            log_fn(f"  [SKIP]  Already exists      : {output_pdf.name}", "sub")
            skipped += 1
            continue

        try:
            with open(output_pdf, "wb") as f:
                f.write(img2pdf.convert([str(p) for p in images]))
            log_fn(f"  [OK]    {output_pdf.name}  ({len(images)} pages)", "ok")
            done += 1
        except Exception as e:
            log_fn(f"  [ERR]   {chapter_dir.name}: {e}", "err")
            errors += 1

    log_fn("", "fg")
    log_fn(f"  Converted : {done} PDFs", "ok")
    log_fn(f"  Skipped   : {skipped} chapters", "sub")
    log_fn(f"  Errors    : {errors}", "err" if errors else "sub")
    return True


# ── Stage 2: PDF Organizer ────────────────────────────────────────────────────

def stage2_organize(source_dir: str, dest_dir: str,
                    batch_size: int, start_chapter: int, end_chapter: int,
                    log_fn, progress_fn) -> bool:
    os.makedirs(dest_dir, exist_ok=True)

    batches = list(range(start_chapter, end_chapter + 1, batch_size))
    total   = len(batches)

    for current, i in enumerate(batches, 1):
        progress_fn(current / total)
        batch_end   = min(i + batch_size - 1, end_chapter)
        folder_name = f"CHAPTER {i:03d} - CHAPTER {batch_end:03d}"
        target_folder = os.path.join(dest_dir, folder_name)
        os.makedirs(target_folder, exist_ok=True)

        for j in range(i, batch_end + 1):
            file_name   = f"CHAPTER {j:03d}.PDF"
            source_file = os.path.join(source_dir, file_name)
            target_file = os.path.join(target_folder, file_name)

            if os.path.exists(source_file):
                shutil.move(source_file, target_file)
                log_fn(f"  [OK]   Routed {file_name}  →  {folder_name}", "ok")
            else:
                log_fn(f"  [WARN] Missing : {file_name}", "warn")

    log_fn("", "fg")
    log_fn("  Organize stage complete — all files routed.", "ok")
    return True


# ── Stage 3: PDF Merger ───────────────────────────────────────────────────────

def stage3_merge(source_dir: str, output_dir: str,
                 log_fn, progress_fn) -> bool:
    folders = sorted([
        d for d in os.listdir(source_dir)
        if os.path.isdir(os.path.join(source_dir, d))
    ])

    if not folders:
        log_fn("  [WARN] No subfolders found to merge.", "warn")
        return False

    total = len(folders)
    log_fn(f"  Found {total} folder(s) to process.", "sub")
    log_fn("", "fg")

    for idx, folder_name in enumerate(folders, 1):
        progress_fn(idx / total)
        folder_path = os.path.join(source_dir, folder_name)
        output_path = os.path.join(output_dir, folder_name + ".PDF")

        if os.path.exists(output_path):
            log_fn(f"  [SKIP] Already exists : {folder_name}.PDF", "sub")
            continue

        log_fn(f"  [···]  Processing     : {folder_name}", "fg")

        pdfs = sorted([
            f for f in os.listdir(folder_path)
            if f.upper().endswith(".PDF")
        ])

        if not pdfs:
            log_fn("         No PDFs found, skipping.", "warn")
            continue

        writer = PdfWriter()
        try:
            for pdf_name in pdfs:
                pdf_path = os.path.join(folder_path, pdf_name)
                reader   = PdfReader(pdf_path)
                for page in reader.pages:
                    writer.add_page(page)
                log_fn(f"         Added : {pdf_name}  ({len(reader.pages)} pages)", "sub")

            with open(output_path, "wb") as f:
                writer.write(f)
            log_fn(f"  [OK]   Saved  : {os.path.basename(output_path)}", "ok")
            log_fn("", "fg")
        except Exception as e:
            log_fn(f"  [ERR]  {folder_name}: {e}", "err")

    log_fn("  All folders merged.", "ok")
    return True


# ═══════════════════════════════════════════════════════════════════════════════
#  GUI COMPONENTS
# ═══════════════════════════════════════════════════════════════════════════════

class DirSelector(ctk.CTkFrame):
    """Labeled directory picker with inline browse button."""
    def __init__(self, parent, label: str, **kw):
        super().__init__(parent, fg_color=C["card"], corner_radius=8, **kw)

        ctk.CTkLabel(self, text=label, font=SMALL,
                     text_color=C["sub"]).grid(row=0, column=0, columnspan=2,
                     sticky="w", padx=12, pady=(9, 2))

        self._var = ctk.StringVar()
        ctk.CTkEntry(self, textvariable=self._var, font=MONO,
                     fg_color=C["panel"], border_color=C["border"],
                     text_color=C["fg"], height=32
                     ).grid(row=1, column=0, sticky="ew", padx=(12, 6), pady=(0, 10))

        ctk.CTkButton(self, text="Browse", width=76, height=32, font=LABEL,
                      fg_color=C["border"], hover_color=C["accent"],
                      text_color=C["fg"], corner_radius=6,
                      command=self._browse
                      ).grid(row=1, column=1, padx=(0, 12), pady=(0, 10))

        self.columnconfigure(0, weight=1)

    def _browse(self):
        path = filedialog.askdirectory()
        if path:
            self._var.set(path)

    def get(self) -> str:
        return self._var.get().strip()

    def set(self, val: str):
        self._var.set(val)


class ParamRow(ctk.CTkFrame):
    """Compact parameter grid: label + entry pairs in a single card."""
    def __init__(self, parent, title: str, fields: list, **kw):
        super().__init__(parent, fg_color=C["card"], corner_radius=8, **kw)

        ctk.CTkLabel(self, text=title, font=SMALL,
                     text_color=C["sub"]).grid(row=0, column=0,
                     columnspan=len(fields) * 2, sticky="w",
                     padx=12, pady=(9, 4))

        self.entries = {}
        for col, (lbl, default, width) in enumerate(fields):
            ctk.CTkLabel(self, text=lbl, font=SMALL,
                         text_color=C["sub"]).grid(row=1, column=col * 2,
                         padx=(12, 4), pady=(0, 4))
            e = ctk.CTkEntry(self, width=width, font=MONO,
                             fg_color=C["panel"], border_color=C["border"],
                             text_color=C["fg"], height=30)
            e.insert(0, str(default))
            e.grid(row=2, column=col * 2, padx=(12, 4), pady=(0, 12))
            self.entries[lbl] = e

    def get(self, key: str) -> str:
        return self.entries[key].get().strip()

    def get_int(self, key: str) -> int:
        return int(self.get(key))


class ExtSelector(ctk.CTkFrame):
    """Checkbox grid for image extension selection + custom input."""
    DEFAULT_EXTS = [".png", ".jpg", ".jpeg", ".webp"]

    def __init__(self, parent, **kw):
        super().__init__(parent, fg_color=C["card"], corner_radius=8, **kw)

        ctk.CTkLabel(self, text="IMAGE EXTENSIONS", font=SMALL,
                     text_color=C["sub"]).grid(row=0, column=0,
                     columnspan=8, sticky="w", padx=12, pady=(9, 4))

        self._vars = {}
        for col, ext in enumerate(self.DEFAULT_EXTS):
            var = ctk.BooleanVar(value=True)
            ctk.CTkCheckBox(self, text=ext, variable=var,
                            font=LABEL, text_color=C["fg"],
                            checkmark_color=C["fg"],
                            fg_color=C["accent"], hover_color=C["accent_h"],
                            border_color=C["border"]
                            ).grid(row=1, column=col, padx=14, pady=(0, 8))
            self._vars[ext] = var

        ctk.CTkLabel(self, text="Custom (comma-sep):", font=SMALL,
                     text_color=C["sub"]).grid(row=2, column=0,
                     columnspan=2, sticky="w", padx=12, pady=(0, 4))
        self._custom = ctk.CTkEntry(self, font=MONO, height=28,
                                    fg_color=C["panel"], border_color=C["border"],
                                    text_color=C["fg"],
                                    placeholder_text=".bmp, .tiff  — leave blank if unused")
        self._custom.grid(row=3, column=0, columnspan=8, sticky="ew",
                          padx=12, pady=(0, 10))

        self.columnconfigure(list(range(8)), weight=1)

    def get_exts(self) -> tuple:
        exts = tuple(e for e, v in self._vars.items() if v.get())
        raw = self._custom.get().strip()
        if raw:
            extras = tuple(x.strip() for x in raw.split(",") if x.strip())
            exts += extras
        return exts or (".png", ".jpg", ".jpeg", ".webp")


class LogPanel(ctk.CTkFrame):
    """Terminal-style log output panel with colour-coded tags."""
    def __init__(self, parent, **kw):
        super().__init__(parent, fg_color=C["log_bg"], corner_radius=8, **kw)

        bar = ctk.CTkFrame(self, fg_color=C["panel"], corner_radius=0, height=30)
        bar.pack(fill="x")
        bar.pack_propagate(False)
        ctk.CTkLabel(bar, text="  PIPELINE OUTPUT",
                     font=MONO_B, text_color=C["accent"]).pack(side="left", padx=6)
        ctk.CTkButton(bar, text="CLR", width=44, height=22, font=SMALL,
                      fg_color=C["border"], hover_color=C["card"],
                      text_color=C["sub"], corner_radius=4,
                      command=self.clear).pack(side="right", padx=8, pady=4)

        self._txt = tk.Text(self, bg=C["log_bg"], fg=C["fg"],
                            font=MONO, relief="flat", bd=0,
                            padx=10, pady=8, wrap="word",
                            state="disabled", cursor="arrow")

        scroll = ctk.CTkScrollbar(self, command=self._txt.yview,
                                  button_color=C["border"],
                                  button_hover_color=C["sub"])
        self._txt.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y", padx=(0, 2), pady=2)
        self._txt.pack(fill="both", expand=True, padx=(4, 0), pady=(0, 4))

        self._txt.tag_config("fg",   foreground=C["fg"])
        self._txt.tag_config("sub",  foreground=C["sub"])
        self._txt.tag_config("ok",   foreground=C["ok"])
        self._txt.tag_config("warn", foreground=C["warn"])
        self._txt.tag_config("err",  foreground=C["err"])
        self._txt.tag_config("head", foreground=C["accent"],
                             font=MONO_B)
        self._txt.tag_config("s1",   foreground=C["stage1"], font=MONO_B)
        self._txt.tag_config("s2",   foreground=C["stage2"], font=MONO_B)
        self._txt.tag_config("s3",   foreground=C["stage3"], font=MONO_B)

    def log(self, msg: str, tag: str = "fg"):
        self._txt.configure(state="normal")
        self._txt.insert("end", msg + "\n", tag)
        self._txt.see("end")
        self._txt.configure(state="disabled")

    def clear(self):
        self._txt.configure(state="normal")
        self._txt.delete("1.0", "end")
        self._txt.configure(state="disabled")


class StageRow(ctk.CTkFrame):
    """Visual stage indicator card used in the Overview tab."""
    def __init__(self, parent, num: str, color: str,
                 title: str, desc: str, **kw):
        super().__init__(parent, fg_color=C["card"], corner_radius=8,
                         height=66, **kw)
        self.pack_propagate(False)

        accent = ctk.CTkFrame(self, fg_color=color, width=4, corner_radius=2)
        accent.pack(side="left", fill="y", padx=(0, 14))

        badge = ctk.CTkFrame(self, fg_color=color, width=28, height=28,
                             corner_radius=6)
        badge.pack(side="left", padx=(0, 12))
        badge.pack_propagate(False)
        ctk.CTkLabel(badge, text=num, font=("Segoe UI", 11, "bold"),
                     text_color="#000").place(relx=0.5, rely=0.5, anchor="center")

        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(side="left", fill="both", expand=True, pady=10)
        ctk.CTkLabel(inner, text=title, font=LABEL_B,
                     text_color=C["fg"]).pack(anchor="w")
        ctk.CTkLabel(inner, text=desc, font=SMALL,
                     text_color=C["sub"]).pack(anchor="w")


# ═══════════════════════════════════════════════════════════════════════════════
#  MAIN APPLICATION
# ═══════════════════════════════════════════════════════════════════════════════

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Manga PDF Pipeline  //  v1.0")
        self.geometry("1120x780")
        self.minsize(900, 660)
        self.configure(fg_color=C["bg"])

        self._running = False
        self._q: queue.Queue = queue.Queue()

        self._build()
        self._dep_check()
        self._poll()

    # ── Dependency Banner ─────────────────────────────────────────────────────

    def _dep_check(self):
        missing = ([] if HAS_IMG2PDF else ["img2pdf"]) + \
                  ([] if HAS_PYPDF   else ["pypdf"])
        if missing:
            self.log(f"[WARN] Missing packages: {', '.join(missing)}", "warn")
            self.log(f"       pip install {' '.join(missing)}", "warn")
            self.log("", "fg")
            self._status.configure(text="● MISSING DEPS",
                                   text_color=C["err"])
        else:
            self._status.configure(text="● READY",
                                   text_color=C["ok"])

    # ── Layout ────────────────────────────────────────────────────────────────

    def _build(self):
        # ── Header bar
        hdr = ctk.CTkFrame(self, fg_color=C["panel"], height=50, corner_radius=0)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        ctk.CTkLabel(hdr, text="  ⬡  MANGA PDF PIPELINE",
                     font=("Segoe UI", 14, "bold"),
                     text_color=C["accent"]).pack(side="left")
        ctk.CTkLabel(hdr, text=" //  Convert · Organize · Merge",
                     font=LABEL, text_color=C["sub"]).pack(side="left")

        self._status = ctk.CTkLabel(hdr, text="● LOADING",
                                    font=LABEL_B, text_color=C["warn"])
        self._status.pack(side="right", padx=18)

        # ── Body: sidebar + content
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True)

        # Sidebar
        side = ctk.CTkFrame(body, fg_color=C["panel"], width=190,
                            corner_radius=0)
        side.pack(side="left", fill="y")
        side.pack_propagate(False)

        ctk.CTkLabel(side, text="PIPELINE", font=SMALL,
                     text_color=C["sub"]).pack(anchor="w", padx=14, pady=(18, 6))

        NAV = [
            ("  Overview",       C["accent"]),
            ("  Stage 1 · Convert",  C["stage1"]),
            ("  Stage 2 · Organize", C["stage2"]),
            ("  Stage 3 · Merge",    C["stage3"]),
        ]
        self._nav_btns = []
        for i, (label, color) in enumerate(NAV):
            b = ctk.CTkButton(side, text=label, anchor="w", height=34,
                              font=LABEL, corner_radius=6,
                              fg_color=C["accent"] if i == 0 else "transparent",
                              hover_color=C["border"],
                              text_color=C["fg"],
                              command=lambda x=i: self._nav(x))
            b.pack(fill="x", padx=8, pady=2)
            self._nav_btns.append(b)

        # Separator
        ctk.CTkFrame(side, fg_color=C["border"], height=1
                     ).pack(fill="x", padx=8, pady=12)

        ctk.CTkLabel(side, text="ABOUT", font=SMALL,
                     text_color=C["sub"]).pack(anchor="w", padx=14, pady=(0, 6))
        ctk.CTkLabel(side,
                     text="Universal manga/comic\nPDF pipeline tool.\n\n"
                          "Works with any project,\nany chapter numbering.",
                     font=SMALL, text_color=C["sub"],
                     justify="left").pack(anchor="w", padx=14)

        # Content panes
        content = ctk.CTkFrame(body, fg_color="transparent")
        content.pack(side="left", fill="both", expand=True)

        self._panes = []
        builders = [self._pane_overview, self._pane_s1,
                    self._pane_s2, self._pane_s3]
        for build_fn in builders:
            pane = ctk.CTkScrollableFrame(content, fg_color="transparent",
                                          scrollbar_button_color=C["border"],
                                          scrollbar_button_hover_color=C["sub"])
            build_fn(pane)
            self._panes.append(pane)

        self._active = 0
        self._panes[0].pack(fill="both", expand=True, padx=16, pady=10)

        # ── Bottom: progress + log
        foot = ctk.CTkFrame(self, fg_color=C["panel"], height=256,
                            corner_radius=0)
        foot.pack(fill="x", side="bottom")
        foot.pack_propagate(False)

        prog_bar_area = ctk.CTkFrame(foot, fg_color="transparent", height=38)
        prog_bar_area.pack(fill="x", padx=16, pady=(8, 2))
        prog_bar_area.pack_propagate(False)

        self._prog_lbl = ctk.CTkLabel(prog_bar_area, text="Idle",
                                      font=SMALL, text_color=C["sub"])
        self._prog_lbl.pack(side="left")

        self._prog_pct = ctk.CTkLabel(prog_bar_area, text="—",
                                      font=LABEL_B, text_color=C["accent"])
        self._prog_pct.pack(side="right")

        self._bar = ctk.CTkProgressBar(foot, height=5,
                                       fg_color=C["border"],
                                       progress_color=C["accent"])
        self._bar.pack(fill="x", padx=16, pady=(0, 6))
        self._bar.set(0)

        self._log = LogPanel(foot)
        self._log.pack(fill="both", expand=True, padx=16, pady=(0, 10))

    # ── Content Panes ─────────────────────────────────────────────────────────

    def _pane_overview(self, p):
        ctk.CTkLabel(p, text="Overview — Full Pipeline",
                     font=HEAD, text_color=C["fg"]).pack(anchor="w", pady=(4, 2))
        ctk.CTkLabel(p, text="Run all three stages sequentially. Set your directories "
                             "and parameters once, then fire.",
                     font=LABEL, text_color=C["sub"]).pack(anchor="w", pady=(0, 14))

        StageRow(p, "1", C["stage1"], "Image → PDF Convert",
                 "Scan chapter subfolders, collect images, write one PDF per chapter."
                 ).pack(fill="x", pady=(0, 6))
        StageRow(p, "2", C["stage2"], "PDF Organizer",
                 "Move flat PDFs into configurable batch subfolders (e.g. CHAPTER 011-018)."
                 ).pack(fill="x", pady=(0, 6))
        StageRow(p, "3", C["stage3"], "Batch Merger",
                 "Losslessly merge each batch folder into one combined PDF. Zero re-encoding."
                 ).pack(fill="x", pady=(0, 18))

        ctk.CTkFrame(p, fg_color=C["border"], height=1).pack(fill="x", pady=(0, 14))

        # Directories
        ctk.CTkLabel(p, text="DIRECTORIES", font=SMALL,
                     text_color=C["sub"]).pack(anchor="w", pady=(0, 6))

        self._ov_src = DirSelector(p, "IMAGE SOURCE  —  root folder containing chapter subfolders")
        self._ov_src.pack(fill="x", pady=(0, 6))
        self._ov_mid = DirSelector(p, "INTERMEDIATE  —  flat PDFs then batched here  (can be same as SOURCE)")
        self._ov_mid.pack(fill="x", pady=(0, 6))
        self._ov_out = DirSelector(p, "FINAL OUTPUT  —  merged PDFs written here  (can be same as INTERMEDIATE)")
        self._ov_out.pack(fill="x", pady=(0, 14))

        # Parameters
        self._ov_params = ParamRow(p, "CHAPTER PARAMETERS", [
            ("Batch Size",    8,   72),
            ("Start Chapter", 1,   72),
            ("End Chapter",   270, 80),
            ("Skip From",     11,  72),
            ("Skip To",       30,  72),
        ])
        self._ov_params.pack(fill="x", pady=(0, 12))

        self._ov_exts = ExtSelector(p)
        self._ov_exts.pack(fill="x", pady=(0, 14))

        self._ov_run = ctk.CTkButton(p, text="▶  RUN FULL PIPELINE", height=46,
                                     font=BTN, corner_radius=8,
                                     fg_color=C["accent"], hover_color=C["accent_h"],
                                     command=self._exec_pipeline)
        self._ov_run.pack(fill="x", pady=(0, 16))

    def _pane_s1(self, p):
        self._stage_header(p, "Stage 1  ·  Image → PDF Convert",
                           "Convert each chapter image folder into an individual PDF file.",
                           C["stage1"])

        self._s1_src = DirSelector(p, "SOURCE  —  root folder containing chapter subfolders")
        self._s1_src.pack(fill="x", pady=(0, 6))
        self._s1_out = DirSelector(p, "OUTPUT  —  flat PDFs written here")
        self._s1_out.pack(fill="x", pady=(0, 12))

        self._s1_skip = ParamRow(p, "SKIP RANGE  (chapters already converted)", [
            ("Skip From", 11, 80),
            ("Skip To",   30, 80),
        ])
        self._s1_skip.pack(fill="x", pady=(0, 12))

        self._s1_exts = ExtSelector(p)
        self._s1_exts.pack(fill="x", pady=(0, 14))

        ctk.CTkButton(p, text="▶  RUN STAGE 1", height=42,
                      font=BTN, corner_radius=8,
                      fg_color=C["stage1"], hover_color=C["accent_h"],
                      command=self._exec_s1).pack(fill="x", pady=(0, 16))

    def _pane_s2(self, p):
        self._stage_header(p, "Stage 2  ·  PDF Organizer",
                           "Move flat PDFs into named batch subfolders.",
                           C["stage2"])

        self._s2_src = DirSelector(p, "SOURCE  —  directory containing flat PDFs")
        self._s2_src.pack(fill="x", pady=(0, 6))
        self._s2_dst = DirSelector(p, "DESTINATION  —  batch subfolders created here")
        self._s2_dst.pack(fill="x", pady=(0, 12))

        self._s2_params = ParamRow(p, "PARAMETERS", [
            ("Batch Size",    8,   80),
            ("Start Chapter", 11,  80),
            ("End Chapter",   270, 90),
        ])
        self._s2_params.pack(fill="x", pady=(0, 14))

        ctk.CTkButton(p, text="▶  RUN STAGE 2", height=42,
                      font=BTN, corner_radius=8,
                      fg_color=C["stage2"], hover_color=C["accent_h"],
                      command=self._exec_s2).pack(fill="x", pady=(0, 16))

    def _pane_s3(self, p):
        self._stage_header(p, "Stage 3  ·  Batch Merger",
                           "Losslessly merge each batch subfolder into a single combined PDF. "
                           "Zero re-encoding — no quality loss.",
                           C["stage3"])

        self._s3_src = DirSelector(p, "SOURCE  —  directory containing batch subfolders")
        self._s3_src.pack(fill="x", pady=(0, 6))
        self._s3_out = DirSelector(p, "OUTPUT  —  merged PDFs saved here  (can equal SOURCE)")
        self._s3_out.pack(fill="x", pady=(0, 14))

        ctk.CTkButton(p, text="▶  RUN STAGE 3", height=42,
                      font=BTN, corner_radius=8,
                      fg_color=C["stage3"], hover_color=C["accent_h"],
                      command=self._exec_s3).pack(fill="x", pady=(0, 16))

    def _stage_header(self, parent, title: str, sub: str, color: str):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(anchor="w", fill="x", pady=(4, 4))

        ctk.CTkFrame(row, fg_color=color, width=4, height=36,
                     corner_radius=2).pack(side="left", padx=(0, 10))

        inner = ctk.CTkFrame(row, fg_color="transparent")
        inner.pack(side="left")
        ctk.CTkLabel(inner, text=title, font=HEAD,
                     text_color=C["fg"]).pack(anchor="w")
        ctk.CTkLabel(inner, text=sub, font=LABEL,
                     text_color=C["sub"]).pack(anchor="w")

        ctk.CTkFrame(parent, fg_color=C["border"], height=1
                     ).pack(fill="x", pady=(8, 14))

    # ── Navigation ────────────────────────────────────────────────────────────

    def _nav(self, idx: int):
        self._panes[self._active].pack_forget()
        self._panes[idx].pack(fill="both", expand=True, padx=16, pady=10)
        self._active = idx
        for i, btn in enumerate(self._nav_btns):
            btn.configure(fg_color=C["accent"] if i == idx else "transparent")

    # ── Log / Progress Helpers ────────────────────────────────────────────────

    def log(self, msg: str, tag: str = "fg"):
        self._q.put((msg, tag))

    def _poll(self):
        try:
            while True:
                msg, tag = self._q.get_nowait()
                self._log.log(msg, tag)
        except queue.Empty:
            pass
        self.after(40, self._poll)

    def _prog(self, val: float, lbl: str = ""):
        self._bar.set(val)
        self._prog_pct.configure(text=f"{int(val * 100)}%")
        if lbl:
            self._prog_lbl.configure(text=lbl)

    def _set_running(self, state: bool, lbl: str = ""):
        self._running = state
        if state:
            self._status.configure(text="● RUNNING", text_color=C["warn"])
            self._prog_lbl.configure(text=lbl or "Running...")
        else:
            self._status.configure(text="● READY", text_color=C["ok"])
            self._prog_lbl.configure(text=lbl or "Idle")

    def _guard(self, needs_img2pdf=False, needs_pypdf=False) -> bool:
        if self._running:
            return False
        if needs_img2pdf and not HAS_IMG2PDF:
            messagebox.showerror("Missing Dependency",
                                 "img2pdf is not installed.\n\nRun:\n  pip install img2pdf")
            return False
        if needs_pypdf and not HAS_PYPDF:
            messagebox.showerror("Missing Dependency",
                                 "pypdf is not installed.\n\nRun:\n  pip install pypdf")
            return False
        return True

    def _get_skip_range(self, param_widget, from_key="Skip From", to_key="Skip To") -> set:
        try:
            a = int(param_widget.get(from_key))
            b = int(param_widget.get(to_key))
            return set(range(a, b + 1))
        except (ValueError, KeyError):
            return set()

    # ── Executors ─────────────────────────────────────────────────────────────

    def _exec_s1(self):
        if not self._guard(needs_img2pdf=True):
            return
        src = self._s1_src.get()
        out = self._s1_out.get()
        if not src or not out:
            messagebox.showwarning("Missing Paths",
                                   "Select source and output directories.")
            return
        skip = self._get_skip_range(self._s1_skip)
        exts = self._s1_exts.get_exts()

        self._log.clear()
        self.log("┌──  STAGE 1  ·  IMAGE → PDF CONVERT  ──┐", "s1")
        self._set_running(True, "Stage 1: Converting...")
        self._prog(0)

        def _work():
            stage1_convert(src, out, skip, exts, self.log,
                           lambda v: self.after(0, lambda: self._prog(v, "Stage 1: Converting...")))
            self.log("└" + "─" * 39 + "┘", "s1")
            self.after(0, lambda: self._set_running(False, "Stage 1 complete"))
            self.after(0, lambda: self._prog(1.0))

        threading.Thread(target=_work, daemon=True).start()

    def _exec_s2(self):
        if not self._guard():
            return
        src = self._s2_src.get()
        dst = self._s2_dst.get()
        if not src or not dst:
            messagebox.showwarning("Missing Paths",
                                   "Select source and destination directories.")
            return
        try:
            batch = self._s2_params.get_int("Batch Size")
            start = self._s2_params.get_int("Start Chapter")
            end   = self._s2_params.get_int("End Chapter")
        except ValueError:
            messagebox.showerror("Invalid Input",
                                 "Batch Size, Start Chapter, End Chapter must be integers.")
            return

        self._log.clear()
        self.log("┌──  STAGE 2  ·  PDF ORGANIZER  ──┐", "s2")
        self._set_running(True, "Stage 2: Organizing...")
        self._prog(0)

        def _work():
            stage2_organize(src, dst, batch, start, end, self.log,
                            lambda v: self.after(0, lambda: self._prog(v, "Stage 2: Organizing...")))
            self.log("└" + "─" * 33 + "┘", "s2")
            self.after(0, lambda: self._set_running(False, "Stage 2 complete"))
            self.after(0, lambda: self._prog(1.0))

        threading.Thread(target=_work, daemon=True).start()

    def _exec_s3(self):
        if not self._guard(needs_pypdf=True):
            return
        src = self._s3_src.get()
        out = self._s3_out.get()
        if not src or not out:
            messagebox.showwarning("Missing Paths",
                                   "Select source and output directories.")
            return

        self._log.clear()
        self.log("┌──  STAGE 3  ·  BATCH MERGER  ──┐", "s3")
        self._set_running(True, "Stage 3: Merging...")
        self._prog(0)

        def _work():
            stage3_merge(src, out, self.log,
                         lambda v: self.after(0, lambda: self._prog(v, "Stage 3: Merging...")))
            self.log("└" + "─" * 32 + "┘", "s3")
            self.after(0, lambda: self._set_running(False, "Stage 3 complete"))
            self.after(0, lambda: self._prog(1.0))

        threading.Thread(target=_work, daemon=True).start()

    def _exec_pipeline(self):
        if not self._guard(needs_img2pdf=True, needs_pypdf=True):
            return
        src = self._ov_src.get()
        mid = self._ov_mid.get()
        out = self._ov_out.get()
        if not src or not mid or not out:
            messagebox.showwarning("Missing Paths",
                                   "All three directory fields are required.")
            return
        try:
            batch = self._ov_params.get_int("Batch Size")
            start = self._ov_params.get_int("Start Chapter")
            end   = self._ov_params.get_int("End Chapter")
            skip  = self._get_skip_range(self._ov_params)
        except ValueError:
            messagebox.showerror("Invalid Input",
                                 "All chapter parameters must be integers.")
            return
        exts = self._ov_exts.get_exts()

        self._log.clear()
        self._set_running(True, "Pipeline starting...")
        self._prog(0)

        def _work():
            # ── Stage 1 ──────────────────────────────────────────────────────
            self.log("┌──  [1/3]  IMAGE → PDF CONVERT  ──────────────────┐", "s1")
            self.after(0, lambda: self._prog(0, "Stage 1/3: Converting..."))
            stage1_convert(src, mid, skip, exts, self.log,
                           lambda v: self.after(0, lambda: self._prog(
                               v * 0.33, "Stage 1/3: Converting...")))
            self.log("└───────────────────────────────────────────────────┘", "s1")
            self.log("", "fg")

            # ── Stage 2 ──────────────────────────────────────────────────────
            self.log("┌──  [2/3]  PDF ORGANIZER  ─────────────────────────┐", "s2")
            stage2_organize(mid, mid, batch, start, end, self.log,
                            lambda v: self.after(0, lambda: self._prog(
                                0.33 + v * 0.33, "Stage 2/3: Organizing...")))
            self.log("└───────────────────────────────────────────────────┘", "s2")
            self.log("", "fg")

            # ── Stage 3 ──────────────────────────────────────────────────────
            self.log("┌──  [3/3]  BATCH MERGER  ──────────────────────────┐", "s3")
            stage3_merge(mid, out, self.log,
                         lambda v: self.after(0, lambda: self._prog(
                             0.66 + v * 0.34, "Stage 3/3: Merging...")))
            self.log("└───────────────────────────────────────────────────┘", "s3")
            self.log("", "fg")

            self.log("╔═══════════════════════════════════════════════════╗", "head")
            self.log("║            PIPELINE COMPLETE  ✓                  ║", "head")
            self.log("╚═══════════════════════════════════════════════════╝", "head")
            self.after(0, lambda: self._set_running(False, "Pipeline complete"))
            self.after(0, lambda: self._prog(1.0))

        threading.Thread(target=_work, daemon=True).start()


# ═══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    app = App()
    app.mainloop()
