#!/usr/bin/env python3
"""Friendly GUI for sorting VLSI project files into this repo."""

from __future__ import annotations

from dataclasses import dataclass
import re
import shutil
import subprocess
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
except Exception:  # pragma: no cover - optional desktop dependency
    DND_FILES = None
    TkinterDnD = None


APP_DIR = Path(__file__).resolve().parent
REPO_ROOT = APP_DIR.parents[1]
PROJECT_FOLDERS = ("rtl", "tb", "sim", "waves", "synthesis", "docs")
IGNORED_DIRS = {
    ".git",
    ".pio",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
}
GIT_MANAGED_PATHS = (".gitignore", "projects", "run_repo_dropper.sh", "tools/repo_dropper")


@dataclass
class FileEntry:
    source: Path
    target: str
    copied_to: Path | None = None


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    value = re.sub(r"_+", "_", value).strip("_")
    return value or "new_project"


def unique_destination(path: Path) -> Path:
    if not path.exists():
        return path

    stem = path.stem
    suffix = path.suffix
    parent = path.parent
    counter = 2
    while True:
        candidate = parent / f"{stem}_{counter}{suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def classify_file(path: Path, fallback: str = "docs") -> str:
    name = path.name.lower()
    suffix = path.suffix.lower()

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
    return any(part in IGNORED_DIRS for part in path.parts)


def run_git(args: list[str]) -> tuple[int, str]:
    proc = subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    output = "\n".join(part for part in (proc.stdout.strip(), proc.stderr.strip()) if part)
    return proc.returncode, output


class RepoDropper:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Repo Dropper - VLSI Portfolio Helper")
        self.root.geometry("1020x680")
        self.root.minsize(920, 620)

        self.entries: list[FileEntry] = []
        self.project_name = tk.StringVar(value="01_nand2")
        self.target_folder = tk.StringVar(value="auto")
        self.commit_message = tk.StringVar(value="Add NAND2 gate project")
        self.create_readme = tk.BooleanVar(value=True)
        self.status_text = tk.StringVar(value="Ready")

        self.configure_style()
        self.build_ui()
        self.refresh_status()

    def configure_style(self) -> None:
        self.root.configure(bg="#eef2f5")
        self.style = ttk.Style(self.root)
        self.style.theme_use("clam")
        self.style.configure(".", font=("Inter", 10))
        self.style.configure("App.TFrame", background="#eef2f5")
        self.style.configure("Panel.TFrame", background="#ffffff", relief="flat")
        self.style.configure("Title.TLabel", background="#eef2f5", foreground="#102a43", font=("Inter", 18, "bold"))
        self.style.configure("Muted.TLabel", background="#eef2f5", foreground="#52616b")
        self.style.configure("PanelTitle.TLabel", background="#ffffff", foreground="#102a43", font=("Inter", 11, "bold"))
        self.style.configure("Panel.TLabel", background="#ffffff", foreground="#243b53")
        self.style.configure("Primary.TButton", background="#2563eb", foreground="#ffffff", padding=(12, 8))
        self.style.map("Primary.TButton", background=[("active", "#1d4ed8")])
        self.style.configure("TButton", padding=(10, 7))
        self.style.configure("TEntry", padding=7)
        self.style.configure("Treeview", rowheight=30, borderwidth=0)
        self.style.configure("Treeview.Heading", font=("Inter", 10, "bold"))

    def build_ui(self) -> None:
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(2, weight=1)

        top = ttk.Frame(self.root, style="App.TFrame", padding=(18, 16, 18, 10))
        top.grid(row=0, column=0, sticky="ew")
        top.columnconfigure(1, weight=1)
        ttk.Label(top, text="Repo Dropper", style="Title.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(
            top,
            text="Sort RTL, testbench, waveforms, and synthesis files into a clean GitHub portfolio.",
            style="Muted.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(3, 0))
        ttk.Label(top, textvariable=self.status_text, style="Muted.TLabel").grid(row=0, column=1, sticky="e")

        setup = ttk.Frame(self.root, style="Panel.TFrame", padding=16)
        setup.grid(row=1, column=0, sticky="ew", padx=18, pady=(0, 12))
        setup.columnconfigure(1, weight=1)
        setup.columnconfigure(4, weight=1)

        ttk.Label(setup, text="1. Project", style="PanelTitle.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Entry(setup, textvariable=self.project_name).grid(row=1, column=0, columnspan=2, sticky="ew", pady=(8, 0))

        ttk.Label(setup, text="2. Placement", style="PanelTitle.TLabel").grid(row=0, column=2, sticky="w", padx=(18, 0))
        folder_menu = ttk.OptionMenu(
            setup,
            self.target_folder,
            self.target_folder.get(),
            "auto",
            *PROJECT_FOLDERS,
            command=lambda _: self.reclassify_entries(),
        )
        folder_menu.grid(row=1, column=2, sticky="ew", padx=(18, 0), pady=(8, 0))

        ttk.Checkbutton(setup, text="Create project README", variable=self.create_readme).grid(
            row=1, column=3, sticky="w", padx=(18, 0), pady=(8, 0)
        )

        ttk.Label(setup, text="3. Git message", style="PanelTitle.TLabel").grid(row=0, column=4, sticky="w", padx=(18, 0))
        ttk.Entry(setup, textvariable=self.commit_message).grid(row=1, column=4, sticky="ew", padx=(18, 0), pady=(8, 0))

        body = ttk.Frame(self.root, style="App.TFrame")
        body.grid(row=2, column=0, sticky="nsew", padx=18)
        body.columnconfigure(0, weight=3)
        body.columnconfigure(1, weight=2)
        body.rowconfigure(0, weight=1)

        left = ttk.Frame(body, style="Panel.TFrame", padding=16)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        left.columnconfigure(0, weight=1)
        left.rowconfigure(2, weight=1)

        self.drop_label = tk.Label(
            left,
            text="Drop files or a folder here",
            bg="#e8f1ff",
            fg="#173b72",
            activebackground="#dbeafe",
            relief="flat",
            height=5,
            font=("Inter", 13, "bold"),
            cursor="hand2",
        )
        self.drop_label.grid(row=0, column=0, sticky="ew")
        self.drop_label.bind("<Button-1>", lambda _event: self.pick_folder())

        if DND_FILES and TkinterDnD:
            self.drop_label.drop_target_register(DND_FILES)
            self.drop_label.dnd_bind("<<Drop>>", self.on_drop)
        else:
            self.drop_label.config(text="Click to choose a folder. Install tkinterdnd2 for drag-and-drop.")

        action_bar = ttk.Frame(left, style="Panel.TFrame")
        action_bar.grid(row=1, column=0, sticky="ew", pady=(12, 10))
        action_bar.columnconfigure(5, weight=1)
        ttk.Button(action_bar, text="Add files", command=self.pick_files).grid(row=0, column=0, padx=(0, 8))
        ttk.Button(action_bar, text="Add folder", command=self.pick_folder).grid(row=0, column=1, padx=(0, 8))
        ttk.Button(action_bar, text="Auto-sort", command=self.reclassify_entries).grid(row=0, column=2, padx=(0, 8))
        ttk.Button(action_bar, text="Clear", command=self.clear_files).grid(row=0, column=3, padx=(0, 8))
        ttk.Button(action_bar, text="Copy into repo", style="Primary.TButton", command=self.copy_into_repo).grid(
            row=0, column=4
        )

        self.file_table = ttk.Treeview(
            left,
            columns=("target", "source", "status"),
            show="headings",
            selectmode="extended",
        )
        self.file_table.heading("target", text="Goes to")
        self.file_table.heading("source", text="Source file")
        self.file_table.heading("status", text="Status")
        self.file_table.column("target", width=110, anchor="center", stretch=False)
        self.file_table.column("source", width=470, anchor="w")
        self.file_table.column("status", width=120, anchor="center", stretch=False)
        self.file_table.grid(row=2, column=0, sticky="nsew")
        scroll = ttk.Scrollbar(left, orient="vertical", command=self.file_table.yview)
        scroll.grid(row=2, column=1, sticky="ns")
        self.file_table.configure(yscrollcommand=scroll.set)

        right = ttk.Frame(body, style="Panel.TFrame", padding=16)
        right.grid(row=0, column=1, sticky="nsew")
        right.columnconfigure(0, weight=1)
        right.rowconfigure(3, weight=1)

        ttk.Label(right, text="Workflow", style="PanelTitle.TLabel").grid(row=0, column=0, sticky="w")
        workflow = (
            "1. Name the project, like 01_nand2.\n"
            "2. Add your folder or files.\n"
            "3. Keep Placement on auto for VLSI files.\n"
            "4. Copy into repo.\n"
            "5. Commit, then push."
        )
        ttk.Label(right, text=workflow, style="Panel.TLabel", justify="left").grid(row=1, column=0, sticky="ew", pady=(8, 16))

        git_buttons = ttk.Frame(right, style="Panel.TFrame")
        git_buttons.grid(row=2, column=0, sticky="ew", pady=(0, 12))
        git_buttons.columnconfigure(0, weight=1)
        git_buttons.columnconfigure(1, weight=1)
        ttk.Button(git_buttons, text="Git add + commit", command=self.git_commit).grid(row=0, column=0, sticky="ew", padx=(0, 8))
        ttk.Button(git_buttons, text="Push", style="Primary.TButton", command=self.git_push).grid(row=0, column=1, sticky="ew")

        self.output = tk.Text(
            right,
            height=16,
            wrap="word",
            bg="#0f172a",
            fg="#dbeafe",
            insertbackground="#dbeafe",
            relief="flat",
            padx=10,
            pady=10,
        )
        self.output.grid(row=3, column=0, sticky="nsew")
        self.output.configure(state="disabled")

        footer = ttk.Frame(self.root, style="App.TFrame", padding=(18, 10, 18, 16))
        footer.grid(row=3, column=0, sticky="ew")
        ttk.Label(
            footer,
            text=f"Repo: {REPO_ROOT}",
            style="Muted.TLabel",
        ).grid(row=0, column=0, sticky="w")

    def log(self, text: str) -> None:
        self.output.configure(state="normal")
        self.output.insert("end", text.rstrip() + "\n\n")
        self.output.see("end")
        self.output.configure(state="disabled")

    def refresh_table(self) -> None:
        self.file_table.delete(*self.file_table.get_children())
        for index, entry in enumerate(self.entries):
            status = "copied" if entry.copied_to else "ready"
            self.file_table.insert(
                "",
                "end",
                iid=str(index),
                values=(entry.target, str(entry.source), status),
            )
        self.status_text.set(f"{len(self.entries)} file(s) selected")

    def selected_indices(self) -> set[int]:
        return {int(item) for item in self.file_table.selection() if item.isdigit()}

    def add_paths(self, paths: list[Path], auto_classify: bool = True) -> None:
        existing = {entry.source for entry in self.entries}
        added = 0

        for path in paths:
            path = path.expanduser().resolve()
            if path.is_dir():
                nested = [file_path for file_path in path.rglob("*") if file_path.is_file() and not should_ignore(file_path)]
                self.add_paths(nested, auto_classify=auto_classify)
                continue
            if not path.exists() or not path.is_file() or should_ignore(path) or path in existing:
                continue

            target = classify_file(path) if auto_classify or self.target_folder.get() == "auto" else self.target_folder.get()
            self.entries.append(FileEntry(source=path, target=target))
            existing.add(path)
            added += 1

        self.refresh_table()
        if added:
            self.log(f"Added {added} file(s).")

    def reclassify_entries(self) -> None:
        selected = self.selected_indices()
        chosen = self.target_folder.get()
        targets = selected or set(range(len(self.entries)))

        for index in targets:
            entry = self.entries[index]
            entry.target = classify_file(entry.source) if chosen == "auto" else chosen

        self.refresh_table()
        self.log("Updated file placement.")

    def on_drop(self, event: object) -> None:
        raw_paths = self.root.tk.splitlist(event.data)  # type: ignore[attr-defined]
        self.add_paths([Path(path) for path in raw_paths], auto_classify=True)

    def pick_files(self) -> None:
        selected = filedialog.askopenfilenames(title="Choose project files")
        self.add_paths([Path(path) for path in selected], auto_classify=True)

    def pick_folder(self) -> None:
        selected = filedialog.askdirectory(title="Choose a project folder")
        if selected:
            self.add_paths([Path(selected)], auto_classify=True)

    def clear_files(self) -> None:
        self.entries.clear()
        self.refresh_table()
        self.log("Cleared selected files.")

    def project_dir(self) -> Path:
        return REPO_ROOT / "projects" / slugify(self.project_name.get())

    def copy_into_repo(self) -> None:
        if not self.entries:
            messagebox.showinfo("No files selected", "Add or drop at least one file first.")
            return

        project_dir = self.project_dir()
        copied: list[Path] = []

        for entry in self.entries:
            target_dir = project_dir / entry.target
            target_dir.mkdir(parents=True, exist_ok=True)
            destination = unique_destination(target_dir / entry.source.name)
            shutil.copy2(entry.source, destination)
            entry.copied_to = destination
            copied.append(destination)

        if self.create_readme.get():
            self.ensure_project_readme(project_dir)

        self.refresh_table()
        summary = "\n".join(f"- {path.relative_to(REPO_ROOT)}" for path in copied[:12])
        if len(copied) > 12:
            summary += f"\n- ...and {len(copied) - 12} more"
        self.log(f"Copied {len(copied)} file(s) into {project_dir.relative_to(REPO_ROOT)}:\n{summary}")
        self.refresh_status()

    def ensure_project_readme(self, project_dir: Path) -> None:
        readme = project_dir / "README.md"
        if readme.exists():
            return

        title = self.project_name.get().strip() or project_dir.name
        readme.write_text(
            f"# {title}\n\n"
            "## Goal\n"
            "Describe what this digital design does and why it matters.\n\n"
            "## Files\n"
            "- `rtl/`: design source\n"
            "- `tb/`: testbench files\n"
            "- `sim/`: simulation scripts or compiled simulation outputs\n"
            "- `waves/`: waveform screenshots, VCD, FST, or GTKWave files\n"
            "- `synthesis/`: Yosys scripts, netlists, reports, JSON, or SVG diagrams\n"
            "- `docs/`: diagrams, notes, and screenshots\n\n"
            "## How to Run\n"
            "```bash\n"
            "cd sim\n"
            "# add your iverilog / verilator command here\n"
            "```\n\n"
            "## Results\n"
            "Add waveform screenshots, synthesis notes, and observations here.\n",
            encoding="utf-8",
        )
        self.log(f"Created {readme.relative_to(REPO_ROOT)}")

    def git_commit(self) -> None:
        message = self.commit_message.get().strip() or "Add project files"
        paths_to_add = [path for path in GIT_MANAGED_PATHS if (REPO_ROOT / path).exists()]
        code, add_output = run_git(["add", *paths_to_add])
        if code != 0:
            self.log(add_output)
            messagebox.showerror("Git add failed", add_output)
            return

        code, commit_output = run_git(["commit", "-m", message, "--", *paths_to_add])
        self.log(commit_output or "Nothing to commit.")
        if code != 0 and "nothing to commit" not in commit_output.lower():
            messagebox.showerror("Git commit failed", commit_output)
            return
        self.refresh_status()

    def git_push(self) -> None:
        code, remote_output = run_git(["remote"])
        if code != 0 or not remote_output.strip():
            msg = "No git remote is configured yet. Add one with: git remote add origin <repo-url>"
            self.log(msg)
            messagebox.showinfo("No remote", msg)
            return

        code, push_output = run_git(["push"])
        self.log(push_output or "Pushed successfully.")
        if code != 0:
            messagebox.showerror("Git push failed", push_output)
        self.refresh_status()

    def refresh_status(self) -> None:
        code, status = run_git(["status", "--short"])
        if code == 0:
            lines = status.splitlines()
            shown = "\n".join(lines[:24])
            if len(lines) > 24:
                shown += f"\n...and {len(lines) - 24} more line(s)"
            self.log("Git status:\n" + (shown or "clean"))


def main() -> int:
    if TkinterDnD:
        root = TkinterDnD.Tk()
    else:
        root = tk.Tk()
    RepoDropper(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
