from __future__ import annotations

import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from .client import BuilderCenterClient
from .discovery import Candidate, extract_candidates
from .export import export_csv, export_xlsx
from .filtering import is_target
from .models import Builder
from .store import BuilderStore

DEFAULT_SOURCES = (
    "https://builder.aws.com/community/cloud-clubs",
    "https://builder.aws.com/community/user-groups",
)


class ScraperGUI(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("AWS SBCL Builder Finder")
        self.geometry("1180x760")
        self.minsize(980, 640)

        self.db_path = Path("data/builders.sqlite3")
        self.builders: list[Builder] = []
        self.running = False

        self.target_var = tk.IntVar(value=100)
        self.status_var = tk.StringVar(value="Ready")
        self.progress_var = tk.DoubleVar(value=0)

        self._build()
        self._load_existing()

    def _build(self) -> None:
        root = ttk.Frame(self, padding=16)
        root.pack(fill="both", expand=True)

        header = ttk.Frame(root)
        header.pack(fill="x")
        ttk.Label(header, text="AWS SBCL Builder Finder", font=("Segoe UI", 20, "bold")).pack(anchor="w")
        ttk.Label(
            header,
            text="Discover public Builder Center profiles, filter them, and export CSV/XLSX.",
        ).pack(anchor="w", pady=(2, 12))

        filters = ttk.LabelFrame(root, text="Discovery", padding=12)
        filters.pack(fill="x", pady=(0, 12))

        ttk.Label(filters, text="Target rows").grid(row=0, column=0, sticky="w")
        ttk.Spinbox(filters, from_=1, to=10000, textvariable=self.target_var, width=8).grid(
            row=0, column=1, padx=(8, 18), sticky="w"
        )
        ttk.Label(filters, text="Location").grid(row=0, column=2, sticky="w")
        ttk.Label(filters, text="India", font=("Segoe UI", 10, "bold")).grid(
            row=0, column=3, padx=(8, 18), sticky="w"
        )
        ttk.Label(filters, text="Followers / Following").grid(row=0, column=4, sticky="w")
        ttk.Label(filters, text="0 / 0", font=("Segoe UI", 10, "bold")).grid(
            row=0, column=5, padx=(8, 18), sticky="w"
        )
        self.start_button = ttk.Button(filters, text="Start Discovery", command=self.start_discovery)
        self.start_button.grid(row=0, column=6, sticky="e")
        filters.columnconfigure(6, weight=1)

        source_frame = ttk.LabelFrame(root, text="Public Builder Center source pages", padding=8)
        source_frame.pack(fill="x", pady=(0, 12))
        self.sources = tk.Text(source_frame, height=3, wrap="none")
        self.sources.pack(fill="x")
        self.sources.insert("1.0", "\n".join(DEFAULT_SOURCES))
        ttk.Label(
            source_frame,
            text="The app only extracts public /community/@profile links from these pages; it does not use private account data.",
        ).pack(anchor="w", pady=(5, 0))

        progress_frame = ttk.Frame(root)
        progress_frame.pack(fill="x", pady=(0, 12))
        ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100).pack(fill="x")
        ttk.Label(progress_frame, textvariable=self.status_var).pack(anchor="w", pady=(4, 0))

        stats = ttk.Frame(root)
        stats.pack(fill="x", pady=(0, 8))
        self.discovered_label = self._stat(stats, "Discovered", 0)
        self.scraped_label = self._stat(stats, "Scraped", 0)
        self.matches_label = self._stat(stats, "Matches", 0)
        self.failed_label = self._stat(stats, "Failed", 0)

        table_frame = ttk.Frame(root)
        table_frame.pack(fill="both", expand=True)

        columns = ("alias", "name", "location", "followers", "following", "email")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="extended")
        headings = {
            "alias": "Alias",
            "name": "Name",
            "location": "Location",
            "followers": "Followers",
            "following": "Following",
            "email": "Public Email",
        }
        widths = {"alias": 130, "name": 180, "location": 190, "followers": 80, "following": 80, "email": 230}
        for column in columns:
            self.tree.heading(column, text=headings[column])
            self.tree.column(column, width=widths[column], anchor="w")
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        actions = ttk.Frame(root)
        actions.pack(fill="x", pady=(10, 0))
        ttk.Button(actions, text="Export CSV", command=lambda: self.export("csv")).pack(side="left")
        ttk.Button(actions, text="Export XLSX", command=lambda: self.export("xlsx")).pack(side="left", padx=8)
        ttk.Button(actions, text="Refresh Stored Targets", command=self._load_existing).pack(side="right")

    @staticmethod
    def _stat(parent: ttk.Frame, title: str, value: int) -> ttk.Label:
        frame = ttk.Frame(parent)
        frame.pack(side="left", padx=(0, 28))
        ttk.Label(frame, text=title).pack(anchor="w")
        label = ttk.Label(frame, text=str(value), font=("Segoe UI", 15, "bold"))
        label.pack(anchor="w")
        return label

    def _set_stats(self, discovered: int, scraped: int, matches: int, failed: int) -> None:
        self.discovered_label.configure(text=str(discovered))
        self.scraped_label.configure(text=str(scraped))
        self.matches_label.configure(text=str(matches))
        self.failed_label.configure(text=str(failed))

    def _load_existing(self) -> None:
        try:
            with BuilderStore(self.db_path) as store:
                self.builders = store.list_targets()
        except Exception:
            self.builders = []
        self._render(self.builders)
        self._set_stats(0, 0, len(self.builders), 0)

    def _render(self, builders: list[Builder]) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)
        for builder in builders:
            self.tree.insert(
                "",
                "end",
                values=(
                    f"@{builder.alias}",
                    builder.display_name,
                    builder.location,
                    builder.followers,
                    builder.following,
                    builder.email or "",
                ),
            )

    def start_discovery(self) -> None:
        if self.running:
            return
        try:
            target = max(1, int(self.target_var.get()))
        except (TypeError, ValueError):
            messagebox.showerror("Invalid target", "Target rows must be a positive number.")
            return

        urls = [line.strip() for line in self.sources.get("1.0", "end").splitlines() if line.strip()]
        if not urls:
            messagebox.showerror("No sources", "Add at least one public Builder Center source page.")
            return

        self.running = True
        self.start_button.configure(state="disabled")
        self.progress_var.set(0)
        thread = threading.Thread(target=self._run_discovery, args=(urls, target), daemon=True)
        thread.start()

    def _run_discovery(self, urls: list[str], target: int) -> None:
        candidates: list[Candidate] = []
        seen: set[str] = set()
        failed = 0
        try:
            with BuilderCenterClient(timeout=20) as client:
                for index, url in enumerate(urls, start=1):
                    try:
                        response = client._client.get(url)
                        response.raise_for_status()
                        for candidate in extract_candidates(response.text):
                            key = candidate.alias.casefold()
                            if key not in seen:
                                seen.add(key)
                                candidates.append(candidate)
                    except Exception:
                        failed += 1
                    self.after(0, self._status, f"Discovering source {index}/{len(urls)}…", index / len(urls) * 20)

                matches: list[Builder] = []
                scraped = 0
                with BuilderStore(self.db_path) as store:
                    total = len(candidates)
                    for index, candidate in enumerate(candidates, start=1):
                        try:
                            builder = client.fetch_profile(candidate.alias)
                            store.upsert(builder)
                            scraped += 1
                            if is_target(builder):
                                matches.append(builder)
                        except Exception:
                            failed += 1

                        progress = 20 + (index / max(total, 1) * 80)
                        self.after(
                            0,
                            self._status,
                            f"Scraping {index}/{total} — {len(matches)} matching profiles",
                            progress,
                        )
                        self.after(0, self._set_stats, len(candidates), scraped, len(matches), failed)
                        self.after(0, self._render, matches)

                        if len(matches) >= target:
                            break

                self.builders = matches
                self.after(0, self._status, f"Finished: {len(matches)} matching profile(s).", 100)
        finally:
            self.after(0, self._finish)

    def _status(self, message: str, progress: float) -> None:
        self.status_var.set(message)
        self.progress_var.set(progress)

    def _finish(self) -> None:
        self.running = False
        self.start_button.configure(state="normal")

    def export(self, fmt: str) -> None:
        if not self.builders:
            messagebox.showinfo("Nothing to export", "No matching profiles are currently loaded.")
            return
        extension = ".csv" if fmt == "csv" else ".xlsx"
        path = filedialog.asksaveasfilename(
            title=f"Export {fmt.upper()}",
            defaultextension=extension,
            filetypes=[(fmt.upper(), f"*{extension}"), ("All files", "*.*")],
            initialfile=f"builder_targets{extension}",
        )
        if not path:
            return
        try:
            if fmt == "csv":
                export_csv(self.builders, path)
            else:
                export_xlsx(self.builders, path)
            messagebox.showinfo("Export complete", f"Exported {len(self.builders)} profile(s).\n\n{path}")
        except Exception as exc:
            messagebox.showerror("Export failed", str(exc))


def main() -> None:
    app = ScraperGUI()
    app.mainloop()


if __name__ == "__main__":
    main()
