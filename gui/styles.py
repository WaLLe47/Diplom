"""Theme definitions and stylesheet builder — glassmorphism style."""

THEMES = {
    "dark": {
        "bg_primary":       "#12081f",
        "bg_secondary":     "rgba(255,255,255,0.05)",
        "bg_sidebar":       "rgba(28,14,48,0.94)",
        "bg_card":          "rgba(255,255,255,0.07)",
        "bg_elevated":      "rgba(255,255,255,0.10)",
        "bg_hover":         "rgba(255,255,255,0.12)",
        "border":           "rgba(255,255,255,0.10)",
        "border_subtle":    "rgba(255,255,255,0.16)",
        "border_glow":      "rgba(192,132,252,0.35)",
        "text_primary":     "#f8f4ff",
        "text_secondary":   "#c4b5d8",
        "text_muted":       "#8b7aa8",
        "accent":           "#c084fc",
        "accent_soft":      "rgba(192,132,252,0.18)",
        "accent_hover":     "#d8b4fe",
        "accent_green":     "#2dd4bf",
        "accent_green_dim": "rgba(45,212,191,0.15)",
        "accent_red":       "#fb7185",
        "accent_orange":    "#fb923c",
        "accent_purple":    "#e879f9",
        "accent_pink":      "#f472b6",
        "btn_primary_bg":   "#ea580c",
        "btn_primary_mid":  "#f472b6",
        "btn_primary_hover":"#fb923c",
        "btn_primary_text": "#ffffff",
        "scrollbar":        "transparent",
        "scrollbar_thumb":  "rgba(255,255,255,0.18)",
        "selection":        "rgba(192,132,252,0.25)",
        "overlay":          "rgba(10,5,20,0.78)",
        "tab_active_bg":    "transparent",
        "tab_inactive_bg":  "transparent",
        "logo_bg":          "rgba(192,132,252,0.15)",
        "logo_border":      "rgba(232,121,249,0.40)",
        "glow":             "rgba(192,132,252,0.10)",
        "drawer_scrim":     "rgba(8,4,18,0.68)",
        "chart_bg":         "rgba(255,255,255,0.96)",
        "chart_border":     "rgba(255,255,255,0.22)",
        "grad_1":           "#1a0f2e",
        "grad_2":           "#140c24",
        "grad_3":           "#0c1228",
    },
    "light": {
        "bg_primary":       "#ede9fe",
        "bg_secondary":     "rgba(255,255,255,0.72)",
        "bg_sidebar":       "rgba(255,255,255,0.88)",
        "bg_card":          "rgba(255,255,255,0.85)",
        "bg_elevated":      "rgba(255,255,255,0.95)",
        "bg_hover":         "rgba(237,233,254,0.9)",
        "border":           "rgba(109,40,217,0.12)",
        "border_subtle":    "rgba(109,40,217,0.20)",
        "border_glow":      "rgba(124,58,237,0.30)",
        "text_primary":     "#1e1033",
        "text_secondary":   "#5b4a78",
        "text_muted":       "#8b7aa8",
        "accent":           "#7c3aed",
        "accent_soft":      "rgba(124,58,237,0.12)",
        "accent_hover":     "#6d28d9",
        "accent_green":     "#0d9488",
        "accent_green_dim": "#ccfbf1",
        "accent_red":       "#e11d48",
        "accent_orange":    "#ea580c",
        "accent_purple":    "#a855f7",
        "accent_pink":      "#db2777",
        "btn_primary_bg":   "#7c3aed",
        "btn_primary_mid":  "#db2777",
        "btn_primary_hover":"#8b5cf6",
        "btn_primary_text": "#ffffff",
        "scrollbar":        "transparent",
        "scrollbar_thumb":  "rgba(109,40,217,0.25)",
        "selection":        "rgba(124,58,237,0.15)",
        "overlay":          "rgba(237,233,254,0.88)",
        "tab_active_bg":    "transparent",
        "tab_inactive_bg":  "transparent",
        "logo_bg":          "rgba(124,58,237,0.10)",
        "logo_border":      "rgba(124,58,237,0.25)",
        "glow":             "rgba(124,58,237,0.08)",
        "drawer_scrim":     "rgba(30,15,50,0.25)",
        "chart_bg":         "#ffffff",
        "chart_border":     "rgba(109,40,217,0.15)",
        "grad_1":           "#f5f3ff",
        "grad_2":           "#ede9fe",
        "grad_3":           "#e0e7ff",
    },
}


def build_stylesheet(theme: str) -> str:
    t = THEMES[theme]
    bg_grad = f"""
        qlineargradient(
            x1:0, y1:0, x2:1, y2:1,
            stop:0 {t['grad_1']},
            stop:0.45 {t['grad_2']},
            stop:1 {t['grad_3']}
        )
    """
    return f"""
/* ══ BASE ════════════════════════════════════════════════════════════════ */
QWidget {{
    background-color: {t['bg_primary']};
    color: {t['text_primary']};
    font-family: "Segoe UI", "SF Pro Text", system-ui, sans-serif;
    font-size: 13px;
    border: none;
    outline: none;
}}
QLabel {{
    background: transparent;
}}
#mainWindow, #mainStack, #contentArea, #contentInner {{
    background: {bg_grad};
}}

/* ══ ACCENT STRIP ════════════════════════════════════════════════════════ */
#accentStrip {{
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 {t['accent_orange']},
        stop:0.35 {t['accent_pink']},
        stop:0.7 {t['accent_purple']},
        stop:1 {t['accent_green']}
    );
    min-height: 3px;
    max-height: 3px;
}}

/* ══ SCROLLBARS ══════════════════════════════════════════════════════════ */
QScrollBar:vertical {{
    background: transparent;
    width: 5px;
    margin: 8px 2px;
    border-radius: 3px;
}}
QScrollBar::handle:vertical {{
    background: {t['scrollbar_thumb']};
    border-radius: 3px;
    min-height: 40px;
}}
QScrollBar::handle:vertical:hover {{
    background: {t['accent']};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar:horizontal {{
    background: transparent;
    height: 5px;
    margin: 2px 8px;
    border-radius: 3px;
}}
QScrollBar::handle:horizontal {{
    background: {t['scrollbar_thumb']};
    border-radius: 3px;
    min-width: 40px;
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}

QScrollArea {{
    background: transparent;
    border: none;
}}

/* ══ SIDEBAR (glass drawer) ══════════════════════════════════════════════ */
#sidebar {{
    background-color: {t['bg_sidebar']};
    border: 1px solid {t['border_subtle']};
    border-left: none;
    border-top-right-radius: 24px;
    border-bottom-right-radius: 24px;
}}
#drawerBackdrop {{
    background: {t['drawer_scrim']};
}}
#menuOpenBtn {{
    background: {t['bg_card']};
    border: 1px solid {t['border_subtle']};
    border-radius: 14px;
    color: {t['text_secondary']};
    font-size: 15px;
    min-width: 40px;
    max-width: 40px;
    min-height: 40px;
    max-height: 40px;
    padding: 0;
}}
#menuOpenBtn:hover {{
    background: {t['bg_hover']};
    border-color: {t['border_glow']};
    color: {t['text_primary']};
}}
#topBar {{
    background: {t['bg_secondary']};
    border-bottom: 1px solid {t['border']};
}}
#sidebarHeader {{
    background-color: transparent;
    border-bottom: 1px solid {t['border']};
    border-top-right-radius: 24px;
}}
#logoBadge {{
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:1,
        stop:0 {t['logo_bg']},
        stop:1 rgba(244,114,182,0.18)
    );
    border: 1px solid {t['logo_border']};
    border-radius: 14px;
    font-size: 17px;
    color: {t['accent']};
    min-width: 40px;
    max-width: 40px;
    min-height: 40px;
    max-height: 40px;
    qproperty-alignment: AlignCenter;
}}
#appTitle {{
    font-size: 15px;
    font-weight: 600;
    color: {t['text_primary']};
}}
#appSubtitle {{
    font-size: 11px;
    color: {t['text_muted']};
}}
#burgerBtn {{
    background: {t['bg_card']};
    border: 1px solid {t['border']};
    border-radius: 12px;
    color: {t['text_secondary']};
    font-size: 13px;
    padding: 0;
}}
#burgerBtn:hover {{
    background: {t['bg_hover']};
    border-color: {t['border_glow']};
    color: {t['text_primary']};
}}

/* ══ NAV ═════════════════════════════════════════════════════════════════ */
#navSection {{
    font-size: 11px;
    font-weight: 600;
    color: {t['text_muted']};
    padding: 16px 16px 6px 16px;
}}
#navBtn {{
    background: transparent;
    border: 1px solid transparent;
    border-radius: 14px;
    color: {t['text_secondary']};
    text-align: left;
    padding: 10px 14px;
    font-size: 13px;
    min-height: 40px;
}}
#navBtn:hover {{
    background: {t['bg_card']};
    border-color: {t['border']};
    color: {t['text_primary']};
}}
#navBtn:disabled {{
    color: {t['text_muted']};
}}
#navBtnPrimary {{
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:1,
        stop:0 {t['btn_primary_hover']},
        stop:0.5 {t['btn_primary_mid']},
        stop:1 {t['accent_purple']}
    );
    color: {t['btn_primary_text']};
    border: 1px solid {t['border_glow']};
    border-radius: 16px;
    text-align: center;
    font-size: 13px;
    font-weight: 600;
    min-height: 46px;
    margin: 8px 6px;
    padding: 0 18px;
}}
#navBtnPrimary:hover {{
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:1,
        stop:0 {t['btn_primary_hover']},
        stop:1 {t['accent_pink']}
    );
}}
#navBtnPrimary:disabled {{
    background: {t['bg_card']};
    color: {t['text_muted']};
    border-color: {t['border']};
}}

/* ══ FILE / PARAMS ═══════════════════════════════════════════════════════ */
#fileInfoBadge {{
    background: {t['bg_card']};
    border: 1px solid {t['border']};
    border-left: 3px solid {t['accent_pink']};
    border-radius: 14px;
    color: {t['text_secondary']};
    font-size: 12px;
    padding: 12px 14px;
    margin: 4px 8px 0 8px;
}}
#paramsCard {{
    background: {t['bg_card']};
    border: 1px solid {t['border']};
    border-radius: 16px;
    margin: 2px 8px;
}}

QSpinBox, QLineEdit {{
    background: {t['bg_elevated']};
    border: 1px solid {t['border']};
    border-radius: 12px;
    padding: 8px 12px;
    color: {t['text_primary']};
    min-height: 32px;
}}
QSpinBox:hover, QLineEdit:hover {{
    border-color: {t['border_subtle']};
}}
QSpinBox:focus, QLineEdit:focus {{
    border-color: {t['accent']};
}}
QSpinBox::up-button, QSpinBox::down-button {{
    width: 20px;
    border: none;
    background: transparent;
}}
QLineEdit::placeholder {{
    color: {t['text_muted']};
}}
QLabel#formLabel {{
    color: {t['text_secondary']};
    font-size: 12px;
}}
#modeBtn {{
    background: {t['bg_elevated']};
    border: 1px solid {t['border']};
    border-radius: 12px;
    color: {t['text_secondary']};
    font-size: 11px;
    font-weight: 500;
    padding: 8px 0;
    min-height: 34px;
}}
#modeBtn:hover {{
    background: {t['bg_hover']};
    color: {t['text_primary']};
}}
#modeBtn:checked {{
    background: {t['accent_soft']};
    border-color: {t['accent']};
    color: {t['accent']};
    font-weight: 600;
}}

/* ══ TOP BAR ═════════════════════════════════════════════════════════════ */
#topBarTitle {{
    font-size: 15px;
    font-weight: 600;
    color: {t['text_primary']};
}}
#statusPill {{
    background: {t['bg_card']};
    border: 1px solid {t['border']};
    border-radius: 24px;
    padding: 2px 4px;
}}
#metricLabel {{
    font-size: 13px;
    font-weight: 600;
    color: {t['accent_green']};
}}
#globalRegPill {{
    background: {t['accent_soft']};
    border: 1px solid {t['border_glow']};
    border-radius: 24px;
    padding: 2px 4px;
}}
#globalRegLabel {{
    font-size: 12px;
    font-weight: 500;
    color: {t['accent']};
    font-family: "Cascadia Mono", "Consolas", monospace;
}}

/* ══ GLASS PANELS ════════════════════════════════════════════════════════ */
#chartPanel, #resultsPanel {{
    background: {t['bg_secondary']};
    border: 1px solid {t['border_subtle']};
    border-radius: 22px;
}}
#chartCanvas {{
    background: {t['chart_bg']};
    border: 1px solid {t['chart_border']};
    border-radius: 16px;
}}
#panelTitle {{
    font-size: 12px;
    font-weight: 600;
    color: {t['text_muted']};
    padding: 0 4px;
}}
#panelCount {{
    font-size: 11px;
    font-weight: 600;
    color: {t['accent']};
    background: {t['accent_soft']};
    border: 1px solid {t['border_glow']};
    border-radius: 14px;
    padding: 4px 12px;
}}

/* ══ TABS ════════════════════════════════════════════════════════════════ */
QTabWidget::pane {{
    background: transparent;
    border: none;
}}
QTabBar::tab {{
    background: transparent;
    color: {t['text_muted']};
    border: none;
    border-bottom: 2px solid transparent;
    padding: 12px 22px;
    margin-right: 4px;
    font-size: 13px;
    font-weight: 500;
}}
QTabBar::tab:selected {{
    color: {t['text_primary']};
    font-weight: 600;
    border-bottom: 2px solid {t['accent_pink']};
}}
QTabBar::tab:hover:!selected {{
    color: {t['text_secondary']};
    border-bottom: 2px solid {t['border']};
}}

/* ══ TABLE ═══════════════════════════════════════════════════════════════ */
QTableWidget {{
    background: {t['bg_card']};
    border: 1px solid {t['border']};
    border-radius: 16px;
    gridline-color: transparent;
    selection-background-color: {t['selection']};
    selection-color: {t['text_primary']};
    alternate-background-color: {t['bg_elevated']};
}}
QHeaderView::section {{
    background: {t['bg_elevated']};
    color: {t['text_muted']};
    border: none;
    border-bottom: 1px solid {t['border']};
    padding: 11px 12px;
    font-size: 10px;
    font-weight: 600;
}}
QTableWidget::item {{
    padding: 9px 12px;
}}
QTableWidget::item:selected {{
    background: {t['selection']};
}}

QTextBrowser {{
    background: {t['bg_card']};
    border: 1px solid {t['border']};
    border-radius: 16px;
    padding: 12px;
    color: {t['text_primary']};
}}

QSplitter::handle:vertical {{
    background: transparent;
    height: 12px;
}}

/* ══ LOADING ═════════════════════════════════════════════════════════════ */
#loadingOverlay {{
    background: {t['overlay']};
}}
#loadingCard {{
    background: {t['bg_sidebar']};
    border: 1px solid {t['border_subtle']};
    border-radius: 24px;
}}
#loadingTitle {{
    font-size: 16px;
    font-weight: 600;
    color: {t['text_primary']};
}}
#loadingSubtitle {{
    font-size: 12px;
    color: {t['text_secondary']};
}}
#stageDot[active="true"] {{
    background: {t['accent_pink']};
    border-radius: 4px;
    min-width: 8px; max-width: 8px;
    min-height: 8px; max-height: 8px;
}}
#stageDot[active="false"] {{
    background: {t['border']};
    border-radius: 4px;
    min-width: 8px; max-width: 8px;
    min-height: 8px; max-height: 8px;
}}
QProgressBar#progressBar {{
    background: {t['border']};
    border: none;
    border-radius: 6px;
    height: 6px;
}}
QProgressBar#progressBar::chunk {{
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 {t['accent_orange']},
        stop:0.5 {t['accent_pink']},
        stop:1 {t['accent_purple']}
    );
    border-radius: 6px;
}}

#hSep {{
    background: {t['border']};
    max-height: 1px;
    min-height: 1px;
    margin: 8px 14px;
}}

/* ══ DIALOG ══════════════════════════════════════════════════════════════ */
QDialog {{
    background: {bg_grad};
}}
#dialogHeader, #dialogTableCard {{
    background: {t['bg_card']};
    border: 1px solid {t['border_subtle']};
    border-radius: 18px;
}}
#dialogTitle {{
    font-size: 16px;
    font-weight: 600;
    color: {t['text_primary']};
}}
#dialogSubtitle {{
    font-size: 12px;
    color: {t['text_secondary']};
}}
QPushButton#dialogClose {{
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 {t['accent_soft']},
        stop:1 rgba(244,114,182,0.20)
    );
    border: 1px solid {t['border_glow']};
    border-radius: 16px;
    color: {t['accent']};
    padding: 11px 28px;
    font-size: 13px;
    font-weight: 600;
    min-height: 44px;
}}
QPushButton#dialogClose:hover {{
    background: {t['accent']};
    color: {t['btn_primary_text']};
}}

#sidebarFooter {{
    background: transparent;
    border-top: 1px solid {t['border']};
    border-bottom-right-radius: 24px;
}}
#versionLabel {{
    font-size: 10px;
    font-weight: 600;
    color: {t['text_muted']};
    background: {t['bg_card']};
    border: 1px solid {t['border']};
    border-radius: 10px;
    padding: 4px 10px;
}}
#themeLabel {{
    font-size: 12px;
    color: {t['text_secondary']};
}}
"""
