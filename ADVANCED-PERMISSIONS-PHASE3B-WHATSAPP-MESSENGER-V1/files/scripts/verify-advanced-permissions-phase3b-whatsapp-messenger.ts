import fs from "node:fs";

function read(file: string) { return fs.readFileSync(file, "utf8"); }
function must(text: string, needle: string, label: string) {
  if (!text.includes(needle)) throw new Error(`${label}: missing ${needle}`);
}

const trpc = read("server/_core/trpc.ts");
for (const name of ["whatsappViewScope","whatsappSendScope","whatsappManageScope","messengerViewScope","messengerSendScope","messengerManageScope"]) must(trpc, name, "trpc");

const routers = read("server/routers.ts");
for (const name of ["whatsappViewScope","whatsappSendScope","whatsappManageScope"]) must(routers, name, "whatsapp wiring");
for (const guard of ["getWAGatewayStatus","listWAGatewayChats","sendWAGatewayText","updateWAGatewayAccountAccess"]) must(routers, guard, "existing WhatsApp security/service wiring");

const messenger = read("server/modules/messenger/router.messenger.ts");
for (const name of ["messengerViewScope","messengerSendScope","messengerManageScope"]) must(messenger, name, "messenger wiring");
for (const guard of ["adminProcedure","protectedProcedure","getChatMessages","createChatMessage"]) must(messenger, guard, "existing Messenger security/service wiring");

for (const forbidden of ["saveTaraSettings","getTaraDashboard","getTaraVoiceSettingsForUi","saveTaraSocialApiSettings","getMetaWhatsappTechnicalSettings"]) {
  if (routers.includes(`${forbidden}.use(`)) throw new Error(`Tara surface appears permission-wired unexpectedly: ${forbidden}`);
}

console.log(JSON.stringify({
  ok: true,
  phase: "3B-whatsapp-messenger-v1",
  verified: ["whatsapp-view","whatsapp-send","whatsapp-manage","messenger-view","messenger-send","messenger-manage","legacy-guards-preserved"],
  excluded: ["tara","meta-tiktok-google-ads","meetings-felfel-tam"]
}, null, 2));