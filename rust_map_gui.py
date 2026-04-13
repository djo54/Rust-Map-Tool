"""
Interface graphique pour le convertisseur Rust .map -> PNG
Supporte: Français, English, Español, Deutsch, 中文, Русский
"""

import sys
import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess

# ─── Traductions ──────────────────────────────────────────────────────────────

LANGS = {
    'fr': 'Français',
    'en': 'English',
    'es': 'Español',
    'de': 'Deutsch',
    'zh': '中文',
    'ru': 'Русский',
}

T = {
    # Titre et labels principaux
    'title': {
        'fr': 'Rust Map → PNG Converter',
        'en': 'Rust Map → PNG Converter',
        'es': 'Rust Map → Convertidor PNG',
        'de': 'Rust Map → PNG Konverter',
        'zh': 'Rust 地图 → PNG 转换器',
        'ru': 'Rust Карта → PNG Конвертер',
    },
    'subtitle': {
        'fr': 'Convertisseur de fichiers .map Rust',
        'en': 'Rust .map file converter',
        'es': 'Convertidor de archivos .map de Rust',
        'de': 'Rust .map-Datei Konverter',
        'zh': 'Rust .map 文件转换器',
        'ru': 'Конвертер файлов .map для Rust',
    },
    # Groupe fichier
    'group_file': {
        'fr': 'Fichier',
        'en': 'File',
        'es': 'Archivo',
        'de': 'Datei',
        'zh': '文件',
        'ru': 'Файл',
    },
    'label_input': {
        'fr': 'Fichier .map :',
        'en': 'Map file:',
        'es': 'Archivo .map:',
        'de': '.map Datei:',
        'zh': '.map 文件：',
        'ru': 'Файл .map:',
    },
    'btn_browse': {
        'fr': 'Parcourir…',
        'en': 'Browse…',
        'es': 'Explorar…',
        'de': 'Durchsuchen…',
        'zh': '浏览…',
        'ru': 'Обзор…',
    },
    'label_output': {
        'fr': 'Dossier de sortie :',
        'en': 'Output folder:',
        'es': 'Carpeta de salida:',
        'de': 'Ausgabeordner:',
        'zh': '输出文件夹：',
        'ru': 'Папка вывода:',
    },
    'btn_browse_out': {
        'fr': 'Choisir…',
        'en': 'Choose…',
        'es': 'Elegir…',
        'de': 'Wählen…',
        'zh': '选择…',
        'ru': 'Выбрать…',
    },
    # Groupe résolution
    'group_res': {
        'fr': 'Résolution de sortie',
        'en': 'Output Resolution',
        'es': 'Resolución de salida',
        'de': 'Ausgabeauflösung',
        'zh': '输出分辨率',
        'ru': 'Разрешение вывода',
    },
    'res_native': {
        'fr': 'Native (4097×4097)',
        'en': 'Native (4097×4097)',
        'es': 'Nativa (4097×4097)',
        'de': 'Nativ (4097×4097)',
        'zh': '原生 (4097×4097)',
        'ru': 'Нативная (4097×4097)',
    },
    'res_custom': {
        'fr': 'Personnalisée :',
        'en': 'Custom:',
        'es': 'Personalizada:',
        'de': 'Benutzerdefiniert:',
        'zh': '自定义：',
        'ru': 'Пользовательская:',
    },
    'res_px': {
        'fr': 'px',
        'en': 'px',
        'es': 'px',
        'de': 'px',
        'zh': '像素',
        'ru': 'пкс',
    },
    # Boutons
    'btn_convert': {
        'fr': '⚙  Convertir',
        'en': '⚙  Convert',
        'es': '⚙  Convertir',
        'de': '⚙  Konvertieren',
        'zh': '⚙  转换',
        'ru': '⚙  Конвертировать',
    },
    'btn_open': {
        'fr': '🖼  Ouvrir le PNG',
        'en': '🖼  Open PNG',
        'es': '🖼  Abrir PNG',
        'de': '🖼  PNG öffnen',
        'zh': '🖼  打开 PNG',
        'ru': '🖼  Открыть PNG',
    },
    'btn_open_folder': {
        'fr': '📂  Ouvrir le dossier',
        'en': '📂  Open folder',
        'es': '📂  Abrir carpeta',
        'de': '📂  Ordner öffnen',
        'zh': '📂  打开文件夹',
        'ru': '📂  Открыть папку',
    },
    # Log / statut
    'group_log': {
        'fr': 'Journal',
        'en': 'Log',
        'es': 'Registro',
        'de': 'Protokoll',
        'zh': '日志',
        'ru': 'Журнал',
    },
    'status_ready': {
        'fr': 'Prêt',
        'en': 'Ready',
        'es': 'Listo',
        'de': 'Bereit',
        'zh': '就绪',
        'ru': 'Готово',
    },
    'status_converting': {
        'fr': 'Conversion en cours…',
        'en': 'Converting…',
        'es': 'Convirtiendo…',
        'de': 'Konvertierung…',
        'zh': '转换中…',
        'ru': 'Конвертирование…',
    },
    'status_done': {
        'fr': 'Terminé !',
        'en': 'Done!',
        'es': '¡Listo!',
        'de': 'Fertig!',
        'zh': '完成！',
        'ru': 'Готово!',
    },
    'status_error': {
        'fr': 'Erreur',
        'en': 'Error',
        'es': 'Error',
        'de': 'Fehler',
        'zh': '错误',
        'ru': 'Ошибка',
    },
    # Messages erreur
    'err_no_file': {
        'fr': 'Veuillez sélectionner un fichier .map.',
        'en': 'Please select a .map file.',
        'es': 'Por favor seleccione un archivo .map.',
        'de': 'Bitte eine .map-Datei auswählen.',
        'zh': '请选择一个 .map 文件。',
        'ru': 'Пожалуйста, выберите файл .map.',
    },
    'err_no_output': {
        'fr': 'Veuillez sélectionner un dossier de sortie.',
        'en': 'Please select an output folder.',
        'es': 'Por favor seleccione una carpeta de salida.',
        'de': 'Bitte einen Ausgabeordner wählen.',
        'zh': '请选择一个输出文件夹。',
        'ru': 'Пожалуйста, выберите папку вывода.',
    },
    'err_invalid_size': {
        'fr': 'Taille invalide. Entrez un nombre entre 256 et 8192.',
        'en': 'Invalid size. Enter a number between 256 and 8192.',
        'es': 'Tamaño inválido. Ingrese un número entre 256 y 8192.',
        'de': 'Ungültige Größe. Geben Sie eine Zahl zwischen 256 und 8192 ein.',
        'zh': '无效大小。请输入256到8192之间的数字。',
        'ru': 'Неверный размер. Введите число от 256 до 8192.',
    },
    'err_script_missing': {
        'fr': 'Script rust_map_to_png.py introuvable.',
        'en': 'Script rust_map_to_png.py not found.',
        'es': 'Script rust_map_to_png.py no encontrado.',
        'de': 'Skript rust_map_to_png.py nicht gefunden.',
        'zh': '找不到脚本 rust_map_to_png.py。',
        'ru': 'Скрипт rust_map_to_png.py не найден.',
    },
    # Filtre fichier
    'filetypes_map': {
        'fr': 'Fichiers Rust Map',
        'en': 'Rust Map Files',
        'es': 'Archivos Rust Map',
        'de': 'Rust-Map-Dateien',
        'zh': 'Rust 地图文件',
        'ru': 'Файлы карт Rust',
    },
    # Info taille
    'info_size': {
        'fr': 'Tailles courantes : 1024 · 2048 · 4097 (native) · 4250',
        'en': 'Common sizes: 1024 · 2048 · 4097 (native) · 4250',
        'es': 'Tamaños comunes: 1024 · 2048 · 4097 (nativo) · 4250',
        'de': 'Übliche Größen: 1024 · 2048 · 4097 (nativ) · 4250',
        'zh': '常用尺寸：1024 · 2048 · 4097（原生）· 4250',
        'ru': 'Обычные размеры: 1024 · 2048 · 4097 (нативный) · 4250',
    },
    'language': {
        'fr': 'Langue',
        'en': 'Language',
        'es': 'Idioma',
        'de': 'Sprache',
        'zh': '语言',
        'ru': 'Язык',
    },
}


def t(key, lang):
    """Récupère la traduction d'une clé pour la langue donnée."""
    return T.get(key, {}).get(lang, T.get(key, {}).get('en', key))


# ─── Application principale ──────────────────────────────────────────────────

class RustMapConverterApp(tk.Tk):
    COLORS = {
        'bg':         '#1e1e2e',
        'panel':      '#2a2a3e',
        'accent':     '#7c5cbf',
        'accent_h':   '#9a78e0',
        'green':      '#4caf50',
        'green_h':    '#66bb6a',
        'text':       '#e0e0f0',
        'text_dim':   '#8888aa',
        'border':     '#44446a',
        'entry_bg':   '#252538',
        'log_bg':     '#141420',
        'error':      '#f44336',
        'warn':       '#ff9800',
        'ok':         '#4caf50',
    }

    def __init__(self):
        super().__init__()

        self.lang = tk.StringVar(value='fr')
        self.lang.trace_add('write', lambda *_: self.refresh_texts())

        self.map_file   = tk.StringVar()
        self.out_folder = tk.StringVar()
        self.res_mode   = tk.StringVar(value='preset')  # 'preset' | 'custom'
        self.res_preset = tk.StringVar(value='2048')
        self.res_custom = tk.StringVar(value='2048')
        self.converting = False
        self.last_output = None

        self._build_ui()
        self.refresh_texts()
        self.center_window()

    # ── Construction UI ───────────────────────────────────────────────────────

    def _build_ui(self):
        C = self.COLORS
        self.configure(bg=C['bg'])
        self.resizable(False, False)
        self.iconbitmap(default='')

        # ── En-tête ──────────────────────────────────────────────────────────
        header = tk.Frame(self, bg=C['accent'], pady=14, padx=20)
        header.pack(fill='x')

        self.lbl_title = tk.Label(header, font=('Segoe UI', 18, 'bold'),
                                  bg=C['accent'], fg='white')
        self.lbl_title.pack(side='left')

        # Sélecteur de langue (côté droit du header)
        lang_frame = tk.Frame(header, bg=C['accent'])
        lang_frame.pack(side='right', padx=4)

        self.lbl_lang = tk.Label(lang_frame, font=('Segoe UI', 9),
                                 bg=C['accent'], fg='white')
        self.lbl_lang.pack(side='left', padx=(0, 6))

        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Lang.TCombobox',
                        fieldbackground=C['entry_bg'],
                        background=C['panel'],
                        foreground=C['text'],
                        selectbackground=C['accent'],
                        selectforeground='white',
                        arrowcolor=C['text'])

        lang_values = [f"{flag} {name}" for flag, (code, name) in zip(
            ['🇫🇷','🇬🇧','🇪🇸','🇩🇪','🇨🇳','🇷🇺'],
            LANGS.items()
        )]
        self._lang_codes = list(LANGS.keys())

        self.cmb_lang = ttk.Combobox(lang_frame, values=lang_values,
                                     state='readonly', width=14,
                                     style='Lang.TCombobox',
                                     font=('Segoe UI', 9))
        self.cmb_lang.current(0)
        self.cmb_lang.pack(side='left')
        self.cmb_lang.bind('<<ComboboxSelected>>', self._on_lang_change)

        # ── Sous-titre ───────────────────────────────────────────────────────
        sub = tk.Frame(self, bg=C['bg'], pady=6)
        sub.pack(fill='x', padx=20)
        self.lbl_subtitle = tk.Label(sub, font=('Segoe UI', 9),
                                     bg=C['bg'], fg=C['text_dim'])
        self.lbl_subtitle.pack(side='left')

        # ── Corps principal ──────────────────────────────────────────────────
        body = tk.Frame(self, bg=C['bg'], padx=20, pady=4)
        body.pack(fill='both')

        # ── Groupe Fichier ───────────────────────────────────────────────────
        self.frm_file = self._make_group(body)
        self.frm_file.pack(fill='x', pady=(0, 10))

        # Fichier input
        row_in = tk.Frame(self.frm_file, bg=C['panel'])
        row_in.pack(fill='x', pady=(8, 4), padx=10)
        self.lbl_input = tk.Label(row_in, width=18, anchor='w',
                                  font=('Segoe UI', 9),
                                  bg=C['panel'], fg=C['text'])
        self.lbl_input.pack(side='left')
        self.ent_input = tk.Entry(row_in, textvariable=self.map_file,
                                  font=('Segoe UI', 9),
                                  bg=C['entry_bg'], fg=C['text'],
                                  insertbackground=C['text'],
                                  relief='flat', bd=4, width=42)
        self.ent_input.pack(side='left', padx=(0, 6))
        self.btn_browse_in = self._make_btn(row_in, '', self._browse_map,
                                            small=True)
        self.btn_browse_in.pack(side='left')

        # Dossier output
        row_out = tk.Frame(self.frm_file, bg=C['panel'])
        row_out.pack(fill='x', pady=(0, 10), padx=10)
        self.lbl_output = tk.Label(row_out, width=18, anchor='w',
                                   font=('Segoe UI', 9),
                                   bg=C['panel'], fg=C['text'])
        self.lbl_output.pack(side='left')
        self.ent_output = tk.Entry(row_out, textvariable=self.out_folder,
                                   font=('Segoe UI', 9),
                                   bg=C['entry_bg'], fg=C['text'],
                                   insertbackground=C['text'],
                                   relief='flat', bd=4, width=42)
        self.ent_output.pack(side='left', padx=(0, 6))
        self.btn_browse_out = self._make_btn(row_out, '', self._browse_out,
                                             small=True)
        self.btn_browse_out.pack(side='left')

        # ── Groupe Résolution ────────────────────────────────────────────────
        self.frm_res = self._make_group(body)
        self.frm_res.pack(fill='x', pady=(0, 10))

        row_res = tk.Frame(self.frm_res, bg=C['panel'])
        row_res.pack(fill='x', padx=10, pady=(8, 0))

        # Boutons preset
        presets = [('1024', '1024'), ('2048', '2048'),
                   ('4097', '4097'), ('4250', '4250')]
        self._preset_btns = {}
        for val, label in presets:
            b = tk.Button(row_res, text=f'{label}×{label}',
                          font=('Segoe UI', 9, 'bold'),
                          relief='flat', cursor='hand2', bd=0,
                          padx=12, pady=6,
                          command=lambda v=val: self._select_preset(v))
            b.pack(side='left', padx=(0, 6))
            self._preset_btns[val] = b
        self._select_preset('2048')

        # Résolution personnalisée
        row_custom = tk.Frame(self.frm_res, bg=C['panel'])
        row_custom.pack(fill='x', padx=10, pady=(6, 0))

        self.lbl_custom = tk.Label(row_custom, font=('Segoe UI', 9),
                                   bg=C['panel'], fg=C['text'])
        self.lbl_custom.pack(side='left')
        self.ent_custom = tk.Entry(row_custom, textvariable=self.res_custom,
                                   font=('Segoe UI', 10, 'bold'),
                                   bg=C['entry_bg'], fg=C['accent_h'],
                                   insertbackground=C['text'],
                                   relief='flat', bd=4, width=7)
        self.ent_custom.pack(side='left', padx=6)
        self.ent_custom.bind('<FocusIn>',  lambda _: self._select_preset(None))
        self.ent_custom.bind('<KeyRelease>', lambda _: self._select_preset(None))
        self.lbl_px = tk.Label(row_custom, font=('Segoe UI', 9),
                               bg=C['panel'], fg=C['text_dim'])
        self.lbl_px.pack(side='left')

        # Hint tailles
        row_hint = tk.Frame(self.frm_res, bg=C['panel'])
        row_hint.pack(fill='x', padx=10, pady=(4, 10))
        self.lbl_hint = tk.Label(row_hint, font=('Segoe UI', 8),
                                 bg=C['panel'], fg=C['text_dim'])
        self.lbl_hint.pack(side='left')

        # ── Bouton Convertir ─────────────────────────────────────────────────
        btn_row = tk.Frame(self, bg=C['bg'], padx=20, pady=6)
        btn_row.pack(fill='x')

        self.btn_convert = tk.Button(btn_row, font=('Segoe UI', 12, 'bold'),
                                     relief='flat', cursor='hand2',
                                     bg=C['accent'], fg='white',
                                     activebackground=C['accent_h'],
                                     activeforeground='white',
                                     padx=24, pady=10, bd=0,
                                     command=self._start_convert)
        self.btn_convert.pack(fill='x')

        # ── Barre de progression ──────────────────────────────────────────────
        prog_frame = tk.Frame(self, bg=C['bg'], padx=20)
        prog_frame.pack(fill='x')

        style.configure('Rust.Horizontal.TProgressbar',
                        troughcolor=C['panel'],
                        background=C['accent'],
                        borderwidth=0, relief='flat')
        self.progressbar = ttk.Progressbar(prog_frame, mode='indeterminate',
                                           style='Rust.Horizontal.TProgressbar',
                                           length=560)
        self.progressbar.pack(fill='x', pady=(6, 2))

        # ── Log ──────────────────────────────────────────────────────────────
        log_outer = tk.Frame(self, bg=C['bg'], padx=20, pady=4)
        log_outer.pack(fill='both', expand=True)
        self.frm_log = self._make_group(log_outer)
        self.frm_log.pack(fill='both', expand=True)

        log_inner = tk.Frame(self.frm_log, bg=C['log_bg'])
        log_inner.pack(fill='both', expand=True, padx=6, pady=(4, 6))

        self.txt_log = tk.Text(log_inner, height=10,
                               font=('Consolas', 8),
                               bg=C['log_bg'], fg=C['text'],
                               insertbackground=C['text'],
                               relief='flat', bd=0,
                               state='disabled',
                               wrap='word')
        scrollbar = tk.Scrollbar(log_inner, command=self.txt_log.yview,
                                 bg=C['panel'], troughcolor=C['log_bg'],
                                 relief='flat', bd=0, width=8)
        self.txt_log.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')
        self.txt_log.pack(side='left', fill='both', expand=True)

        # Tags de couleur dans le log
        self.txt_log.tag_configure('ok',   foreground=C['ok'])
        self.txt_log.tag_configure('err',  foreground=C['error'])
        self.txt_log.tag_configure('warn', foreground=C['warn'])
        self.txt_log.tag_configure('dim',  foreground=C['text_dim'])

        # ── Boutons résultat ──────────────────────────────────────────────────
        res_row = tk.Frame(self, bg=C['bg'], padx=20, pady=6)
        res_row.pack(fill='x')

        self.btn_open_png = tk.Button(res_row, font=('Segoe UI', 9),
                                      relief='flat', cursor='hand2',
                                      bg=C['green'], fg='white',
                                      activebackground=C['green_h'],
                                      activeforeground='white',
                                      padx=14, pady=6, bd=0, state='disabled',
                                      command=self._open_png)
        self.btn_open_png.pack(side='left', padx=(0, 8))

        self.btn_open_folder = tk.Button(res_row, font=('Segoe UI', 9),
                                         relief='flat', cursor='hand2',
                                         bg=C['panel'], fg=C['text'],
                                         activebackground=C['border'],
                                         padx=14, pady=6, bd=0, state='disabled',
                                         command=self._open_folder)
        self.btn_open_folder.pack(side='left')

        # ── Statut ───────────────────────────────────────────────────────────
        self.lbl_status = tk.Label(self, font=('Segoe UI', 8),
                                   bg=C['bg'], fg=C['text_dim'], pady=4)
        self.lbl_status.pack()

    # ── Widgets helpers ───────────────────────────────────────────────────────

    def _make_group(self, parent):
        C = self.COLORS
        frame = tk.LabelFrame(parent, bg=C['panel'], fg=C['text_dim'],
                              font=('Segoe UI', 9, 'bold'),
                              relief='flat', bd=1,
                              highlightbackground=C['border'],
                              highlightthickness=1)
        return frame

    def _make_btn(self, parent, text, command, small=False):
        C = self.COLORS
        return tk.Button(parent, text=text, command=command,
                         font=('Segoe UI', 9 if not small else 8),
                         relief='flat', cursor='hand2', bd=0,
                         bg=C['panel'], fg=C['text'],
                         activebackground=C['border'],
                         padx=10 if small else 16,
                         pady=4)

    def _select_preset(self, val):
        C = self.COLORS
        self.res_mode.set('preset' if val else 'custom')
        if val:
            self.res_preset.set(val)
        for v, b in self._preset_btns.items():
            active = (val == v)
            b.configure(
                bg=C['accent'] if active else C['border'],
                fg='white' if active else C['text'],
                activebackground=C['accent_h'] if active else C['border'],
            )

    # ── Langue ───────────────────────────────────────────────────────────────

    def _on_lang_change(self, event=None):
        idx = self.cmb_lang.current()
        self.lang.set(self._lang_codes[idx])

    def refresh_texts(self):
        L = self.lang.get()
        self.title(t('title', L))
        self.lbl_title.configure(text=t('title', L))
        self.lbl_subtitle.configure(text=t('subtitle', L))
        self.lbl_lang.configure(text=t('language', L) + ':')

        # Groupes
        self.frm_file.configure(text=f"  {t('group_file', L)}  ")
        self.frm_res.configure(text=f"  {t('group_res', L)}  ")
        self.frm_log.configure(text=f"  {t('group_log', L)}  ")

        # Labels
        self.lbl_input.configure(text=t('label_input', L))
        self.btn_browse_in.configure(text=t('btn_browse', L))
        self.lbl_output.configure(text=t('label_output', L))
        self.btn_browse_out.configure(text=t('btn_browse_out', L))
        self.lbl_custom.configure(text=t('res_custom', L))
        self.lbl_px.configure(text=t('res_px', L))
        self.lbl_hint.configure(text=t('info_size', L))

        # Boutons
        self.btn_convert.configure(text=t('btn_convert', L))
        self.btn_open_png.configure(text=t('btn_open', L))
        self.btn_open_folder.configure(text=t('btn_open_folder', L))

        # Statut
        if not self.converting:
            self.lbl_status.configure(text=t('status_ready', L))

    # ── Parcourir fichiers ────────────────────────────────────────────────────

    def _browse_map(self):
        L = self.lang.get()
        path = filedialog.askopenfilename(
            title=t('label_input', L),
            filetypes=[
                (t('filetypes_map', L), '*.map'),
                ('All files', '*.*'),
            ]
        )
        if path:
            self.map_file.set(path)
            # Auto-remplir dossier de sortie
            if not self.out_folder.get():
                self.out_folder.set(os.path.dirname(path))

    def _browse_out(self):
        L = self.lang.get()
        folder = filedialog.askdirectory(title=t('label_output', L))
        if folder:
            self.out_folder.set(folder)

    # ── Conversion ────────────────────────────────────────────────────────────

    def _get_size(self):
        if self.res_mode.get() == 'preset':
            return int(self.res_preset.get())
        else:
            try:
                v = int(self.res_custom.get())
                if 256 <= v <= 8192:
                    return v
            except ValueError:
                pass
            return None

    def _start_convert(self):
        L = self.lang.get()
        if self.converting:
            return

        # Validation
        map_path = self.map_file.get().strip()
        out_dir  = self.out_folder.get().strip()

        if not map_path or not os.path.isfile(map_path):
            messagebox.showerror(t('status_error', L), t('err_no_file', L))
            return
        if not out_dir:
            messagebox.showerror(t('status_error', L), t('err_no_output', L))
            return

        size = self._get_size()
        if size is None:
            messagebox.showerror(t('status_error', L), t('err_invalid_size', L))
            return

        # Chemin du script de conversion
        script = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              'rust_map_to_png.py')
        if not os.path.isfile(script):
            messagebox.showerror(t('status_error', L), t('err_script_missing', L))
            return

        # Chemin de sortie
        base = os.path.splitext(os.path.basename(map_path))[0]
        out_path = os.path.join(out_dir, f"{base}_{size}x{size}.png")
        self.last_output = out_path

        # Lancer la conversion dans un thread
        self.converting = True
        self._log_clear()
        self.btn_convert.configure(state='disabled',
                                   bg=self.COLORS['border'])
        self.btn_open_png.configure(state='disabled')
        self.btn_open_folder.configure(state='disabled')
        self.progressbar.start(12)
        self.lbl_status.configure(text=t('status_converting', L),
                                  fg=self.COLORS['accent_h'])

        cmd = [sys.executable, '-X', 'utf8', script,
               map_path, '-o', out_path, '-s', str(size)]

        thread = threading.Thread(target=self._run_conversion,
                                  args=(cmd, L), daemon=True)
        thread.start()

    def _run_conversion(self, cmd, L):
        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='replace'
            )
            for line in proc.stdout:
                self._log(line.rstrip())
            proc.wait()
            success = (proc.returncode == 0)
        except Exception as e:
            self._log(str(e), tag='err')
            success = False

        self.after(0, self._conversion_done, success, L)

    def _conversion_done(self, success, L):
        self.converting = False
        self.progressbar.stop()
        self.progressbar['value'] = 0

        self.btn_convert.configure(state='normal',
                                   bg=self.COLORS['accent'])

        if success:
            self.lbl_status.configure(text=t('status_done', L),
                                      fg=self.COLORS['ok'])
            self._log(f"\n✔ {t('status_done', L)} → {self.last_output}", tag='ok')
            self.btn_open_png.configure(state='normal')
            self.btn_open_folder.configure(state='normal')
        else:
            self.lbl_status.configure(text=t('status_error', L),
                                      fg=self.COLORS['error'])
            self._log(f"\n✖ {t('status_error', L)}", tag='err')

    # ── Log ───────────────────────────────────────────────────────────────────

    def _log(self, text, tag=None):
        def _insert():
            self.txt_log.configure(state='normal')
            self.txt_log.insert('end', text + '\n', tag or '')
            self.txt_log.see('end')
            self.txt_log.configure(state='disabled')
        self.after(0, _insert)

    def _log_clear(self):
        self.txt_log.configure(state='normal')
        self.txt_log.delete('1.0', 'end')
        self.txt_log.configure(state='disabled')

    # ── Ouvrir résultat ───────────────────────────────────────────────────────

    def _open_png(self):
        if self.last_output and os.path.isfile(self.last_output):
            os.startfile(self.last_output)

    def _open_folder(self):
        folder = self.out_folder.get()
        if folder and os.path.isdir(folder):
            os.startfile(folder)

    # ── Centrer fenêtre ───────────────────────────────────────────────────────

    def center_window(self):
        self.update_idletasks()
        w, h = self.winfo_width(), self.winfo_height()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.geometry(f'+{x}+{y}')


# ─── Lancement ────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    app = RustMapConverterApp()
    app.mainloop()
