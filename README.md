#  Divisão de Gastos

Aplicativo desktop em Python para dividir gastos entre amigos, família ou colegas — sem planilha, sem discussão.

> Nasceu de uma corrida de Uber dividida entre três amigos, duas pessoas conseguiram dividir a conta pelo próprio aplicativo de corrida, mas uma não conseguiu, logo, ficou devendo para duas pessoas. Ao acordar e fazer essa continha para repassar o valor pensei em automatizar essa questão com um aplicativo.

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-003B57?logo=sqlite&logoColor=white)
![CustomTkinter](https://img.shields.io/badge/CustomTkinter-1e1e1e?logo=python&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-green)

---

##  O problema

Dividir contas em grupo é chato. Streaming, Uber, cartão, aluguel, jantar — cada um paga uma coisa, cada um deve uma parte diferente, e no fim das contas alguém sempre fica no prejuízo (ou na dúvida). Planilhas resolvem o cálculo, mas não a conversa: quem paga quem, e quanto? E muita das vezes ficamos com preguiça de cobrar ou anotar quanto cada um deve.

Este app resolve os dois. Você registra os gastos, ele calcula os saldos e sugere a menor quantidade possível de transferências pra zerar tudo.

---

##  Funcionalidades

-  **Múltiplas pessoas** com avatar emoji personalizável
-  **Registro de gastos** com divisão automática (incluindo o rateio dos centavos)
-  **Registro de pagamentos** (quem pagou pra quem e quando)
-  **Sugestão inteligente** de transferências —> o mínimo de pagamentos possível
-  **Ranking dos caloteiros** — visualização divertida de quem mais deve
-  **Faixa de estatísticas** — total gasto, pago de volta, maior credor e maior devedor
-  **Copiar para o WhatsApp** — texto formatado pronto pra colar no grupo
-  **Exportar CSV** — histórico completo em formato compatível com Excel
-  **Tema claro e escuro**
-  **Interface em abas** — Resumo · Histórico · Pessoas

---

##  Screenshots

<img width="1366" height="721" alt="image" src="https://github.com/user-attachments/assets/33ead8b5-ed3a-4afe-b3ce-8e14b8b3d7dc" />
<img width="1347" height="694" alt="image" src="https://github.com/user-attachments/assets/de1e9fd2-9141-485c-bbcd-8e73dbbe2b71" />
<img width="409" height="674" alt="image" src="https://github.com/user-attachments/assets/e9c6f4b0-2ab4-49d2-bcbf-83a371d791e7" />
<img width="1366" height="721" alt="image" src="https://github.com/user-attachments/assets/bf456d21-c36e-4791-b343-6e84c6d4ba40" />


---

##  Como funciona o cálculo

O principal do app são duas funções em `banco.py`:

### 1. `calcular_saldos`

Para cada pessoa, o saldo é:

```
saldo = (o que ela pagou)
      - (a cota dela em cada gasto)
      + (pagamentos que ela fez a outros)
      - (pagamentos que ela recebeu)
```

- **Saldo positivo** → tem a receber
- **Saldo negativo** → deve
- **Saldo zero** → quitado

A soma dos saldos é sempre zero (verificado nos testes), porque dinheiro não some nem aparece do nada.

### 2. `sugerir_pagamentos`

Um algoritmo que casa o maior devedor com o maior credor, abate o valor menor, e repete até todos zerarem. O resultado é a lista de transferências a fazer — geralmente a menor possível na prática.

### O detalhe dos centavos

Se R$ 10,00 é dividido entre 3 pessoas, a divisão "justa" não existe: sobram R$ 0,01. O app resolve distribuindo o centavo extra nas primeiras pessoas da lista de participantes:

```
R$ 10,00 / 3 = R$ 3,33 + R$ 3,33 + R$ 3,34
```

Sem isso, o saldo final não fecharia e o app mostraria uma dívida fantasma de R$ 0,01.

---

##  Como rodar

### Pré-requisitos

- Python 3.10+
- `pip`

### Passo a passo

```bash
# 1. Clone o repositório
git clone https://github.com/lucasbarbosaas/divisao-de-gastos.git
cd divisao-de-gastos

# 2. (Opcional) Crie um ambiente virtual
python -m venv .venv
source .venv/bin/activate       # Linux / macOS
# ou .venv\Scripts\activate      # Windows

# 3. Instale a dependência
pip install customtkinter

# 4. Rode o app
python gui.py
```

O banco de dados (`gastos.db`) é criado automaticamente na primeira execução.

### Rodando os testes

```bash
pip install pytest
pytest -v
```

---

##  Estrutura do projeto

```
divisao-de-gastos/
├── gui.py            # Interface (CustomTkinter)
├── banco.py          # Persistência + lógica de cálculo (SQLite)     
├── README.md
└── gastos.db         # Gerado em runtime — não comitar
```

---

##  Stack

| Camada          | Tecnologia      | Por quê                                          |
|-----------------|-----------------|--------------------------------------------------|
| Interface       | CustomTkinter   | Tkinter com cara moderna, sem depender de webview |
| Persistência    | SQLite          | Zero configuração, um arquivo só, ideal pra desktop |
| Linguagem       | Python 3.10+    | —                                                |

---

##  Roadmap

- [x] Divisão de gastos com os centavos divididos corretamente
- [x] Sugestão de pagamentos
- [x] Avatares emoji personalizáveis
- [x] Tema claro/escuro
- [x] Abas (Resumo / Histórico / Pessoas)
- [x] Copiar para WhatsApp
- [x] Exportar CSV
- [ ] Persistir tema e aba ativa entre sessões
- [ ] Confirmação antes de excluir gasto/pagamento
- [ ] **Grupos/contextos** — separar "Uber do réveillon" de "viagem da praia"
- [ ] **Gráfico temporal** — evolução do saldo de cada pessoa ao longo do tempo
- [ ] **Análise estatística** — regressão sobre padrões de pagamento
- [ ] Empacotamento com PyInstaller (`.exe` / `.app`)

---

##  O que aprendi construindo isso

- **Modelagem relacional** — cinco tabelas, chaves estrangeiras, e o cuidado de nunca duplicar dado (divisão calculado uma vez, não em cada consulta).
- **Algoritmos gananciosos** — o problema de "quem paga quem" é um caso clássico de *debt settlement*; a solução gananciosa não é ótima matematicamente, mas é suficientemente boa e trivial de explicar.
- **Aritmética inteira em centavos** — nunca usei `float` pra dinheiro. Tudo é `int` representando centavos. `R$ 10,00` = `1000`. Elimina os erros de arredondamento que assombram qualquer app financeiro.
- **Testes como rede de segurança** — o invariante "soma dos saldos = 0" pegou pelo menos dois bugs durante o desenvolvimento.
- **UX de ferramenta interna** — um app que ninguém quer usar duas vezes precisa ser óbvio na primeira. Daí a insistência em emojis, cores e feedback imediato.

---

##  Contribuições

Sugestões, issues e pull requests são bem-vindos. Se encontrar um bug ou tiver uma ideia, abre uma issue — adoraria conversar.

---

##  Contato

- **LinkedIn:** [lucas barbosa](https://linkedin.com/in/lucas-barbosa-26b141377)
- **GitHub:** [@lucasbarbosaas](https://github.com/lucasbarbosaas)

---

## 📄 Licença

MIT — use, modifique, distribua. Só não me culpe se o grupo do WhatsApp brigar. 😄
