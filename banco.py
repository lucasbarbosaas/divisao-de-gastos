import sqlite3


def conectar():
    conn = sqlite3.connect("gastos.db")
    conn.execute("PRAGMA foreign_keys = ON")
    _criar_schema(conn)
    return conn

def conectar():
    conn = sqlite3.connect("gastos.db")
    conn.execute("PRAGMA foreign_keys = ON")
    _criar_schema(conn)
    return conn


def _criar_schema(conn):
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS pessoas (
        id   INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL UNIQUE,
        avatar TEXT
    );
    -- ... resto das tabelas igual ...
    """)
    # migração: bancos antigos não têm a coluna avatar
    try:
        conn.execute("ALTER TABLE pessoas ADD COLUMN avatar TEXT")
    except sqlite3.OperationalError:
        pass
    conn.commit()


def calcular_saldos(conn):
    cur = conn.cursor()
    cur.execute("""
        SELECT p.id, p.nome, p.avatar,
            (SELECT COALESCE(SUM(a.valor), 0)
               FROM adiantamentos a
               JOIN gastos g ON g.id = a.gasto_id
              WHERE a.pessoa_id = p.id)
          - (SELECT COALESCE(SUM(pc.valor_devido), 0)
               FROM participacoes pc
               JOIN gastos g ON g.id = pc.gasto_id
              WHERE pc.pessoa_id = p.id)
          + (SELECT COALESCE(SUM(valor), 0) FROM repasses WHERE de_pessoa_id   = p.id)
          - (SELECT COALESCE(SUM(valor), 0) FROM repasses WHERE para_pessoa_id = p.id)
            AS saldo
        FROM pessoas p
        ORDER BY p.nome
    """)
    return cur.fetchall()


def listar_pessoas(conn):
    return conn.execute(
        "SELECT id, nome, avatar FROM pessoas ORDER BY nome").fetchall()


def atualizar_avatar(conn, pessoa_id, avatar):
    conn.execute("UPDATE pessoas SET avatar = ? WHERE id = ?", (avatar, pessoa_id))
    conn.commit()

def sugerir_pagamentos(saldos):
    credores = [[nome, saldo] for nome, saldo in saldos if saldo > 0]
    devedores = [[nome, -saldo] for nome, saldo in saldos if saldo < 0]

    pagamentos = []
    i = 0
    j = 0
    while i < len(devedores) and j < len(credores):
        nome_dev, divida = devedores[i]
        nome_cred, credito = credores[j]

        valor = min(divida, credito)
        pagamentos.append((nome_dev, nome_cred, valor))

        devedores[i][1] -= valor
        credores[j][1] -= valor

        if devedores[i][1] == 0:
            i += 1
        if credores[j][1] == 0:
            j += 1

    return pagamentos

def adicionar_pessoa(conn, nome):
    try:
        conn.execute("INSERT INTO pessoas (nome) VALUES (?)", (nome,))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False

def adicionar_gasto(conn, descricao, valor_total, data, pagadores, participantes_ids):
    n = len(participantes_ids)
    base = valor_total // n
    resto = valor_total % n

    cur = conn.cursor()
    cur.execute(
        "INSERT INTO gastos (descricao, valor_total, data) VALUES (?, ?, ?)",
        (descricao, valor_total, data))
    gasto_id = cur.lastrowid

    for k, pessoa_id in enumerate(participantes_ids):
        parte = base + (1 if k < resto else 0)
        cur.execute(
            "INSERT INTO participacoes (gasto_id, pessoa_id, valor_devido) VALUES (?, ?, ?)",
            (gasto_id, pessoa_id, parte))

    for pessoa_id, valor in pagadores:
        cur.execute(
            "INSERT INTO adiantamentos (gasto_id, pessoa_id, valor) VALUES (?, ?, ?)",
            (gasto_id, pessoa_id, valor))

    conn.commit()
    return gasto_id

def adicionar_repasse(conn, de_id, para_id, valor, data):
    conn.execute(
        "INSERT INTO repasses (de_pessoa_id, para_pessoa_id, valor, data) VALUES (?, ?, ?, ?)",
        (de_id, para_id, valor, data))
    conn.commit()

def listar_gastos(conn):
    """Histórico do mais recente para o mais antigo."""
    return conn.execute("""
        SELECT id, descricao, valor_total, data
        FROM gastos
        ORDER BY data DESC, id DESC
    """).fetchall()


def remover_gasto(conn, gasto_id):
    """Apaga o gasto e suas linhas dependentes."""
    
    conn.execute("DELETE FROM participacoes WHERE gasto_id = ?", (gasto_id,))
    conn.execute("DELETE FROM adiantamentos WHERE gasto_id = ?", (gasto_id,))
    conn.execute("DELETE FROM gastos        WHERE id       = ?", (gasto_id,))
    conn.commit()

def listar_repasses(conn):
    return conn.execute("""
        SELECT r.id, p1.nome, p2.nome, r.valor, r.data
        FROM repasses r
        JOIN pessoas p1 ON p1.id = r.de_pessoa_id
        JOIN pessoas p2 ON p2.id = r.para_pessoa_id
        ORDER BY r.data DESC, r.id DESC
    """).fetchall()


def remover_repasse(conn, repasse_id):
    conn.execute("DELETE FROM repasses WHERE id = ?", (repasse_id,))
    conn.commit()


def limpar_tudo(conn):
    """Apaga TUDO."""
    conn.executescript("""
        DELETE FROM adiantamentos;
        DELETE FROM participacoes;
        DELETE FROM gastos;
        DELETE FROM repasses;
        DELETE FROM pessoas;
    """)
    conn.commit()

def estatisticas(conn):
    """Números agregados para a faixa de estatísticas do topo."""
    saldos = calcular_saldos(conn)
    total_gasto = conn.execute(
        "SELECT COALESCE(SUM(valor_total), 0) FROM gastos").fetchone()[0]
    total_repasses = conn.execute(
        "SELECT COALESCE(SUM(valor), 0) FROM repasses").fetchone()[0]

    positivos = [s for s in saldos if s[3] > 0]
    negativos = [s for s in saldos if s[3] < 0]

    return {
        "total_gasto":    total_gasto,
        "total_repasses": total_repasses,
        "credor":  max(positivos, key=lambda x: x[3]) if positivos else None,
        "devedor": min(negativos, key=lambda x: x[3]) if negativos else None,
    }


def repasses_por_pessoa(conn):
    """{pessoa_id: quantos repasses já pagou}. Usado no caloteirômetro."""
    return dict(conn.execute("""
        SELECT de_pessoa_id, COUNT(*) FROM repasses GROUP BY de_pessoa_id
    """).fetchall())


def exportar_csv(conn, caminho):
    """Exporta gastos + repasses. Separador ';' e BOM para abrir no Excel BR."""
    import csv
    gastos   = listar_gastos(conn)
    repasses = listar_repasses(conn)

    with open(caminho, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["Tipo", "Data", "Descrição", "Valor (R$)"])
        for _gid, desc, valor, data in gastos:
            w.writerow(["Gasto", data, desc,
                        f"{valor / 100:.2f}".replace(".", ",")])
        for _rid, de, para, valor, data in repasses:
            w.writerow(["Pagamento", data, f"{de} → {para}",
                        f"{valor / 100:.2f}".replace(".", ",")])
    return caminho