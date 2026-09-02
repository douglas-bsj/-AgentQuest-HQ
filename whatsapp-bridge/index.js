/**
 * AgentQuest HQ — Ponte de WhatsApp (Baileys)
 *
 * Servidor HTTP local que conecta o WhatsApp via Baileys, sem Docker,
 * Postgres, Redis ou virtualizacao. A sessao fica em arquivos locais.
 *
 * Endpoints:
 *   GET  /status  -> estado da conexao e se ha QR pendente
 *   GET  /qr      -> QR Code em base64 (data URL) para parear
 *   POST /send    -> { number, text } envia mensagem de texto
 *   POST /logout  -> encerra a sessao e apaga as credenciais
 *
 * Mensagens recebidas sao repassadas para o webhook do AgentQuest.
 *
 * Variaveis de ambiente:
 *   BRIDGE_PORT    porta deste servidor            (padrao 8765)
 *   AGENTQUEST_URL base do AgentQuest para webhook (padrao http://localhost:8000)
 *   AUTH_DIR       pasta da sessao                 (padrao ./auth_state)
 *   IGNORE_GROUPS  "true" para ignorar grupos      (padrao true)
 */

const http = require("http");
const path = require("path");
const fs = require("fs");

const makeWASocket = require("baileys").default;
const {
  useMultiFileAuthState,
  DisconnectReason,
  fetchLatestBaileysVersion,
} = require("baileys");
const QRCode = require("qrcode");
const pino = require("pino");

const BRIDGE_PORT = parseInt(process.env.BRIDGE_PORT || "8765", 10);
const AGENTQUEST_URL = (process.env.AGENTQUEST_URL || "http://localhost:8000").replace(/\/$/, "");
const AUTH_DIR = process.env.AUTH_DIR || path.join(__dirname, "auth_state");
const IGNORE_GROUPS = (process.env.IGNORE_GROUPS || "true") === "true";

const logger = pino({ level: "warn" });

let sock = null;
let connectionState = "close"; // close | connecting | open
let qrDataUrl = null;
let lastError = null;
let reconnectAttempts = 0;

function log(msg) {
  console.log(`[BRIDGE] ${msg}`);
}

async function encaminharParaAgentQuest(payload) {
  try {
    const res = await fetch(`${AGENTQUEST_URL}/api/webhook/whatsapp`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      log(`Webhook retornou ${res.status}`);
    }
  } catch (e) {
    log(`Falha ao entregar webhook: ${e.message}`);
  }
}

/**
 * Classifica o remetente pelo JID.
 *
 * Filtrar apenas "@g.us" nao basta: o WhatsApp entrega grupos, canais
 * (newsletter), listas de transmissao e comunidades com sufixos diferentes, e
 * todos apareciam como se fossem conversa individual. Aqui a regra e invertida:
 * so e tratado como pessoa aquilo que comprovadamente e pessoa.
 */
function classificarJid(jid) {
  if (!jid) return "desconhecido";
  if (jid.endsWith("@g.us")) return "grupo";
  if (jid.endsWith("@newsletter")) return "canal";
  if (jid.endsWith("@broadcast") || jid === "status@broadcast") return "transmissao";
  if (jid.endsWith("@s.whatsapp.net") || jid.endsWith("@lid")) {
    // IDs de 18 digitos nao sao telefone: sao grupos/canais no formato novo
    const numero = jid.split("@")[0].replace(/\D/g, "");
    if (numero.length > 15) return "grupo";
    return "individual";
  }
  return "desconhecido";
}

function extrairTexto(msg) {
  const m = msg.message;
  if (!m) return "";
  return (
    m.conversation ||
    m.extendedTextMessage?.text ||
    m.imageMessage?.caption ||
    m.videoMessage?.caption ||
    m.documentMessage?.caption ||
    ""
  );
}

async function conectar() {
  const { state, saveCreds } = await useMultiFileAuthState(AUTH_DIR);
  const { version } = await fetchLatestBaileysVersion();

  sock = makeWASocket({
    version,
    auth: state,
    logger,
    printQRInTerminal: false,
    syncFullHistory: false,
    markOnlineOnConnect: false,
    browser: ["AgentQuest HQ", "Chrome", "1.0.0"],
  });

  sock.ev.on("creds.update", saveCreds);

  sock.ev.on("connection.update", async (update) => {
    const { connection, lastDisconnect, qr } = update;

    if (qr) {
      qrDataUrl = await QRCode.toDataURL(qr, { margin: 1, width: 400 });
      connectionState = "connecting";
      log("QR Code gerado — aguardando pareamento.");
    }

    if (connection === "open") {
      connectionState = "open";
      qrDataUrl = null;
      lastError = null;
      reconnectAttempts = 0;
      log("WhatsApp conectado.");
    }

    if (connection === "close") {
      connectionState = "close";
      const codigo = lastDisconnect?.error?.output?.statusCode;

      if (codigo === DisconnectReason.loggedOut) {
        // Sessao invalidada pelo proprio WhatsApp: limpa as credenciais para
        // que um novo QR possa ser gerado no proximo connect.
        log("Sessao encerrada no aparelho — credenciais descartadas.");
        try {
          fs.rmSync(AUTH_DIR, { recursive: true, force: true });
        } catch (e) {
          log(`Nao foi possivel limpar a sessao: ${e.message}`);
        }
        qrDataUrl = null;
        lastError = "logged_out";
        return;
      }

      // Reconexao com espera progressiva, para nao entrar em laco agressivo
      reconnectAttempts += 1;
      const esperaMs = Math.min(30000, 2000 * reconnectAttempts);
      lastError = lastDisconnect?.error?.message || "conexao encerrada";
      log(`Conexao caiu (${lastError}). Nova tentativa em ${esperaMs / 1000}s.`);
      setTimeout(() => conectar().catch((e) => log(`Erro ao reconectar: ${e.message}`)), esperaMs);
    }
  });

  sock.ev.on("messages.upsert", async ({ messages, type }) => {
    if (type !== "notify") return;

    for (const msg of messages) {
      if (msg.key.fromMe) continue;

      const remoteJid = msg.key.remoteJid || "";
      const tipo = classificarJid(remoteJid);

      // Transmissoes/status nunca sao demandas de atendimento
      if (tipo === "transmissao") continue;

      if (IGNORE_GROUPS && tipo !== "individual") {
        log(`Ignorada mensagem de ${tipo} (${remoteJid}) conforme configuracao.`);
        continue;
      }

      const texto = extrairTexto(msg);
      if (!texto.trim()) continue;

      const numero = remoteJid.split("@")[0];
      log(`Mensagem recebida [${tipo}] de ${numero} (${remoteJid}): "${texto.slice(0, 60)}"`);

      // Formato compativel com o webhook que o AgentQuest ja recebe da Evolution
      await encaminharParaAgentQuest({
        event: "messages.upsert",
        instance: "baileys",
        data: {
          key: { remoteJid, fromMe: false, id: msg.key.id },
          pushName: msg.pushName || numero,
          message: { conversation: texto },
          messageTimestamp: msg.messageTimestamp,
        },
      });
    }
  });
}

// ── Servidor HTTP local ────────────────────────────────────────────
function responder(res, status, corpo) {
  res.writeHead(status, { "Content-Type": "application/json; charset=utf-8" });
  res.end(JSON.stringify(corpo));
}

function lerCorpo(req) {
  return new Promise((resolve, reject) => {
    let dados = "";
    req.on("data", (c) => (dados += c));
    req.on("end", () => {
      try {
        resolve(dados ? JSON.parse(dados) : {});
      } catch (e) {
        reject(e);
      }
    });
    req.on("error", reject);
  });
}

const servidor = http.createServer(async (req, res) => {
  const url = new URL(req.url, `http://localhost:${BRIDGE_PORT}`);

  if (req.method === "GET" && url.pathname === "/status") {
    return responder(res, 200, {
      state: connectionState,
      qr_pending: Boolean(qrDataUrl),
      last_error: lastError,
      number: sock?.user?.id ? sock.user.id.split(":")[0] : null,
    });
  }

  if (req.method === "GET" && url.pathname === "/qr") {
    if (!qrDataUrl) {
      return responder(res, 404, {
        status: connectionState === "open" ? "already_connected" : "no_qr",
        message: connectionState === "open"
          ? "WhatsApp ja esta conectado."
          : "Nenhum QR Code disponivel no momento.",
      });
    }
    return responder(res, 200, { status: "qr_ready", qr_base64: qrDataUrl });
  }

  if (req.method === "POST" && url.pathname === "/send") {
    if (connectionState !== "open" || !sock) {
      return responder(res, 503, { status: "error", message: "WhatsApp nao esta conectado." });
    }
    try {
      const corpo = await lerCorpo(req);
      const numero = String(corpo.number || "").replace(/\D/g, "");
      const texto = String(corpo.text || "");
      if (!numero || !texto) {
        return responder(res, 400, { status: "error", message: "Informe 'number' e 'text'." });
      }
      const jid = `${numero}@s.whatsapp.net`;
      await sock.sendMessage(jid, { text: texto });
      log(`Mensagem enviada para ${numero}.`);
      return responder(res, 200, { status: "sent", destination: numero });
    } catch (e) {
      return responder(res, 500, { status: "error", message: e.message });
    }
  }

  if (req.method === "POST" && url.pathname === "/logout") {
    try {
      if (sock) await sock.logout();
    } catch (e) {
      log(`Erro ao encerrar sessao: ${e.message}`);
    }
    try {
      fs.rmSync(AUTH_DIR, { recursive: true, force: true });
    } catch (e) {
      log(`Erro ao limpar credenciais: ${e.message}`);
    }
    connectionState = "close";
    qrDataUrl = null;
    conectar().catch((e) => log(`Erro ao reiniciar: ${e.message}`));
    return responder(res, 200, { status: "logged_out" });
  }

  return responder(res, 404, { status: "error", message: "Rota nao encontrada." });
});

servidor.listen(BRIDGE_PORT, "127.0.0.1", () => {
  log(`Ponte de WhatsApp ouvindo em http://127.0.0.1:${BRIDGE_PORT}`);
  log(`Webhook do AgentQuest: ${AGENTQUEST_URL}/api/webhook/whatsapp`);
  conectar().catch((e) => log(`Erro na conexao inicial: ${e.message}`));
});
