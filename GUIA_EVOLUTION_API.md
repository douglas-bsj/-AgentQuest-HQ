# 📱 Guia de Integração WhatsApp — Evolution API

Este guia explica como conectar o seu **WhatsApp pessoal** (ou da sua empresa) ao **AgentQuest HQ** usando a **Evolution API v2**.

---

## 🎯 Como funciona a integração:
1. **Entrada de Mensagens:** Quando um cliente te manda mensagem no WhatsApp, a Evolution API avisa o AgentQuest HQ imediatamente (via Webhook).
2. **Squad de Agentes:** Os 8 agentes processam a mensagem, analisam histórico, calculam prazos/valores e montam o rascunho de resposta ideal.
3. **Aprovação Humana:** O rascunho aparece no seu painel web.
4. **Disparo Automático:** Quando você clica em **"✅ Aprovar & Executar"**, o AgentQuest HQ envia a mensagem pelo seu próprio WhatsApp automaticamente.

---

## 🛠️ PASSO 1: Baixar e Rodar a Evolution API

A Evolution API roda localmente no seu computador via **Docker** (a forma mais fácil e estável).

### Se você já tem o Docker Desktop instalado:
Abra o terminal (PowerShell) e execute um único comando:

```powershell
docker run -d `
  --name evolution-api `
  -p 8080:8080 `
  -e AUTHENTICATION_API_KEY=agentquest-secreto-123 `
  -v evolution_instances:/evolution/instances `
  atendai/evolution-api:v2.1.2
```

> 💡 **Nota:** Se você não tem Docker, você também pode usar serviços em nuvem gratuitos como Render ou Railway para hospedar a Evolution API.

---

## 📱 PASSO 2: Conectar seu WhatsApp (Escanear QR Code)

Após o container subir:

1. Abra o painel da Evolution API no seu navegador:  
   👉 `http://localhost:8080/manager` *(ou via API Postman/Swagger em `http://localhost:8080/docs`)*
2. Crie uma nova instância chamada **`agentquest`**.
3. Um **QR Code** será exibido na tela.
4. Pegue o seu celular:
   - Abra o **WhatsApp**
   - Vá em **Aparelhos Conectados** > **Conectar um Aparelho**
   - Aponte a câmera para o QR Code da tela.
5. Pronto! Seu WhatsApp está conectado à Evolution API.

---

## ⚙️ PASSO 3: Configurar no Painel do AgentQuest HQ

1. Abra o painel do AgentQuest (`http://127.0.0.1:8000`).
2. Clique no ícone de **⚙️ (Configurações)** no topo direito.
3. Clique na aba **"💬 Canais & Mensageria"**.
4. Preencha os campos conforme abaixo:
   - **Tipo de Conexão:** `Evolution API (Recomendado)`
   - **URL da API / Host:** `http://localhost:8080`
   - **Nome da Instância:** `agentquest`
   - **Token / API Key:** `agentquest-secreto-123`
   - **Webhook de Entrada:** `http://127.0.0.1:8000/api/webhook/whatsapp`
5. Clique em **"💾 Salvar Configurações"**.

---

## 🔗 PASSO 4: Ativar o Webhook na Evolution API

Para o WhatsApp enviar as mensagens para o AgentQuest em tempo real:

1. Na Evolution API, configure o Webhook da instância `agentquest` para:  
   👉 `http://127.0.0.1:8000/api/webhook/whatsapp`
2. Marque o evento: **`MESSAGES_UPSERT`**.

---

## 🧪 Como Testar:

1. Peça para alguém (ou use outro celular) mandar uma mensagem para o seu WhatsApp:  
   *Exemplo:* `"Olá, gostaria de saber o valor da proposta comercial do projeto."`
2. Em segundos, veja o card da missão aparecer no painel **AgentQuest HQ**.
3. Clique em **"✅ Aprovar & Executar"**.
4. A resposta será enviada do seu WhatsApp pessoal direto para a pessoa! 🚀
