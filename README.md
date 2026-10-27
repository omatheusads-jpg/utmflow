# 🚀 UtmFlow — Plataforma de Tracking, Lucro Real & Meta Ads Manager

UtmFlow é uma plataforma profissional de AdTech construída em **Python Puro (Zero Dependências PIP Externas)** com frontend reativo em Dark Mode (Tailwind CSS + Lucide Icons), Web Audio API Ka-ching para vendas em tempo real, réplica do Facebook Ads Manager, atribuição UTM estilo UTMify, Meta CAPI Server-Side e Motor de Regras Automáticas (Stop Loss e Escala).

---

## 🏛️ Arquitetura do Sistema

- **Backend:** Python 3 Standard Library (`http.server.ThreadingHTTPServer`, `sqlite3`, `urllib.request`, `json`, `hashlib`, `uuid`, `threading`).
- **Zero PIP:** Não necessita de `requirements.txt` ou `pip install`, iniciando instantaneamente no Render ou em qualquer servidor Linux/Windows.
- **Frontend SPA:** Arquivo único com Tailwind CSS CDN, ícones Lucide, Web Audio API nativo (Ka-ching sem arquivos MP3 externos), Drag & Drop de cards com persistência no SQLite e filtros hierárquicos.
- **Rastreamento:** `/utmflow.js` captura parâmetros UTM, persistência em cookies (90 dias) e decora automaticamente botões de checkout (Kiwify, Hotmart, Greenn, Cakto, Wiapy, Eduzz, etc.).
- **Meta Graph API & CAPI:** Suporte a OAuth 2.0 (1-clique com troca de token de 60 dias) e Token Permanente de BM (que nunca expira), paginação por cursor (`paging.cursors.after`) e disparo Purchase CAPI com hash SHA-256.

---

## ⚡ Como Rodar Localmente

```bash
# 1. Navegue até a pasta do projeto
cd C:\Users\ohebe\.gemini\antigravity\scratch\nexustrack

# 2. Inicie o servidor (padrão porta 8000 ou passe como argumento)
python server.py 8000
```

Abra o seu navegador em: `http://localhost:8000`

---

## 🌐 Deploy Gratuito no Render (Passo a Passo)

1. Crie um repositório no seu GitHub (ex: `utmflow`) e suba os arquivos:
   - `server.py`
   - `index.html`
   - `utmflow.js`
2. Acesse [render.com](https://render.com) e crie uma conta gratuita.
3. No painel, clique em **New +** ➔ **Web Service**.
4. Conecte com o seu repositório do GitHub.
5. Configure as opções de deploy:
   - **Name:** `utmflow-app` (ou o nome que desejar)
   - **Runtime:** `Python 3`
   - **Build Command:** *(deixe em branco ou digite `true`)*
   - **Start Command:** `python server.py 10000`
   - **Instance Type:** `Free`
6. Clique em **Create Web Service**.
   Em menos de 1 minuto, seu sistema estará online em uma URL como:
   `https://utmflow-app.onrender.com`

---

## 🔑 Como Conectar com a Meta Ads

### Modo 1: Token Permanente (Que NUNCA Expira) — Recomendado
1. Acesse o **Gerenciador de Negócios da Meta**: [business.facebook.com/settings](https://business.facebook.com/settings).
2. No menu lateral, vá em **Usuários ➔ Usuários do Sistema**.
3. Clique em **Adicionar**, defina um nome (ex: `UtmFlow Admin`) e escolha o papel de **Administrador**.
4. **Vincular o Aplicativo com Controle Total:**
   - No menu lateral, clique em **Contas ➔ Aplicativos**.
   - Adicione o seu App da Meta ou crie um app básico em [developers.facebook.com](https://developers.facebook.com).
   - Clique em **Atribuir Pessoas** (ou Usuário do Sistema) e dê **Controle Total (Gerenciar Aplicativo)** ao usuário criado.
5. Volte em **Usuários do Sistema**, clique no usuário criado e clique em **Gerar Novo Token**.
6. Selecione o seu App, escolha a expiração como **NUNCA** e marque a permissão:
   - `ads_read` (leitura de anúncios e insights)
7. Copie o token gerado (`EAAB...`).
8. No painel do UtmFlow:
   - Vá na aba **Taxas & Conexão Meta**.
   - Clique no botão **Adicionar Token Permanente BM**.
   - Cole o token e clique em **Validar & Importar Contas**.
   - Pronto! Todas as contas de anúncio da BM serão importadas imediatamente.

### Modo 2: Login 1-Clique Oficial Meta (OAuth 2.0 - 60 Dias)
1. Acesse [developers.facebook.com/apps](https://developers.facebook.com/apps) e crie um App do tipo **Outro** ou **Empresa**.
2. Adicione o produto **Facebook Login para Empresas**.
3. Nas configurações do Facebook Login, adicione em **URIs de redirecionamento do OAuth válidos**:
   `https://SEU-DOMINIO.onrender.com/api/integrations/meta/callback`
4. Vá em **Configurações ➔ Básico** e copie o **ID do Aplicativo** e a **Chave Secreta**.
5. No painel do UtmFlow (aba **Taxas & Conexão Meta**), cole o App ID e App Secret e clique em **Salvar Chaves**.
6. Clique no botão azul **Conectar com Facebook (1-Clique)**.

---

## 🛒 Como Cadastrar os Webhooks das Plataformas

No UtmFlow, acesse a aba **Webhooks & Pixel** e copie a URL referente à sua plataforma:

- **Kiwify:** `https://SEU-DOMINIO/api/webhook/kiwify`
- **Hotmart:** `https://SEU-DOMINIO/api/webhook/hotmart`
- **Greenn:** `https://SEU-DOMINIO/api/webhook/greenn`
- **Cakto:** `https://SEU-DOMINIO/api/webhook/cakto`
- **Wiapy:** `https://SEU-DOMINIO/api/webhook/wiapy`

---

## 🏷️ Instalação do Pixel na Página de Vendas (`utmflow.js`)

Cole este trecho dentro da tag `<head>` de todas as páginas do seu funil:

```html
<!-- UtmFlow Pixel & Checkout Link Decorator v2.0 -->
<script src="https://SEU-DOMINIO/utmflow.js" defer></script>
```
