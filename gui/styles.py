"""
Custom stylesheet layer applied ON TOP of qt-material dark_purple theme.
qt-material handles all standard widgets; we only override our named components.
"""

# Extra colours that extend the purple palette
_ACCENT_ORANGE  = "#f97316"
_ACCENT_PINK    = "#e040fb"
_ACCENT_PURPLE  = "#ab47bc"
_ACCENT_CYAN    = "#26c6da"
_ACCENT_GREEN   = "#26c6da"
_TEXT_DIM       = "rgba(255,255,255,0.45)"
_BORDER_SUBTLE  = "rgba(255,255,255,0.10)"
_BORDER_ACCENT  = "rgba(171,71,188,0.55)"

# ── Run button gradient ────────────────────────────────────────────────────────
_RUN_BTN = f"""
#navBtnPrimary {{
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0   {_ACCENT_ORANGE},
        stop:0.5 {_ACCENT_PINK},
        stop:1   {_ACCENT_PURPLE}
    );
    color: #ffffff;
    border: none;
    border-radius: 8px;
    font-size: 13px;
    font-weight: 700;
    min-height: 40px;
    margin: 2px 0;
    padding: 0 12px;
}}
#navBtnPrimary:hover {{
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 #fb923c,
        stop:1 {_ACCENT_PINK}
    );
}}
#navBtnPrimary:disabled {{
    background: rgba(255,255,255,0.08);
    color: {_TEXT_DIM};
}}
"""

# ── Accent strip at very top ───────────────────────────────────────────────────
_STRIP = f"""
#accentStrip {{
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0   {_ACCENT_ORANGE},
        stop:0.3 {_ACCENT_PINK},
        stop:0.6 {_ACCENT_PURPLE},
        stop:1   {_ACCENT_CYAN}
    );
    min-height: 3px;
    max-height: 3px;
}}
"""

# ── Top bar ────────────────────────────────────────────────────────────────────
_TOPBAR = f"""
#topBar {{
    border-bottom: 1px solid {_BORDER_SUBTLE};
}}
#topBarTitle {{
    font-size: 14px;
    font-weight: 700;
    color: #ffffff;
}}
#statusPill {{
    border: 1px solid {_BORDER_SUBTLE};
    border-radius: 8px;
    padding: 3px 10px;
    background: rgba(255,255,255,0.06);
}}
#metricLabel {{
    font-size: 13px;
    font-weight: 700;
    color: {_ACCENT_CYAN};
}}
#globalRegPill {{
    border: 1px solid {_BORDER_ACCENT};
    border-radius: 8px;
    padding: 3px 10px;
    background: rgba(171,71,188,0.15);
}}
#globalRegLabel {{
    font-size: 12px;
    font-weight: 600;
    color: {_ACCENT_PINK};
    font-family: "Cascadia Mono", "Consolas", monospace;
}}
"""

# ── Sidebar ────────────────────────────────────────────────────────────────────
_SIDEBAR = f"""
#sidebar {{
    border-right: 1px solid {_BORDER_SUBTLE};
}}
#sidebarHeader {{
    border-bottom: 1px solid {_BORDER_SUBTLE};
}}
#logoBadge {{
    background: rgba(171,71,188,0.20);
    border: 1px solid rgba(171,71,188,0.45);
    border-radius: 8px;
    font-size: 18px;
    font-weight: 800;
    color: {_ACCENT_PINK};
    min-width: 40px;
    max-width: 40px;
    min-height: 40px;
    max-height: 40px;
    qproperty-alignment: AlignCenter;
}}
#appTitle {{
    font-size: 14px;
    font-weight: 700;
    color: #ffffff;
}}
#appSubtitle {{
    font-size: 11px;
    color: {_TEXT_DIM};
}}
#navSection {{
    font-size: 10px;
    font-weight: 700;
    color: {_TEXT_DIM};
    padding: 4px 0 0 0;
    letter-spacing: 0.8px;
}}
#navBtn {{
    background: transparent;
    border: none;
    border-radius: 6px;
    text-align: left;
    padding: 6px 10px;
    font-size: 13px;
    min-height: 34px;
    color: rgba(255,255,255,0.75);
}}
#navBtn:hover {{
    background: rgba(255,255,255,0.07);
    color: #ffffff;
}}
#navBtn:disabled {{
    color: {_TEXT_DIM};
}}
#navBtn:focus {{
    outline: none;
    border: none;
}}
#hSep {{
    background: {_BORDER_SUBTLE};
    max-height: 1px;
    min-height: 1px;
    margin: 4px 0;
}}
#fileInfoBadge {{
    border-left: 3px solid {_ACCENT_ORANGE};
    border-radius: 4px;
    padding: 8px 10px;
    margin: 0;
    font-size: 12px;
    color: rgba(255,255,255,0.80);
    background: rgba(255,255,255,0.05);
}}
#paramsCard {{
    background: rgba(255,255,255,0.04);
    border: 1px solid {_BORDER_SUBTLE};
    border-radius: 8px;
}}
#formLabel {{
    font-size: 12px;
    color: rgba(255,255,255,0.70);
    min-width: 82px;
    max-width: 82px;
}}
#themeLabel {{
    font-size: 12px;
    color: rgba(255,255,255,0.65);
}}
"""

# ── Mode toggle (Свободный / Ручной / Поровну) ───────────────────────────────
_MODE_BTN = f"""
#modeToggle {{
    background: rgba(255,255,255,0.04);
    border: 1px solid {_BORDER_SUBTLE};
    border-radius: 7px;
}}
#modeBtnLeft, #modeBtnMid, #modeBtnRight {{
    background: transparent;
    border: none;
    border-radius: 0;
    color: rgba(255,255,255,0.62);
    font-size: 11px;
    font-weight: 600;
    padding: 0 4px;
    min-height: 32px;
    max-height: 32px;
}}
#modeBtnLeft {{
    border-top-left-radius: 6px;
    border-bottom-left-radius: 6px;
}}
#modeBtnRight {{
    border-top-right-radius: 6px;
    border-bottom-right-radius: 6px;
}}
#modeBtnMid {{
    border-left: 1px solid {_BORDER_SUBTLE};
    border-right: 1px solid {_BORDER_SUBTLE};
}}
#modeBtnLeft:hover, #modeBtnMid:hover, #modeBtnRight:hover {{
    background: rgba(255,255,255,0.08);
    color: #ffffff;
}}
#modeBtnLeft:checked, #modeBtnMid:checked, #modeBtnRight:checked {{
    background: rgba(171,71,188,0.28);
    color: {_ACCENT_PINK};
    font-weight: 700;
}}
#modeBtnLeft:focus, #modeBtnMid:focus, #modeBtnRight:focus {{
    outline: none;
}}
"""

# ── Tabs ───────────────────────────────────────────────────────────────────────
_TABS = f"""
QTabWidget#chartTabs::pane {{
    border: none;
    border-top: 1px solid {_BORDER_SUBTLE};
    background: transparent;
}}
QTabWidget#chartTabs QTabBar {{
    background: transparent;
}}
QTabWidget#chartTabs QTabBar::tab {{
    background: transparent;
    color: rgba(255,255,255,0.50);
    border: none;
    border-bottom: 2px solid transparent;
    padding: 10px 22px;
    font-size: 13px;
    font-weight: 500;
    margin-right: 2px;
}}
QTabWidget#chartTabs QTabBar::tab:selected {{
    color: #ffffff;
    font-weight: 700;
    border-bottom: 2px solid {_ACCENT_PINK};
    background: transparent;
}}
QTabWidget#chartTabs QTabBar::tab:hover:!selected {{
    color: rgba(255,255,255,0.80);
    background: rgba(255,255,255,0.05);
}}
"""

# ── Results panel ──────────────────────────────────────────────────────────────
_RESULTS = f"""
#panelTitle {{
    font-size: 10px;
    font-weight: 700;
    color: {_TEXT_DIM};
    letter-spacing: 0.6px;
}}
#panelCount {{
    font-size: 11px;
    font-weight: 700;
    color: {_ACCENT_PINK};
    background: rgba(171,71,188,0.15);
    border: 1px solid {_BORDER_ACCENT};
    border-radius: 10px;
    padding: 3px 10px;
}}
"""

# ── Loading overlay ────────────────────────────────────────────────────────────
_LOADING = f"""
#loadingOverlay {{
    background: rgba(25,20,35,0.88);
}}
#loadingCard {{
    border: 1px solid {_BORDER_SUBTLE};
    border-radius: 12px;
    background: #2a2535;
}}
#loadingTitle {{
    font-size: 15px;
    font-weight: 700;
    color: #ffffff;
}}
#loadingSubtitle {{
    font-size: 12px;
    color: rgba(255,255,255,0.60);
}}
QProgressBar#progressBar {{
    background: rgba(255,255,255,0.10);
    border: none;
    border-radius: 4px;
    height: 5px;
}}
QProgressBar#progressBar::chunk {{
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0   {_ACCENT_ORANGE},
        stop:0.4 {_ACCENT_PINK},
        stop:1   {_ACCENT_PURPLE}
    );
    border-radius: 4px;
}}
"""

# ── Dialog ─────────────────────────────────────────────────────────────────────
_DIALOG = f"""
#dialogHeader {{
    background: rgba(255,255,255,0.05);
    border: 1px solid {_BORDER_SUBTLE};
    border-radius: 8px;
}}
#dialogTitle {{
    font-size: 15px;
    font-weight: 700;
    color: #ffffff;
}}
#dialogSubtitle {{
    font-size: 12px;
    color: rgba(255,255,255,0.60);
}}
QPushButton#dialogClose {{
    background: rgba(171,71,188,0.20);
    border: 1px solid {_BORDER_ACCENT};
    border-radius: 8px;
    color: {_ACCENT_PINK};
    padding: 10px 28px;
    font-size: 13px;
    font-weight: 700;
    min-height: 42px;
}}
QPushButton#dialogClose:hover {{
    background: {_ACCENT_PURPLE};
    color: #ffffff;
    border-color: {_ACCENT_PURPLE};
}}
"""

# ── Drawer backdrop ────────────────────────────────────────────────────────────
_DRAWER = f"""
#drawerBackdrop {{
    background: rgba(10, 8, 16, 0.55);
}}
"""

# ── Burger / close btn ─────────────────────────────────────────────────────────
_BTNS = f"""
#menuOpenBtn {{
    background: rgba(255,255,255,0.06);
    border: 1px solid {_BORDER_SUBTLE};
    border-radius: 6px;
    color: rgba(255,255,255,0.70);
    font-size: 14px;
}}
#burgerBtn {{
    background: rgba(255,255,255,0.06);
    border: 1px solid {_BORDER_SUBTLE};
    border-radius: 6px;
    padding: 0;
}}
#burgerBtn:hover, #menuOpenBtn:hover {{
    background: rgba(255,255,255,0.12);
    color: #ffffff;
    border-color: rgba(255,255,255,0.20);
}}
"""

_TEXT_BROWSER = '\n/* Details QTextBrowser - remove qt-material dividers */\nQTextBrowser {\n    border: none;\n    outline: none;\n    background: transparent;\n    padding: 4px 6px;\n}\nQTextBrowser QScrollBar:vertical {\n    background: transparent;\n    width: 4px;\n    margin: 4px 2px;\n}\nQTextBrowser QScrollBar::handle:vertical {\n    background: rgba(255,255,255,0.20);\n    border-radius: 2px;\n    min-height: 30px;\n}\nQTextBrowser QScrollBar::add-line:vertical,\nQTextBrowser QScrollBar::sub-line:vertical { height: 0; }\n'

CUSTOM_CSS = (
    _STRIP + _TOPBAR + _SIDEBAR + _MODE_BTN +
    _TABS + _RESULTS + _LOADING + _DIALOG +
    _DRAWER + _BTNS + _RUN_BTN + _TEXT_BROWSER
)


def get_extra() -> dict:
    """qt-material extra overrides for dark_purple."""
    return {
        "font_family":       "Segoe UI",
        "font_size":         "13px",
        "line_height":       "20px",
        "danger":            "#f44336",
        "warning":           "#ffc107",
        "success":           "#26c6da",
        "density_scale":     "-1",
        "button_shape":      "default",
        "primaryColor":      "#ab47bc",
        "primaryLightColor": "#df78ef",
    }

