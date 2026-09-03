export const APP_USER_ROLES = [
  "Admin",
  "Developer",
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

// Legacy-only compatibility values. They are intentionally NOT exposed as active TCRM roles.
const LEGACY_ROLE_MAP: Record<string, string> = {
  admin: "Admin",
  developer: "Developer",
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
  const key = raw.replace(/\s+/g, "").toLowerCase();
  return LEGACY_ROLE_MAP[key] ?? raw;
}

export function isAdminRole(role?: string | null): boolean {
  const normalized = normalizeUserRole(role);
  return normalized === "Admin" || normalized === "Developer" || normalized === "Moderator";
}

export function isManagerRole(role?: string | null): boolean {
  const normalized = normalizeUserRole(role);
  return normalized === "Admin" || normalized === "Developer" || normalized === "SalesManager" || normalized === "Moderator";
}

export function isDeveloperRole(role?: string | null): boolean {
  return normalizeUserRole(role) === "Developer";
}

export const SALES_AGENT_ROLES = ["SalesAgent", "ColdSalesAgent"] as const;

/** Sales permissions/scope shared by inbound and cold/outbound sales agents. */
export function isSalesAgentRole(role?: string | null): boolean {
  return SALES_AGENT_ROLES.includes(normalizeUserRole(role) as (typeof SALES_AGENT_ROLES)[number]);
}

/** Lead-generation forms may auto-distribute only to the regular inbound sales pool. */
export function isLeadGenerationAutoDistributionRole(role?: string | null): boolean {
  return normalizeUserRole(role) === "SalesAgent";
}

export function isTechnicalAccountManagerRole(role?: string | null): boolean {
  return normalizeUserRole(role) === "TechnicalAccountManager";
}

export function isMediaBuyerRole(role?: string | null): boolean {
  return normalizeUserRole(role) === "MediaBuyer";
}

export function isViewerRole(role?: string | null): boolean {
  return normalizeUserRole(role) === "Viewer";
}

/** Legacy compatibility only; these roles are not selectable in TCRM anymore. */
export function isAfterSalesRole(role?: string | null): boolean {
  const normalized = normalizeUserRole(role);
  return normalized === "ServiceAdvisor" || normalized === "PartsAgent" || normalized === "CrmFollowUp";
}

export function isTaraModeratorRole(role?: string | null): boolean {
  return normalizeUserRole(role) === "Moderator";
}

// TARA_PRODUCTION_HARDENING_V1_ITEM3_MODERATOR
// TARA_MODERATOR_V1R4_OPERATIONAL_ACCESS
