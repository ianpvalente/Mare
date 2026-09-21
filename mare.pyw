# -*- coding: utf-8 -*-
"""
Maré — agenda de área de trabalho em um arquivo só.
Interface: customtkinter (instalado automaticamente na primeira vez).
Dados: mare_dados.json, na mesma pasta deste arquivo.
"""

import json
import os
import random
import string
import sys
from datetime import date, datetime, timedelta

# ----------------------------------------------------------------
# instala dependências na primeira execução (sem console)
# ----------------------------------------------------------------
FROZEN = getattr(sys, "frozen", False)   # True quando roda como .exe / .app
IS_MAC = sys.platform == "darwin"

def ensure_packages():
    if FROZEN:
        return
    try:
        import customtkinter  # noqa
        return
    except ImportError:
        pass
    import tkinter as _tk
    import subprocess
    r = _tk.Tk()
    r.title("Maré")
    r.geometry("380x100+480+320")
    _tk.Label(r, text="Preparando o Maré pela primeira vez…\n"
                      "(instalando componentes visuais, ~30 s)").pack(expand=True)
    r.update()
    cmd = [sys.executable, "-m", "pip", "install", "--user", "customtkinter"]
    if os.name == "nt":
        subprocess.call(cmd, creationflags=0x08000000)
    else:
        subprocess.call(cmd)
    r.destroy()

ensure_packages()

import tkinter as tk
import tkinter.font as tkfont
from tkinter import messagebox
import customtkinter as ctk

if os.name == "nt":
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("mare.agenda")
    except Exception:
        pass

try:
    import winsound
except ImportError:
    winsound = None

# ----------------------------------------------------------------
# aparência
# ----------------------------------------------------------------
BG          = "#F6F5F1"
SURFACE     = "#FFFFFF"
FIELD       = "#FBFBF8"
INK         = "#25291F"
INK_SOFT    = "#6B7060"
LINE        = "#E3E1D8"
GRIDLINE    = "#EFEDE6"
ACCENT      = "#33604A"
ACCENT_DARK = "#2A5140"
ACCENT_SOFT = "#E4EEE7"
HOLIDAY     = "#8E4A56"
HOLIDAY_BG  = "#F5EAEA"
NOW_COLOR   = "#B0543F"
WARN_COLOR  = "#9A6A22"
DIM         = "#CFCEC5"

PALETTE = [
    ("verde",  "#33604A"),
    ("azul",   "#2F5876"),
    ("vinho",  "#8E3B48"),
    ("ameixa", "#7C5069"),
    ("âmbar",  "#9A6A22"),
    ("mar",    "#2E6E6A"),
]
def color_of(cid):
    for k, c in PALETTE:
        if k == cid:
            return c
    return PALETTE[0][1]

def blend(hexc, t):
    """Mistura a cor com branco (t = fração de branco, 0–1)."""
    r = int(hexc[1:3], 16); g = int(hexc[3:5], 16); b = int(hexc[5:7], 16)
    r = int(r + (255 - r) * t); g = int(g + (255 - g) * t); b = int(b + (255 - b) * t)
    return "#%02x%02x%02x" % (r, g, b)

def shade(hexc, t):
    """Mistura a cor com preto (t = fração de preto, 0–1)."""
    r = int(hexc[1:3], 16); g = int(hexc[3:5], 16); b = int(hexc[5:7], 16)
    r = int(r * (1 - t)); g = int(g * (1 - t)); b = int(b * (1 - t))
    return "#%02x%02x%02x" % (r, g, b)

WD = ["seg", "ter", "qua", "qui", "sex", "sáb", "dom"]
MONTHS = ["janeiro", "fevereiro", "março", "abril", "maio", "junho",
          "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]

H0, H1 = 6, 24
HH = 40
PURGE_DAYS = 60

BASE_DIR = os.path.dirname(os.path.abspath(sys.executable if FROZEN else __file__))
RES_DIR  = getattr(sys, "_MEIPASS", BASE_DIR)   # arquivos embutidos no app

def _data_dir():
    """Script solto: dados ao lado do arquivo. App: pasta de dados do usuário."""
    if not FROZEN:
        return BASE_DIR
    home = os.path.expanduser("~")
    if os.name == "nt":
        base = os.environ.get("APPDATA") or home
    elif IS_MAC:
        base = os.path.join(home, "Library", "Application Support")
    else:
        base = os.environ.get("XDG_DATA_HOME") or os.path.join(home, ".local", "share")
    p = os.path.join(base, "Mare")
    os.makedirs(p, exist_ok=True)
    return p

DATA_DIR  = _data_dir()
DATA_FILE = os.path.join(DATA_DIR, "mare_dados.json")
ICO_FILE  = os.path.join(RES_DIR, "mare.ico")

# quem já usava a versão .pyw: se houver dados ao lado do app, traz para a pasta nova
if FROZEN and not os.path.exists(DATA_FILE):
    _old = os.path.join(BASE_DIR, "mare_dados.json")
    if os.path.exists(_old):
        try:
            import shutil
            shutil.copy2(_old, DATA_FILE)
        except Exception:
            pass

RCLICK = "<Button-2>" if IS_MAC else "<Button-3>"   # clique direito
ICON_PNG_B64 = "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"

# ----------------------------------------------------------------
# dados
# ----------------------------------------------------------------
def load_data():
    d = {}
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                d = json.load(f)
        except Exception:
            d = {}
    return (d.get("events", []), d.get("routines", []), d.get("notif", {}),
            d.get("lists", []), d.get("tasks", []), d.get("filters", {}),
            d.get("settings", {}), d.get("urg_dismissed", {}))

def save_data():
    tmp = DATA_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump({"events": EVENTS, "routines": ROUTINES, "notif": NOTIF,
                   "lists": LISTS, "tasks": TASKS, "filters": FILTERS,
                   "settings": SETTINGS, "urg_dismissed": URGD},
                  f, ensure_ascii=False, indent=1)
    os.replace(tmp, DATA_FILE)

EVENTS, ROUTINES, NOTIF, LISTS, TASKS, FILTERS, SETTINGS, URGD = load_data()
SETTINGS.setdefault("insistent", True)
URGD.clear()  # dispensar um aviso de urgência vale só até fechar o app

def new_id(prefix="e"):
    return prefix + datetime.now().strftime("%y%m%d%H%M%S") + \
           "".join(random.choices(string.ascii_lowercase, k=4))

# ----------------------------------------------------------------
# datas e feriados
# ----------------------------------------------------------------
def fmt(d): return d.strftime("%Y-%m-%d")
def parse(s): return datetime.strptime(s, "%Y-%m-%d").date()
def br(dstr):
    try:
        return parse(dstr).strftime("%d/%m/%Y")
    except Exception:
        return dstr
def start_of_week(d): return d - timedelta(days=d.weekday())
def minutes(t):
    h, m = t.split(":")
    return int(h) * 60 + int(m)
def hhmm(m):
    return "%02d:%02d" % divmod(m, 60)

def easter(y):
    a = y % 19; b = y // 100; c = y % 100
    d = b // 4; e = b % 4; f = (b + 8) // 25; g = (b - f + 1) // 3
    h = (19*a + b - d - g + 15) % 30
    i = c // 4; k = c % 4
    l = (32 + 2*e + 2*i - h - k) % 7
    m = (a + 11*h + 22*l) // 451
    mo = (h + l - 7*m + 114) // 31
    da = ((h + l - 7*m + 114) % 31) + 1
    return date(y, mo, da)

_hcache = {}
def holidays(y):
    if y in _hcache:
        return _hcache[y]
    e = easter(y)
    m = {}
    def put(d, name): m[fmt(d)] = name
    put(date(y, 1, 1),  "Confraternização")
    put(date(y, 1, 20), "São Sebastião (RJ)")
    put(e - timedelta(days=48), "Carnaval")
    put(e - timedelta(days=47), "Carnaval")
    put(e - timedelta(days=2),  "Sexta-feira Santa")
    put(date(y, 4, 21), "Tiradentes")
    put(date(y, 4, 23), "São Jorge (RJ)")
    put(date(y, 5, 1),  "Dia do Trabalho")
    put(e + timedelta(days=60), "Corpus Christi")
    put(date(y, 9, 7),  "Independência")
    put(date(y, 10, 12), "N. Sra. Aparecida")
    put(date(y, 11, 2),  "Finados")
    put(date(y, 11, 15), "Proclamação da República")
    put(date(y, 11, 20), "Consciência Negra")
    put(date(y, 12, 25), "Natal")
    _hcache[y] = m
    return m

def holiday_of(d):
    return holidays(d.year).get(fmt(d))

# ----------------------------------------------------------------
# consultas
# ----------------------------------------------------------------
def events_on_day(d):
    key = fmt(d)
    out = []
    for ev in EVENTS:
        rep = ev.get("repeat")
        if rep:
            if key < ev["date"]:
                continue
            ed = parse(ev["date"])
            if rep == "yearly" and (d.month, d.day) == (ed.month, ed.day):
                out.append(ev)
            elif rep == "monthly" and d.day == ed.day:
                out.append(ev)
            elif rep == "weekly" and d.weekday() == ed.weekday():
                out.append(ev)
        elif ev.get("endDate"):
            if ev["date"] <= key <= ev["endDate"]:
                out.append(ev)
        elif ev["date"] == key:
            out.append(ev)
    return out

def timed_events(d):
    evs = [e for e in events_on_day(d) if not e.get("allDay") and e.get("start")]
    evs.sort(key=lambda e: (minutes(e["start"]), e["id"]))
    return evs

def allday_events(d):
    return [e for e in events_on_day(d) if e.get("allDay") or not e.get("start")]

def tasks_on(d):
    key = fmt(d)
    return [t for t in TASKS if t.get("date") == key]

def conflicts_at(dstr, start, end, ignore=()):
    try:
        d = parse(dstr)
        s = minutes(start)
    except Exception:
        return []
    e = minutes(end) if end else s + 60
    out = []
    for ev in timed_events(d):
        if ev["id"] in ignore:
            continue
        s2 = minutes(ev["start"])
        e2 = minutes(ev["end"]) if ev.get("end") else s2 + 60
        if s < e2 and s2 < e:
            out.append(ev)
    return out

def used_colors(dstr, start, end, allday, ignore=()):
    """Cores já ocupadas no mesmo horário (ou no mesmo dia, para dia inteiro)."""
    try:
        d = parse(dstr)
    except Exception:
        return set()
    if allday or not start:
        return {e.get("color") for e in allday_events(d) if e["id"] not in ignore}
    return {c.get("color") for c in conflicts_at(dstr, start, end, ignore=ignore)}

def routine_items(rt):
    if rt.get("items"):
        return [dict(it) for it in rt["items"]]
    groups = {}
    for e in EVENTS:
        if e.get("routineId") == rt["id"]:
            k = (e["title"], e.get("start"), e.get("end"), e.get("color"))
            groups.setdefault(k, set()).add(parse(e["date"]).weekday())
    return [{"title": t, "days": sorted(ds), "start": s, "end": en, "color": c}
            for (t, s, en, c), ds in groups.items()]

def list_by_id(lid):
    return next((l for l in LISTS if l["id"] == lid), None)

def eff_urgency(ev):
    u = ev.get("urgency")
    if u and u != "normal":
        return u
    l = list_by_id(ev.get("listId")) if ev.get("listId") else None
    lu = (l or {}).get("urgency")
    return lu if lu and lu != "normal" else None

def next_occurrence(ev, ref):
    """Próxima data (>= ref) em que o evento acontece, ou None."""
    rep = ev.get("repeat")
    d0 = parse(ev["date"])
    if not rep:
        if d0 >= ref:
            return d0
        if ev.get("endDate") and parse(ev["endDate"]) >= ref:
            return ref
        return None
    if rep == "weekly":
        base = max(d0, ref)
        return base + timedelta(days=(d0.weekday() - base.weekday()) % 7)
    if rep == "monthly":
        y, m = ref.year, ref.month
        for _ in range(24):
            try:
                c = date(y, m, d0.day)
                if c >= ref and c >= d0:
                    return c
            except ValueError:
                pass
            m += 1
            if m > 12:
                m = 1; y += 1
        return None
    if rep == "yearly":
        y = ref.year
        for _ in range(8):
            try:
                c = date(y, d0.month, d0.day)
                if c >= ref and c >= d0:
                    return c
            except ValueError:
                pass
            y += 1
        return None
    return None

def days_label(nd):
    dias = (nd - date.today()).days
    if dias < 0:
        return "já passou"
    if dias == 0:
        return "é hoje!"
    if dias == 1:
        return "é amanhã"
    return "faltam %d dias" % dias

def vis_key(ev):
    if ev.get("routineId"):
        return "r:" + ev["routineId"]
    if ev.get("listId"):
        return "l:" + ev["listId"]
    return "solo"

def visible_in_overview(ev):
    return FILTERS.get(vis_key(ev), True)

def purge_old():
    """Apaga eventos/tarefas concluídos há mais de PURGE_DAYS dias."""
    cutoff = fmt(date.today() - timedelta(days=PURGE_DAYS))
    global EVENTS, TASKS
    before = len(EVENTS) + len(TASKS)
    EVENTS = [e for e in EVENTS
              if e.get("repeat") or (e.get("endDate") or e["date"]) >= cutoff]
    TASKS = [t for t in TASKS
             if not (t.get("done") and (t.get("doneDate") or "0") < cutoff)]
    ids = {e["id"] for e in EVENTS}
    for k in list(URGD.keys()):
        if k not in ids:
            del URGD[k]
    if len(EVENTS) + len(TASKS) != before:
        save_data()

# ----------------------------------------------------------------
# iniciar com o Windows
# ----------------------------------------------------------------
def _launch_cmd():
    """Comando que abre o Maré (app empacotado ou script solto)."""
    if FROZEN:
        return [sys.executable]
    exe = sys.executable
    if os.name == "nt" and exe.lower().endswith("python.exe"):
        pw = os.path.join(os.path.dirname(exe), "pythonw.exe")
        if os.path.exists(pw):
            exe = pw
    return [exe, os.path.abspath(__file__)]

_MAC_PLIST = os.path.expanduser("~/Library/LaunchAgents/com.mare.agenda.plist")
_LINUX_DESKTOP = os.path.expanduser("~/.config/autostart/mare.desktop")

def autostart_enabled():
    if os.name == "nt":
        try:
            import winreg
            k = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                               r"Software\Microsoft\Windows\CurrentVersion\Run")
            winreg.QueryValueEx(k, "Mare")
            return True
        except OSError:
            return False
    if IS_MAC:
        return os.path.exists(_MAC_PLIST)
    return os.path.exists(_LINUX_DESKTOP)

def set_autostart(on):
    cmd = _launch_cmd()
    if os.name == "nt":
        import winreg
        k = winreg.CreateKey(winreg.HKEY_CURRENT_USER,
                             r"Software\Microsoft\Windows\CurrentVersion\Run")
        if on:
            winreg.SetValueEx(k, "Mare", 0, winreg.REG_SZ,
                              " ".join('"%s"' % c for c in cmd))
        else:
            try:
                winreg.DeleteValue(k, "Mare")
            except OSError:
                pass
        return
    if IS_MAC:
        if on:
            os.makedirs(os.path.dirname(_MAC_PLIST), exist_ok=True)
            args = "".join("<string>%s</string>" % c for c in cmd)
            with open(_MAC_PLIST, "w", encoding="utf-8") as f:
                f.write('<?xml version="1.0" encoding="UTF-8"?>\n'
                        '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" '
                        '"http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n'
                        '<plist version="1.0"><dict>'
                        '<key>Label</key><string>com.mare.agenda</string>'
                        '<key>ProgramArguments</key><array>%s</array>'
                        '<key>RunAtLoad</key><true/>'
                        '</dict></plist>\n' % args)
        elif os.path.exists(_MAC_PLIST):
            os.remove(_MAC_PLIST)
        return
    if on:
        os.makedirs(os.path.dirname(_LINUX_DESKTOP), exist_ok=True)
        with open(_LINUX_DESKTOP, "w", encoding="utf-8") as f:
            f.write("[Desktop Entry]\nType=Application\nName=Maré\nExec=%s\n"
                    "X-GNOME-Autostart-enabled=true\n"
                    % " ".join('"%s"' % c for c in cmd))
    elif os.path.exists(_LINUX_DESKTOP):
        os.remove(_LINUX_DESKTOP)

# ----------------------------------------------------------------
# desenho
# ----------------------------------------------------------------
def rrect(c, x0, y0, x1, y1, r, **kw):
    r = max(1, min(r, (x1 - x0) / 2, (y1 - y0) / 2))
    pts = [x0+r, y0, x1-r, y0, x1, y0, x1, y0+r, x1, y1-r, x1, y1,
           x1-r, y1, x0+r, y1, x0, y1, x0, y1-r, x0, y0+r, x0, y0]
    return c.create_polygon(pts, smooth=True, **kw)

def clusters(evs):
    """Agrupa eventos com horário que se sobrepõem em cadeia."""
    out = []
    cur, cur_end = [], -1
    for ev in evs:
        s = minutes(ev["start"])
        e = minutes(ev["end"]) if ev.get("end") else s + 60
        if cur and s < cur_end:
            cur.append(ev)
            cur_end = max(cur_end, e)
        else:
            if cur:
                out.append(cur)
            cur, cur_end = [ev], e
    if cur:
        out.append(cur)
    return out

class DateField(ctk.CTkFrame):
    """Data em três caixinhas (dia / mês / ano), com dropdown e digitação."""
    def __init__(self, master, app, optional=False):
        super().__init__(master, fg_color="transparent")
        self.optional = optional
        hoje = date.today()
        days = (["—"] if optional else []) + ["%02d" % i for i in range(1, 32)]
        months = ["%02d" % i for i in range(1, 13)]
        years = [str(y) for y in range(hoje.year - 1, hoje.year + 6)]
        kw = dict(height=30, corner_radius=8, fg_color=FIELD, border_color=LINE,
                  button_color=ACCENT, button_hover_color=ACCENT_DARK,
                  text_color=INK, font=app.f_ui, dropdown_font=app.f_ui)
        self.d = ctk.CTkComboBox(self, width=62, values=days, **kw)
        self.m = ctk.CTkComboBox(self, width=62, values=months, **kw)
        self.y = ctk.CTkComboBox(self, width=82, values=years, **kw)
        self.d.pack(side="left")
        self._slash(app)
        self.m.pack(side="left")
        self._slash(app)
        self.y.pack(side="left")
        if optional:
            self.d.set("—")
            self.m.set("%02d" % hoje.month)
            self.y.set(str(hoje.year))
        else:
            self.set(hoje)

    def _slash(self, app):
        ctk.CTkLabel(self, text="/", text_color=INK_SOFT,
                     font=app.f_ui).pack(side="left", padx=2)

    def set(self, d):
        self.d.set("%02d" % d.day)
        self.m.set("%02d" % d.month)
        self.y.set(str(d.year))

    def get(self):
        """date, ou None se vazio (quando opcional). ValueError se inválida."""
        dv = self.d.get().strip()
        if self.optional and dv in ("", "—"):
            return None
        return date(int(self.y.get().strip()), int(self.m.get().strip()), int(dv))

    def set_state(self, st):
        for w in (self.d, self.m, self.y):
            w.configure(state=st)

    def on_change(self, fn):
        for w in (self.d, self.m, self.y):
            w.configure(command=lambda v, fn=fn: fn())
            ent = getattr(w, "_entry", None)
            if ent is not None:
                ent.bind("<KeyRelease>", lambda e, fn=fn: fn())

# ----------------------------------------------------------------
# aplicativo
# ----------------------------------------------------------------
class App(ctk.CTk):
    def __init__(self):
        ctk.set_appearance_mode("light")
        super().__init__(fg_color=BG)
        self.title("Maré — agenda")
        self.geometry("1180x780")
        self.minsize(900, 600)
        self._set_icon()
        self.after(350, self._set_icon)

        fams = set(tkfont.families(self))
        serif = "Georgia" if "Georgia" in fams else "Times New Roman"
        self.f_brand = ctk.CTkFont(family=serif, size=24, slant="italic")
        self.f_title = ctk.CTkFont(family=serif, size=18)
        self.f_h     = ctk.CTkFont(family=serif, size=16)
        self.f_ui    = ctk.CTkFont(family="Segoe UI", size=12)
        self.f_lab   = ctk.CTkFont(family="Segoe UI", size=11)
        self.tf_day   = (serif, 12)
        self.tf_small = ("Segoe UI", 8)
        self._meas = tkfont.Font(family="Segoe UI", size=8)

        self.view = "week"
        self.cursor = date.today()
        self.alarms = {}
        self.blocker = None
        self.card = None
        self._drag = None
        self._tip = None
        self._tip_after = None
        self._urg_widgets = []

        purge_old()
        self._build_header()
        self.body = ctk.CTkFrame(self, fg_color="transparent")
        self.body.pack(fill="both", expand=True)
        ctk.CTkLabel(self, text="clique = abrir · arrastar = mover · borda de baixo = "
                                "esticar · clique direito = excluir   ·   dados em " + DATA_FILE,
                     text_color=INK_SOFT, font=ctk.CTkFont(size=10),
                     anchor="w").pack(fill="x", padx=20, pady=(0, 5))

        self.bind("<Escape>", lambda e: self.close_modal())
        self.render()
        self.after(1500, self.tick)

    def _set_icon(self):
        try:
            if os.name == "nt" and os.path.exists(ICO_FILE):
                self.iconbitmap(ICO_FILE)
            else:
                img = tk.PhotoImage(data=ICON_PNG_B64)
                self.iconphoto(True, img)
                self._icon_ref = img
        except Exception:
            pass

    # ---------------- cabeçalho ----------------
    def _build_header(self):
        h = ctk.CTkFrame(self, fg_color="transparent")
        h.pack(fill="x", padx=20, pady=(14, 8))

        ctk.CTkButton(h, text="☰", command=self.open_browser, width=38, height=32,
                      fg_color=SURFACE, hover_color=ACCENT_SOFT, text_color=INK,
                      border_width=1, border_color=LINE, corner_radius=9,
                      font=self.f_ui).pack(side="left", padx=(0, 12))
        ctk.CTkLabel(h, text="Maré", text_color=ACCENT,
                     font=self.f_brand).pack(side="left", padx=(0, 16))

        self.seg = ctk.CTkSegmentedButton(
            h, values=["Ano", "Mês", "Semana", "Dia"],
            command=self._seg_change, font=self.f_ui,
            fg_color="#ECEAE2", text_color=INK,
            selected_color="#CFE2D6", selected_hover_color="#C2D9CB",
            unselected_color="#ECEAE2", unselected_hover_color=ACCENT_SOFT,
            corner_radius=9, height=32)
        self.seg.set("Semana")
        self.seg.pack(side="left")

        def navbtn(txt, cmd, w=34):
            return ctk.CTkButton(h, text=txt, command=cmd, width=w, height=32,
                                 fg_color=SURFACE, hover_color=ACCENT_SOFT,
                                 text_color=INK, border_width=1, border_color=LINE,
                                 corner_radius=9, font=self.f_ui)
        navbtn("‹", lambda: self.shift(-1)).pack(side="left", padx=(14, 3))
        navbtn("›", lambda: self.shift(1)).pack(side="left", padx=(0, 3))
        navbtn("Hoje", self.go_today, w=56).pack(side="left")

        self.period = ctk.CTkLabel(h, text="", text_color=INK, font=self.f_title)
        self.period.pack(side="left", padx=14)

        ctk.CTkButton(h, text="+ Evento", command=lambda: self.open_event(None),
                      fg_color=ACCENT, hover_color=ACCENT_DARK, height=32,
                      corner_radius=9, font=self.f_ui).pack(side="right")
        ctk.CTkButton(h, text="+ Rotina", command=self.open_routine,
                      fg_color=SURFACE, hover_color=ACCENT_SOFT, text_color=INK,
                      border_width=1, border_color=LINE, height=32,
                      corner_radius=9, font=self.f_ui).pack(side="right", padx=(0, 8))

    def _seg_change(self, value):
        self.view = {"Ano": "year", "Mês": "month", "Semana": "week", "Dia": "day"}[value]
        self.render()

    def go_today(self):
        self.cursor = date.today()
        self.render()

    def shift(self, k):
        d = self.cursor
        if self.view == "year":
            self.cursor = date(d.year + k, 1, 1)
        elif self.view == "month":
            m = d.month + k
            y = d.year + (m - 1) // 12
            m = (m - 1) % 12 + 1
            self.cursor = date(y, m, 1)
        elif self.view == "week":
            self.cursor = d + timedelta(days=7 * k)
        else:
            self.cursor = d + timedelta(days=k)
        self.render()

    # ---------------- utilidades de UI ----------------
    def _entry(self, parent, w=120, ph=""):
        e = ctk.CTkEntry(parent, width=w, height=30, placeholder_text=ph,
                         fg_color=FIELD, border_color=LINE, text_color=INK,
                         corner_radius=8, font=self.f_ui)
        e._ph = ph
        return e

    def _val(self, e):
        """Valor do campo, ignorando o texto de exemplo que às vezes vaza."""
        v = e.get().strip()
        return "" if v == getattr(e, "_ph", None) else v

    def _label(self, parent, text):
        return ctk.CTkLabel(parent, text=text, text_color=INK_SOFT, font=self.f_lab)

    def _trunc(self, text, maxpx):
        if self._meas.measure(text) <= maxpx:
            return text
        while text and self._meas.measure(text + "…") > maxpx:
            text = text[:-1]
        return text + "…"

    # tooltip flutuante
    def _tip_show(self, text, x, y):
        self._tip_hide()
        t = tk.Toplevel(self)
        t.overrideredirect(True)
        t.attributes("-topmost", True)
        tk.Label(t, text=text, bg=INK, fg="#F6F5F1", font=("Segoe UI", 9),
                 justify="left", padx=9, pady=5).pack()
        t.geometry("+%d+%d" % (x + 14, y + 14))
        self._tip = t

    def _tip_hide(self):
        if self._tip_after:
            try:
                self.after_cancel(self._tip_after)
            except Exception:
                pass
            self._tip_after = None
        if self._tip is not None:
            try:
                self._tip.destroy()
            except Exception:
                pass
            self._tip = None

    def _bind_tip(self, canvas, tag, textfn):
        def enter(e):
            canvas.configure(cursor="hand2")
            self._tip_after = self.after(
                400, lambda x=e.x_root, y=e.y_root: self._tip_show(textfn(), x, y))
        def leave(_):
            canvas.configure(cursor="")
            self._tip_hide()
        canvas.tag_bind(tag, "<Enter>", enter)
        canvas.tag_bind(tag, "<Leave>", leave)
        canvas.tag_bind(tag, "<ButtonPress>", lambda e: self._tip_hide(), add="+")

    def event_tipfn(self, ev, d):
        def fn():
            when = ("dia inteiro" if ev.get("allDay") or not ev.get("start")
                    else ev["start"] + ("–" + ev["end"] if ev.get("end") else ""))
            return "%s\n%s · %s" % (ev["title"], when, days_label(d))
        return fn

    # ---------------- filtros (mês / ano) ----------------
    def filter_bar(self, parent):
        bar = ctk.CTkFrame(parent, fg_color="transparent")
        def add_chip(key, label, color):
            var = tk.BooleanVar(value=FILTERS.get(key, True))
            def flip():
                FILTERS[key] = var.get()
                save_data()
                self.render()
            ctk.CTkCheckBox(bar, text=label, variable=var, command=flip,
                            fg_color=color, hover_color=shade(color, 0.2),
                            border_color=blend(color, 0.4), text_color=INK,
                            checkbox_width=16, checkbox_height=16,
                            corner_radius=8, font=self.f_lab
                            ).pack(side="left", padx=(0, 14))
        for rt in ROUTINES:
            its = routine_items(rt)
            c = color_of(its[0]["color"]) if its else ACCENT
            add_chip("r:" + rt["id"], rt["name"], c)
        for l in LISTS:
            evs = [e for e in EVENTS if e.get("listId") == l["id"]]
            c = color_of(evs[0].get("color")) if evs else ACCENT
            add_chip("l:" + l["id"], l["name"], c)
        add_chip("solo", "eventos avulsos", INK_SOFT)
        return bar

    # ---------------- render ----------------
    def render(self):
        self.close_modal()
        self._tip_hide()
        self.seg.set({"year": "Ano", "month": "Mês",
                      "week": "Semana", "day": "Dia"}[self.view])
        for w in self.body.winfo_children():
            w.destroy()
        if self.view == "year":
            self.render_year()
        elif self.view == "month":
            self.render_month()
        else:
            days = ([self.cursor] if self.view == "day"
                    else [start_of_week(self.cursor) + timedelta(days=i) for i in range(7)])
            self.render_grid(days)
        self.refresh_banners()

    # ---------------- visão anual ----------------
    def render_year(self):
        y = self.cursor.year
        self.period.configure(text=str(y))
        sf = ctk.CTkScrollableFrame(self.body, fg_color="transparent")
        sf.pack(fill="both", expand=True, padx=12)
        self.filter_bar(self.body).pack(anchor="center", pady=(4, 2))
        holder = ctk.CTkFrame(sf, fg_color="transparent")
        holder.pack(anchor="center", pady=4)
        today = date.today()
        for m in range(12):
            card = ctk.CTkFrame(holder, fg_color=SURFACE, corner_radius=12,
                                border_width=1, border_color=LINE)
            card.grid(row=m // 4, column=m % 4, padx=7, pady=7)
            c = tk.Canvas(card, width=238, height=188, bg=SURFACE,
                          highlightthickness=0)
            c.pack(padx=8, pady=8)
            c.create_text(8, 14, text=MONTHS[m], anchor="w", fill=INK, font=self.tf_day)
            cw, x0, y0, rh = 32, 6, 38, 24
            for i, w in enumerate(WD):
                c.create_text(x0 + i * cw + cw / 2, y0, text=w[0],
                              fill=INK_SOFT, font=self.tf_small)
            first = date(y, m + 1, 1)
            lead = first.weekday()
            nxt = date(y + (m + 1) // 12, (m + 1) % 12 + 1, 1)
            ndays = (nxt - timedelta(days=1)).day
            for dnum in range(1, ndays + 1):
                idx = lead + dnum - 1
                col, row = idx % 7, idx // 7
                cx = x0 + col * cw + cw / 2
                cy = y0 + 18 + row * rh
                d = date(y, m + 1, dnum)
                if holiday_of(d):
                    rrect(c, cx - 13, cy - 9, cx + 13, cy + 11, 7,
                          fill=HOLIDAY_BG, outline="")
                if d == today:
                    rrect(c, cx - 13, cy - 9, cx + 13, cy + 11, 7,
                          fill="", outline=ACCENT, width=2)
                c.create_text(cx, cy, text=str(dnum),
                              fill=HOLIDAY if holiday_of(d) else INK,
                              font=self.tf_small)
                evs = [e for e in events_on_day(d) if visible_in_overview(e)]
                k = min(len(evs), 3)
                for j, ev in enumerate(evs[:3]):
                    ox = cx - (k * 6) / 2 + j * 6 + 1
                    c.create_oval(ox, cy + 6, ox + 4, cy + 10,
                                  fill=color_of(ev.get("color")), outline="")
            def on_click(e, mm=m, lead=lead, ndays=ndays):
                col = int((e.x - 6) // 32)
                row = int((e.y - 44) // 24)
                dnum = row * 7 + col - lead + 1
                if 0 <= col < 7 and 1 <= dnum <= ndays:
                    self.cursor = date(y, mm + 1, dnum)
                    self.view = "day"
                    self.render()
            c.bind("<Button-1>", on_click)

    # ---------------- visão mensal ----------------
    def render_month(self):
        y, m = self.cursor.year, self.cursor.month
        self.period.configure(text="%s %d" % (MONTHS[m - 1], y))
        wrap = ctk.CTkFrame(self.body, fg_color=SURFACE, corner_radius=14,
                            border_width=1, border_color=LINE)
        wrap.pack(fill="both", expand=True, padx=20, pady=(2, 4))
        c = tk.Canvas(wrap, bg=SURFACE, highlightthickness=0)
        c.pack(fill="both", expand=True, padx=10, pady=10)
        self.filter_bar(self.body).pack(anchor="center", pady=(2, 4))

        first = date(y, m, 1)
        lead = first.weekday()
        nxt = date(y + m // 12, m % 12 + 1, 1)
        ndays = (nxt - timedelta(days=1)).day
        rows = (lead + ndays + 6) // 7
        today = date.today()

        def draw(_=None):
            c.delete("all")
            W = max(c.winfo_width(), 500)
            Hc = max(c.winfo_height(), 300)
            colw = W / 7
            headh = 22
            rowh = (Hc - headh) / rows
            for i, w in enumerate(WD):
                c.create_text(i * colw + colw / 2, headh / 2, text=w,
                              fill=INK_SOFT, font=self.tf_small)
            for r in range(rows + 1):
                c.create_line(0, headh + r * rowh, W, headh + r * rowh, fill=GRIDLINE)
            for i in range(8):
                c.create_line(i * colw, headh, i * colw, Hc, fill=GRIDLINE)
            for dnum in range(1, ndays + 1):
                idx = lead + dnum - 1
                col, row = idx % 7, idx // 7
                x0 = col * colw
                y0 = headh + row * rowh
                d = date(y, m, dnum)
                hol = holiday_of(d)
                if d == today:
                    rrect(c, x0 + 4, y0 + 3, x0 + 26, y0 + 20, 9,
                          fill=ACCENT, outline="")
                    c.create_text(x0 + 15, y0 + 11, text=str(dnum),
                                  fill="#FFFFFF", font=self.tf_small)
                else:
                    c.create_text(x0 + 15, y0 + 11, text=str(dnum),
                                  fill=HOLIDAY if hol else INK, font=self.tf_small)
                if hol:
                    c.create_text(x0 + 30, y0 + 11, anchor="w",
                                  text=self._trunc(hol, colw - 36),
                                  fill=HOLIDAY, font=self.tf_small)
                evs = [e for e in events_on_day(d) if visible_in_overview(e)]
                maxbars = max(1, int((rowh - 24) // 16))
                yy = y0 + 22
                for ev in evs[:maxbars]:
                    tag = "mv_%s_%d" % (ev["id"], dnum)
                    base = color_of(ev.get("color"))
                    soft = ev.get("allDay") or not ev.get("start")
                    rrect(c, x0 + 4, yy, x0 + colw - 4, yy + 14, 6,
                          fill=blend(base, 0.78) if soft else base,
                          outline="", tags=(tag,))
                    label = ev["title"] if soft else (ev["start"] + " " + ev["title"])
                    c.create_text(x0 + 9, yy + 7, anchor="w",
                                  text=self._trunc(label, colw - 16),
                                  fill=base if soft else "#FFFFFF",
                                  font=self.tf_small, tags=(tag,))
                    c.tag_bind(tag, "<Button-1>",
                               lambda e, ev=ev: self.open_event(ev))
                    c.tag_bind(tag, RCLICK,
                               lambda e, ev=ev: self.event_menu(ev, e.x_root, e.y_root))
                    self._bind_tip(c, tag, self.event_tipfn(ev, d))
                    yy += 16
                if len(evs) > maxbars:
                    c.create_text(x0 + 8, yy + 6, anchor="w",
                                  text="+%d" % (len(evs) - maxbars),
                                  fill=INK_SOFT, font=self.tf_small)
            def cell_click(e):
                if c.find_withtag("current") and any(
                        t.startswith("mv_") for t in c.gettags("current")):
                    return
                col = int(e.x // colw)
                row = int((e.y - headh) // rowh)
                dnum = row * 7 + col - lead + 1
                if 0 <= col < 7 and 1 <= dnum <= ndays:
                    self.cursor = date(y, m, dnum)
                    self.view = "day"
                    self.render()
            c.bind("<Button-1>", cell_click)
        c.bind("<Configure>", draw)
        self.after(10, draw)

    # ---------------- semana / dia ----------------
    def render_grid(self, days):
        if len(days) == 7:
            a, b = days[0], days[6]
            self.period.configure(text="%d %s – %d %s %d" % (
                a.day, MONTHS[a.month - 1][:3], b.day, MONTHS[b.month - 1][:3], b.year))
        else:
            d = days[0]
            self.period.configure(text="%s, %d de %s de %d" % (
                WD[d.weekday()], d.day, MONTHS[d.month - 1], d.year))

        wrap = ctk.CTkFrame(self.body, fg_color=SURFACE, corner_radius=14,
                            border_width=1, border_color=LINE)
        wrap.pack(fill="both", expand=True, padx=20, pady=(2, 8))

        self.head = tk.Canvas(wrap, bg=SURFACE, highlightthickness=0, height=44)
        self.head.pack(anchor="w", padx=12, pady=(12, 0))

        row = ctk.CTkFrame(wrap, fg_color="transparent")
        row.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        self.grid_c = tk.Canvas(row, bg=SURFACE, highlightthickness=0)
        sb = ctk.CTkScrollbar(row, command=self.grid_c.yview, width=14)
        self.grid_c.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y", padx=(4, 0))
        self.grid_c.pack(side="left", fill="both", expand=True)

        def wheel(e, k=None):
            if self.grid_c.winfo_exists():
                if k is None:
                    k = -e.delta if IS_MAC else -e.delta // 120
                    if k == 0:
                        k = -1 if e.delta > 0 else 1
                self.grid_c.yview_scroll(k, "units")
        self.grid_c.bind("<MouseWheel>", wheel)
        self.grid_c.bind("<Button-4>", lambda e: wheel(e, -1))
        self.grid_c.bind("<Button-5>", lambda e: wheel(e, 1))
        self.head.bind("<MouseWheel>", wheel)

        self._days = days
        self.grid_c.bind("<Configure>", lambda e: self.draw_all())
        self.after(10, self.draw_all)

    def draw_all(self):
        if not hasattr(self, "grid_c") or not self.grid_c.winfo_exists():
            return
        days = self._days
        gc, hc = self.grid_c, self.head
        gc.delete("all")
        hc.delete("all")
        self._drag = None

        W = max(gc.winfo_width(), 500)
        LEFT = 48
        colw = (W - LEFT - 2) / len(days)
        total_h = (H1 - H0) * HH + 6
        gc.configure(scrollregion=(0, 0, W, total_h))
        today = date.today()
        self._geom = (LEFT, colw, days)

        # ----- cabeçalho -----
        extras = []
        for d in days:
            ads = allday_events(d)
            tks = tasks_on(d)
            n = (1 if holiday_of(d) else 0) + min(len(ads), 2) + \
                (1 if len(ads) > 2 else 0) + min(len(tks), 2)
            extras.append(n)
        max_extra = max(extras) if extras else 0
        head_h = 34 + max_extra * 19 + 2
        hc.configure(width=W, height=head_h)

        for i, d in enumerate(days):
            cx = LEFT + i * colw + colw / 2
            label = "%s %d" % (WD[d.weekday()], d.day)
            if d == today:
                tw = self._meas.measure(label) + 26
                rrect(hc, cx - tw / 2, 4, cx + tw / 2, 28, 12, fill=ACCENT, outline="")
                hc.create_text(cx, 16, text=label, fill="#FFFFFF", font=self.tf_day)
            else:
                hc.create_text(cx, 16, text=label, fill=INK, font=self.tf_day)
            yy = 36
            hol = holiday_of(d)
            if hol:
                hc.create_text(cx, yy + 6, text=self._trunc(hol, colw - 10),
                               fill=HOLIDAY, font=self.tf_small)
                yy += 19
            ads = allday_events(d)
            for ev in ads[:2]:
                tag = "ad_" + ev["id"]
                base = color_of(ev.get("color"))
                rrect(hc, LEFT + i * colw + 4, yy, LEFT + (i + 1) * colw - 4, yy + 16, 8,
                      fill=blend(base, 0.78), outline="", tags=(tag,))
                hc.create_text(cx, yy + 8, text=self._trunc(ev["title"], colw - 20),
                               fill=base, font=self.tf_small, tags=(tag,))
                hc.tag_bind(tag, "<Button-1>", lambda e, ev=ev: self.open_event(ev))
                hc.tag_bind(tag, RCLICK,
                            lambda e, ev=ev: self.event_menu(ev, e.x_root, e.y_root))
                self._bind_tip(hc, tag, self.event_tipfn(ev, d))
                yy += 19
            if len(ads) > 2:
                hc.create_text(cx, yy + 7, text="+%d" % (len(ads) - 2),
                               fill=INK_SOFT, font=self.tf_small)
                yy += 19
            for t in tasks_on(d)[:2]:
                tag = "tk_" + t["id"]
                done = t.get("done")
                rrect(hc, LEFT + i * colw + 4, yy, LEFT + (i + 1) * colw - 4, yy + 16, 8,
                      fill="#F1F0EA", outline="", tags=(tag,))
                hc.create_text(cx, yy + 8,
                               text=self._trunc(("✓ " if done else "☐ ") + t["title"],
                                                colw - 20),
                               fill=INK_SOFT if done else INK,
                               font=self.tf_small, tags=(tag,))
                def toggle(e, t=t):
                    t["done"] = not t.get("done")
                    t["doneDate"] = fmt(date.today()) if t["done"] else None
                    save_data()
                    self.draw_all()
                hc.tag_bind(tag, "<Button-1>", toggle)
                yy += 19

        # ----- grade -----
        for i, d in enumerate(days):
            if d == today:
                gc.create_rectangle(LEFT + i * colw, 0, LEFT + (i + 1) * colw, total_h,
                                    fill="#FAF9F4", outline="")
            ads = allday_events(d)
            if ads:
                gc.create_rectangle(LEFT + i * colw, 0, LEFT + (i + 1) * colw, total_h,
                                    fill=blend(color_of(ads[0].get("color")), 0.94),
                                    outline="")
        for h in range(H0, H1):
            yy = (h - H0) * HH
            gc.create_line(LEFT, yy, W, yy, fill=GRIDLINE)
            gc.create_text(LEFT - 7, yy + 8, text="%02dh" % h, anchor="e",
                           fill=INK_SOFT, font=self.tf_small)
        for i in range(len(days) + 1):
            x = LEFT + i * colw
            gc.create_line(x, 0, x, total_h, fill=LINE if i in (0, len(days)) else GRIDLINE)

        # eventos em cascata quando sobrepostos
        for i, d in enumerate(days):
            bx0 = LEFT + i * colw + 3
            bx1 = LEFT + (i + 1) * colw - 3
            for cluster in clusters(timed_events(d)):
                for k, ev in enumerate(cluster):
                    s = minutes(ev["start"])
                    e = minutes(ev["end"]) if ev.get("end") else s + 60
                    y0 = (s - H0 * 60) / 60 * HH
                    y1 = max(y0 + 18, (e - H0 * 60) / 60 * HH - 1)
                    dx = min(k * 12, max(0, (bx1 - bx0) - 46))
                    x0 = bx0 + dx
                    y0 = min(y0 + k * 18, y1 - 18)
                    tag = "ev_" + ev["id"]
                    rrect(gc, x0, y0, bx1, y1, 8, fill=color_of(ev.get("color")),
                          outline=SURFACE, width=1 if k else 0, tags=(tag,))
                    label = ev["title"]
                    if y1 - y0 >= 32 and len(cluster) == 1:
                        label += "\n" + ev["start"] + \
                                 ("–" + ev["end"] if ev.get("end") else "")
                    gc.create_text(x0 + 7, y0 + 4, text=label, anchor="nw",
                                   fill="#FFFFFF", font=self.tf_small,
                                   width=max(20, bx1 - x0 - 12), tags=(tag,))
                    gc.tag_bind(tag, "<ButtonPress-1>",
                                lambda e, ev=ev, col=i: self._drag_press(e, ev, col))
                    gc.tag_bind(tag, RCLICK,
                                lambda e, ev=ev: self.event_menu(ev, e.x_root, e.y_root))
                    self._bind_tip(gc, tag, self.event_tipfn(ev, d))

        gc.bind("<B1-Motion>", self._drag_motion)
        gc.bind("<ButtonRelease-1>", self._drag_release)

        # linha do agora
        now = datetime.now()
        if today in days:
            mins = now.hour * 60 + now.minute
            if H0 * 60 <= mins < H1 * 60:
                i = days.index(today)
                yy = (mins - H0 * 60) / 60 * HH
                gc.create_line(LEFT + i * colw, yy, LEFT + (i + 1) * colw, yy,
                               fill=NOW_COLOR, width=2)
                gc.create_oval(LEFT + i * colw - 3, yy - 3, LEFT + i * colw + 3, yy + 3,
                               fill=NOW_COLOR, outline="")

        def dbl(e):
            cur = gc.find_withtag("current")
            if cur and any("ev_" in t for t in gc.gettags(cur[0])):
                return
            cy = gc.canvasy(e.y)
            i = int((e.x - LEFT) // colw)
            if 0 <= i < len(days):
                h = min(H1 - 1, max(H0, int(cy // HH) + H0))
                self.open_event(None, fmt(days[i]), "%02d:00" % h)
        gc.bind("<Double-1>", dbl)

    # ---------------- arrastar / redimensionar ----------------
    def _drag_press(self, e, ev, col):
        gc = self.grid_c
        cy = gc.canvasy(e.y)
        s = minutes(ev["start"])
        en = minutes(ev["end"]) if ev.get("end") else s + 60
        y1 = (en - H0 * 60) / 60 * HH
        mode = "resize" if (y1 - cy) <= 8 else "move"
        self._drag = {"ev": ev, "mode": mode, "col": col,
                      "px": e.x, "py": cy, "moved": False,
                      "grab": cy - (s - H0 * 60) / 60 * HH, "target": None}

    def _drag_motion(self, e):
        dg = self._drag
        if not dg:
            return
        gc = self.grid_c
        cy = gc.canvasy(e.y)
        if not dg["moved"] and abs(e.x - dg["px"]) < 4 and abs(cy - dg["py"]) < 4:
            return
        dg["moved"] = True
        self._tip_hide()
        LEFT, colw, days = self._geom
        ev = dg["ev"]
        s = minutes(ev["start"])
        en = minutes(ev["end"]) if ev.get("end") else s + 60
        dur = en - s
        gc.delete("ghost")
        if dg["mode"] == "move":
            i = max(0, min(len(days) - 1, int((e.x - LEFT) // colw)))
            top = cy - dg["grab"]
            smin = int(round((top / HH * 60 + H0 * 60) / 15)) * 15
            smin = max(H0 * 60, min(H1 * 60 - 15, smin))
            emin = min(H1 * 60, smin + dur)
            dg["target"] = (i, smin, emin)
        else:
            i = dg["col"]
            emin = int(round((cy / HH * 60 + H0 * 60) / 15)) * 15
            emin = max(s + 15, min(H1 * 60, emin))
            dg["target"] = (i, s, emin)
        i, smin, emin = dg["target"]
        y0 = (smin - H0 * 60) / 60 * HH
        y1 = (emin - H0 * 60) / 60 * HH
        x0 = LEFT + i * colw + 3
        x1 = LEFT + (i + 1) * colw - 3
        gc.create_rectangle(x0, y0, x1, y1, outline=color_of(ev.get("color")),
                            width=2, dash=(4, 2), tags=("ghost",))
        ty = y0 - 9 if y0 > 14 else y1 + 9
        gc.create_text(x0 + 4, ty, anchor="w",
                       text="%s–%s" % (hhmm(smin), hhmm(emin)),
                       fill=INK_SOFT, font=self.tf_small, tags=("ghost",))

    def _drag_release(self, e):
        dg = self._drag
        self._drag = None
        if not dg:
            return
        gc = self.grid_c
        gc.delete("ghost")
        ev = dg["ev"]
        if not dg["moved"]:
            self.open_event(ev)
            return
        if not dg["target"]:
            return
        LEFT, colw, days = self._geom
        i, smin, emin = dg["target"]
        if dg["mode"] == "move":
            ev["date"] = fmt(days[i])
        ev["start"] = hhmm(smin)
        ev["end"] = hhmm(emin)
        NOTIF.pop(ev["id"], None)
        save_data()
        self.draw_all()

    # ---------------- painéis dentro da janela ----------------
    def open_modal(self, width=520):
        self.close_modal()
        self._tip_hide()
        self.blocker = tk.Frame(self, bg=DIM)
        self.blocker.place(x=0, y=0, relwidth=1, relheight=1)
        self.blocker.bind("<Button-1>", lambda e: self.close_modal())
        self.card = ctk.CTkFrame(self, fg_color=SURFACE, corner_radius=16,
                                 border_width=1, border_color=LINE, width=width)
        self.card.place(relx=0.5, rely=0.5, anchor="center")
        return self.card

    def close_modal(self):
        for w in (self.card, self.blocker):
            if w is not None:
                try:
                    w.destroy()
                except Exception:
                    pass
        self.card = self.blocker = None

    # ---------------- evento ----------------
    def open_event(self, ev, date_str=None, start_str=None):
        card = self.open_modal()
        pad = {"padx": 22}
        top = ctk.CTkFrame(card, fg_color="transparent")
        top.pack(fill="x", pady=(18, 10), **pad)
        ctk.CTkLabel(top, text="Editar evento" if ev else "Novo evento",
                     text_color=INK, font=self.f_title).pack(side="left")
        lbl_count = ctk.CTkLabel(top, text="", text_color=ACCENT, font=self.f_lab)
        lbl_count.pack(side="right")

        self._label(card, "Título").pack(anchor="w", **pad)
        e_title = self._entry(card, w=440, ph="Prova de Estatística, viagem, consulta…")
        e_title.pack(anchor="w", **pad)

        # cores
        crow = ctk.CTkFrame(card, fg_color="transparent")
        crow.pack(anchor="w", pady=(12, 2), **pad)
        color_var = {"v": (ev or {}).get("color") or "verde"}
        cbtns = {}
        def pick(k):
            color_var["v"] = k
            for kk, b in cbtns.items():
                b.configure(border_width=2 if kk == k else 0)
        for k, c in PALETTE:
            b = ctk.CTkButton(crow, text="", width=26, height=26, corner_radius=13,
                              fg_color=c, hover_color=c, border_color=INK,
                              border_width=2 if k == color_var["v"] else 0,
                              command=lambda k=k: pick(k))
            b.pack(side="left", padx=(0, 8))
            cbtns[k] = b

        allday = tk.BooleanVar(value=bool((ev or {}).get("allDay")))
        cb = ctk.CTkCheckBox(card, text="Dia inteiro (sem horário)", variable=allday,
                             text_color=INK, font=self.f_ui, corner_radius=6,
                             fg_color=ACCENT, hover_color=ACCENT_DARK,
                             border_color=LINE, checkbox_width=20, checkbox_height=20)
        cb.pack(anchor="w", pady=(12, 10), **pad)

        r1 = ctk.CTkFrame(card, fg_color="transparent")
        r1.pack(anchor="w", **pad)
        c1 = ctk.CTkFrame(r1, fg_color="transparent"); c1.pack(side="left", padx=(0, 16))
        self._label(c1, "Data").pack(anchor="w")
        e_date = DateField(c1, self); e_date.pack()
        c2 = ctk.CTkFrame(r1, fg_color="transparent"); c2.pack(side="left")
        self._label(c2, "Até (opcional)").pack(anchor="w")
        e_edate = DateField(c2, self, optional=True); e_edate.pack()

        r2 = ctk.CTkFrame(card, fg_color="transparent")
        r2.pack(anchor="w", pady=(10, 0), **pad)
        c3 = ctk.CTkFrame(r2, fg_color="transparent"); c3.pack(side="left", padx=(0, 12))
        self._label(c3, "Início").pack(anchor="w")
        e_start = self._entry(c3, w=80, ph="HH:MM"); e_start.pack()
        c4 = ctk.CTkFrame(r2, fg_color="transparent"); c4.pack(side="left", padx=(0, 12))
        self._label(c4, "Fim").pack(anchor="w")
        e_end = self._entry(c4, w=80, ph="HH:MM"); e_end.pack()
        c5 = ctk.CTkFrame(r2, fg_color="transparent"); c5.pack(side="left")
        self._label(c5, "Avisar").pack(anchor="w")
        remind = ctk.CTkOptionMenu(c5, width=140, height=30, corner_radius=8,
                                   values=["na hora", "5 min antes", "10 min antes",
                                           "15 min antes", "30 min antes"],
                                   fg_color=FIELD, button_color=ACCENT,
                                   button_hover_color=ACCENT_DARK, text_color=INK,
                                   font=self.f_ui, dropdown_font=self.f_ui)
        remind.pack()

        r3 = ctk.CTkFrame(card, fg_color="transparent")
        r3.pack(anchor="w", pady=(10, 0), **pad)
        c6 = ctk.CTkFrame(r3, fg_color="transparent"); c6.pack(side="left", padx=(0, 12))
        self._label(c6, "Repete").pack(anchor="w")
        repeat = ctk.CTkOptionMenu(c6, width=130, height=30, corner_radius=8,
                                   values=["não repete", "toda semana",
                                           "todo mês", "todo ano"],
                                   fg_color=FIELD, button_color=ACCENT,
                                   button_hover_color=ACCENT_DARK, text_color=INK,
                                   font=self.f_ui, dropdown_font=self.f_ui)
        repeat.pack()
        c7 = ctk.CTkFrame(r3, fg_color="transparent"); c7.pack(side="left", padx=(0, 12))
        self._label(c7, "Lista").pack(anchor="w")
        list_names = ["nenhuma"] + [l["name"] for l in LISTS] + ["+ nova lista…"]
        lst_menu = ctk.CTkOptionMenu(c7, width=150, height=30, corner_radius=8,
                                     values=list_names,
                                     fg_color=FIELD, button_color=ACCENT,
                                     button_hover_color=ACCENT_DARK, text_color=INK,
                                     font=self.f_ui, dropdown_font=self.f_ui)
        lst_menu.pack()
        c8 = ctk.CTkFrame(r3, fg_color="transparent"); c8.pack(side="left")
        self._label(c8, "Urgência").pack(anchor="w")
        urg = ctk.CTkOptionMenu(c8, width=120, height=30, corner_radius=8,
                                values=["normal", "importante", "urgente"],
                                fg_color=FIELD, button_color=ACCENT,
                                button_hover_color=ACCENT_DARK, text_color=INK,
                                font=self.f_ui, dropdown_font=self.f_ui)
        urg.pack()

        def on_list_pick(v):
            if v == "+ nova lista…":
                dlg = ctk.CTkInputDialog(text="Nome da nova lista:", title="Maré")
                name = (dlg.get_input() or "").strip()
                if name:
                    LISTS.append({"id": new_id("l"), "name": name, "urgency": None})
                    save_data()
                    lst_menu.configure(values=["nenhuma"] +
                                       [l["name"] for l in LISTS] + ["+ nova lista…"])
                    lst_menu.set(name)
                else:
                    lst_menu.set("nenhuma")
        lst_menu.configure(command=on_list_pick)

        self._label(card, "Notas (opcional)").pack(anchor="w", pady=(10, 2), **pad)
        e_notes = ctk.CTkTextbox(card, width=440, height=52, fg_color=FIELD,
                                 border_color=LINE, border_width=1, text_color=INK,
                                 corner_radius=8, font=self.f_ui)
        e_notes.pack(anchor="w", **pad)

        acts = ctk.CTkFrame(card, fg_color="transparent")
        acts.pack(fill="x", pady=(16, 18), **pad)

        def refresh_dyn(*_):
            # contagem regressiva
            try:
                nd = e_date.get()
                lbl_count.configure(text=days_label(nd))
            except Exception:
                nd = None
                lbl_count.configure(text="")
            # cores já ocupadas no horário ficam indisponíveis
            dstr = fmt(nd) if nd else ""
            taken = used_colors(dstr, self._val(e_start) or None,
                                self._val(e_end) or None, allday.get(),
                                ignore={(ev or {}).get("id")})
            for k, b in cbtns.items():
                base = color_of(k)
                if k in taken and k != color_var["v"]:
                    b.configure(state="disabled", fg_color=blend(base, 0.78))
                else:
                    b.configure(state="normal", fg_color=base)
            if color_var["v"] in taken:
                free = [k for k, _ in PALETTE if k not in taken]
                if free:
                    pick(free[0])

        def toggle():
            st = "disabled" if allday.get() else "normal"
            e_start.configure(state=st)
            e_end.configure(state=st)
            e_edate.set_state("normal" if allday.get() else "disabled")
            refresh_dyn()
        cb.configure(command=toggle)
        e_date.on_change(refresh_dyn)
        for w in (e_start, e_end):
            w.bind("<KeyRelease>", refresh_dyn)

        def do_save():
            title = self._val(e_title)
            try:
                nd = e_date.get()
            except Exception:
                messagebox.showwarning("Maré", "Data inválida. Confira dia, mês e ano.",
                                       parent=self)
                return
            dstr = fmt(nd)
            if not title:
                messagebox.showwarning("Maré", "Preencha o título.", parent=self)
                return
            ad = allday.get()
            start = self._val(e_start) or None
            end = self._val(e_end) or None
            if not ad:
                for t in (start, end):
                    if t:
                        try:
                            minutes(t)
                        except Exception:
                            messagebox.showwarning("Maré", "Horário inválido. Use HH:MM, ex.: 14:30.",
                                                   parent=self)
                            return
            edate = None
            if ad:
                try:
                    ed = e_edate.get()
                except Exception:
                    messagebox.showwarning("Maré", "Data final inválida. Confira dia, mês e ano.",
                                           parent=self)
                    return
                edate = fmt(ed) if ed else None
            rem = {"na hora": 0, "5 min antes": 5, "10 min antes": 10,
                   "15 min antes": 15, "30 min antes": 30}[remind.get()]
            rep = {"não repete": None, "toda semana": "weekly",
                   "todo mês": "monthly", "todo ano": "yearly"}[repeat.get()]
            lname = lst_menu.get()
            lid = next((l["id"] for l in LISTS if l["name"] == lname), None)
            # cor não pode repetir no mesmo horário: ajusta sozinho se precisar
            color = color_var["v"]
            taken = used_colors(dstr, start, end, ad, ignore={(ev or {}).get("id")})
            if color in taken:
                free = [k for k, _ in PALETTE if k not in taken]
                if free:
                    color = free[0]
            data = {
                "id": ev["id"] if ev else new_id(),
                "title": title, "date": dstr, "allDay": ad,
                "endDate": edate if (ad and not rep) else None,
                "start": None if ad else start,
                "end": None if ad else end,
                "remind": rem, "repeat": rep, "color": color,
                "listId": lid,
                "urgency": None if urg.get() == "normal" else urg.get(),
                "notes": e_notes.get("1.0", "end").strip() or None,
                "routineId": ev.get("routineId") if ev else None,
            }
            global EVENTS
            if ev:
                EVENTS = [data if x["id"] == ev["id"] else x for x in EVENTS]
                NOTIF.pop(ev["id"], None)
            else:
                EVENTS.append(data)
            save_data()
            self.render()

        del_ref = {}
        def do_delete():
            if ev.get("routineId"):
                b = del_ref["b"]
                self.event_menu(ev, b.winfo_rootx(), b.winfo_rooty() + b.winfo_height() + 2)
            else:
                self.delete_events([ev])

        if ev:
            del_ref["b"] = ctk.CTkButton(
                acts, text="Excluir…" if ev.get("routineId") else "Excluir",
                command=do_delete, width=80, height=32,
                fg_color="transparent", hover_color="#F3E4E0",
                text_color=NOW_COLOR, border_width=1, border_color="#E4C9C1",
                corner_radius=9, font=self.f_ui)
            del_ref["b"].pack(side="left")
        ctk.CTkButton(acts, text="Salvar", command=do_save, width=110, height=32,
                      fg_color=ACCENT, hover_color=ACCENT_DARK, corner_radius=9,
                      font=self.f_ui).pack(side="right")
        ctk.CTkButton(acts, text="Cancelar", command=self.close_modal, width=90, height=32,
                      fg_color=SURFACE, hover_color=ACCENT_SOFT, text_color=INK,
                      border_width=1, border_color=LINE, corner_radius=9,
                      font=self.f_ui).pack(side="right", padx=8)

        # preencher
        e_title.insert(0, (ev or {}).get("title") or "")
        if (ev or {}).get("date"):
            e_date.set(parse(ev["date"]))
        elif date_str:
            e_date.set(parse(date_str))
        # sem nada disso, o DateField já vem com o dia de hoje
        if (ev or {}).get("endDate"):
            e_edate.set(parse(ev["endDate"]))
        if (ev or {}).get("start") or start_str:
            e_start.insert(0, (ev or {}).get("start") or start_str)
        if (ev or {}).get("end"):
            e_end.insert(0, ev["end"])
        rem = int((ev or {}).get("remind") or 0)
        remind.set({0: "na hora", 5: "5 min antes", 10: "10 min antes",
                    15: "15 min antes", 30: "30 min antes"}.get(rem, "na hora"))
        repeat.set({None: "não repete", "weekly": "toda semana",
                    "monthly": "todo mês", "yearly": "todo ano"}.get(
                        (ev or {}).get("repeat"), "não repete"))
        l = list_by_id((ev or {}).get("listId")) if ev else None
        lst_menu.set(l["name"] if l else "nenhuma")
        urg.set((ev or {}).get("urgency") or "normal")
        if (ev or {}).get("notes"):
            e_notes.insert("1.0", ev["notes"])
        toggle()
        e_title.focus_set()

    # ---------------- rotina (criar / editar) ----------------
    def open_routine(self, rt=None):
        card = self.open_modal(width=660)
        pad = {"padx": 22}
        ctk.CTkLabel(card, text="Editar rotina" if rt else "Nova rotina",
                     text_color=INK, font=self.f_title).pack(anchor="w", pady=(18, 10), **pad)

        r1 = ctk.CTkFrame(card, fg_color="transparent")
        r1.pack(anchor="w", **pad)
        c1 = ctk.CTkFrame(r1, fg_color="transparent"); c1.pack(side="left", padx=(0, 12))
        self._label(c1, "Nome da rotina").pack(anchor="w")
        e_name = self._entry(c1, w=250, ph="Semana de aulas"); e_name.pack()
        c2 = ctk.CTkFrame(r1, fg_color="transparent"); c2.pack(side="left", padx=(0, 12))
        self._label(c2, "Começa em").pack(anchor="w")
        e_start = DateField(c2, self); e_start.pack()
        c3 = ctk.CTkFrame(r1, fg_color="transparent"); c3.pack(side="left")
        self._label(c3, "Semanas").pack(anchor="w")
        e_weeks = self._entry(c3, w=70); e_weeks.pack()

        if rt:
            e_name.insert(0, rt.get("name") or "")
            try:
                e_start.set(parse(rt.get("start")))
            except Exception:
                pass
            e_weeks.insert(0, str(rt.get("weeks") or 4))
        else:
            e_start.set(start_of_week(date.today() + timedelta(days=7)))
            e_weeks.insert(0, "4")

        ctk.CTkLabel(card, text=("Ao salvar, os eventos da rotina são recriados do zero com os blocos abaixo."
                                 if rt else
                                 "Cada bloco vira um evento nos dias marcados, em todas as semanas."),
                     text_color=INK_SOFT, font=self.f_lab).pack(anchor="w", pady=(8, 6), **pad)

        sf = ctk.CTkScrollableFrame(card, width=596, height=230, fg_color="#F3F2EC",
                                    corner_radius=10)
        sf.pack(**pad)
        blocks = []

        def add_block(item=None):
            box = ctk.CTkFrame(sf, fg_color=SURFACE, corner_radius=10,
                               border_width=1, border_color=LINE)
            box.pack(fill="x", pady=4, padx=4)
            top = ctk.CTkFrame(box, fg_color="transparent")
            top.pack(fill="x", padx=10, pady=(8, 4))
            e_t = self._entry(top, w=460, ph="Ex.: Aula de Micro, Terapia, Estudo…")
            e_t.pack(side="left")
            def rm():
                blocks[:] = [b for b in blocks if b["box"] is not box]
                box.destroy()
            ctk.CTkButton(top, text="✕", command=rm, width=28, height=28,
                          fg_color="transparent", hover_color="#F3E4E0",
                          text_color=INK_SOFT, corner_radius=8).pack(side="right")

            bot = ctk.CTkFrame(box, fg_color="transparent")
            bot.pack(fill="x", padx=10, pady=(0, 8))
            dvars = []
            for w in WD:
                st = {"on": False}
                bt = ctk.CTkButton(bot, text=w, width=36, height=26, corner_radius=8,
                                   fg_color="#EFEEE8", text_color=INK_SOFT,
                                   hover_color=ACCENT_SOFT, font=self.f_lab)
                def paint(st=st, bt=bt):
                    bt.configure(fg_color=ACCENT if st["on"] else "#EFEEE8",
                                 text_color="#FFFFFF" if st["on"] else INK_SOFT,
                                 hover_color=ACCENT_DARK if st["on"] else ACCENT_SOFT)
                def flip(st=st, paint=paint):
                    st["on"] = not st["on"]; paint()
                bt.configure(command=flip)
                bt.pack(side="left", padx=1)
                st["paint"] = paint
                dvars.append(st)
            e_s = self._entry(bot, w=62, ph="início"); e_s.pack(side="left", padx=(8, 3))
            e_e = self._entry(bot, w=62, ph="fim"); e_e.pack(side="left", padx=(0, 6))
            cor = ctk.CTkOptionMenu(bot, width=92, height=28, corner_radius=8,
                                    values=[k for k, _ in PALETTE],
                                    fg_color=FIELD, button_color=ACCENT,
                                    button_hover_color=ACCENT_DARK, text_color=INK,
                                    font=self.f_lab, dropdown_font=self.f_lab)
            cor.pack(side="left")
            if item:
                e_t.insert(0, item.get("title") or "")
                for i in item.get("days") or []:
                    if 0 <= i < 7:
                        dvars[i]["on"] = True; dvars[i]["paint"]()
                if item.get("start"): e_s.insert(0, item["start"])
                if item.get("end"): e_e.insert(0, item["end"])
                if item.get("color"): cor.set(item["color"])
            blocks.append({"box": box, "title": e_t, "days": dvars,
                           "start": e_s, "end": e_e, "color": cor})

        if rt:
            for it in routine_items(rt):
                add_block(it)
            if not blocks:
                add_block()
        else:
            add_block()

        acts = ctk.CTkFrame(card, fg_color="transparent")
        acts.pack(fill="x", pady=(10, 18), **pad)
        ctk.CTkButton(acts, text="+ adicionar bloco", command=add_block, height=30,
                      fg_color=SURFACE, hover_color=ACCENT_SOFT, text_color=INK,
                      border_width=1, border_color=LINE, corner_radius=9,
                      font=self.f_ui).pack(side="left")

        def do_save():
            global EVENTS
            try:
                start = e_start.get()
            except Exception:
                messagebox.showwarning("Maré", "Data de início inválida. Confira dia, mês e ano.",
                                       parent=self)
                return
            try:
                weeks = max(1, int(e_weeks.get()))
            except ValueError:
                weeks = 4
            items = []
            for b in blocks:
                title = self._val(b["title"])
                days = [i for i, st in enumerate(b["days"]) if st["on"]]
                s = self._val(b["start"])
                e = self._val(b["end"]) or None
                if not title or not days or not s:
                    continue
                try:
                    minutes(s)
                    if e:
                        minutes(e)
                except Exception:
                    messagebox.showwarning("Maré", "Horário inválido em \"%s\". Use HH:MM." % title,
                                           parent=self)
                    return
                items.append({"title": title, "days": days, "start": s, "end": e,
                              "color": b["color"].get()})
            if not items:
                messagebox.showwarning(
                    "Maré", "Preencha ao menos um bloco com título, dias e horário de início.",
                    parent=self)
                return
            rid = rt["id"] if rt else new_id("r")
            base = start_of_week(start)
            cand = []
            for w in range(weeks):
                for it in items:
                    for dw in it["days"]:
                        d = base + timedelta(days=w * 7 + dw)
                        if d < start:
                            continue
                        cand.append((fmt(d), it))
            if rt:
                EVENTS = [e for e in EVENTS if e.get("routineId") != rid]
            cnt = 0
            for dstr, it in cand:
                EVENTS.append({
                    "id": new_id() + str(cnt), "title": it["title"],
                    "date": dstr, "allDay": False, "endDate": None,
                    "start": it["start"], "end": it["end"],
                    "remind": 0, "repeat": None, "color": it["color"],
                    "listId": None, "urgency": None,
                    "notes": None, "routineId": rid,
                })
                cnt += 1
            rec = {"id": rid, "name": self._val(e_name) or "Rotina",
                   "start": fmt(start), "weeks": weeks,
                   "items": [dict(it) for it in items]}
            if rt:
                for i, r in enumerate(ROUTINES):
                    if r["id"] == rid:
                        ROUTINES[i] = rec
                        break
            else:
                ROUTINES.append(rec)
            save_data()
            self.render()
            self.toast(("Rotina atualizada (%d eventos)" if rt
                        else "Rotina criada (%d eventos)") % len(cand), undo=False)

        ctk.CTkButton(acts, text="Salvar alterações" if rt else "Criar eventos",
                      command=do_save, width=140, height=30,
                      fg_color=ACCENT, hover_color=ACCENT_DARK, corner_radius=9,
                      font=self.f_ui).pack(side="right")
        ctk.CTkButton(acts, text="Cancelar", command=self.close_modal, width=90, height=30,
                      fg_color=SURFACE, hover_color=ACCENT_SOFT, text_color=INK,
                      border_width=1, border_color=LINE, corner_radius=9,
                      font=self.f_ui).pack(side="right", padx=8)

    # ---------------- painel da agenda (botão ☰) ----------------
    def open_browser(self, tab=None):
        card = self.open_modal(width=660)
        pad = {"padx": 20}
        ctk.CTkLabel(card, text="Minha agenda", text_color=INK,
                     font=self.f_title).pack(anchor="w", pady=(16, 2), **pad)
        tabs = ctk.CTkTabview(card, width=616, height=490,
                              fg_color="transparent",
                              segmented_button_fg_color="#ECEAE2",
                              segmented_button_selected_color="#CFE2D6",
                              segmented_button_selected_hover_color="#C2D9CB",
                              segmented_button_unselected_color="#ECEAE2",
                              segmented_button_unselected_hover_color=ACCENT_SOFT,
                              text_color=INK)
        tabs.pack(pady=(0, 14), **pad)
        t_ev = tabs.add("Eventos")
        t_rt = tabs.add("Rotinas")
        t_ls = tabs.add("Listas")
        t_tk = tabs.add("Tarefas")
        t_cf = tabs.add("Ajustes")
        if tab:
            tabs.set(tab)

        REP = {"weekly": "toda semana", "monthly": "todo mês", "yearly": "todo ano"}

        # ===== aba eventos =====
        topr = ctk.CTkFrame(t_ev, fg_color="transparent")
        topr.pack(fill="x", pady=(6, 6))
        srch = self._entry(topr, w=400, ph="Buscar por título…")
        srch.pack(side="left", padx=(4, 10))
        show_done = tk.BooleanVar(value=False)
        ctk.CTkCheckBox(topr, text="mostrar concluídos", variable=show_done,
                        command=lambda: refresh(), fg_color=ACCENT,
                        hover_color=ACCENT_DARK, border_color=LINE, text_color=INK,
                        checkbox_width=17, checkbox_height=17,
                        font=self.f_lab).pack(side="left")
        lst = ctk.CTkScrollableFrame(t_ev, width=576, height=372,
                                     fg_color="#F3F2EC", corner_radius=10)
        lst.pack()

        def ev_row(ev, d, gray=False):
            row = ctk.CTkFrame(lst, fg_color=SURFACE, corner_radius=8)
            row.pack(fill="x", pady=2, padx=4)
            ctk.CTkFrame(row, width=10, height=10, corner_radius=5,
                         fg_color=blend(color_of(ev.get("color")), 0.5 if gray else 0)
                         ).pack(side="left", padx=(10, 8))
            when = "%s %d %s" % (WD[d.weekday()], d.day, MONTHS[d.month - 1][:3])
            if not ev.get("allDay") and ev.get("start"):
                when += " · " + ev["start"] + ("–" + ev["end"] if ev.get("end") else "")
            else:
                when += " · dia inteiro"
            extra = []
            if ev.get("repeat"):
                extra.append(REP.get(ev["repeat"], ""))
            if ev.get("listId"):
                l = list_by_id(ev["listId"])
                extra.append("lista: " + (l["name"] if l else "?"))
            if ev.get("routineId"):
                r = next((x for x in ROUTINES if x["id"] == ev["routineId"]), None)
                extra.append("rotina: " + (r["name"] if r else "?"))
            if eff_urgency(ev):
                extra.append(eff_urgency(ev))
            txt = when + "  —  " + ev["title"] + \
                  (("   (" + ", ".join(extra) + ")") if extra else "")
            lb = ctk.CTkLabel(row, text=txt,
                              text_color=INK_SOFT if gray else INK,
                              font=self.f_lab, anchor="w")
            lb.pack(side="left", fill="x", expand=True, pady=6)
            lb.bind("<Button-1>", lambda e, ev=ev: self.open_event(ev))
            def kill(ev=ev):
                lab = ("\"%s\" excluído (todas as repetições)" % ev["title"]
                       if ev.get("repeat") else None)
                self.delete_events([ev], label=lab)
                self.open_browser()
            ctk.CTkButton(row, text="✕", command=kill, width=28, height=24,
                          fg_color="transparent", hover_color="#F3E4E0",
                          text_color=NOW_COLOR, corner_radius=8
                          ).pack(side="right", padx=6)

        def refresh(*_):
            for w in lst.winfo_children():
                w.destroy()
            q = self._val(srch).lower()
            hoje = date.today()
            seen = set()
            rows = 0
            for i in range(120):
                if rows >= 150:
                    break
                d = hoje + timedelta(days=i)
                for ev in events_on_day(d):
                    if ev["id"] in seen:
                        continue
                    seen.add(ev["id"])
                    if q and q not in ev["title"].lower():
                        continue
                    rows += 1
                    if rows > 150:
                        break
                    ev_row(ev, d)
            if show_done.get():
                ctk.CTkLabel(lst, text="Concluídos (últimos %d dias)" % PURGE_DAYS,
                             text_color=INK_SOFT, font=self.f_lab).pack(pady=(10, 2))
                past = [e for e in EVENTS
                        if not e.get("repeat") and not e.get("routineId")
                        and (e.get("endDate") or e["date"]) < fmt(hoje)]
                past.sort(key=lambda e: e["date"], reverse=True)
                for ev in past:
                    if q and q not in ev["title"].lower():
                        continue
                    ev_row(ev, parse(ev["date"]), gray=True)
            if rows == 0 and not show_done.get():
                ctk.CTkLabel(lst, text="Nada encontrado nos próximos 120 dias.",
                             text_color=INK_SOFT, font=self.f_lab).pack(pady=20)
        srch.bind("<KeyRelease>", refresh)
        refresh()

        # ===== aba rotinas =====
        rl = ctk.CTkScrollableFrame(t_rt, width=576, height=410,
                                    fg_color="#F3F2EC", corner_radius=10)
        rl.pack(pady=(8, 0))
        if not ROUTINES:
            ctk.CTkLabel(rl, text="Nenhuma rotina criada. Use o botão “+ Rotina”.",
                         text_color=INK_SOFT, font=self.f_lab).pack(pady=20)
        for rt in list(ROUTINES):
            n = sum(1 for e in EVENTS if e.get("routineId") == rt["id"])
            row = ctk.CTkFrame(rl, fg_color=SURFACE, corner_radius=8)
            row.pack(fill="x", pady=3, padx=4)
            ctk.CTkLabel(row, text="%s — a partir de %s, %s sem. (%d eventos)" %
                         (rt["name"], br(rt["start"]), rt["weeks"], n),
                         text_color=INK, font=self.f_lab,
                         anchor="w").pack(side="left", padx=10, pady=8)
            def kill(rt=rt, n=n):
                evs = [e for e in EVENTS if e.get("routineId") == rt["id"]]
                self.delete_events(evs, [rt],
                                   "Rotina \"%s\" excluída (%d eventos)" % (rt["name"], n))
                self.open_browser("Rotinas")
            ctk.CTkButton(row, text="excluir", command=kill, width=62, height=24,
                          fg_color="transparent", hover_color="#F3E4E0",
                          text_color=NOW_COLOR, corner_radius=8,
                          font=self.f_lab).pack(side="right", padx=(2, 8))
            ctk.CTkButton(row, text="editar", command=lambda rt=rt: self.open_routine(rt),
                          width=56, height=24, fg_color="transparent",
                          hover_color=ACCENT_SOFT, text_color=ACCENT, corner_radius=8,
                          font=self.f_lab).pack(side="right")

        # ===== aba listas =====
        addr = ctk.CTkFrame(t_ls, fg_color="transparent")
        addr.pack(fill="x", pady=(6, 6))
        e_lname = self._entry(addr, w=300, ph="Nova lista (ex.: Provas)")
        e_lname.pack(side="left", padx=(4, 8))
        def add_list():
            name = self._val(e_lname)
            if not name:
                return
            LISTS.append({"id": new_id("l"), "name": name, "urgency": None})
            save_data()
            self.open_browser("Listas")
        ctk.CTkButton(addr, text="criar", command=add_list, width=70, height=30,
                      fg_color=ACCENT, hover_color=ACCENT_DARK, corner_radius=9,
                      font=self.f_ui).pack(side="left")
        ll = ctk.CTkScrollableFrame(t_ls, width=576, height=356,
                                    fg_color="#F3F2EC", corner_radius=10)
        ll.pack()
        if not LISTS:
            ctk.CTkLabel(ll, text="Uma lista agrupa eventos avulsos (ex.: todas as provas)\n"
                                  "para ligar/desligar juntos na visão mensal e anual.",
                         text_color=INK_SOFT, font=self.f_lab).pack(pady=20)
        for l in list(LISTS):
            n = sum(1 for e in EVENTS if e.get("listId") == l["id"])
            row = ctk.CTkFrame(ll, fg_color=SURFACE, corner_radius=8)
            row.pack(fill="x", pady=3, padx=4)
            ctk.CTkLabel(row, text="%s (%d eventos)" % (l["name"], n),
                         text_color=INK, font=self.f_lab,
                         anchor="w").pack(side="left", padx=10, pady=8)
            def kill_list(l=l):
                for e in EVENTS:
                    if e.get("listId") == l["id"]:
                        e["listId"] = None
                LISTS.remove(l)
                FILTERS.pop("l:" + l["id"], None)
                save_data()
                self.open_browser("Listas")
                self.toast("Lista removida (os eventos continuam na agenda)", undo=False)
            ctk.CTkButton(row, text="excluir lista", command=kill_list, width=90,
                          height=24, fg_color="transparent", hover_color="#F3E4E0",
                          text_color=NOW_COLOR, corner_radius=8,
                          font=self.f_lab).pack(side="right", padx=(2, 8))
            u = ctk.CTkOptionMenu(row, width=110, height=24, corner_radius=8,
                                  values=["normal", "importante", "urgente"],
                                  fg_color=FIELD, button_color=ACCENT,
                                  button_hover_color=ACCENT_DARK, text_color=INK,
                                  font=self.f_lab, dropdown_font=self.f_lab)
            u.set(l.get("urgency") or "normal")
            def set_u(v, l=l):
                l["urgency"] = None if v == "normal" else v
                save_data()
                self.refresh_banners()
            u.configure(command=set_u)
            u.pack(side="right", padx=4)
            ctk.CTkLabel(row, text="urgência:", text_color=INK_SOFT,
                         font=self.f_lab).pack(side="right")

        # ===== aba tarefas =====
        addt = ctk.CTkFrame(t_tk, fg_color="transparent")
        addt.pack(fill="x", pady=(6, 6))
        e_task = self._entry(addt, w=260, ph="Nova tarefa (ex.: enviar trabalho)")
        e_task.pack(side="left", padx=(4, 8))
        e_tdate = DateField(addt, self, optional=True)
        e_tdate.pack(side="left", padx=(0, 8))
        def add_task():
            title = self._val(e_task)
            if not title:
                return
            try:
                dvd = e_tdate.get()
            except Exception:
                messagebox.showwarning("Maré", "Data da tarefa inválida. Confira dia, mês e ano.",
                                       parent=self)
                return
            dv = fmt(dvd) if dvd else None
            TASKS.append({"id": new_id("t"), "title": title, "date": dv,
                          "done": False, "doneDate": None})
            save_data()
            self.open_browser("Tarefas")
        ctk.CTkButton(addt, text="adicionar", command=add_task, width=90, height=30,
                      fg_color=ACCENT, hover_color=ACCENT_DARK, corner_radius=9,
                      font=self.f_ui).pack(side="left")
        tl = ctk.CTkScrollableFrame(t_tk, width=576, height=356,
                                    fg_color="#F3F2EC", corner_radius=10)
        tl.pack()
        if not TASKS:
            ctk.CTkLabel(tl, text="Tarefas são pendências sem horário.\n"
                                  "Com data, aparecem no topo do dia na semana; "
                                  "concluídas somem sozinhas após %d dias." % PURGE_DAYS,
                         text_color=INK_SOFT, font=self.f_lab).pack(pady=20)
        pend = [t for t in TASKS if not t.get("done")]
        done = [t for t in TASKS if t.get("done")]
        for t in pend + done:
            row = ctk.CTkFrame(tl, fg_color=SURFACE, corner_radius=8)
            row.pack(fill="x", pady=2, padx=4)
            var = tk.BooleanVar(value=bool(t.get("done")))
            def flip(t=t, var=None, v=None):
                pass
            def mk_flip(t, var):
                def _f():
                    t["done"] = var.get()
                    t["doneDate"] = fmt(date.today()) if t["done"] else None
                    save_data()
                    self.open_browser("Tarefas")
                return _f
            txt = t["title"] + ((" · " + br(t["date"])) if t.get("date") else "")
            ctk.CTkCheckBox(row, text=txt, variable=var, command=mk_flip(t, var),
                            fg_color=ACCENT, hover_color=ACCENT_DARK,
                            border_color=LINE,
                            text_color=INK_SOFT if t.get("done") else INK,
                            checkbox_width=17, checkbox_height=17,
                            font=self.f_lab).pack(side="left", padx=10, pady=7)
            def kill_task(t=t):
                TASKS.remove(t)
                save_data()
                self.open_browser("Tarefas")
            ctk.CTkButton(row, text="✕", command=kill_task, width=28, height=24,
                          fg_color="transparent", hover_color="#F3E4E0",
                          text_color=NOW_COLOR, corner_radius=8
                          ).pack(side="right", padx=6)

        # ===== aba ajustes =====
        box = ctk.CTkFrame(t_cf, fg_color="transparent")
        box.pack(fill="x", pady=(14, 0), padx=8)
        auto_var = tk.BooleanVar(value=autostart_enabled())
        def set_auto():
            try:
                set_autostart(auto_var.get())
                self.toast("Vai abrir junto com o computador" if auto_var.get()
                           else "Não abre mais sozinho", undo=False)
            except Exception:
                messagebox.showwarning("Maré", "Não consegui ativar a abertura automática.",
                                       parent=self)
        sw1 = ctk.CTkSwitch(box, text="Abrir o Maré quando ligar o computador",
                            variable=auto_var, command=set_auto,
                            progress_color=ACCENT, text_color=INK, font=self.f_ui)
        sw1.pack(anchor="w", pady=6)
        ins_var = tk.BooleanVar(value=bool(SETTINGS.get("insistent", True)))
        def set_ins():
            SETTINGS["insistent"] = ins_var.get()
            save_data()
        ctk.CTkSwitch(box, text="Alarme insistente (repete o aviso a cada 2 min até dispensar)",
                      variable=ins_var, command=set_ins,
                      progress_color=ACCENT, text_color=INK,
                      font=self.f_ui).pack(anchor="w", pady=6)
        ctk.CTkLabel(box, text="Eventos e tarefas concluídos há mais de %d dias são\n"
                               "apagados automaticamente ao abrir o app." % PURGE_DAYS,
                     text_color=INK_SOFT, font=self.f_lab,
                     justify="left").pack(anchor="w", pady=(14, 0))

    # ---------------- urgência (banners) ----------------
    def refresh_banners(self):
        for w in self._urg_widgets:
            try:
                w.destroy()
            except Exception:
                pass
        self._urg_widgets = []
        hoje = date.today()
        tkey = fmt(hoje)
        items = []
        for ev in EVENTS:
            u = eff_urgency(ev)
            if not u:
                continue
            if URGD.get(ev["id"]) == tkey:
                continue
            nd = next_occurrence(ev, hoje)
            if nd is None:
                continue
            items.append((nd, 0 if u == "urgente" else 1, u, ev))
        items.sort(key=lambda x: (x[0], x[1]))
        y = 66
        for nd, _, u, ev in items[:4]:
            col = NOW_COLOR if u == "urgente" else WARN_COLOR
            f = ctk.CTkFrame(self, fg_color=blend(col, 0.68), corner_radius=10,
                             border_width=1, border_color=blend(col, 0.35))
            f.place(relx=1.0, x=-18, y=y, anchor="ne")
            txt = "%s — %s" % (ev["title"], days_label(nd))
            ctk.CTkLabel(f, text=txt, text_color=shade(col, 0.25),
                         font=self.f_lab).pack(side="left", padx=(12, 6), pady=6)
            def dismiss(ev=ev, f=f):
                URGD[ev["id"]] = fmt(date.today())
                save_data()
                self.refresh_banners()
            ctk.CTkButton(f, text="✕", command=dismiss, width=22, height=20,
                          fg_color="transparent", hover_color=blend(col, 0.5),
                          text_color=shade(col, 0.25), corner_radius=6,
                          font=self.f_lab).pack(side="left", padx=(0, 8))
            self._urg_widgets.append(f)
            y += 40

    # ---------------- exclusão rápida / desfazer ----------------
    def delete_events(self, evs, routines=None, label=None):
        global EVENTS, ROUTINES
        ids = {e["id"] for e in evs}
        EVENTS = [e for e in EVENTS if e["id"] not in ids]
        rts = routines or []
        rids = {r["id"] for r in rts}
        ROUTINES = [r for r in ROUTINES if r["id"] not in rids]
        for i in ids:
            NOTIF.pop(i, None)
        save_data()
        self._undo = {"events": list(evs), "routines": list(rts)}
        self.render()
        if not label:
            label = "1 evento excluído" if len(evs) == 1 else "%d eventos excluídos" % len(evs)
        self.toast(label)

    def undo_delete(self):
        global EVENTS, ROUTINES
        u = getattr(self, "_undo", None)
        if not u:
            return
        EVENTS.extend(u["events"])
        ROUTINES.extend(u["routines"])
        self._undo = None
        save_data()
        self.render()
        self.toast("Restaurado", undo=False)

    def toast(self, text, undo=True):
        old = getattr(self, "_toast", None)
        if old is not None:
            try:
                old.destroy()
            except Exception:
                pass
        f = ctk.CTkFrame(self, fg_color=INK, corner_radius=12)
        f.place(relx=0.5, rely=1.0, y=-18, anchor="s")
        ctk.CTkLabel(f, text=text, text_color="#F6F5F1",
                     font=self.f_ui).pack(side="left", padx=(16, 12), pady=8)
        if undo:
            ctk.CTkButton(f, text="Desfazer", command=self.undo_delete,
                          width=84, height=26, fg_color="transparent",
                          hover_color="#3A3F33", text_color="#9FD1B4",
                          border_width=1, border_color="#4A4F41",
                          corner_radius=8, font=self.f_lab).pack(side="left", padx=(0, 12))
        self._toast = f
        def kill(f=f):
            if getattr(self, "_toast", None) is f:
                self._toast = None
                try:
                    f.destroy()
                except Exception:
                    pass
        self.after(7000, kill)

    def event_menu(self, ev, x, y):
        m = tk.Menu(self, tearoff=0, bg=SURFACE, fg=INK,
                    activebackground=ACCENT_SOFT, activeforeground=INK,
                    relief="flat", bd=1, font=("Segoe UI", 9))
        m.add_command(label="Editar", command=lambda: self.open_event(ev))
        m.add_separator()
        m.add_command(label="Excluir (todas as repetições)" if ev.get("repeat")
                      else "Excluir este evento",
                      command=lambda: self.delete_events([ev]))
        if ev.get("routineId"):
            rid = ev["routineId"]
            all_evs = [e for e in EVENTS if e.get("routineId") == rid]
            fwd = [e for e in all_evs if e["date"] >= ev["date"]]
            rt = next((r for r in ROUTINES if r["id"] == rid), None)
            name = rt["name"] if rt else "rotina"
            m.add_separator()
            m.add_command(
                label="Excluir daqui em diante (%d eventos)" % len(fwd),
                command=lambda: self.delete_events(
                    fwd, label="%d eventos da rotina excluídos" % len(fwd)))
            m.add_command(
                label="Excluir a rotina \"%s\" inteira (%d eventos)" % (name, len(all_evs)),
                command=lambda: self.delete_events(
                    all_evs, [rt] if rt else [],
                    "Rotina \"%s\" excluída (%d eventos)" % (name, len(all_evs))))
        try:
            m.tk_popup(x, y)
        finally:
            m.grab_release()

    # ---------------- alarmes ----------------
    def tick(self):
        self.after(20000, self.tick)
        now = datetime.now()
        today = fmt(now.date())
        if getattr(self, "_last_day", None) != today:
            self._last_day = today
            self.refresh_banners()
        for k in list(NOTIF.keys()):
            if NOTIF[k].get("date") != today:
                del NOTIF[k]
        changed = False
        for ev in timed_events(now.date()):
            log = NOTIF.get(ev["id"])
            if log and log.get("state") in ("done", "shown"):
                continue
            if log and log.get("state") == "pending":
                fire = datetime.fromisoformat(log["at"])
            else:
                base = datetime.combine(now.date(), datetime.min.time())
                fire = base + timedelta(minutes=minutes(ev["start"]) - int(ev.get("remind") or 0))
            if fire <= now < fire + timedelta(minutes=30):
                NOTIF[ev["id"]] = {"state": "shown", "date": today}
                changed = True
                self.show_alarm(ev)
        if changed:
            save_data()
        if now.minute % 5 == 0 and now.second < 20 and self.view in ("week", "day"):
            try:
                self.draw_all()
            except Exception:
                pass

    def show_alarm(self, ev):
        if ev["id"] in self.alarms:
            return
        top = ctk.CTkToplevel(self, fg_color=INK)
        top.overrideredirect(True)
        top.attributes("-topmost", True)
        w, h = 340, 138
        sw, sh = top.winfo_screenwidth(), top.winfo_screenheight()
        n = len(self.alarms)
        top.geometry("%dx%d+%d+%d" % (w, h, sw - w - 18, sh - h - 64 - n * (h + 10)))

        ctk.CTkLabel(top, text="Hora de: " + ev["title"], text_color="#F6F5F1",
                     font=self.f_h, anchor="w").pack(fill="x", padx=18, pady=(16, 0))
        ctk.CTkLabel(top, text=(ev.get("start") or "") +
                     ("–" + ev["end"] if ev.get("end") else ""),
                     text_color="#C9CDBF", font=self.f_lab,
                     anchor="w").pack(fill="x", padx=18)
        acts = ctk.CTkFrame(top, fg_color="transparent")
        acts.pack(fill="x", padx=16, pady=14)

        def resolve(action):
            today = fmt(date.today())
            if action == "snooze":
                NOTIF[ev["id"]] = {"state": "pending", "date": today,
                                   "at": (datetime.now() + timedelta(minutes=5)).isoformat()}
            else:
                NOTIF[ev["id"]] = {"state": "done", "date": today}
            save_data()
            self.alarms.pop(ev["id"], None)
            top.destroy()

        ctk.CTkButton(acts, text="+5 min", command=lambda: resolve("snooze"),
                      fg_color="transparent", hover_color="#3A3F33",
                      text_color="#F6F5F1", border_width=1, border_color="#4A4F41",
                      corner_radius=9, height=34).pack(side="left", expand=True,
                                                       fill="x", padx=(0, 8))
        ctk.CTkButton(acts, text="Dispensar", command=lambda: resolve("done"),
                      fg_color=ACCENT, hover_color=ACCENT_DARK, corner_radius=9,
                      height=34).pack(side="left", expand=True, fill="x")
        self.alarms[ev["id"]] = top
        top.lift()
        self._ring()

        def nag():
            if ev["id"] in self.alarms and SETTINGS.get("insistent", True):
                try:
                    top.lift()
                    top.attributes("-topmost", True)
                    self._ring()
                    top.after(120000, nag)
                except Exception:
                    pass
        top.after(120000, nag)

    def _ring(self):
        self.bell()
        if winsound:
            try:
                winsound.MessageBeep(winsound.MB_ICONASTERISK)
            except Exception:
                pass


# ----------------------------------------------------------------
if __name__ == "__main__":
    app = App()
    app.mainloop()
