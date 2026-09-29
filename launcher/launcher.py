"""QuickHub - Global Hotkey Micro-Tools Launcher

Press Ctrl + Shift + K anywhere to open your tools palette.
"""

import os
import sys
import json
import ctypes
import ctypes.wintypes
import threading
import webbrowser
import tkinter as tk
from tkinter import font as tkfont
from PIL import Image, ImageDraw
import pystray


# --- CONFIGURATION & HOTKEY ---
HOTKEY_ID = 101
MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_NOREPEAT = 0x4000
VK_K = 0x4B  # 'K' key

WM_HOTKEY = 0x0312
WM_QUIT = 0x0012

def get_tools_config_path():
    """Find tools.json: first check alongside executable/script, then check bundled resources."""
    # 1. Look for user-provided tools.json next to the .exe or script
    if getattr(sys, "frozen", False):
        exe_dir = os.path.dirname(sys.executable)
    else:
        exe_dir = os.path.dirname(os.path.abspath(__file__))

    local_path = os.path.join(exe_dir, "tools.json")
    if os.path.exists(local_path):
        return local_path

    # 2. Look in PyInstaller temporary extraction directory
    if hasattr(sys, "_MEIPASS"):
        bundled_path = os.path.join(sys._MEIPASS, "tools.json")
        if os.path.exists(bundled_path):
            return bundled_path

    return local_path


# Fallback tools if tools.json is missing
DEFAULT_TOOLS = [
    {
        "id": "gst-verifier",
        "name": "GSTIN Verifier Pro",
        "description": "Verify official taxpayer identity, filing status, address, & business activities.",
        "category": "Tax & Compliance",
        "badge": "Active",
        "icon": "🏛️",
        "url": "http://127.0.0.1:5000",
        "keywords": ["gst", "gstin", "tax", "taxpayer", "verify", "company"]
    }
]


def load_tools():
    """Load tools from tools.json or fallback."""
    config_path = get_tools_config_path()
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading {config_path}: {e}")
    return DEFAULT_TOOLS



# --- SPOTLIGHT COMMAND PALETTE UI ---
class QuickHubUI:
    def __init__(self, root):
        self.root = root
        self.tools = load_tools()
        self.filtered_tools = list(self.tools)
        self.selected_index = 0

        # Window styling
        self.root.title("QuickHub")
        self.root.overrideredirect(True)  # Frameless spotlight look
        self.root.attributes("-topmost", True)
        self.root.configure(bg="#0f172a")

        # Dimensions
        self.width = 620
        self.height = 420
        self.center_window()

        self.setup_ui()
        self.bind_events()

        # Hide on startup
        self.root.withdraw()
        self.is_visible = False

    def center_window(self):
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        x = (screen_w - self.width) // 2
        y = int(screen_h * 0.22)  # Upper third of screen like Spotlight / Raycast
        self.root.geometry(f"{self.width}x{self.height}+{x}+{y}")

    def setup_ui(self):
        # Outer border frame
        self.outer_frame = tk.Frame(self.root, bg="#334155", padx=1, pady=1)
        self.outer_frame.pack(fill=tk.BOTH, expand=True)

        self.main_container = tk.Frame(self.outer_frame, bg="#0f172a", padx=16, pady=14)
        self.main_container.pack(fill=tk.BOTH, expand=True)

        # Header / Search Box Row
        self.search_frame = tk.Frame(self.main_container, bg="#1e293b", padx=14, pady=10)
        self.search_frame.pack(fill=tk.X, pady=(0, 10))

        # Search Icon
        self.search_icon_lbl = tk.Label(
            self.search_frame, text="🔍", font=("Segoe UI Emoji", 14), bg="#1e293b", fg="#94a3b8"
        )
        self.search_icon_lbl.pack(side=tk.LEFT, padx=(0, 10))

        # Search Entry
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self.on_search_change)
        self.search_entry = tk.Entry(
            self.search_frame,
            textvariable=self.search_var,
            font=("Segoe UI", 13),
            bg="#1e293b",
            fg="#f8fafc",
            insertbackground="#38bdf8",
            relief=tk.FLAT,
            bd=0
        )
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Keyboard Shortcut Hint Badge
        self.shortcut_hint = tk.Label(
            self.search_frame,
            text="Ctrl+Shift+K",
            font=("Segoe UI", 8, "bold"),
            bg="#334155",
            fg="#94a3b8",
            padx=6,
            pady=2
        )
        self.shortcut_hint.pack(side=tk.RIGHT)

        # Tools List Scroll Area
        self.list_canvas = tk.Canvas(
            self.main_container,
            bg="#0f172a",
            highlightthickness=0,
            bd=0
        )
        self.list_canvas.pack(fill=tk.BOTH, expand=True)

        self.list_inner = tk.Frame(self.list_canvas, bg="#0f172a")
        self.canvas_window = self.list_canvas.create_window(
            (0, 0), window=self.list_inner, anchor="nw"
        )

        self.list_inner.bind("<Configure>", lambda e: self.list_canvas.configure(scrollregion=self.list_canvas.bbox("all")))
        self.list_canvas.bind("<Configure>", lambda e: self.list_canvas.itemconfig(self.canvas_window, width=e.width))

        # Bottom Status Bar
        self.footer = tk.Frame(self.main_container, bg="#0f172a", pady=6)
        self.footer.pack(fill=tk.X)

        self.footer_left = tk.Label(
            self.footer,
            text="↑↓ to navigate • ↵ to open • Esc to close",
            font=("Segoe UI", 8),
            bg="#0f172a",
            fg="#64748b"
        )
        self.footer_left.pack(side=tk.LEFT)

        self.footer_count = tk.Label(
            self.footer,
            text=f"{len(self.tools)} tools available",
            font=("Segoe UI", 8),
            bg="#0f172a",
            fg="#64748b"
        )
        self.footer_count.pack(side=tk.RIGHT)

        self.render_tool_list()

    def bind_events(self):
        self.root.bind("<Escape>", lambda e: self.hide())
        self.root.bind("<Down>", self.on_key_down)
        self.root.bind("<Up>", self.on_key_up)
        self.root.bind("<Return>", self.on_key_enter)
        self.root.bind("<FocusOut>", self.on_focus_out)

    def on_focus_out(self, event):
        # Auto hide when user clicks outside the window
        # Small delay to avoid accidental closes during internal focus switches
        self.root.after(100, self.check_focus_and_hide)

    def check_focus_and_hide(self):
        focused = self.root.focus_get()
        if focused is None and self.is_visible:
            self.hide()

    def on_search_change(self, *args):
        query = self.search_var.get().strip().lower()
        if not query:
            self.filtered_tools = list(self.tools)
        else:
            self.filtered_tools = [
                t for t in self.tools
                if query in t.get("name", "").lower()
                or query in t.get("description", "").lower()
                or query in t.get("category", "").lower()
                or any(query in kw.lower() for kw in t.get("keywords", []))
            ]

        self.selected_index = 0
        self.render_tool_list()

    def render_tool_list(self):
        # Clear existing items
        for widget in self.list_inner.winfo_children():
            widget.destroy()

        if not self.filtered_tools:
            empty_lbl = tk.Label(
                self.list_inner,
                text="No tools match your search.",
                font=("Segoe UI", 10),
                bg="#0f172a",
                fg="#64748b",
                pady=40
            )
            empty_lbl.pack(fill=tk.X)
            return

        for idx, tool in enumerate(self.filtered_tools):
            is_selected = (idx == self.selected_index)
            bg_color = "#1e293b" if is_selected else "#0f172a"
            border_color = "#38bdf8" if is_selected else "#1e293b"

            item_card = tk.Frame(
                self.list_inner,
                bg=bg_color,
                highlightbackground=border_color,
                highlightthickness=1,
                padx=12,
                pady=8,
                cursor="hand2"
            )
            item_card.pack(fill=tk.X, pady=3)

            # Left Icon
            icon_lbl = tk.Label(
                item_card,
                text=tool.get("icon", "⚡"),
                font=("Segoe UI Emoji", 16),
                bg=bg_color,
                fg="#ffffff"
            )
            icon_lbl.pack(side=tk.LEFT, padx=(0, 12))

            # Center text info
            text_frame = tk.Frame(item_card, bg=bg_color)
            text_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

            # Title Row
            title_row = tk.Frame(text_frame, bg=bg_color)
            title_row.pack(fill=tk.X)

            title_lbl = tk.Label(
                title_row,
                text=tool.get("name", "Untitled"),
                font=("Segoe UI", 10, "bold"),
                bg=bg_color,
                fg="#f8fafc" if is_selected else "#e2e8f0"
            )
            title_lbl.pack(side=tk.LEFT)

            # Badge / Category
            badge_text = tool.get("badge") or tool.get("category", "")
            badge_fg = "#22c55e" if "active" in badge_text.lower() else "#94a3b8"
            badge_lbl = tk.Label(
                title_row,
                text=badge_text,
                font=("Segoe UI", 8),
                bg=bg_color,
                fg=badge_fg,
                padx=6
            )
            badge_lbl.pack(side=tk.LEFT, padx=(6, 0))

            # Description
            desc_lbl = tk.Label(
                text_frame,
                text=tool.get("description", ""),
                font=("Segoe UI", 8),
                bg=bg_color,
                fg="#94a3b8",
                anchor="w",
                justify=tk.LEFT
            )
            desc_lbl.pack(fill=tk.X, pady=(2, 0))

            # Right action hint
            if is_selected:
                enter_hint = tk.Label(
                    item_card,
                    text="↵ Open",
                    font=("Segoe UI", 8, "bold"),
                    bg=bg_color,
                    fg="#38bdf8"
                )
                enter_hint.pack(side=tk.RIGHT, padx=6)

            # Click binding
            for w in (item_card, icon_lbl, text_frame, title_row, title_lbl, badge_lbl, desc_lbl):
                w.bind("<Button-1>", lambda e, target_tool=tool: self.launch_tool(target_tool))

    def on_key_down(self, event):
        if self.filtered_tools:
            self.selected_index = (self.selected_index + 1) % len(self.filtered_tools)
            self.render_tool_list()

    def on_key_up(self, event):
        if self.filtered_tools:
            self.selected_index = (self.selected_index - 1) % len(self.filtered_tools)
            self.render_tool_list()

    def on_key_enter(self, event):
        if self.filtered_tools and 0 <= self.selected_index < len(self.filtered_tools):
            tool = self.filtered_tools[self.selected_index]
            self.launch_tool(tool)

    def launch_tool(self, tool):
        url = tool.get("url")
        if url:
            webbrowser.open_new_tab(url)
        self.hide()

    def show(self):
        self.center_window()
        self.tools = load_tools()
        self.on_search_change()
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
        self.search_entry.focus_set()
        self.search_entry.select_range(0, tk.END)
        self.is_visible = True

    def hide(self):
        self.root.withdraw()
        self.is_visible = False


# --- GLOBAL HOTKEY LISTENER (ctypes Windows API) ---
class HotkeyWorker(threading.Thread):
    def __init__(self, callback):
        super().__init__(daemon=True)
        self.callback = callback
        self.user32 = ctypes.windll.user32

    def run(self):
        # Register Ctrl + Shift + K
        # MOD_CONTROL | MOD_SHIFT | MOD_NOREPEAT
        modifiers = MOD_CONTROL | MOD_SHIFT | MOD_NOREPEAT
        if not self.user32.RegisterHotKey(None, HOTKEY_ID, modifiers, VK_K):
            print("Failed to register global hotkey Ctrl+Shift+K. Trying Alt+Space fallback...")
            # Fallback to Alt + Space
            self.user32.RegisterHotKey(None, HOTKEY_ID, MOD_ALT | MOD_NOREPEAT, 0x20)

        msg = ctypes.wintypes.MSG()
        while self.user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
            if msg.message == WM_HOTKEY and msg.wParam == HOTKEY_ID:
                self.callback()
            self.user32.TranslateMessage(ctypes.byref(msg))
            self.user32.DispatchMessageW(ctypes.byref(msg))


# --- SYSTEM TRAY ICON ---
def create_tray_image():
    # Draw a clean 64x64 blue lightning bolt/hub icon
    image = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    # Circle background
    draw.ellipse([4, 4, 60, 60], fill="#2563eb", outline="#3b82f6", width=2)
    # Lightning / Zap glyph
    points = [(36, 12), (20, 34), (32, 34), (28, 52), (46, 28), (34, 28)]
    draw.polygon(points, fill="#ffffff")
    return image


def setup_tray(on_open, on_exit):
    tray_image = create_tray_image()
    menu = pystray.Menu(
        pystray.MenuItem("Open QuickHub (Ctrl+Shift+K)", on_open, default=True),
        pystray.MenuItem("Exit", on_exit)
    )
    tray = pystray.Icon("QuickHub", tray_image, "QuickHub Tools Launcher", menu)
    return tray


# --- MAIN APPLICATION ENTRY ---
def main():
    root = tk.Tk()
    app = QuickHubUI(root)

    def trigger_show():
        # Tkinter requires GUI operations on main thread
        root.after(0, app.show)

    # Start Windows global hotkey thread
    hotkey_thread = HotkeyWorker(trigger_show)
    hotkey_thread.start()

    # System Tray
    def on_tray_exit(icon, item):
        icon.stop()
        root.after(0, root.destroy)
        os._exit(0)

    def on_tray_open(icon, item):
        trigger_show()

    tray_icon = setup_tray(on_tray_open, on_tray_exit)
    tray_thread = threading.Thread(target=tray_icon.run, daemon=True)
    tray_thread.start()

    print("=" * 60)
    print(" QuickHub is running in the background!")
    print(" Press Ctrl + Shift + K anywhere to open the tools palette.")
    print(" Right-click the system tray icon to exit.")
    print("=" * 60)

    # Run Tkinter mainloop
    root.mainloop()


if __name__ == "__main__":
    main()
