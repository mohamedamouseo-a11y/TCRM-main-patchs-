import mysql, { type ResultSetHeader, type RowDataPacket } from "mysql2/promise";
import {
  encryptDarwishAiProviderSecret,
  normalizeDarwishAiProviderDraft,
  normalizeDarwishAiProviderModelDraft,
} from "./darwishAiProviderFoundationService";

export const DARWISH_AI_PROVIDER_SETTINGS_STATUS = "phase3_settings_ready_not_integrated" as const;
type JsonObject = Record<string, unknown>;
let pool: ReturnType<typeof mysql.createPool> | null = null;

function db() {
  const url = process.env.DATABASE_URL?.trim();
  if (!url) throw new Error("DATABASE_URL is required");
  return pool ??= mysql.createPool(url);
}
const n = (v: unknown) => Number(v);
const b = (v: unknown) => Boolean(Number(v));
const j = (v: unknown) => {
  if (v == null || v === "") return null;
  if (typeof v === "object") return v as JsonObject;
  try { return JSON.parse(String(v)); } catch { return null; }
};
const js = (v: unknown) => v == null ? null : JSON.stringify(v);
function id(v: unknown, field = "id") {
  const x = Number(v);
  if (!Number.isSafeInteger(x) || x <= 0) throw new Error(`${field} must be a positive integer`);
  return x;
}
function boundedInt(v: unknown, field: string, min: number, max: number) {
  const x = Number(v);
  if (!Number.isInteger(x) || x < min || x > max) throw new Error(`${field} is invalid`);
  return x;
}
function text(v: unknown, field: string, max: number) {
  const x = String(v ?? "").trim();
  if (!x || x.length > max) throw new Error(`${field} is invalid`);
  return x;
}
function config(v: unknown) {
  if (v == null) return null;
  if (typeof v !== "object" || Array.isArray(v)) throw new Error("config must be an object");
  return v as JsonObject;
}

export async function getDarwishAiProviderSettings() {
  const q = db();
  const [[providers], [models], [secrets], [policies], [targets]] = await Promise.all([
    q.query<RowDataPacket[]>("SELECT id,provider_key,display_name,adapter_type,base_url,enabled,config_json,created_at,updated_at FROM darwish_ai_providers ORDER BY display_name,id"),
    q.query<RowDataPacket[]>("SELECT id,provider_id,model_key,display_name,enabled,config_json,created_at,updated_at FROM darwish_ai_provider_models ORDER BY provider_id,display_name,model_key,id"),
    q.query<RowDataPacket[]>("SELECT id,provider_id,secret_key,key_version,updated_at FROM darwish_ai_provider_secrets ORDER BY provider_id,secret_key,id"),
    q.query<RowDataPacket[]>("SELECT id,route_key,display_name,selection_strategy,enabled,max_attempts,timeout_ms,config_json,created_at,updated_at FROM darwish_ai_routing_policies ORDER BY route_key,id"),
    q.query<RowDataPacket[]>("SELECT id,policy_id,provider_id,model_id,priority,weight,enabled,timeout_ms,config_json,created_at,updated_at FROM darwish_ai_routing_targets ORDER BY policy_id,priority,id"),
  ]);
  return {
    status: DARWISH_AI_PROVIDER_SETTINGS_STATUS,
    providers: providers.map(r => ({ id:n(r.id), providerKey:String(r.provider_key), displayName:String(r.display_name), adapterType:String(r.adapter_type), baseUrl:r.base_url == null ? null : String(r.base_url), enabled:b(r.enabled), config:j(r.config_json), createdAt:r.created_at, updatedAt:r.updated_at })),
    models: models.map(r => ({ id:n(r.id), providerId:n(r.provider_id), modelKey:String(r.model_key), displayName:r.display_name == null ? null : String(r.display_name), enabled:b(r.enabled), config:j(r.config_json), createdAt:r.created_at, updatedAt:r.updated_at })),
    secrets: secrets.map(r => ({ id:n(r.id), providerId:n(r.provider_id), secretKey:String(r.secret_key), configured:true as const, keyVersion:String(r.key_version), updatedAt:r.updated_at })),
    policies: policies.map(r => ({ id:n(r.id), routeKey:String(r.route_key), displayName:String(r.display_name), selectionStrategy:r.selection_strategy === "weighted_random" ? "weighted_random" as const : "priority" as const, enabled:b(r.enabled), maxAttempts:n(r.max_attempts), timeoutMs:n(r.timeout_ms), config:j(r.config_json), createdAt:r.created_at, updatedAt:r.updated_at })),
    targets: targets.map(r => ({ id:n(r.id), policyId:n(r.policy_id), providerId:n(r.provider_id), modelId:n(r.model_id), priority:n(r.priority), weight:n(r.weight), enabled:b(r.enabled), timeoutMs:r.timeout_ms == null ? null : n(r.timeout_ms), config:j(r.config_json), createdAt:r.created_at, updatedAt:r.updated_at })),
    security: { secretsEncryptedAtRest:true, plaintextSecretsReturned:false },
    integration: { darwishAiCallsRoutedThroughRegistry:false, outboundActions:0 },
  };
}

export async function saveDarwishAiProvider(input: any) {
  const x = normalizeDarwishAiProviderDraft(input);
  if (input.id) {
    const providerId = id(input.id);
    await db().execute("UPDATE darwish_ai_providers SET provider_key=?,display_name=?,adapter_type=?,base_url=?,enabled=?,config_json=? WHERE id=?", [x.providerKey,x.displayName,x.adapterType,x.baseUrl,x.enabled,js(x.config),providerId]);
    return { id: providerId };
  }
  const [r] = await db().execute<ResultSetHeader>("INSERT INTO darwish_ai_providers (provider_key,display_name,adapter_type,base_url,enabled,config_json) VALUES (?,?,?,?,?,?)", [x.providerKey,x.displayName,x.adapterType,x.baseUrl,x.enabled,js(x.config)]);
  return { id:n(r.insertId) };
}
export async function deleteDarwishAiProvider(providerIdRaw: number) {
  const providerId = id(providerIdRaw);
  const [rows] = await db().query<RowDataPacket[]>("SELECT COUNT(*) total FROM darwish_ai_routing_targets WHERE provider_id=?", [providerId]);
  if (n(rows[0]?.total) > 0) throw new Error("Remove routing targets before deleting this provider");
  const c = await db().getConnection();
  try {
    await c.beginTransaction();
    await c.execute("DELETE FROM darwish_ai_provider_secrets WHERE provider_id=?", [providerId]);
    await c.execute("DELETE FROM darwish_ai_provider_models WHERE provider_id=?", [providerId]);
    await c.execute("DELETE FROM darwish_ai_providers WHERE id=?", [providerId]);
    await c.commit();
  } catch (e) { await c.rollback(); throw e; } finally { c.release(); }
  return { deleted:true };
}
export async function saveDarwishAiProviderModel(input: any) {
  const providerId = id(input.providerId, "providerId");
  const x = normalizeDarwishAiProviderModelDraft(input);
  if (input.id) {
    const modelId = id(input.id);
    await db().execute("UPDATE darwish_ai_provider_models SET provider_id=?,model_key=?,display_name=?,enabled=?,config_json=? WHERE id=?", [providerId,x.modelKey,x.displayName,x.enabled,js(x.config),modelId]);
    return { id:modelId };
  }
  const [r] = await db().execute<ResultSetHeader>("INSERT INTO darwish_ai_provider_models (provider_id,model_key,display_name,enabled,config_json) VALUES (?,?,?,?,?)", [providerId,x.modelKey,x.displayName,x.enabled,js(x.config)]);
  return { id:n(r.insertId) };
}
export async function deleteDarwishAiProviderModel(modelIdRaw: number) {
  const modelId = id(modelIdRaw);
  const [rows] = await db().query<RowDataPacket[]>("SELECT COUNT(*) total FROM darwish_ai_routing_targets WHERE model_id=?", [modelId]);
  if (n(rows[0]?.total) > 0) throw new Error("Remove routing targets before deleting this model");
  await db().execute("DELETE FROM darwish_ai_provider_models WHERE id=?", [modelId]);
  return { deleted:true };
}
export async function setDarwishAiProviderSecret(input: any) {
  const providerId = id(input.providerId, "providerId");
  const encrypted = encryptDarwishAiProviderSecret(input.secretKey, input.value);
  await db().execute("INSERT INTO darwish_ai_provider_secrets (provider_id,secret_key,encrypted_value,key_version) VALUES (?,?,?,?) ON DUPLICATE KEY UPDATE encrypted_value=VALUES(encrypted_value),key_version=VALUES(key_version),updated_at=CURRENT_TIMESTAMP", [providerId,encrypted.secretKey,encrypted.encryptedValue,encrypted.keyVersion]);
  return { providerId, secretKey:encrypted.secretKey, configured:true as const };
}
export async function deleteDarwishAiProviderSecret(input: any) {
  await db().execute("DELETE FROM darwish_ai_provider_secrets WHERE provider_id=? AND secret_key=?", [id(input.providerId,"providerId"),text(input.secretKey,"secretKey",128)]);
  return { deleted:true };
}
export async function saveDarwishAiRoutingPolicy(input: any) {
  const x = {
    routeKey:text(input.routeKey,"routeKey",128).toLowerCase(),
    displayName:text(input.displayName,"displayName",191),
    selectionStrategy:input.selectionStrategy,
    enabled:input.enabled ?? true,
    maxAttempts:boundedInt(input.maxAttempts,"maxAttempts",1,100),
    timeoutMs:boundedInt(input.timeoutMs,"timeoutMs",100,600000),
    config:config(input.config),
  };
  if (!/^[a-z0-9][a-z0-9._-]{0,127}$/.test(x.routeKey)) throw new Error("routeKey contains unsupported characters");
  if (input.id) {
    const policyId = id(input.id);
    await db().execute("UPDATE darwish_ai_routing_policies SET route_key=?,display_name=?,selection_strategy=?,enabled=?,max_attempts=?,timeout_ms=?,config_json=? WHERE id=?", [x.routeKey,x.displayName,x.selectionStrategy,x.enabled,x.maxAttempts,x.timeoutMs,js(x.config),policyId]);
    return { id:policyId };
  }
  const [r] = await db().execute<ResultSetHeader>("INSERT INTO darwish_ai_routing_policies (route_key,display_name,selection_strategy,enabled,max_attempts,timeout_ms,config_json) VALUES (?,?,?,?,?,?,?)", [x.routeKey,x.displayName,x.selectionStrategy,x.enabled,x.maxAttempts,x.timeoutMs,js(x.config)]);
  return { id:n(r.insertId) };
}
export async function deleteDarwishAiRoutingPolicy(policyIdRaw: number) {
  const policyId = id(policyIdRaw);
  const c = await db().getConnection();
  try {
    await c.beginTransaction();
    await c.execute("DELETE FROM darwish_ai_routing_targets WHERE policy_id=?", [policyId]);
    await c.execute("DELETE FROM darwish_ai_routing_policies WHERE id=?", [policyId]);
    await c.commit();
  } catch (e) { await c.rollback(); throw e; } finally { c.release(); }
  return { deleted:true };
}
export async function saveDarwishAiRoutingTarget(input: any) {
  const x = {
    policyId:id(input.policyId,"policyId"), providerId:id(input.providerId,"providerId"), modelId:id(input.modelId,"modelId"),
    priority:boundedInt(input.priority,"priority",0,1000000), weight:boundedInt(input.weight,"weight",1,1000000),
    enabled:input.enabled ?? true, timeoutMs:input.timeoutMs == null ? null : boundedInt(input.timeoutMs,"timeoutMs",100,600000), config:config(input.config),
  };
  const [m] = await db().query<RowDataPacket[]>("SELECT provider_id FROM darwish_ai_provider_models WHERE id=? LIMIT 1",[x.modelId]);
  if (!m.length || n(m[0].provider_id) !== x.providerId) throw new Error("Selected model does not belong to selected provider");
  if (input.id) {
    const targetId = id(input.id);
    await db().execute("UPDATE darwish_ai_routing_targets SET policy_id=?,provider_id=?,model_id=?,priority=?,weight=?,enabled=?,timeout_ms=?,config_json=? WHERE id=?", [x.policyId,x.providerId,x.modelId,x.priority,x.weight,x.enabled,x.timeoutMs,js(x.config),targetId]);
    return { id:targetId };
  }
  const [r] = await db().execute<ResultSetHeader>("INSERT INTO darwish_ai_routing_targets (policy_id,provider_id,model_id,priority,weight,enabled,timeout_ms,config_json) VALUES (?,?,?,?,?,?,?,?)", [x.policyId,x.providerId,x.modelId,x.priority,x.weight,x.enabled,x.timeoutMs,js(x.config)]);
  return { id:n(r.insertId) };
}
export async function deleteDarwishAiRoutingTarget(targetIdRaw: number) {
  await db().execute("DELETE FROM darwish_ai_routing_targets WHERE id=?", [id(targetIdRaw)]);
  return { deleted:true };
}
export function getDarwishAiProviderSettingsState() {
  return {
    status:DARWISH_AI_PROVIDER_SETTINGS_STATUS,
    providersHardcoded:false, modelsHardcoded:false, settingsHardcoded:false,
    secretsEncryptedAtRest:true, plaintextSecretsReturned:false,
    basicUiSupported:true, advancedUiCollapsible:true, routingConfigurationSupported:true,
    darwishAiCallsRoutedThroughRegistry:false, providerAdaptersInvokedByThisPhase:false, outboundActions:0,
  } as const;
}
