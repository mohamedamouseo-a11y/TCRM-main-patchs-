export const DEVELOPER_ROLE = "Developer" as const;

export const APP_USER_ROLES = [
  "Admin",
  DEVELOPER_ROLE,
  "SalesManager",
  "SalesAgent",
  "ColdSalesAgent",
  "TechnicalAccountManager",
  "AccountManager",
  "AccountManagerLead",
  "Viewer",
  "MediaBuyer",
  "BusinessDeveloper",
  "Moderator",
] as const;

export type AppUserRole = (typeof APP_USER_ROLES)[number];

// Legacy-only compatibility values. They are intentionally not selectable in the TCRM UI.
const LEGACY_ROLE_MAP: Record<string, string> = {
  admin: "Admin",
  developer: DEVELOPER_ROLE,
  superadmin: "Admin",
  super_admin: "Admin",
  superadministrator: "Admin",
  salesmanager: "SalesManager",
  sales_manager: "SalesManager",
  salesagent: "SalesAgent",
  sales_agent: "SalesAgent",
  coldsalesagent: "ColdSalesAgent",
  cold_sales_agent: "ColdSalesAgent",
  outboundsalesagent: "ColdSalesAgent",
  outbound_sales_agent: "ColdSalesAgent",
  technicalaccountmanager: "TechnicalAccountManager",
  technical_account_manager: "TechnicalAccountManager",
  tam: "TechnicalAccountManager",
  accountmanager: "AccountManager",
  account_manager: "AccountManager",
  accountmanagerlead: "AccountManagerLead",
  account_manager_lead: "AccountManagerLead",
  serviceadvisor: "ServiceAdvisor",
  service_advisor: "ServiceAdvisor",
  partsagent: "PartsAgent",
  parts_agent: "PartsAgent",
  crmfollowup: "CrmFollowUp",
  crm_followup: "CrmFollowUp",
  viewer: "Viewer",
  mediabuyer: "MediaBuyer",
  media_buyer: "MediaBuyer",
  businessdeveloper: "BusinessDeveloper",
  business_developer: "BusinessDeveloper",
  bd: "BusinessDeveloper",
  moderator: "Moderator",
  taramoderator: "Moderator",
  tara_moderator: "Moderator",
};

export function normalizeUserRole(role?: string | null): string {
  if (!role) return "SalesAgent";
  const raw = String(role).trim();
  if (APP_USER_ROLES.includes(raw as AppUserRole)) return raw;
  const key = raw.replace(/[\s_-]+/g, "").toLowerCase();
  return LEGACY_ROLE_MAP[key] ?? raw;
}

// TCRM_DEVELOPER_SUPERADMIN_UI_ACCESS_V1
export function normalizeAccessRole(role?: string | null): string {
  const normalized = normalizeUserRole(role);
  return normalized === DEVELOPER_ROLE ? "Admin" : normalized;
}

export function isAdminRole(role?: string | null): boolean {
  const normalized = normalizeUserRole(role);
  return normalized === "Admin" || normalized === DEVELOPER_ROLE;
}

// TCRM_DEVELOPER_ADMIN_SURFACE_ACCESS_V1
export function hasAdminSurfaceAccess(role?: string | null): boolean {
  return normalizeAccessRole(role) === "Admin";
}

export function isManagerRole(role?: string | null): boolean {
  const normalized = normalizeUserRole(role);
  return normalized === "Admin" || normalized === DEVELOPER_ROLE || normalized === "SalesManager";
}

export const SALES_AGENT_ROLES = ["SalesAgent", "ColdSalesAgent"] as const;

export function isSalesAgentRole(role?: string | null): boolean {
  return SALES_AGENT_ROLES.includes(normalizeUserRole(role) as (typeof SALES_AGENT_ROLES)[number]);
}

export function isTechnicalAccountManagerRole(role?: string | null): boolean {
  return normalizeUserRole(role) === "TechnicalAccountManager";
}

export function isMediaBuyerRole(role?: string | null): boolean {
  return normalizeUserRole(role) === "MediaBuyer";
}

export function isBusinessDeveloperRole(role?: string | null): boolean {
  return normalizeUserRole(role) === "BusinessDeveloper";
}

export function isTaraModeratorRole(role?: string | null): boolean {
  const key = String(role || "").trim().replace(/[\s_-]+/g, "").toLowerCase();
  return key === "moderator" || key === "taramoderator";
}

// TARA_PRODUCTION_HARDENING_V1_ITEM3_MODERATOR
// TARA_MODERATOR_V1R4_OPERATIONAL_ACCESS

// TARA_MODERATOR_V1R5_FINAL_SCOPE
