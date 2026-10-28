import datetime
import hashlib
import sys
import tkinter as tk
from tkinter import filedialog, messagebox

import customtkinter as ctk

from banco import (
    conectar, calcular_saldos, sugerir_pagamentos,
    adicionar_pessoa, listar_pessoas, adicionar_gasto, adicionar_repasse,
    listar_gastos, remover_gasto, listar_repasses, remover_repasse,
    limpar_tudo, atualizar_avatar,
    estatisticas, repasses_por_pessoa, exportar_csv,
)

# ============================ PALETAS ============================ #
PALETA_DARK = {
    "bg": "#08090a", "panel": "#0f1011", "card": "#1a1b1e",
    "border": "#2a2c30", "text": "#f7f8f8", "dim": "#8a8f98",
    "accent": "#6e79e8", "accent_h": "#5b66d9",
    "accent_bg": "#252850", "accent_text": "#a5b0ff",
    "ok": "#4ade80", "ok_bg": "#14351f",
    "neg": "#f87171", "neg_bg": "#3a1616",
    "pill_neutral_bg": "#202124", "pill_neutral_text": "#8a8f98",
    "input_bg": "#16171a", "on_accent": "#ffffff",
}

PALETA_LIGHT = {
    "bg": "#ffffff", "panel": "#f8f9fa", "card": "#ffffff",
    "border": "#e5e7eb", "text": "#111827", "dim": "#6b7280",
    "accent": "#5e6ad2", "accent_h": "#4f5bb8",
    "accent_bg": "#e0e7ff", "accent_text": "#4338ca",
    "ok": "#059669", "ok_bg": "#dcfce7",
    "neg": "#dc2626", "neg_bg": "#fee2e2",
    "pill_neutral_bg": "#f3f4f6", "pill_neutral_text": "#6b7280",
    "input_bg": "#ffffff", "on_accent": "#ffffff",
}

C = dict(PALETA_DARK)


def aplicar_modo(modo):
    global C
    ctk.set_appearance_mode(modo)
    C = dict(PALETA_DARK if modo == "Dark" else PALETA_LIGHT)


aplicar_modo("Dark")


# ============================ AVATARES ============================ #
AVATARES = [
    "🧑", "👨", "👩", "🧔", "👱", "🧓",
    "👦", "👧", "👴", "👵", "👶", "🤴",
    "👸", "🧙", "🧚", "🦸", "🦹", "🥷",
    "💃", "🕺", "👮", "👷", "💂", "🤵",
]

CORES_AVATAR = ["#e5534b", "#3fb950", "#2d7dd2", "#d29922",
                "#a371f7", "#db6cb9", "#39c5cf", "#f78166"]


def fonte_emoji(size):
    if sys.platform == "darwin":
        return ctk.CTkFont("Apple Color Emoji", size)
    if sys.platform.startswith("win"):
        return ctk.CTkFont("Segoe UI Emoji", size)
    return ctk.CTkFont("Noto Color Emoji", size)


def avatar_de(nome, avatar_salvo=None):
    h = int(hashlib.md5(nome.encode("utf-8")).hexdigest(), 16)
    emoji = avatar_salvo or AVATARES[h % len(AVATARES)]
    cor = CORES_AVATAR[(h >> 8) % len(CORES_AVATAR)]
    return emoji, cor


def reais(centavos):
    sinal = "-" if centavos < 0 else ""
    v = f"{abs(centavos) / 100:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{sinal}R$ {v}"


def criar_avatar(parent, nome, size=36, avatar_salvo=None, on_click=None):
    emoji, cor = avatar_de(nome, avatar_salvo)
    fr = ctk.CTkFrame(parent, width=size, height=size,
                      fg_color=cor, corner_radius=size // 2)
    fr.pack_propagate(False)
    lbl = ctk.CTkLabel(fr, text=emoji, font=fonte_emoji(int(size * 0.55)),
                       text_color="white")
    lbl.pack(expand=True)
    if on_click:
        fr.bind("<Button-1>", lambda _e: on_click())
        lbl.bind("<Button-1>", lambda _e: on_click())
        fr.configure(cursor="hand2")
        lbl.configure(cursor="hand2")
    return fr


# ================================================================== #
# Diálogo: escolher avatar                                           #
# ================================================================== #
class EscolherAvatarJanela(ctk.CTkToplevel):
    def __init__(self, master, nome_atual, ao_escolher):
        super().__init__(master)
        self.title(f"Avatar de {nome_atual}")
        self.geometry("400x340")
        self.configure(fg_color=C["bg"])
        self.transient(master)
        self.after(150, self.lift)
        self.after(150, self.grab_set)

        self.ao_escolher = ao_escolher

        ctk.CTkLabel(self, text=f"Escolha uma carinha para {nome_atual}",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=C["text"]).pack(pady=(18, 14))

        grid = ctk.CTkFrame(self, fg_color="transparent")
        grid.pack(padx=16)

        for i, emoji in enumerate(AVATARES):
            ctk.CTkButton(
                grid, text=emoji, font=fonte_emoji(26),
                width=48, height=48,
                fg_color=C["card"], hover_color=C["accent_bg"],
                text_color=C["text"], corner_radius=10,
                command=lambda e=emoji: self._escolher(e)
            ).grid(row=i // 6, column=i % 6, padx=3, pady=3)

    def _escolher(self, emoji):
        self.ao_escolher(emoji)
        self.destroy()


# ================================================================== #
# Diálogo: novo gasto                                                #
# ================================================================== #
class NovoGastoJanela(ctk.CTkToplevel):
    def __init__(self, master, pessoas, ao_salvar):
        super().__init__(master)
        self.title("Novo gasto")
        self.geometry("420x720")
        self.configure(fg_color=C["bg"])
        self.transient(master)
        self.after(150, self.lift)
        self.after(150, self.grab_set)

        self.ao_salvar = ao_salvar
        self.ids, self.avatares = {}, {}
        for pid, nome, avatar in pessoas:
            self.ids[nome] = pid
            self.avatares[nome] = avatar

        ctk.CTkLabel(self, text="Novo gasto",
                     font=ctk.CTkFont(size=17, weight="bold"),
                     text_color=C["text"]).pack(anchor="w", padx=18, pady=(18, 8))

        self._campo("Descrição");        self.entry_desc = self._entry()
        self._campo("Valor total (R$)"); self.entry_valor = self._entry()
        self._campo("Data (AAAA-MM-DD)")
        self.entry_data = self._entry()
        self.entry_data.insert(0, datetime.date.today().isoformat())

        self._campo("Participantes  ·  quem pagou o quê")
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent", height=190)
        self.scroll.pack(fill="x", padx=14, pady=4)

        self.vars, self.entries_pago = {}, {}
        for nome in self.ids:
            linha = ctk.CTkFrame(self.scroll, fg_color=C["card"], corner_radius=10)
            linha.pack(fill="x", pady=2)
            criar_avatar(linha, nome, 26, self.avatares[nome]).pack(
                side="left", padx=(8, 8), pady=6)
            var = ctk.BooleanVar(value=True)
            ctk.CTkCheckBox(linha, text=nome, variable=var,
                            onvalue=True, offvalue=False,
                            fg_color=C["accent"], hover_color=C["accent_h"],
                            text_color=C["text"]).pack(side="left")
            entry = ctk.CTkEntry(linha, width=90, placeholder_text="0,00",
                                 fg_color=C["input_bg"], border_color=C["border"],
                                 text_color=C["text"], corner_radius=8)
            entry.pack(side="right", padx=8, pady=6)
            self.vars[nome] = var
            self.entries_pago[nome] = entry

        self.lbl_erro = ctk.CTkLabel(self, text="", text_color=C["neg"],
                                     font=ctk.CTkFont(size=11), wraplength=380,
                                     justify="left")
        self.lbl_erro.pack(anchor="w", padx=18, pady=(8, 0))

        ctk.CTkButton(self, text="Salvar gasto", command=self._salvar,
                      fg_color=C["accent"], hover_color=C["accent_h"],
                      text_color=C["on_accent"],
                      font=ctk.CTkFont(size=13, weight="bold"),
                      corner_radius=10, height=42
                      ).pack(fill="x", padx=18, pady=12)

    def _campo(self, texto):
        ctk.CTkLabel(self, text=texto.upper(),
                     font=ctk.CTkFont(size=10, weight="bold"),
                     text_color=C["dim"]).pack(anchor="w", padx=18, pady=(12, 2))

    def _entry(self):
        e = ctk.CTkEntry(self, fg_color=C["input_bg"], border_color=C["border"],
                         text_color=C["text"], corner_radius=8, height=36)
        e.pack(fill="x", padx=18)
        return e

    def _salvar(self):
        descricao = self.entry_desc.get().strip()
        texto_valor = self.entry_valor.get().strip().replace(",", ".")
        data = self.entry_data.get().strip()
        participantes = [self.ids[n] for n, v in self.vars.items() if v.get()]

        try:
            valor_total = round(float(texto_valor) * 100)
        except ValueError:
            self.lbl_erro.configure(text="Valor inválido."); return
        try:
            datetime.date.fromisoformat(data)
        except ValueError:
            self.lbl_erro.configure(text="Data inválida (use AAAA-MM-DD)."); return
        if not descricao:
            self.lbl_erro.configure(text="Digite uma descrição."); return
        if valor_total <= 0:
            self.lbl_erro.configure(text="O valor deve ser maior que zero."); return
        if not participantes:
            self.lbl_erro.configure(text="Marque ao menos um participante."); return

        pagadores = []
        try:
            for nome, entry in self.entries_pago.items():
                texto = entry.get().strip().replace(",", ".")
                if texto:
                    v = round(float(texto) * 100)
                    if v > 0:
                        pagadores.append((self.ids[nome], v))
        except ValueError:
            self.lbl_erro.configure(text="Valor pago inválido."); return

        soma_paga = sum(v for _, v in pagadores)
        if soma_paga != valor_total:
            self.lbl_erro.configure(
                text=f"O que foi pago ({reais(soma_paga)}) precisa "
                     f"somar o total ({reais(valor_total)}).")
            return

        conn = conectar()
        adicionar_gasto(conn, descricao, valor_total, data, pagadores, participantes)
        conn.close()
        self.ao_salvar(); self.destroy()


# ================================================================== #
# Diálogo: registrar pagamento                                       #
# ================================================================== #
class RepasseJanela(ctk.CTkToplevel):
    def __init__(self, master, pessoas, ao_salvar):
        super().__init__(master)
        self.title("Registrar pagamento")
        self.geometry("380x480")
        self.configure(fg_color=C["bg"])
        self.transient(master)
        self.after(150, self.lift)
        self.after(150, self.grab_set)

        self.ao_salvar = ao_salvar
        self.ids = {nome: pid for pid, nome, _ in pessoas}

        ctk.CTkLabel(self, text="Registrar pagamento",
                     font=ctk.CTkFont(size=17, weight="bold"),
                     text_color=C["text"]).pack(anchor="w", padx=18, pady=(18, 8))

        self._campo("Quem pagou");   self.menu_de = self._menu()
        self._campo("Quem recebeu"); self.menu_para = self._menu()
        nomes = list(self.ids)
        if len(nomes) > 1:
            self.menu_para.set(nomes[1])

        self._campo("Valor (R$)");       self.entry_valor = self._entry()
        self._campo("Data (AAAA-MM-DD)")
        self.entry_data = self._entry()
        self.entry_data.insert(0, datetime.date.today().isoformat())

        self.lbl_erro = ctk.CTkLabel(self, text="", text_color=C["neg"],
                                     font=ctk.CTkFont(size=11), wraplength=340,
                                     justify="left")
        self.lbl_erro.pack(anchor="w", padx=18, pady=(10, 0))

        ctk.CTkButton(self, text="Registrar pagamento", command=self._salvar,
                      fg_color=C["accent"], hover_color=C["accent_h"],
                      text_color=C["on_accent"],
                      font=ctk.CTkFont(size=13, weight="bold"),
                      corner_radius=10, height=42
                      ).pack(fill="x", padx=18, pady=12)

    def _campo(self, texto):
        ctk.CTkLabel(self, text=texto.upper(),
                     font=ctk.CTkFont(size=10, weight="bold"),
                     text_color=C["dim"]).pack(anchor="w", padx=18, pady=(12, 2))

    def _entry(self):
        e = ctk.CTkEntry(self, fg_color=C["input_bg"], border_color=C["border"],
                         text_color=C["text"], corner_radius=8, height=36)
        e.pack(fill="x", padx=18)
        return e

    def _menu(self):
        m = ctk.CTkOptionMenu(
            self, values=list(self.ids), fg_color=C["input_bg"],
            button_color=C["accent"], button_hover_color=C["accent_h"],
            text_color=C["text"], corner_radius=8, height=36)
        m.pack(fill="x", padx=18)
        return m

    def _salvar(self):
        de, para = self.menu_de.get(), self.menu_para.get()
        texto_valor = self.entry_valor.get().strip().replace(",", ".")
        data = self.entry_data.get().strip()

        if de == para:
            self.lbl_erro.configure(text="Quem pagou e quem recebeu devem ser diferentes."); return
        try:
            valor = round(float(texto_valor) * 100)
        except ValueError:
            self.lbl_erro.configure(text="Valor inválido."); return
        try:
            datetime.date.fromisoformat(data)
        except ValueError:
            self.lbl_erro.configure(text="Data inválida (use AAAA-MM-DD)."); return
        if valor <= 0:
            self.lbl_erro.configure(text="O valor deve ser maior que zero."); return

        conn = conectar()
        adicionar_repasse(conn, self.ids[de], self.ids[para], valor, data)
        conn.close()
        self.ao_salvar(); self.destroy()


# ================================================================== #
# Janela principal                                                   #
# ================================================================== #
class DivisaoApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Divisão de Gastos")
        self.geometry("1100x720")
        self.minsize(900, 560)
        self.configure(fg_color=C["bg"])
        self._build_ui()

    # ---------------------- construção ---------------------- #
    def _build_ui(self):
        self.configure(fg_color=C["bg"])

        # header
        hdr = ctk.CTkFrame(self, fg_color=C["panel"], corner_radius=0, height=60)
        hdr.pack(fill="x"); hdr.pack_propagate(False)
        ctk.CTkLabel(hdr, text="Divisão de Gastos",
                     font=ctk.CTkFont(size=17, weight="bold"),
                     text_color=C["text"]).pack(side="left", padx=(20, 10))
        ctk.CTkLabel(hdr, text="divida sem dor de cabeça",
                     font=ctk.CTkFont(size=11),
                     text_color=C["dim"]).pack(side="left")

        atual = ctk.get_appearance_mode()
        ctk.CTkButton(hdr, text="☀️  Claro" if atual == "Dark" else "🌙  Escuro",
                      command=self._alternar_tema,
                      fg_color="transparent", hover_color=C["card"],
                      border_width=1, border_color=C["border"],
                      text_color=C["text"], corner_radius=10, height=34, width=110
                      ).pack(side="right", padx=20)

        # corpo
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=12, pady=12)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)

        # sidebar
        left = ctk.CTkFrame(body, fg_color=C["panel"], width=230, corner_radius=14)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        left.pack_propagate(False)

        ctk.CTkButton(left, text="Novo gasto", command=self._abrir_novo_gasto,
                      fg_color=C["accent"], hover_color=C["accent_h"],
                      text_color=C["on_accent"],
                      font=ctk.CTkFont(size=13, weight="bold"),
                      corner_radius=10, height=44
                      ).pack(fill="x", padx=14, pady=(14, 6))

        ctk.CTkButton(left, text="Registrar pagamento",
                      command=self._abrir_repasse,
                      fg_color="transparent", hover_color=C["card"],
                      border_width=1, border_color=C["border"],
                      text_color=C["text"], corner_radius=10, height=40
                      ).pack(fill="x", padx=14, pady=(0, 14))

        ctk.CTkLabel(left, text="COMPARTILHAR",
                     font=ctk.CTkFont(size=10, weight="bold"),
                     text_color=C["dim"]).pack(anchor="w", padx=16, pady=(0, 4))

        ctk.CTkButton(left, text="📋  Copiar p/ WhatsApp",
                      command=self._copiar_whatsapp,
                      fg_color="transparent", hover_color=C["accent_bg"],
                      border_width=1, border_color=C["border"],
                      text_color=C["accent_text"], corner_radius=10, height=36
                      ).pack(fill="x", padx=14, pady=(0, 6))

        ctk.CTkButton(left, text="📥  Exportar CSV",
                      command=self._exportar_csv,
                      fg_color="transparent", hover_color=C["card"],
                      border_width=1, border_color=C["border"],
                      text_color=C["text"], corner_radius=10, height=36
                      ).pack(fill="x", padx=14, pady=(0, 14))

        # mensagem
        self.lbl_msg = ctk.CTkLabel(left, text="", font=ctk.CTkFont(size=11),
                                    text_color=C["dim"], wraplength=200,
                                    justify="left")
        self.lbl_msg.pack(anchor="w", padx=16, pady=(0, 8))

        # zona de perigo (bottom)
        ctk.CTkButton(left, text="Limpar todos os dados",
                      command=self._limpar_tudo,
                      fg_color="transparent", hover_color=C["neg_bg"],
                      text_color=C["neg"], corner_radius=10, height=34
                      ).pack(fill="x", padx=14, pady=(0, 14), side="bottom")

        # ----- TABS ----- #
        self.tabview = ctk.CTkTabview(
            body,
            fg_color=C["panel"],
            segmented_button_fg_color=C["card"],
            segmented_button_selected_color=C["accent"],
            segmented_button_selected_hover_color=C["accent_h"],
            segmented_button_unselected_color=C["card"],
            segmented_button_unselected_hover_color=C["border"],
            text_color=C["text"],
            corner_radius=14,
        )
        self.tabview.grid(row=0, column=1, sticky="nsew")

        tab_resumo  = self.tabview.add("Resumo")
        tab_hist    = self.tabview.add("Histórico")
        tab_pessoas = self.tabview.add("Pessoas")

        # Resumo: stats + saldos + caloteirômetro + quem paga quem
        self.scroll_resumo = ctk.CTkScrollableFrame(
            tab_resumo, fg_color="transparent",
            scrollbar_button_color=C["border"],
            scrollbar_button_hover_color=C["accent"])
        self.scroll_resumo.pack(fill="both", expand=True, padx=2, pady=2)

        self.stats_frame = ctk.CTkFrame(self.scroll_resumo, fg_color="transparent")
        self.stats_frame.pack(fill="x", padx=6, pady=(4, 10))
        for i in range(4):
            self.stats_frame.columnconfigure(i, weight=1)

        # Histórico
        self.scroll_hist = ctk.CTkScrollableFrame(
            tab_hist, fg_color="transparent",
            scrollbar_button_color=C["border"],
            scrollbar_button_hover_color=C["accent"])
        self.scroll_hist.pack(fill="both", expand=True, padx=2, pady=2)

        # Pessoas: cadastro fixo no topo + lista scrollável abaixo
        cadastro = ctk.CTkFrame(tab_pessoas, fg_color="transparent")
        cadastro.pack(fill="x", padx=10, pady=(10, 6))

        self.entry_nome = ctk.CTkEntry(
            cadastro, placeholder_text="Nome da nova pessoa",
            fg_color=C["input_bg"], border_color=C["border"],
            text_color=C["text"], corner_radius=8, height=38)
        self.entry_nome.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.entry_nome.bind("<Return>", lambda _e: self._cadastrar_pessoa())

        ctk.CTkButton(cadastro, text="＋ Adicionar",
                      command=self._cadastrar_pessoa,
                      fg_color=C["card"], hover_color=C["border"],
                      text_color=C["text"], corner_radius=10, height=38,
                      width=110).pack(side="right")

        self.scroll_pessoas = ctk.CTkScrollableFrame(
            tab_pessoas, fg_color="transparent",
            scrollbar_button_color=C["border"],
            scrollbar_button_hover_color=C["accent"])
        self.scroll_pessoas.pack(fill="both", expand=True, padx=2, pady=2)

        self.atualizar()

    # ---------------------- tema ---------------------- #
    def _alternar_tema(self):
        atual = ctk.get_appearance_mode()
        aplicar_modo("Light" if atual == "Dark" else "Dark")
        for w in self.winfo_children():
            w.destroy()
        self._build_ui()

    # ---------------------- ações ---------------------- #
    def _cadastrar_pessoa(self):
        nome = self.entry_nome.get().strip()
        if not nome:
            self.lbl_msg.configure(text="Digite um nome.", text_color=C["neg"]); return
        conn = conectar()
        ok = adicionar_pessoa(conn, nome)
        conn.close()
        if ok:
            self.lbl_msg.configure(text=f"{nome} adicionado(a).", text_color=C["ok"])
            self.entry_nome.delete(0, "end")
            self.atualizar()
        else:
            self.lbl_msg.configure(text=f"{nome} já existe.", text_color=C["neg"])

    def _abrir_novo_gasto(self):
        conn = conectar(); pessoas = listar_pessoas(conn); conn.close()
        if not pessoas:
            self.lbl_msg.configure(text="Cadastre pessoas antes.", text_color=C["neg"]); return
        NovoGastoJanela(self, pessoas, ao_salvar=self.atualizar)

    def _abrir_repasse(self):
        conn = conectar(); pessoas = listar_pessoas(conn); conn.close()
        if len(pessoas) < 2:
            self.lbl_msg.configure(text="Cadastre ao menos 2 pessoas.",
                                   text_color=C["neg"]); return
        RepasseJanela(self, pessoas, ao_salvar=self.atualizar)

    def _abrir_avatar_picker(self, pessoa_id, nome):
        def ao_escolher(emoji):
            conn = conectar()
            atualizar_avatar(conn, pessoa_id, emoji)
            conn.close()
            self.atualizar()
        EscolherAvatarJanela(self, nome, ao_escolher)

    def _copiar_whatsapp(self):
        conn = conectar()
        saldos = calcular_saldos(conn)
        pagamentos = sugerir_pagamentos([(n, s) for _, n, _, s in saldos])
        conn.close()

        if not pagamentos:
            texto = "✅ *Tudo acertado!*\n\nNinguém deve nada a ninguém. 🎉"
        else:
            linhas = ["💸 *Divisão de gastos*", ""]
            for devedor, credor, valor in pagamentos:
                linhas.append(f"• {devedor} → {credor}: *{reais(valor)}*")
            total = sum(v for _, _, v in pagamentos)
            linhas += ["", f"_Total em transferências: {reais(total)}_"]
            texto = "\n".join(linhas)

        self.clipboard_clear()
        self.clipboard_append(texto)
        self.lbl_msg.configure(text="✅ Copiado! Cole no WhatsApp.",
                               text_color=C["ok"])

    def _exportar_csv(self):
        caminho = filedialog.asksaveasfilename(
            title="Exportar histórico",
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv"), ("Todos os arquivos", "*.*")],
            initialfile=f"divisao_{datetime.date.today().isoformat()}.csv")
        if not caminho:
            return
        conn = conectar()
        exportar_csv(conn, caminho)
        conn.close()
        nome = caminho.replace("\\", "/").split("/")[-1]
        self.lbl_msg.configure(text=f"✅ Exportado: {nome}", text_color=C["ok"])

    def _remover_gasto(self, gid):
        conn = conectar(); remover_gasto(conn, gid); conn.close()
        self.atualizar()

    def _remover_repasse(self, rid):
        conn = conectar(); remover_repasse(conn, rid); conn.close()
        self.atualizar()

    def _limpar_tudo(self):
        if not messagebox.askyesno(
                "Limpar tudo",
                "Apagar TODAS as pessoas, gastos e pagamentos?\n\n"
                "Isso não pode ser desfeito."):
            return
        conn = conectar(); limpar_tudo(conn); conn.close()
        self.lbl_msg.configure(text="Tudo limpo.", text_color=C["ok"])
        self.atualizar()

    # ---------------------- helpers visuais ---------------------- #
    def _pill(self, parent, texto, bg, texto_cor):
        fr = ctk.CTkFrame(parent, fg_color=bg, corner_radius=8)
        ctk.CTkLabel(fr, text=texto,
                     font=ctk.CTkFont("Courier New", 12, "bold"),
                     text_color=texto_cor).pack(padx=10, pady=3)
        return fr

    def _titulo(self, parent, texto):
        ctk.CTkLabel(parent, text=texto.upper(),
                     font=ctk.CTkFont(size=10, weight="bold"),
                     text_color=C["dim"]).pack(anchor="w", padx=18, pady=(18, 6))

    def _vazio(self, parent, texto, cor=None):
        ctk.CTkLabel(parent, text=texto, font=ctk.CTkFont(size=12),
                     text_color=cor or C["dim"]).pack(anchor="w", padx=22, pady=6)

    def _build_stats_card(self, col, icone, label, valor, cor):
        card = ctk.CTkFrame(self.stats_frame, fg_color=C["card"], corner_radius=10)
        card.grid(row=0, column=col, sticky="nsew", padx=4)
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(padx=14, pady=10, fill="both", expand=True)

        top = ctk.CTkFrame(inner, fg_color="transparent")
        top.pack(anchor="w")
        ctk.CTkLabel(top, text=icone, font=fonte_emoji(11),
                     text_color=C["dim"]).pack(side="left", padx=(0, 4))
        ctk.CTkLabel(top, text=label, font=ctk.CTkFont(size=10),
                     text_color=C["dim"]).pack(side="left")
        ctk.CTkLabel(inner, text=valor,
                     font=ctk.CTkFont(size=15, weight="bold"),
                     text_color=cor, anchor="w").pack(anchor="w", pady=(2, 0))

    # ---------------------- aba Resumo ---------------------- #
    def _render_stats(self, stats):
        for w in self.stats_frame.winfo_children():
            w.destroy()

        credor_txt, credor_cor = "—", C["dim"]
        if stats["credor"]:
            _, nome, _, saldo = stats["credor"]
            credor_txt = f"{nome} · {reais(saldo)}"
            credor_cor = C["ok"]

        devedor_txt, devedor_cor = "Ninguém 🎉", C["dim"]
        if stats["devedor"]:
            _, nome, _, saldo = stats["devedor"]
            devedor_txt = f"{nome} · {reais(abs(saldo))}"
            devedor_cor = C["neg"]

        self._build_stats_card(0, "💰", "Total gasto",
                               reais(stats["total_gasto"]), C["text"])
        self._build_stats_card(1, "🔄", "Pago de volta",
                               reais(stats["total_repasses"]), C["ok"])
        self._build_stats_card(2, "👑", "Maior credor", credor_txt, credor_cor)
        self._build_stats_card(3, "🏆", "Maior caloteiro", devedor_txt, devedor_cor)

    def _cartao_saldo(self, pid, nome, avatar, saldo):
        if saldo > 0:
            bg, txt, status = C["ok_bg"], C["ok"], "a receber"
        elif saldo < 0:
            bg, txt, status = C["neg_bg"], C["neg"], "a pagar"
        else:
            bg, txt, status = C["pill_neutral_bg"], C["dim"], "quitado"

        card = ctk.CTkFrame(self.scroll_resumo, fg_color=C["card"], corner_radius=12)
        card.pack(fill="x", padx=14, pady=3)

        criar_avatar(card, nome, 38, avatar,
                     on_click=lambda: self._abrir_avatar_picker(pid, nome)
                     ).pack(side="left", padx=(12, 12), pady=8)
        ctk.CTkLabel(card, text=nome, font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=C["text"]).pack(side="left")
        ctk.CTkLabel(card, text=f"· {status}", font=ctk.CTkFont(size=11),
                     text_color=C["dim"]).pack(side="left", padx=8)

        texto = reais(saldo) if saldo != 0 else "✓"
        self._pill(card, texto, bg, txt).pack(side="right", padx=14)

    def _secao_caloteirometro(self, saldos, repasses_por_pessoa):
        self._titulo(self.scroll_resumo, "🏆 Ranking dos caloteiros")

        devedores = [s for s in saldos if s[3] < 0]
        if not devedores:
            self._vazio(self.scroll_resumo, "Todo mundo em dia! 😇", cor=C["ok"])
            return

        devedores.sort(key=lambda x: x[3])
        max_divida   = abs(devedores[0][3])
        total_divida = sum(abs(s[3]) for s in devedores)
        medalhas     = ["🥇", "🥈", "🥉"]

        for i, (pid, nome, avatar, saldo) in enumerate(devedores):
            medalha = medalhas[i] if i < 3 else "  "
            n_rep = repasses_por_pessoa.get(pid, 0)
            if n_rep == 0:
                status_txt = "🚩 Caloteiro master"
            elif n_rep < 3:
                status_txt = "😅 Ainda devendo"
            else:
                status_txt = "💪 Pagando aos poucos"

            row = ctk.CTkFrame(self.scroll_resumo, fg_color=C["card"],
                               corner_radius=10)
            row.pack(fill="x", padx=14, pady=3)

            ctk.CTkLabel(row, text=medalha, font=fonte_emoji(16), width=30
                         ).pack(side="left", padx=(8, 4), pady=8)

            criar_avatar(row, nome, 26, avatar).pack(side="left",
                                                     padx=(0, 10), pady=6)

            bloco = ctk.CTkFrame(row, fg_color="transparent")
            bloco.pack(side="left", padx=(0, 10))
            ctk.CTkLabel(bloco, text=nome,
                         font=ctk.CTkFont(size=12, weight="bold"),
                         text_color=C["text"], anchor="w").pack(anchor="w")
            ctk.CTkLabel(bloco, text=status_txt,
                         font=ctk.CTkFont(size=9),
                         text_color=C["dim"], anchor="w").pack(anchor="w")

            # BARRA — tk.Frame + place (funciona; CTkFrame + place não)
            bar_bg = tk.Frame(row, bg=C["pill_neutral_bg"], height=14)
            bar_bg.pack(side="left", fill="x", expand=True, padx=(4, 10), pady=8)
            bar_bg.pack_propagate(False)

            ratio = max(0.02, abs(saldo) / max_divida)
            tk.Frame(bar_bg, bg=C["neg"]).place(
                x=0, y=0, relheight=1.0, relwidth=ratio)

            ctk.CTkLabel(row, text=reais(saldo),
                         font=ctk.CTkFont("Courier New", 12, "bold"),
                         text_color=C["neg"]).pack(side="right", padx=12)

        if len(devedores) > 1:
            pior = devedores[0]
            pct = abs(pior[3]) / total_divida
            if pct >= 0.5:
                msg = (f"🏆 {pior[1]} é o caloteiro-mor: "
                       f"{pct * 100:.0f}% da dívida total 🐢")
            else:
                msg = (f"💸 Dívida total: {reais(total_divida)} "
                       f"dividida entre {len(devedores)} pessoas")
            self._vazio(self.scroll_resumo, msg, cor=C["dim"])

    def _cartao_pagamento(self, devedor, credor, valor):
        card = ctk.CTkFrame(self.scroll_resumo, fg_color=C["card"], corner_radius=12)
        card.pack(fill="x", padx=14, pady=3)

        criar_avatar(card, devedor, 28).pack(side="left", padx=(12, 6), pady=8)
        ctk.CTkLabel(card, text=devedor, font=ctk.CTkFont(size=12),
                     text_color=C["text"]).pack(side="left")
        ctk.CTkLabel(card, text="→", font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=C["dim"]).pack(side="left", padx=8)
        criar_avatar(card, credor, 28).pack(side="left", padx=(0, 6))
        ctk.CTkLabel(card, text=credor, font=ctk.CTkFont(size=12),
                     text_color=C["text"]).pack(side="left")

        self._pill(card, reais(valor), C["accent_bg"], C["accent_text"]
                   ).pack(side="right", padx=14)

    # ---------------------- aba Histórico ---------------------- #
    def _cartao_gasto(self, gid, descricao, valor, data_br):
        card = ctk.CTkFrame(self.scroll_hist, fg_color=C["card"], corner_radius=12)
        card.pack(fill="x", padx=14, pady=3)

        ctk.CTkButton(card, text="✕", width=28, height=28,
                      fg_color="transparent", hover_color=C["neg_bg"],
                      text_color=C["neg"], corner_radius=14,
                      command=lambda g=gid: self._remover_gasto(g)
                      ).pack(side="right", padx=(0, 8))

        ctk.CTkLabel(card, text=reais(valor),
                     font=ctk.CTkFont("Courier New", 13, "bold"),
                     text_color=C["text"]).pack(side="right", padx=8)

        self._pill(card, data_br, C["pill_neutral_bg"], C["pill_neutral_text"]
                   ).pack(side="right", padx=4)

        ctk.CTkLabel(card, text=descricao, font=ctk.CTkFont(size=13),
                     text_color=C["text"]).pack(side="left", padx=16, pady=10)

    def _cartao_repasse(self, rid, devedor, credor, valor, data_br):
        card = ctk.CTkFrame(self.scroll_hist, fg_color=C["card"], corner_radius=12)
        card.pack(fill="x", padx=14, pady=3)

        ctk.CTkButton(card, text="✕", width=28, height=28,
                      fg_color="transparent", hover_color=C["neg_bg"],
                      text_color=C["neg"], corner_radius=14,
                      command=lambda r=rid: self._remover_repasse(r)
                      ).pack(side="right", padx=(0, 8))

        ctk.CTkLabel(card, text=reais(valor),
                     font=ctk.CTkFont("Courier New", 13, "bold"),
                     text_color=C["ok"]).pack(side="right", padx=8)

        self._pill(card, data_br, C["pill_neutral_bg"], C["pill_neutral_text"]
                   ).pack(side="right", padx=4)

        criar_avatar(card, devedor, 22).pack(side="left", padx=(12, 4), pady=8)
        ctk.CTkLabel(card, text=devedor, font=ctk.CTkFont(size=12),
                     text_color=C["text"]).pack(side="left")
        ctk.CTkLabel(card, text="→", font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=C["dim"]).pack(side="left", padx=4)
        criar_avatar(card, credor, 22).pack(side="left", padx=(0, 4))
        ctk.CTkLabel(card, text=credor, font=ctk.CTkFont(size=12),
                     text_color=C["text"]).pack(side="left")

    # ---------------------- aba Pessoas ---------------------- #
    def _render_pessoas(self, saldos):
        for w in self.scroll_pessoas.winfo_children():
            w.destroy()

        if not saldos:
            self._vazio(self.scroll_pessoas,
                        "Ninguém cadastrado ainda. Adicione a primeira pessoa acima.")
            return

        self._titulo(self.scroll_pessoas, "Clique no avatar para trocar a carinha")

        for pid, nome, avatar, _saldo in saldos:
            card = ctk.CTkFrame(self.scroll_pessoas, fg_color=C["card"],
                                corner_radius=12)
            card.pack(fill="x", padx=14, pady=3)

            criar_avatar(card, nome, 38, avatar,
                         on_click=lambda p=pid, n=nome: self._abrir_avatar_picker(p, n)
                         ).pack(side="left", padx=(12, 12), pady=8)

            ctk.CTkLabel(card, text=nome,
                         font=ctk.CTkFont(size=14, weight="bold"),
                         text_color=C["text"]).pack(side="left")

            ctk.CTkButton(card, text="Trocar carinha",
                          command=lambda p=pid, n=nome: self._abrir_avatar_picker(p, n),
                          fg_color="transparent", hover_color=C["accent_bg"],
                          border_width=1, border_color=C["border"],
                          text_color=C["dim"], corner_radius=8, height=28,
                          width=120).pack(side="right", padx=14)

    # ---------------------- atualização ---------------------- #
    def atualizar(self):
        conn = conectar()
        saldos     = calcular_saldos(conn)
        pagamentos = sugerir_pagamentos([(n, s) for _, n, _, s in saldos])
        gastos     = listar_gastos(conn)
        repasses   = listar_repasses(conn)
        stats      = estatisticas(conn)
        rep_por_pessoa = repasses_por_pessoa(conn)
        conn.close()

        # ----- aba Resumo ----- #
        self._render_stats(stats)
        for w in self.scroll_resumo.winfo_children():
            if w is self.stats_frame:
                continue
            w.destroy()
        # reempacotar stats_frame no topo (foi preservado)
        self.stats_frame.pack_forget()
        self.stats_frame.pack(fill="x", padx=6, pady=(4, 10))

        self._titulo(self.scroll_resumo, "Saldos")
        if not saldos:
            self._vazio(self.scroll_resumo,
                        "Ninguém cadastrado ainda. Vá na aba Pessoas.")
        for pid, nome, avatar, saldo in saldos:
            self._cartao_saldo(pid, nome, avatar, saldo)

        self._secao_caloteirometro(saldos, rep_por_pessoa)

        self._titulo(self.scroll_resumo, "Quem paga quem")
        if not pagamentos:
            self._vazio(self.scroll_resumo, "Tudo acertado ✓", cor=C["ok"])
        for devedor, credor, valor in pagamentos:
            self._cartao_pagamento(devedor, credor, valor)

        # ----- aba Histórico ----- #
        for w in self.scroll_hist.winfo_children():
            w.destroy()

        self._titulo(self.scroll_hist, "Gastos")
        if not gastos:
            self._vazio(self.scroll_hist, "Nenhum gasto registrado.")
        for gid, desc, valor, data in gastos:
            self._cartao_gasto(gid, desc, valor,
                               "/".join(reversed(data.split("-"))))

        self._titulo(self.scroll_hist, "Pagamentos")
        if not repasses:
            self._vazio(self.scroll_hist, "Nenhum pagamento registrado.")
        for rid, de, para, valor, data in repasses:
            self._cartao_repasse(rid, de, para, valor,
                                 "/".join(reversed(data.split("-"))))

        # ----- aba Pessoas ----- #
        self._render_pessoas(saldos)


if __name__ == "__main__":
    app = DivisaoApp()
    app.mainloop()