#!/usr/bin/env python3
"""VLSI Portfolio Builder — organiser + GitHub file manager."""

from __future__ import annotations

import base64
import json
import os
import re
import shutil
import subprocess
import threading
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
except Exception:
    DND_FILES = None
    TkinterDnD = None

# ── Paths ─────────────────────────────────────────────────────────────────────
APP_DIR   = Path(__file__).resolve().parent
REPO_ROOT = APP_DIR.parents[1]
PROJECT_FOLDERS = ("rtl", "tb", "sim", "waves", "synthesis", "docs")
IGNORED_DIRS    = {".git", ".pio", ".venv", "__pycache__", "build", "dist", "node_modules",
                   "db", "incremental_db", "simulation", ".qsys_edit"}
IGNORED_EXTS    = {
    # Quartus build artifacts
    ".cdb", ".hdb", ".rdb", ".kpt", ".logdb", ".ammdb", ".bpm", ".idb",
    ".dfp", ".rcfdb", ".dpi", ".sig", ".ddb", ".tdb", ".qdb", ".qpg", ".qtl",
    ".sof", ".pof", ".stp", ".sft", ".jdi", ".pin", ".smsg", ".vo",
    ".lpc", ".rrp", ".rtlv", ".vpr", ".hif", ".hier_info", ".db_info",
    # Quartus misc
    ".sci", ".xrf", ".qmsg", ".summary",
    # Backup files
    ".bak",
}
IGNORED_NAMES   = {"_vmake", "_info", "modelsim.ini", "README"}
GIT_MANAGED     = (".gitignore", "projects", "run_repo_dropper.sh", "tools/repo_dropper")
HISTORY_FILE    = APP_DIR / ".project_history.json"
CONFIG_FILE     = APP_DIR / ".gh_config.json"

# ── Theme ─────────────────────────────────────────────────────────────────────
C = {
    "bg":      "#0d1117",
    "surf":    "#161b22",
    "surf2":   "#21262d",
    "border":  "#30363d",
    "accent":  "#6366f1",
    "accent2": "#4f46e5",
    "success": "#238636",
    "danger":  "#da3633",
    "text":    "#e6edf3",
    "muted":   "#8b949e",
    "dim":     "#484f58",
}

CAT = {
    "rtl":       ("#60a5fa", "⬡ "),
    "tb":        ("#34d399", "⧉ "),
    "waves":     ("#a78bfa", "〜"),
    "synthesis": ("#fb923c", "⬢ "),
    "sim":       ("#fbbf24", "⚙ "),
    "docs":      ("#f472b6", "◎ "),
}


# ── Data / Logic ──────────────────────────────────────────────────────────────
@dataclass
class FileEntry:
    source: Path
    target: str
    copied_to: Path | None = None


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    return re.sub(r"_+", "_", value).strip("_") or "new_project"


def unique_destination(path: Path) -> Path:
    if not path.exists():
        return path
    stem, suffix, parent = path.stem, path.suffix, path.parent
    n = 2
    while True:
        c = parent / f"{stem}_{n}{suffix}"
        if not c.exists():
            return c
        n += 1


def classify_file(path: Path, fallback: str = "docs") -> str:
    name, suffix = path.name.lower(), path.suffix.lower()
    if name.endswith(("_tb.v", "_tb.sv", ".tb.v", ".tb.sv")) or "testbench" in name:
        return "tb"
    if suffix in {".v", ".sv", ".svh", ".vhd", ".vhdl"}:
        return "rtl"
    if suffix in {".vcd", ".fst", ".ghw", ".gtkw", ".sav"} or "wave" in name:
        return "waves"
    if suffix in {".ys", ".json", ".svg", ".rpt", ".rep", ".log"} or "synth" in name:
        return "synthesis"
    if suffix in {".sh", ".mk", ".makefile"} or name in {"makefile", "run_sim"}:
        return "sim"
    if suffix in {".md", ".png", ".jpg", ".jpeg", ".gif", ".pdf"}:
        return "docs"
    return fallback


def should_ignore(path: Path) -> bool:
    if any(part in IGNORED_DIRS for part in path.parts):
        return True
    if path.suffix.lower() in IGNORED_EXTS:
        return True
    if path.name in IGNORED_NAMES:
        return True
    return False


def run_git(
    args: list[str],
    *,
    env: dict[str, str] | None = None,
    timeout: int | None = None,
) -> tuple[int, str]:
    try:
        p = subprocess.run(
            ["git", *args],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
            env={**os.environ, **(env or {})},
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return 124, "git command timed out. Check your GitHub credentials, then try again."
    return p.returncode, "\n".join(x for x in (p.stdout.strip(), p.stderr.strip()) if x)


def github_auth_hint(output: str) -> str:
    text = output.lower()
    auth_markers = (
        "authentication failed",
        "could not read username",
        "terminal prompts disabled",
        "permission denied",
        "invalid username or password",
        "support for password authentication was removed",
    )
    if not any(marker in text for marker in auth_markers):
        return output
    hint = (
        "\n\nGitHub does not accept your account password for HTTPS pushes.\n"
        "Use one of these options:\n"
        "1. Create a GitHub Personal Access Token and use it when Git asks for a password.\n"
        "2. Switch this repo to SSH and push with your SSH key.\n"
        "\nOn macOS, the Allow / Deny / Always Allow prompt is Keychain asking whether "
        "Git may read saved credentials. If you trust this repo and Git install, choose "
        "Always Allow so future pushes do not keep asking."
    )
    return (output or "GitHub authentication failed.") + hint


def load_history() -> list[str]:
    try:
        d = json.loads(HISTORY_FILE.read_text())
        return d if isinstance(d, list) else []
    except Exception:
        return []


def save_history(names: list[str]) -> None:
    try:
        HISTORY_FILE.write_text(json.dumps(names[:12]))
    except Exception:
        pass


def load_config() -> dict:
    try:
        return json.loads(CONFIG_FILE.read_text())
    except Exception:
        return {}


def save_config(cfg: dict) -> None:
    try:
        CONFIG_FILE.write_text(json.dumps(cfg, indent=2))
    except Exception:
        pass


# ── GitHub API ────────────────────────────────────────────────────────────────
class GitHubAPI:
    BASE = "https://api.github.com"

    def __init__(self, token: str, owner: str, repo: str) -> None:
        self.token = token
        self.owner = owner
        self.repo  = repo

    @property
    def _hdrs(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def _req(self, url: str, method: str = "GET", body: dict | None = None):
        data = json.dumps(body).encode() if body else None
        hdrs = {**self._hdrs, **({"Content-Type": "application/json"} if data else {})}
        req  = urllib.request.Request(url, data=data, headers=hdrs, method=method)
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                raw = r.read()
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as e:
            try:
                msg = json.loads(e.read()).get("message", str(e))
            except Exception:
                msg = str(e)
            raise RuntimeError(msg) from e

    def tree(self) -> list[dict]:
        d = self._req(
            f"{self.BASE}/repos/{self.owner}/{self.repo}/git/trees/HEAD?recursive=1")
        return d.get("tree", [])

    def file(self, path: str) -> dict:
        return self._req(
            f"{self.BASE}/repos/{self.owner}/{self.repo}/contents/{path}")

    def put(self, path: str, content_str: str, sha: str | None, msg: str) -> dict:
        body: dict = {
            "message": msg,
            "content": base64.b64encode(content_str.encode("utf-8")).decode(),
        }
        if sha:
            body["sha"] = sha
        return self._req(
            f"{self.BASE}/repos/{self.owner}/{self.repo}/contents/{path}",
            method="PUT", body=body)

    def delete(self, path: str, sha: str, msg: str) -> dict:
        return self._req(
            f"{self.BASE}/repos/{self.owner}/{self.repo}/contents/{path}",
            method="DELETE", body={"message": msg, "sha": sha})


# ── Tooltip ───────────────────────────────────────────────────────────────────
class Tooltip:
    def __init__(self, widget: tk.Widget, text: str) -> None:
        self._tip: tk.Toplevel | None = None
        widget.bind("<Enter>", lambda _: self._show(widget, text))
        widget.bind("<Leave>", lambda _: self._hide())

    def _show(self, w: tk.Widget, text: str) -> None:
        x = w.winfo_rootx() + 16
        y = w.winfo_rooty() + w.winfo_height() + 4
        self._tip = tk.Toplevel(w)
        self._tip.wm_overrideredirect(True)
        self._tip.wm_geometry(f"+{x}+{y}")
        tk.Label(self._tip, text=text, bg=C["surf2"], fg=C["muted"],
                 relief="flat", padx=10, pady=5, font=("Inter", 9)).pack()

    def _hide(self) -> None:
        if self._tip:
            self._tip.destroy()
            self._tip = None


# ── Main App ──────────────────────────────────────────────────────────────────
class RepoDropper:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Repo Dropper  ·  VLSI Portfolio Builder")
        self.root.geometry("1200x780")
        self.root.minsize(1000, 660)
        self.root.configure(bg=C["bg"])

        # organiser state
        self.entries:  list[FileEntry] = []
        self.history:  list[str]       = load_history()
        self.project_name   = tk.StringVar(value=self.history[0] if self.history else "01_nand2")
        self.dest_path      = tk.StringVar(value="projects/")
        self.target_folder  = tk.StringVar(value="auto")
        self.commit_message = tk.StringVar()
        self.create_readme  = tk.BooleanVar(value=True)
        self.status_text    = tk.StringVar(value="Ready")
        self.branch_text    = tk.StringVar(value="")

        # github browser state
        self.gh_api: GitHubAPI | None = None
        self._gh_cfg = load_config()
        self._gh_token  = tk.StringVar(value=self._gh_cfg.get("token", ""))
        self._gh_owner  = tk.StringVar(value=self._gh_cfg.get("owner", "AnshSankrityayan"))
        self._gh_repo   = tk.StringVar(value=self._gh_cfg.get("repo",  "vlsi-portfolio"))
        self._gh_status = tk.StringVar(value="Not connected")
        self._edit_path = ""
        self._edit_sha  = ""
        self._blob_shas: dict[str, str] = {}   # path -> sha for all blobs

        self.project_name.trace_add("write", self._auto_commit_msg)
        self._auto_commit_msg()

        self._build_styles()
        self._build_ui()
        self._refresh_git_info()
        self.refresh_status()

    # ── Styles ────────────────────────────────────────────────────────────────
    def _build_styles(self) -> None:
        s = ttk.Style(self.root)
        s.theme_use("clam")

        s.configure(".", background=C["bg"], foreground=C["text"],
                    font=("Inter", 10), borderwidth=0, relief="flat")

        for name, bg in (("App", C["bg"]), ("Card", C["surf"]), ("Card2", C["surf2"])):
            s.configure(f"{name}.TFrame", background=bg)
            s.configure(f"{name}.TLabel", background=bg, foreground=C["text"])

        s.configure("Title.TLabel", background=C["bg"], foreground=C["text"],
                    font=("Inter", 16, "bold"))
        s.configure("Sub.TLabel",   background=C["bg"], foreground=C["muted"],
                    font=("Inter", 10))
        s.configure("Head.TLabel",  background=C["surf"], foreground=C["muted"],
                    font=("Inter", 9, "bold"))
        s.configure("Chip.TLabel",  background=C["surf2"], foreground=C["muted"],
                    font=("Inter", 9))

        # Notebook
        s.configure("TNotebook",     background=C["bg"], borderwidth=0, tabmargins=0)
        s.configure("TNotebook.Tab", background=C["surf2"], foreground=C["muted"],
                    padding=(16, 8), font=("Inter", 10))
        s.map("TNotebook.Tab",
              background=[("selected", C["surf"])],
              foreground=[("selected", C["text"])])

        # Buttons
        s.configure("TButton", background=C["surf2"], foreground=C["text"],
                    padding=(12, 7), borderwidth=1, relief="flat")
        s.map("TButton", background=[("active", C["border"]), ("pressed", C["border"])])

        s.configure("Accent.TButton", background=C["accent"], foreground="#fff",
                    padding=(14, 8), font=("Inter", 10, "bold"))
        s.map("Accent.TButton",
              background=[("active", C["accent2"]), ("pressed", C["accent2"])])

        s.configure("Go.TButton", background=C["success"], foreground="#fff",
                    padding=(14, 8), font=("Inter", 10, "bold"))
        s.map("Go.TButton",
              background=[("active", "#1a7f37"), ("pressed", "#1a7f37")])

        s.configure("Del.TButton", background=C["danger"], foreground="#fff",
                    padding=(10, 6))
        s.map("Del.TButton",
              background=[("active", "#b91c1c"), ("pressed", "#b91c1c")])

        s.configure("TEntry", fieldbackground=C["surf2"], foreground=C["text"],
                    insertcolor=C["text"], bordercolor=C["border"],
                    lightcolor=C["border"], darkcolor=C["border"], padding=8)
        s.map("TEntry", bordercolor=[("focus", C["accent"])])

        s.configure("TCombobox", fieldbackground=C["surf2"], foreground=C["text"],
                    background=C["surf2"], selectbackground=C["accent"],
                    arrowcolor=C["muted"], padding=6)
        s.map("TCombobox",
              fieldbackground=[("readonly", C["surf2"])],
              foreground=[("readonly", C["text"])])

        s.configure("TCheckbutton", background=C["surf"], foreground=C["text"])
        s.map("TCheckbutton", background=[("active", C["surf"])])

        s.configure("Treeview", background=C["surf2"], fieldbackground=C["surf2"],
                    foreground=C["text"], rowheight=26, borderwidth=0)
        s.configure("Treeview.Heading", background=C["surf"], foreground=C["muted"],
                    font=("Inter", 9, "bold"), relief="flat")
        s.map("Treeview",
              background=[("selected", C["accent"])],
              foreground=[("selected", "#fff")])

        s.configure("TScrollbar", background=C["surf2"], troughcolor=C["surf2"],
                    arrowsize=10)
        s.map("TScrollbar", background=[("active", C["border"])])
        s.configure("TSeparator", background=C["border"])

    # ── UI skeleton ───────────────────────────────────────────────────────────
    def _build_ui(self) -> None:
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)
        self._build_header()
        self._build_body()
        self._build_footer()

    # ── Header ────────────────────────────────────────────────────────────────
    def _build_header(self) -> None:
        hdr = ttk.Frame(self.root, style="App.TFrame", padding=(20, 12, 20, 10))
        hdr.grid(row=0, column=0, sticky="ew")
        hdr.columnconfigure(1, weight=1)

        ttk.Label(hdr, text="◈  Repo Dropper", style="Title.TLabel").grid(
            row=0, column=0, rowspan=2, sticky="w")

        info = ttk.Frame(hdr, style="App.TFrame")
        info.grid(row=0, column=2, rowspan=2, sticky="e")
        ttk.Label(info, textvariable=self.status_text, style="Sub.TLabel").pack(
            side="right", padx=(8, 0))
        ttk.Label(info, textvariable=self.branch_text,
                  style="Chip.TLabel", padding=(8, 3)).pack(side="right")

        ttk.Label(hdr, text="Organise VLSI files  ·  Browse & edit your GitHub repo directly.",
                  style="Sub.TLabel").grid(row=1, column=0, sticky="w", pady=(2, 0))

        ttk.Separator(self.root).grid(row=0, column=0, sticky="sew")

    # ── Body: notebook with two tabs ──────────────────────────────────────────
    def _build_body(self) -> None:
        nb = ttk.Notebook(self.root, style="TNotebook")
        nb.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        self.root.rowconfigure(1, weight=1)

        t1 = ttk.Frame(nb, style="App.TFrame", padding=(14, 10, 14, 0))
        nb.add(t1, text="  ⬇  Organiser  ")
        t1.columnconfigure(0, weight=3)
        t1.columnconfigure(1, weight=0)
        t1.columnconfigure(2, weight=2)
        t1.rowconfigure(0, weight=1)
        self._build_left(t1)
        ttk.Separator(t1, orient="vertical").grid(row=0, column=1, sticky="ns", padx=10)
        self._build_right(t1)

        t2 = ttk.Frame(nb, style="App.TFrame", padding=(14, 10, 14, 6))
        nb.add(t2, text="  ◈  GitHub Browser  ")
        self._build_browser(t2)

    # ── Organiser — left panel ────────────────────────────────────────────────
    def _build_left(self, parent: ttk.Frame) -> None:
        col = ttk.Frame(parent, style="App.TFrame")
        col.grid(row=0, column=0, sticky="nsew")
        col.columnconfigure(0, weight=1)
        col.rowconfigure(2, weight=1)

        cfg = ttk.Frame(col, style="Card.TFrame", padding=(14, 10))
        cfg.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        for i in (1, 3):
            cfg.columnconfigure(i, weight=1)

        ttk.Label(cfg, text="PROJECT", style="Head.TLabel").grid(row=0, column=0, sticky="w")
        self._name_box = ttk.Combobox(cfg, textvariable=self.project_name,
                                      values=self.history, width=20)
        self._name_box.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(4, 0))
        Tooltip(self._name_box, "Slug used as the project name")

        ttk.Label(cfg, text="PLACEMENT", style="Head.TLabel").grid(
            row=0, column=2, sticky="w", padx=(14, 0))
        place_box = ttk.Combobox(cfg, textvariable=self.target_folder,
                                 values=["auto", *PROJECT_FOLDERS],
                                 state="readonly", width=13)
        place_box.grid(row=1, column=2, columnspan=2, sticky="ew",
                       padx=(14, 0), pady=(4, 0))
        place_box.bind("<<ComboboxSelected>>", lambda _: self.reclassify_entries())

        ttk.Checkbutton(cfg, text=" Auto-README", variable=self.create_readme).grid(
            row=1, column=4, padx=(14, 0), pady=(4, 0))

        # Destination path row
        ttk.Label(cfg, text="DESTINATION IN REPO", style="Head.TLabel").grid(
            row=2, column=0, sticky="w", pady=(10, 0))
        dest_row = ttk.Frame(cfg, style="Card.TFrame")
        dest_row.grid(row=3, column=0, columnspan=5, sticky="ew", pady=(4, 0))
        dest_row.columnconfigure(0, weight=1)
        ttk.Entry(dest_row, textvariable=self.dest_path).grid(
            row=0, column=0, sticky="ew", padx=(0, 6))
        browse_btn = ttk.Button(dest_row, text="📂 Browse",
                                command=self._pick_dest_folder, padding=(8, 5))
        browse_btn.grid(row=0, column=1)
        Tooltip(browse_btn, "Pick any folder inside the repo as the destination")

        bar = ttk.Frame(col, style="App.TFrame")
        bar.grid(row=1, column=0, sticky="ew", pady=(0, 6))
        bar.columnconfigure(4, weight=1)

        for ci, (label, cmd, style, tip) in enumerate([
            ("＋ Files",   self.pick_files,          "TButton",    "Pick individual files"),
            ("＋ Folder",  self.pick_folder,          "TButton",    "Add an entire project folder"),
            ("⟳ Re-sort", self.reclassify_entries,   "TButton",    "Re-classify selected or all files"),
            ("✕ Clear",   self.clear_files,           "Del.TButton","Remove all files from the list"),
        ]):
            b = ttk.Button(bar, text=label, command=cmd, style=style)
            b.grid(row=0, column=ci, padx=(0, 6))
            Tooltip(b, tip)

        copy_btn = ttk.Button(bar, text="⬇  Copy into repo",
                              style="Accent.TButton", command=self.copy_into_repo)
        copy_btn.grid(row=0, column=4, sticky="e")
        Tooltip(copy_btn, "Copy sorted files into  projects/<name>/")

        tbl_wrap = ttk.Frame(col, style="Card.TFrame", padding=2)
        tbl_wrap.grid(row=2, column=0, sticky="nsew")
        tbl_wrap.columnconfigure(0, weight=1)
        tbl_wrap.rowconfigure(1, weight=1)

        self._drop_zone = tk.Label(
            tbl_wrap,
            text="⬇   Drop a project folder here\nor use  ＋ Folder  above",
            bg=C["surf2"], fg=C["dim"], font=("Inter", 13),
            cursor="hand2", justify="center",
        )
        self._drop_zone.grid(row=1, column=0, sticky="nsew")
        self._drop_zone.bind("<Button-1>", lambda _: self.pick_folder())
        if DND_FILES and TkinterDnD:
            self._drop_zone.drop_target_register(DND_FILES)
            self._drop_zone.dnd_bind("<<Drop>>", self.on_drop)

        self.file_table = ttk.Treeview(
            tbl_wrap, columns=("cat", "file", "status"),
            show="headings", selectmode="extended",
        )
        self.file_table.heading("cat",    text="FOLDER")
        self.file_table.heading("file",   text="FILE")
        self.file_table.heading("status", text="STATUS")
        self.file_table.column("cat",    width=110, anchor="center", stretch=False)
        self.file_table.column("file",   width=430, anchor="w")
        self.file_table.column("status", width=90,  anchor="center", stretch=False)

        vsb = ttk.Scrollbar(tbl_wrap, orient="vertical", command=self.file_table.yview)
        self.file_table.configure(yscrollcommand=vsb.set)
        vsb.grid(row=1, column=1, sticky="ns")

        self.file_table.bind("<Double-1>",  self._on_double_click)
        self.file_table.bind("<Delete>",    lambda _: self._remove_selected())
        self.file_table.bind("<BackSpace>", lambda _: self._remove_selected())
        self._bind_context_menu()

        self._stats_bar = ttk.Frame(tbl_wrap, style="Card.TFrame", padding=(8, 4))
        self._stats_bar.grid(row=2, column=0, columnspan=2, sticky="ew")

    # ── Organiser — right panel ───────────────────────────────────────────────
    def _build_right(self, parent: ttk.Frame) -> None:
        col = ttk.Frame(parent, style="App.TFrame")
        col.grid(row=0, column=2, sticky="nsew")
        col.columnconfigure(0, weight=1)
        col.rowconfigure(2, weight=1)

        git_card = ttk.Frame(col, style="Card.TFrame", padding=(14, 12))
        git_card.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        git_card.columnconfigure(0, weight=1)

        ttk.Label(git_card, text="COMMIT MESSAGE", style="Head.TLabel").pack(anchor="w")
        ttk.Entry(git_card, textvariable=self.commit_message).pack(fill="x", pady=(4, 10))

        row = ttk.Frame(git_card, style="Card.TFrame")
        row.pack(fill="x")
        row.columnconfigure((0, 1, 2), weight=1)
        commit_btn = ttk.Button(row, text="✓  Commit", command=self.git_commit)
        commit_btn.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        Tooltip(commit_btn, "git add + git commit")
        pull_btn = ttk.Button(row, text="↓  Pull", command=self.git_pull)
        pull_btn.grid(row=0, column=1, sticky="ew", padx=(0, 6))
        Tooltip(pull_btn, "git pull --rebase from origin")
        push_btn = ttk.Button(row, text="↑  Push", style="Go.TButton", command=self.git_push)
        push_btn.grid(row=0, column=2, sticky="ew")
        Tooltip(push_btn, "git push to origin")

        ref_btn = ttk.Button(git_card, text="⟳  Refresh status",
                             command=self.refresh_status, padding=(8, 5))
        ref_btn.pack(fill="x", pady=(8, 0))

        guide = ttk.Frame(col, style="Card.TFrame", padding=(14, 12))
        guide.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        ttk.Label(guide, text="WORKFLOW", style="Head.TLabel").pack(anchor="w", pady=(0, 8))
        for num, text in [
            ("1", "Name your project  (e.g.  01_nand2)"),
            ("2", "Drop or add your project folder"),
            ("3", "Verify categories in the table"),
            ("4", "Click  ⬇ Copy into repo"),
            ("5", "Write a commit message & commit"),
            ("6", "Push to GitHub"),
        ]:
            r = ttk.Frame(guide, style="Card.TFrame")
            r.pack(fill="x", pady=2)
            tk.Label(r, text=f" {num} ", bg=C["accent"], fg="#fff",
                     font=("Inter", 8, "bold"), padx=3, pady=2).pack(side="left")
            ttk.Label(r, text=f"  {text}", style="Card.TLabel",
                      font=("Inter", 9)).pack(side="left")

        log_card = ttk.Frame(col, style="Card.TFrame")
        log_card.grid(row=2, column=0, sticky="nsew")
        log_card.columnconfigure(0, weight=1)
        log_card.rowconfigure(1, weight=1)

        ttk.Label(log_card, text="GIT OUTPUT", style="Head.TLabel",
                  padding=(12, 8, 0, 4)).grid(row=0, column=0, sticky="w")

        mono = ("JetBrains Mono" if self._font_exists("JetBrains Mono")
                else "Menlo" if self._font_exists("Menlo") else "Courier")
        self.output = tk.Text(
            log_card, wrap="word",
            bg="#0d1117", fg="#c9d1d9",
            insertbackground="#c9d1d9",
            selectbackground=C["border"],
            font=(mono, 9), relief="flat", padx=12, pady=8, spacing1=2,
        )
        self.output.grid(row=1, column=0, sticky="nsew")
        for tag, fg in (("ok","#3fb950"),("err","#f85149"),("warn","#d29922"),("info","#58a6ff")):
            self.output.tag_configure(tag, foreground=fg)
        self.output.configure(state="disabled")

        vsb2 = ttk.Scrollbar(log_card, orient="vertical", command=self.output.yview)
        vsb2.grid(row=1, column=1, sticky="ns")
        self.output.configure(yscrollcommand=vsb2.set)

    # ── GitHub Browser tab ────────────────────────────────────────────────────
    def _build_browser(self, parent: ttk.Frame) -> None:
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(1, weight=1)

        # ── Connect strip ─────────────────────────────────────────────────────
        cs = ttk.Frame(parent, style="Card.TFrame", padding=(14, 10))
        cs.grid(row=0, column=0, sticky="ew", pady=(0, 8))

        ttk.Label(cs, text="OWNER", style="Head.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Entry(cs, textvariable=self._gh_owner, width=18).grid(
            row=1, column=0, sticky="ew", padx=(0, 8), pady=(4, 0))

        ttk.Label(cs, text="REPO", style="Head.TLabel").grid(row=0, column=1, sticky="w")
        ttk.Entry(cs, textvariable=self._gh_repo, width=22).grid(
            row=1, column=1, sticky="ew", padx=(0, 8), pady=(4, 0))

        ttk.Label(cs, text="PERSONAL ACCESS TOKEN", style="Head.TLabel").grid(
            row=0, column=2, sticky="w")
        self._token_entry = ttk.Entry(cs, textvariable=self._gh_token,
                                      width=36, show="●")
        self._token_entry.grid(row=1, column=2, sticky="ew", padx=(0, 8), pady=(4, 0))

        show_btn = ttk.Button(cs, text="👁", width=3,
                              command=self._toggle_token_visibility, padding=(4, 6))
        show_btn.grid(row=1, column=3, padx=(0, 8), pady=(4, 0))
        Tooltip(show_btn, "Show / hide token")

        conn_btn = ttk.Button(cs, text="🔌  Connect", style="Accent.TButton",
                              command=self._connect_github, padding=(12, 6))
        conn_btn.grid(row=1, column=4, pady=(4, 0))

        self._conn_status = ttk.Label(cs, textvariable=self._gh_status,
                                      style="Head.TLabel", padding=(10, 0))
        self._conn_status.grid(row=1, column=5, padx=(4, 0), pady=(4, 0))
        cs.columnconfigure(2, weight=1)

        # ── Main pane ─────────────────────────────────────────────────────────
        pane = ttk.Frame(parent, style="App.TFrame")
        pane.grid(row=1, column=0, sticky="nsew")
        pane.columnconfigure(0, weight=1)
        pane.columnconfigure(2, weight=2)
        pane.rowconfigure(0, weight=1)

        # Tree panel
        tree_card = ttk.Frame(pane, style="Card.TFrame", padding=(0, 0))
        tree_card.grid(row=0, column=0, sticky="nsew")
        tree_card.columnconfigure(0, weight=1)
        tree_card.rowconfigure(1, weight=1)

        tree_hdr = ttk.Frame(tree_card, style="Card.TFrame", padding=(12, 8, 8, 6))
        tree_hdr.grid(row=0, column=0, columnspan=2, sticky="ew")
        ttk.Label(tree_hdr, text="REPOSITORY TREE", style="Head.TLabel").pack(side="left")

        self._gh_tree = ttk.Treeview(tree_card, show="tree", selectmode="browse")
        self._gh_tree.column("#0", minwidth=260, stretch=True)
        vsb_t = ttk.Scrollbar(tree_card, orient="vertical",   command=self._gh_tree.yview)
        hsb_t = ttk.Scrollbar(tree_card, orient="horizontal", command=self._gh_tree.xview)
        self._gh_tree.configure(yscrollcommand=vsb_t.set, xscrollcommand=hsb_t.set)
        self._gh_tree.grid(row=1, column=0, sticky="nsew")
        vsb_t.grid(row=1, column=1, sticky="ns")
        hsb_t.grid(row=2, column=0, sticky="ew")
        self._gh_tree.bind("<<TreeviewSelect>>", self._on_tree_select)
        self._gh_tree.bind("<Double-1>",          self._on_tree_double_click)

        ttk.Separator(pane, orient="vertical").grid(row=0, column=1, sticky="ns", padx=8)

        # Editor panel
        ed_card = ttk.Frame(pane, style="Card.TFrame", padding=(0, 0))
        ed_card.grid(row=0, column=2, sticky="nsew")
        ed_card.columnconfigure(0, weight=1)
        ed_card.rowconfigure(2, weight=1)

        ed_hdr = ttk.Frame(ed_card, style="Card.TFrame", padding=(12, 8, 8, 6))
        ed_hdr.grid(row=0, column=0, columnspan=2, sticky="ew")
        ttk.Label(ed_hdr, text="EDITOR", style="Head.TLabel").pack(side="left")
        self._edit_path_lbl = ttk.Label(ed_hdr, text="Select a file in the tree →",
                                        style="Chip.TLabel", padding=(8, 2))
        self._edit_path_lbl.pack(side="left", padx=(8, 0))

        ed_btns = ttk.Frame(ed_card, style="Card.TFrame", padding=(10, 6))
        ed_btns.grid(row=1, column=0, columnspan=2, sticky="ew")
        save_btn = ttk.Button(ed_btns, text="✓  Save to GitHub",
                              style="Go.TButton", command=self._gh_save)
        save_btn.pack(side="left")
        Tooltip(save_btn, "Commit this file directly to GitHub")
        ttk.Button(ed_btns, text="✕  Cancel",
                   command=self._gh_cancel_edit).pack(side="left", padx=(8, 0))

        self._editor = tk.Text(
            ed_card, wrap="none",
            bg="#0d1117", fg="#c9d1d9",
            insertbackground="#c9d1d9",
            selectbackground=C["border"],
            font=("Menlo" if self._font_exists("Menlo") else "Courier", 10),
            relief="flat", padx=12, pady=8,
        )
        self._editor.grid(row=2, column=0, sticky="nsew")
        vsb_e = ttk.Scrollbar(ed_card, orient="vertical",   command=self._editor.yview)
        hsb_e = ttk.Scrollbar(ed_card, orient="horizontal", command=self._editor.xview)
        self._editor.configure(yscrollcommand=vsb_e.set, xscrollcommand=hsb_e.set)
        vsb_e.grid(row=2, column=1, sticky="ns")
        hsb_e.grid(row=3, column=0, sticky="ew")

        # ── Action bar ────────────────────────────────────────────────────────
        act = ttk.Frame(parent, style="App.TFrame", padding=(0, 8, 0, 0))
        act.grid(row=2, column=0, sticky="ew")

        for label, cmd, style, tip in [
            ("⟳  Refresh",     self._gh_refresh,     "TButton",    "Reload tree from GitHub"),
            ("＋ Upload File",  self._gh_upload,       "TButton",    "Upload a local file to selected folder"),
            ("📁 New Folder",   self._gh_new_folder,   "TButton",    "Create a new folder in selected location"),
            ("✎  Edit File",   self._gh_edit,         "Accent.TButton","Load selected file into editor"),
            ("✕  Delete",      self._gh_delete,       "Del.TButton","Delete selected file or folder"),
        ]:
            b = ttk.Button(act, text=label, command=cmd, style=style)
            b.pack(side="left", padx=(0, 8))
            Tooltip(b, tip)

        # ── Browser log ───────────────────────────────────────────────────────
        log_row = ttk.Frame(parent, style="App.TFrame")
        log_row.grid(row=3, column=0, sticky="ew", pady=(6, 0))
        log_row.columnconfigure(0, weight=1)

        self._gh_log_var = tk.StringVar(value="")
        self._gh_log_lbl = ttk.Label(log_row, textvariable=self._gh_log_var,
                                     style="Sub.TLabel", padding=(2, 0))
        self._gh_log_lbl.grid(row=0, column=0, sticky="w")

    # ── Footer ────────────────────────────────────────────────────────────────
    def _build_footer(self) -> None:
        ttk.Separator(self.root).grid(row=2, column=0, sticky="ew")
        foot = ttk.Frame(self.root, style="App.TFrame", padding=(18, 5, 18, 8))
        foot.grid(row=3, column=0, sticky="ew")
        ttk.Label(foot, text=f"Repo:  {REPO_ROOT}", style="Sub.TLabel").pack(side="left")
        ttk.Label(foot,
                  text="Double-click row to move folder  ·  Right-click for options  ·  Delete to remove",
                  style="Sub.TLabel").pack(side="right")

    # ── Helpers ───────────────────────────────────────────────────────────────
    @staticmethod
    def _font_exists(name: str) -> bool:
        try:
            import tkinter.font as tf
            return name in tf.families()
        except Exception:
            return False

    def _auto_commit_msg(self, *_) -> None:
        slug = slugify(self.project_name.get())
        self.commit_message.set(f"feat: add {slug} project")
        if self.dest_path.get().startswith("projects/"):
            self.dest_path.set(f"projects/{slug}")

    def log(self, text: str, tag: str = "") -> None:
        self.output.configure(state="normal")
        if tag:
            self.output.insert("end", text.rstrip() + "\n\n", tag)
        else:
            self.output.insert("end", text.rstrip() + "\n\n")
        self.output.see("end")
        self.output.configure(state="disabled")

    def _gh_log(self, text: str) -> None:
        self._gh_log_var.set(text)

    def _toggle_token_visibility(self) -> None:
        self._token_entry.configure(
            show="" if self._token_entry.cget("show") == "●" else "●")

    def _rebuild_stats(self) -> None:
        for w in self._stats_bar.winfo_children():
            w.destroy()
        if not self.entries:
            return
        counts: dict[str, int] = {}
        for e in self.entries:
            counts[e.target] = counts.get(e.target, 0) + 1
        for cat, n in sorted(counts.items()):
            color, icon = CAT.get(cat, ("#94a3b8", "• "))
            tk.Label(self._stats_bar, text=f"{icon}{cat}  {n}",
                     bg=C["surf"], fg=color, font=("Inter", 9),
                     padx=6, pady=1).pack(side="left", padx=(0, 4))

    def _sync_table_visibility(self) -> None:
        if self.entries:
            self._drop_zone.grid_remove()
            self.file_table.grid(row=1, column=0, sticky="nsew")
        else:
            self.file_table.grid_remove()
            self._drop_zone.grid(row=1, column=0, sticky="nsew")

    def refresh_table(self) -> None:
        self.file_table.delete(*self.file_table.get_children())
        for i, entry in enumerate(self.entries):
            color, icon = CAT.get(entry.target, ("#94a3b8", "• "))
            status = "✓ copied" if entry.copied_to else "ready"
            self.file_table.insert("", "end", iid=str(i),
                                   values=(f"{icon}{entry.target}",
                                           str(entry.source), status),
                                   tags=(entry.target,))
            self.file_table.tag_configure(entry.target, foreground=color)
        self.status_text.set(f"{len(self.entries)} file(s)")
        self._rebuild_stats()
        self._sync_table_visibility()

    def selected_indices(self) -> set[int]:
        return {int(x) for x in self.file_table.selection() if x.isdigit()}

    # ── Context menu ──────────────────────────────────────────────────────────
    def _bind_context_menu(self) -> None:
        ctx = tk.Menu(self.root, tearoff=0,
                      bg=C["surf"], fg=C["text"],
                      activebackground=C["accent"], activeforeground="#fff",
                      font=("Inter", 10))
        ctx.add_command(label="Remove selected", command=self._remove_selected)
        ctx.add_separator()
        for folder in PROJECT_FOLDERS:
            color, icon = CAT.get(folder, ("#94a3b8", "• "))
            ctx.add_command(label=f"{icon} Move to  {folder}/",
                            command=lambda f=folder: self._move_selected_to(f))
        for btn in ("<Button-2>", "<Button-3>"):
            self.file_table.bind(btn, lambda e, m=ctx: m.post(e.x_root, e.y_root))

    # ── File management (organiser) ───────────────────────────────────────────
    def add_paths(self, paths: list[Path], auto: bool = True) -> None:
        existing = {e.source for e in self.entries}
        added = 0
        for path in paths:
            path = path.expanduser().resolve()
            if path.is_dir():
                self.add_paths(
                    [f for f in path.rglob("*") if f.is_file() and not should_ignore(f)],
                    auto=auto)
                continue
            if not path.exists() or not path.is_file() \
                    or should_ignore(path) or path in existing:
                continue
            t = classify_file(path) if (auto or self.target_folder.get() == "auto") \
                else self.target_folder.get()
            self.entries.append(FileEntry(source=path, target=t))
            existing.add(path)
            added += 1
        self.refresh_table()
        if added:
            self.log(f"Added {added} file(s).", "info")

    def reclassify_entries(self) -> None:
        sel = self.selected_indices()
        chosen = self.target_folder.get()
        for i in sel or set(range(len(self.entries))):
            e = self.entries[i]
            e.target = classify_file(e.source) if chosen == "auto" else chosen
        self.refresh_table()
        self.log("Re-sorted files.", "info")

    def _remove_selected(self) -> None:
        for i in sorted(self.selected_indices(), reverse=True):
            self.entries.pop(i)
        self.refresh_table()

    def _move_selected_to(self, folder: str) -> None:
        for i in self.selected_indices():
            self.entries[i].target = folder
        self.refresh_table()

    def _on_double_click(self, event) -> None:
        if self.file_table.identify_region(event.x, event.y) != "cell":
            return
        if self.file_table.identify_column(event.x) != "#1":
            return
        row_id = self.file_table.identify_row(event.y)
        if not row_id or not row_id.isdigit():
            return
        index = int(row_id)

        pop = tk.Toplevel(self.root)
        pop.title("Move to folder")
        pop.configure(bg=C["surf"])
        pop.geometry("200x250")
        pop.resizable(False, False)
        ttk.Label(pop, text="Choose target folder:", style="Card.TLabel",
                  padding=(10, 8, 10, 4)).pack(anchor="w")
        for folder in PROJECT_FOLDERS:
            color, icon = CAT.get(folder, ("#94a3b8", "• "))
            tk.Button(
                pop, text=f"  {icon}{folder}",
                bg=C["surf2"], fg=color,
                activebackground=C["border"], activeforeground=color,
                font=("Inter", 10), relief="flat", padx=12, pady=6, anchor="w",
                command=lambda f=folder, p=pop, i=index: (
                    self.entries.__setitem__(
                        i, FileEntry(self.entries[i].source, f, self.entries[i].copied_to)),
                    self.refresh_table(), p.destroy()
                ),
            ).pack(fill="x", padx=8, pady=2)

    def on_drop(self, event) -> None:
        self.add_paths([Path(p) for p in self.root.tk.splitlist(event.data)])

    def pick_files(self) -> None:
        self.add_paths([Path(p) for p in filedialog.askopenfilenames(title="Choose files")])

    def pick_folder(self) -> None:
        sel = filedialog.askdirectory(title="Choose a project folder")
        if sel:
            self.add_paths([Path(sel)])

    def clear_files(self) -> None:
        self.entries.clear()
        self.refresh_table()
        self.log("Cleared.", "warn")

    def _pick_dest_folder(self) -> None:
        sel = filedialog.askdirectory(
            title="Choose destination folder inside repo",
            initialdir=str(REPO_ROOT),
        )
        if not sel:
            return
        sel_path = Path(sel).resolve()
        try:
            rel = sel_path.relative_to(REPO_ROOT)
            self.dest_path.set(str(rel))
        except ValueError:
            messagebox.showerror("Outside repo",
                                 f"That folder is outside the repo root:\n{REPO_ROOT}\n\n"
                                 "Choose a folder inside the repo.")

    def project_dir(self) -> Path:
        dest = self.dest_path.get().strip().lstrip("/")
        return REPO_ROOT / dest if dest else REPO_ROOT / "projects" / slugify(self.project_name.get())

    def copy_into_repo(self) -> None:
        if not self.entries:
            messagebox.showinfo("No files", "Add at least one file first.")
            return
        proj = self.project_dir()
        copied: list[Path] = []
        for entry in self.entries:
            d = proj / entry.target
            d.mkdir(parents=True, exist_ok=True)
            dest = unique_destination(d / entry.source.name)
            shutil.copy2(entry.source, dest)
            entry.copied_to = dest
            copied.append(dest)

        if self.create_readme.get():
            self._ensure_readme(proj)

        name = self.project_name.get().strip()
        if name and name not in self.history:
            self.history.insert(0, name)
            save_history(self.history)
            self._name_box["values"] = self.history

        self.refresh_table()
        lines = "\n".join(f"  {p.relative_to(REPO_ROOT)}" for p in copied[:15])
        if len(copied) > 15:
            lines += f"\n  … and {len(copied) - 15} more"
        self.log(f"Copied {len(copied)} file(s) into"
                 f" {proj.relative_to(REPO_ROOT)}:\n{lines}", "ok")
        self.refresh_status()

    def _ensure_readme(self, proj: Path) -> None:
        readme = proj / "README.md"
        if readme.exists():
            return
        title = self.project_name.get().strip() or proj.name
        readme.write_text(
            f"# {title}\n\n"
            "## Goal\nDescribe what this digital design does and why it matters.\n\n"
            "## Files\n"
            "- `rtl/`: design source\n- `tb/`: testbench files\n"
            "- `sim/`: simulation scripts\n- `waves/`: waveform files\n"
            "- `synthesis/`: Yosys scripts, netlists, reports\n"
            "- `docs/`: diagrams and notes\n\n"
            "## How to Run\n```bash\ncd sim\n# iverilog / verilator command here\n```\n\n"
            "## Results\nAdd waveform screenshots and observations here.\n",
            encoding="utf-8",
        )
        self.log(f"Created {readme.relative_to(REPO_ROOT)}", "info")

    # ── Git (organiser tab) ───────────────────────────────────────────────────
    def git_commit(self) -> None:
        msg   = self.commit_message.get().strip() or "feat: add project files"
        paths = [p for p in GIT_MANAGED if (REPO_ROOT / p).exists()]
        code, out = run_git(["add", *paths])
        if code != 0:
            self.log(out, "err"); messagebox.showerror("git add failed", out); return
        code, out = run_git(["commit", "-m", msg, "--", *paths])
        tag = ("ok" if code == 0
               else "warn" if "nothing to commit" in out.lower() else "err")
        self.log(out or "Nothing to commit.", tag)
        if code != 0 and "nothing to commit" not in out.lower():
            messagebox.showerror("git commit failed", out); return
        self.refresh_status()

    def git_pull(self) -> None:
        self.log("Pulling from origin…", "info")

        cfg   = load_config()
        token = cfg.get("token", "").strip()
        owner = cfg.get("owner", "").strip()
        repo  = cfg.get("repo",  "").strip()
        url_args: list[str] = []
        if token and owner and repo:
            url_args = [f"https://{owner}:{token}@github.com/{owner}/{repo}.git", "main"]

        def worker() -> None:
            # Stash any uncommitted changes so rebase can proceed cleanly
            run_git(["stash"])
            c, out = run_git(["pull", "--rebase", *url_args], timeout=120)
            run_git(["stash", "pop"])

            def done() -> None:
                safe = out.replace(token, "***") if token else out
                self.log(safe or "Pulled.", "ok" if c == 0 else "err")
                if c != 0:
                    messagebox.showerror("git pull failed", safe)
                self._refresh_git_info()
                self.refresh_status()

            self.root.after(0, done)

        threading.Thread(target=worker, daemon=True).start()

    def git_push(self) -> None:
        code, remotes = run_git(["remote"])
        if code != 0 or not remotes.strip():
            msg = "No remote configured.\nRun:  git remote add origin <url>"
            self.log(msg, "warn"); messagebox.showinfo("No remote", msg); return
        self.log("Pushing to origin...", "info")

        # Build an authenticated URL so Git never needs to prompt for credentials.
        cfg   = load_config()
        token = cfg.get("token", "").strip()
        owner = cfg.get("owner", "").strip()
        repo  = cfg.get("repo",  "").strip()
        push_args = ["push"]
        if token and owner and repo:
            push_args = ["push", f"https://{owner}:{token}@github.com/{owner}/{repo}.git", "HEAD:main"]

        def worker() -> None:
            c, out = run_git(push_args, timeout=120)

            def done() -> None:
                # Strip the token from any output before displaying
                safe_out = out.replace(token, "***") if token else out
                shown = safe_out if c == 0 else github_auth_hint(safe_out)
                self.log(shown or "Pushed.", "ok" if c == 0 else "err")
                if c != 0:
                    messagebox.showerror("git push failed", shown)
                self._refresh_git_info()
                self.refresh_status()

            self.root.after(0, done)

        threading.Thread(target=worker, daemon=True).start()

    def refresh_status(self) -> None:
        code, status = run_git(["status", "--short"])
        if code == 0:
            lines = status.splitlines()
            shown = "\n".join(lines[:24])
            if len(lines) > 24:
                shown += f"\n… {len(lines) - 24} more"
            self.log("git status:\n" + (shown or "clean — nothing to commit"), "info")

    def _refresh_git_info(self) -> None:
        _, branch = run_git(["rev-parse", "--abbrev-ref", "HEAD"])
        _, remote = run_git(["remote", "get-url", "origin"])
        parts: list[str] = []
        if branch:
            parts.append(f"⎇  {branch.strip()}")
        if remote:
            parts.append(remote.strip().replace("https://github.com/", ""))
        self.branch_text.set("  ·  ".join(parts))

    # ── GitHub Browser — connection ───────────────────────────────────────────
    def _connect_github(self) -> None:
        token = self._gh_token.get().strip()
        owner = self._gh_owner.get().strip()
        repo  = self._gh_repo.get().strip()
        if not (token and owner and repo):
            messagebox.showwarning("Missing info",
                                   "Fill in Owner, Repo, and Personal Access Token.")
            return
        self._gh_status.set("Connecting…")
        self._gh_log("Connecting to GitHub…")

        def worker():
            try:
                api = GitHubAPI(token, owner, repo)
                items = api.tree()
                self.gh_api = api
                save_config({"token": token, "owner": owner, "repo": repo})
                self.root.after(0, lambda: self._on_connected(items))
            except Exception as exc:
                self.root.after(0, lambda e=exc: self._on_connect_error(str(e)))

        threading.Thread(target=worker, daemon=True).start()

    def _on_connected(self, items: list[dict]) -> None:
        self._gh_status.set(f"✓ Connected  —  {len(items)} objects")
        self._gh_log(f"Loaded {len(items)} objects from GitHub.")
        self._populate_tree(items)

    def _on_connect_error(self, msg: str) -> None:
        self._gh_status.set("✗ Connection failed")
        self._gh_log(f"Error: {msg}")
        messagebox.showerror("GitHub connection failed", msg)

    # ── GitHub Browser — tree ─────────────────────────────────────────────────
    def _populate_tree(self, items: list[dict]) -> None:
        self._gh_tree.delete(*self._gh_tree.get_children())
        self._blob_shas.clear()

        sorted_items = sorted(items, key=lambda x: (x["path"].count("/"), x["path"]))

        for item in sorted_items:
            path   = item["path"]
            parent = str(Path(path).parent) if "/" in path else ""
            name   = Path(path).name

            if item["type"] == "tree":
                self._gh_tree.insert(parent, "end", iid=path,
                                     text=f"  📁  {name}", open=False)
            else:
                self._blob_shas[path] = item.get("sha", "")
                icon = self._file_icon(name)
                self._gh_tree.insert(parent, "end", iid=path,
                                     text=f"  {icon}  {name}")

    @staticmethod
    def _file_icon(name: str) -> str:
        n = name.lower()
        if n.endswith(("_tb.v", "_tb.sv", "_tb.vhd")):    return "⧉"
        if n.endswith((".v", ".sv", ".svh", ".vhd", ".vhdl")): return "⬡"
        if n.endswith((".vcd", ".fst", ".gtkw", ".sav")): return "〜"
        if n.endswith((".ys", ".rpt", ".rep")):            return "⬢"
        if n.endswith((".sh", ".mk")) or n == "makefile":  return "⚙"
        if n.endswith(".md"):                              return "◎"
        if n.endswith(".py"):                              return "◈"
        if n.endswith((".json", ".yaml", ".yml")):         return " {}"
        if n.endswith((".png", ".jpg", ".gif", ".svg")):   return "▣"
        if n.endswith(".pdf"):                             return "▤"
        if n in (".gitignore", ".gitkeep", ".gitattributes"): return "◌"
        return "◇"

    def _on_tree_select(self, _event=None) -> None:
        sel = self._gh_tree.selection()
        if not sel:
            return
        path = sel[0]
        if path in self._blob_shas:
            self._edit_path_lbl.configure(text=f"  {path}")
        else:
            self._edit_path_lbl.configure(text=f"  📁 {path}/")

    def _on_tree_double_click(self, _event=None) -> None:
        sel = self._gh_tree.selection()
        if sel and sel[0] in self._blob_shas:
            self._gh_edit()

    def _selected_tree_path(self) -> str | None:
        sel = self._gh_tree.selection()
        return sel[0] if sel else None

    def _selected_parent_path(self) -> str:
        path = self._selected_tree_path()
        if not path:
            return ""
        if path in self._blob_shas:
            return str(Path(path).parent) if "/" in path else ""
        return path

    # ── GitHub Browser — edit / save ──────────────────────────────────────────
    def _gh_edit(self) -> None:
        if not self.gh_api:
            messagebox.showinfo("Not connected", "Connect to GitHub first."); return
        path = self._selected_tree_path()
        if not path or path not in self._blob_shas:
            messagebox.showinfo("Select a file", "Select a file (not a folder) in the tree."); return

        self._gh_log(f"Loading {path} …")

        def worker():
            try:
                data    = self.gh_api.file(path)  # type: ignore[union-attr]
                content = base64.b64decode(data["content"]).decode("utf-8")
                sha     = data["sha"]
                self.root.after(0, lambda: self._load_editor(path, content, sha))
            except UnicodeDecodeError:
                self.root.after(0, lambda: self._load_editor(
                    path, "⚠  Binary file — cannot edit as text.", ""))
            except Exception as exc:
                self.root.after(0, lambda e=exc: self._gh_log(f"Error: {e}"))

        threading.Thread(target=worker, daemon=True).start()

    def _load_editor(self, path: str, content: str, sha: str) -> None:
        self._edit_path = path
        self._edit_sha  = sha
        self._edit_path_lbl.configure(text=f"  ✎  {path}")
        self._editor.configure(state="normal")
        self._editor.delete("1.0", "end")
        self._editor.insert("1.0", content)
        self._gh_log(f"Loaded: {path}")

    def _gh_save(self) -> None:
        if not self.gh_api:
            messagebox.showinfo("Not connected", "Connect to GitHub first."); return
        if not self._edit_path:
            messagebox.showinfo("Nothing to save", "Open a file in the editor first."); return

        content = self._editor.get("1.0", "end-1c")
        msg     = simpledialog.askstring(
            "Commit message",
            f"Message for  {self._edit_path}:",
            initialvalue=f"edit: update {Path(self._edit_path).name}",
            parent=self.root,
        )
        if not msg:
            return

        self._gh_log(f"Saving {self._edit_path} …")

        def worker():
            try:
                self.gh_api.put(self._edit_path, content,  # type: ignore[union-attr]
                                self._edit_sha or None, msg)
                self.root.after(0, lambda: (
                    self._gh_log(f"✓ Saved  {self._edit_path}"),
                    self._gh_refresh(),
                ))
            except Exception as exc:
                self.root.after(0, lambda e=exc: (
                    self._gh_log(f"Save failed: {e}"),
                    messagebox.showerror("Save failed", str(e)),
                ))

        threading.Thread(target=worker, daemon=True).start()

    def _gh_cancel_edit(self) -> None:
        self._editor.delete("1.0", "end")
        self._edit_path = ""
        self._edit_sha  = ""
        self._edit_path_lbl.configure(text="Select a file in the tree →")
        self._gh_log("Edit cancelled.")

    # ── GitHub Browser — delete ───────────────────────────────────────────────
    def _gh_delete(self) -> None:
        if not self.gh_api:
            messagebox.showinfo("Not connected", "Connect to GitHub first."); return
        path = self._selected_tree_path()
        if not path:
            messagebox.showinfo("Nothing selected", "Select a file or folder in the tree."); return

        is_file   = path in self._blob_shas
        is_folder = not is_file
        label     = f"file  {path}" if is_file else f"folder  {path}/  and all its contents"

        if not messagebox.askyesno("Delete?",
                                   f"Permanently delete {label} from GitHub?\n\nThis cannot be undone.",
                                   icon="warning"):
            return

        if is_file:
            targets = {path: self._blob_shas[path]}
        else:
            prefix  = path + "/"
            targets = {p: s for p, s in self._blob_shas.items()
                       if p == path or p.startswith(prefix)}

        if not targets:
            messagebox.showinfo("Empty folder",
                                "No files found to delete (folder may already be empty)."); return

        self._gh_log(f"Deleting {len(targets)} file(s)…")

        def worker():
            deleted = 0
            errors: list[str] = []
            for p, sha in targets.items():
                try:
                    self.gh_api.delete(p, sha, f"remove: delete {Path(p).name}")  # type: ignore[union-attr]
                    deleted += 1
                except Exception as exc:
                    errors.append(f"{p}: {exc}")
            def done():
                msg = f"✓ Deleted {deleted} file(s)."
                if errors:
                    msg += f"  {len(errors)} error(s): {errors[0]}"
                self._gh_log(msg)
                self._gh_refresh()
            self.root.after(0, done)

        threading.Thread(target=worker, daemon=True).start()

    # ── GitHub Browser — create ───────────────────────────────────────────────
    def _gh_upload(self) -> None:
        if not self.gh_api:
            messagebox.showinfo("Not connected", "Connect to GitHub first."); return

        local = filedialog.askopenfilename(title="Choose a file to upload")
        if not local:
            return

        parent = self._selected_parent_path()
        name   = Path(local).name
        dest   = f"{parent}/{name}".lstrip("/")

        dest_input = simpledialog.askstring(
            "Destination path",
            "Path in repository (edit if needed):",
            initialvalue=dest,
            parent=self.root,
        )
        if not dest_input:
            return

        try:
            content = Path(local).read_text(encoding="utf-8")
        except UnicodeDecodeError:
            messagebox.showerror("Binary file",
                                 "Binary files cannot be uploaded via this editor.\n"
                                 "Use git push for images/PDFs."); return

        existing_sha = self._blob_shas.get(dest_input.strip())
        msg = simpledialog.askstring(
            "Commit message",
            f"Message for upload of  {name}:",
            initialvalue=f"feat: add {name}",
            parent=self.root,
        )
        if not msg:
            return

        self._gh_log(f"Uploading {name} …")

        def worker():
            try:
                self.gh_api.put(dest_input.strip(), content, existing_sha, msg)  # type: ignore[union-attr]
                self.root.after(0, lambda: (
                    self._gh_log(f"✓ Uploaded  {dest_input.strip()}"),
                    self._gh_refresh(),
                ))
            except Exception as exc:
                self.root.after(0, lambda e=exc: (
                    self._gh_log(f"Upload failed: {e}"),
                    messagebox.showerror("Upload failed", str(e)),
                ))

        threading.Thread(target=worker, daemon=True).start()

    def _gh_new_folder(self) -> None:
        if not self.gh_api:
            messagebox.showinfo("Not connected", "Connect to GitHub first."); return

        parent = self._selected_parent_path()
        name   = simpledialog.askstring("New folder", "Folder name:",
                                        parent=self.root)
        if not name:
            return

        path = f"{parent}/{name}/.gitkeep".lstrip("/")
        msg  = simpledialog.askstring("Commit message", "Commit message:",
                                      initialvalue=f"feat: create {name}/",
                                      parent=self.root)
        if not msg:
            return

        self._gh_log(f"Creating folder {name}/ …")

        def worker():
            try:
                self.gh_api.put(path, "", None, msg)  # type: ignore[union-attr]
                self.root.after(0, lambda: (
                    self._gh_log(f"✓ Created folder {name}/"),
                    self._gh_refresh(),
                ))
            except Exception as exc:
                self.root.after(0, lambda e=exc: (
                    self._gh_log(f"Create failed: {e}"),
                    messagebox.showerror("Create failed", str(e)),
                ))

        threading.Thread(target=worker, daemon=True).start()

    # ── GitHub Browser — refresh ──────────────────────────────────────────────
    def _gh_refresh(self) -> None:
        if not self.gh_api:
            messagebox.showinfo("Not connected", "Connect to GitHub first."); return
        self._gh_log("Refreshing tree…")

        def worker():
            try:
                items = self.gh_api.tree()  # type: ignore[union-attr]
                self.root.after(0, lambda: (
                    self._populate_tree(items),
                    self._gh_log(f"✓ Refreshed — {len(items)} objects"),
                ))
            except Exception as exc:
                self.root.after(0, lambda e=exc: self._gh_log(f"Refresh failed: {e}"))

        threading.Thread(target=worker, daemon=True).start()


# ── Entry point ───────────────────────────────────────────────────────────────
def main() -> int:
    root = TkinterDnD.Tk() if TkinterDnD else tk.Tk()
    RepoDropper(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
