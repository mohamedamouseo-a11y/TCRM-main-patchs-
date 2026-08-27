export const ACCESS_EFFECTS = ["allow", "deny"] as const;
export type AccessEffect = (typeof ACCESS_EFFECTS)[number];

export const ACCESS_SCOPES = ["own", "assigned", "team", "department", "branch", "custom", "all"] as const;
export type AccessScope = (typeof ACCESS_SCOPES)[number];

export const ACCESS_OPERATORS = ["eq", "neq", "in", "not_in", "lt", "lte", "gt", "gte", "exists"] as const;
export type AccessOperator = (typeof ACCESS_OPERATORS)[number];

export type AccessRiskLevel = "low" | "medium" | "high" | "critical";

export interface AccessCondition {
  left: string;
  operator: AccessOperator;
  right?: unknown;
}

export interface AccessPermissionDefinition {
  key: string;
  module: string;
  resource: string;
  action: string;
  risk: AccessRiskLevel;
  description: string;
}

export interface AccessDecision {
  allowed: boolean;
  effect: AccessEffect;
  permission: string;
  scope: AccessScope | null;
  reason: string;
  source: string;
  matchedPolicies: Array<{
    source: string;
    sourceId?: number | string | null;
    effect: AccessEffect;
    scope: AccessScope;
  }>;
}

const p = (
  key: string,
  module: string,
  resource: string,
  action: string,
  risk: AccessRiskLevel,
  description: string,
): AccessPermissionDefinition => ({ key, module, resource, action, risk, description });

export const ACCESS_PERMISSION_REGISTRY: readonly AccessPermissionDefinition[] = [
  p("dashboard.view", "dashboard", "dashboard", "view", "low", "View CRM dashboard"),

  p("sales.leads.list", "sales", "leads", "list", "low", "List leads"),
  p("sales.leads.view", "sales", "leads", "view", "low", "View leads"),
  p("sales.leads.create", "sales", "leads", "create", "medium", "Create leads"),
  p("sales.leads.edit", "sales", "leads", "edit", "medium", "Edit leads"),
  p("sales.leads.delete", "sales", "leads", "delete", "high", "Delete leads"),
  p("sales.leads.assign", "sales", "leads", "assign", "high", "Assign leads"),
  p("sales.leads.reassign", "sales", "leads", "reassign", "high", "Reassign leads"),
  p("sales.leads.import", "sales", "leads", "import", "high", "Import leads"),
  p("sales.leads.export", "sales", "leads", "export", "critical", "Export leads"),

  p("sales.deals.list", "sales", "deals", "list", "low", "List deals"),
  p("sales.deals.view", "sales", "deals", "view", "low", "View deals"),
  p("sales.deals.create", "sales", "deals", "create", "medium", "Create deals"),
  p("sales.deals.edit", "sales", "deals", "edit", "medium", "Edit deals"),
  p("sales.deals.delete", "sales", "deals", "delete", "high", "Delete deals"),
  p("sales.deals.approve", "sales", "deals", "approve", "high", "Approve sensitive deal actions"),

  p("sales.quotations.list", "sales", "quotations", "list", "low", "List quotations"),
  p("sales.quotations.view", "sales", "quotations", "view", "low", "View quotations"),
  p("sales.quotations.create", "sales", "quotations", "create", "medium", "Create quotations"),
  p("sales.quotations.edit", "sales", "quotations", "edit", "medium", "Edit quotations"),
  p("sales.quotations.delete", "sales", "quotations", "delete", "high", "Delete quotations"),
  p("sales.quotations.approve", "sales", "quotations", "approve", "high", "Approve quotations"),
  p("sales.quotations.print", "sales", "quotations", "print", "medium", "Print quotations"),
  p("sales.quotations.export", "sales", "quotations", "export", "high", "Export quotations"),

  p("clients.records.list", "clients", "records", "list", "low", "List clients"),
  p("clients.records.view", "clients", "records", "view", "low", "View clients"),
  p("clients.records.create", "clients", "records", "create", "medium", "Create clients"),
  p("clients.records.edit", "clients", "records", "edit", "medium", "Edit clients"),
  p("clients.records.delete", "clients", "records", "delete", "critical", "Delete clients"),
  p("clients.records.restore", "clients", "records", "restore", "high", "Restore clients"),
  p("clients.records.export", "clients", "records", "export", "critical", "Export client data"),

  p("clients.contracts.view", "clients", "contracts", "view", "medium", "View contracts"),
  p("clients.contracts.create", "clients", "contracts", "create", "high", "Create contracts"),
  p("clients.contracts.edit", "clients", "contracts", "edit", "high", "Edit contracts"),
  p("clients.contracts.download", "clients", "contracts", "download", "high", "Download contracts"),
  p("clients.contracts.approve", "clients", "contracts", "approve", "critical", "Approve contracts"),

  p("clients.renewals.view", "clients", "renewals", "view", "medium", "View renewals"),
  p("clients.renewals.edit", "clients", "renewals", "edit", "high", "Edit renewals"),
  p("clients.renewals.approve", "clients", "renewals", "approve", "critical", "Approve renewals"),

  p("marketing.campaigns.list", "marketing", "campaigns", "list", "low", "List campaigns"),
  p("marketing.campaigns.view", "marketing", "campaigns", "view", "low", "View campaigns"),
  p("marketing.campaigns.create", "marketing", "campaigns", "create", "medium", "Create campaigns"),
  p("marketing.campaigns.edit", "marketing", "campaigns", "edit", "high", "Edit campaigns"),
  p("marketing.campaigns.publish", "marketing", "campaigns", "publish", "critical", "Publish campaigns"),
  p("marketing.campaigns.budget_change", "marketing", "campaigns", "budget_change", "critical", "Change campaign budgets"),
  p("marketing.campaigns.delete", "marketing", "campaigns", "delete", "critical", "Delete campaigns"),
  p("marketing.campaigns.export", "marketing", "campaigns", "export", "high", "Export campaign data"),

  p("communications.inbox.view", "communications", "inbox", "view", "medium", "View inbox"),
  p("communications.inbox.reply", "communications", "inbox", "reply", "medium", "Reply from inbox"),
  p("communications.chat.view", "communications", "chat", "view", "low", "View central chat"),
  p("communications.chat.send", "communications", "chat", "send", "medium", "Send chat messages"),

  p("files.crm.list", "files", "crm_files", "list", "low", "List CRM files"),
  p("files.crm.view", "files", "crm_files", "view", "medium", "View CRM files"),
  p("files.crm.upload", "files", "crm_files", "upload", "medium", "Upload CRM files"),
  p("files.crm.download", "files", "crm_files", "download", "high", "Download CRM files"),
  p("files.crm.share", "files", "crm_files", "share", "critical", "Share CRM files publicly"),
  p("files.crm.delete", "files", "crm_files", "delete", "high", "Delete CRM files"),

  p("workspace.tws.view", "workspace", "tws", "view", "low", "Open TWS workspace"),
  p("workspace.tws.manage", "workspace", "tws", "manage", "high", "Manage TWS workspace"),
  p("hr.thrs.view", "hr", "thrs", "view", "medium", "View THRS"),
  p("hr.thrs.manage", "hr", "thrs", "manage", "high", "Manage THRS"),

  p("ai_staff.tara.execute", "ai_staff", "tara", "execute", "high", "Execute Tara actions"),
  p("ai_staff.zaghloul.execute", "ai_staff", "zaghloul", "execute", "high", "Execute Zaghloul actions"),
  p("ai_staff.felfel.execute", "ai_staff", "felfel", "execute", "high", "Execute Felfel actions"),
  p("ai_staff.darwish.execute", "ai_staff", "darwish", "execute", "high", "Execute Darwish actions"),
  p("ai_staff.shawky.execute", "ai_staff", "shawky", "execute", "high", "Execute Shawky actions"),
  p("ai_staff.wadie.execute", "ai_staff", "wadie", "execute", "high", "Execute Wadie actions"),
  p("ai_staff.rakan.execute", "ai_staff", "rakan", "execute", "critical", "Execute Rakan actions"),

  p("reports.operational.view", "reports", "operational", "view", "medium", "View operational reports"),
  p("reports.operational.export", "reports", "operational", "export", "high", "Export operational reports"),
  p("reports.financial.view", "reports", "financial", "view", "high", "View financial reports"),
  p("reports.financial.export", "reports", "financial", "export", "critical", "Export financial reports"),

  p("settings.general.view", "settings", "general", "view", "low", "View settings"),
  p("settings.general.manage", "settings", "general", "manage", "high", "Manage settings"),
  p("settings.users.view", "settings", "users", "view", "high", "View users"),
  p("settings.users.manage", "settings", "users", "manage", "critical", "Manage users"),
  p("settings.integrations.view", "settings", "integrations", "view", "high", "View integrations"),
  p("settings.integrations.manage", "settings", "integrations", "manage", "critical", "Manage integrations"),
  p("settings.audit.view", "settings", "audit", "view", "high", "View audit logs"),

  p("security.access.overview", "security", "access", "overview", "high", "View access-control overview"),
  p("security.access.roles.view", "security", "access_roles", "view", "high", "View roles"),
  p("security.access.roles.manage", "security", "access_roles", "manage", "critical", "Manage roles and permissions"),
  p("security.access.users.manage", "security", "access_users", "manage", "critical", "Assign roles and user overrides"),
  p("security.access.temporary.manage", "security", "temporary_access", "manage", "critical", "Manage temporary access"),
  p("security.access.simulate", "security", "access_simulator", "simulate", "high", "Simulate access decisions"),
  p("security.access.decisions.view", "security", "access_decisions", "view", "high", "View access decision logs"),
] as const;

export const ACCESS_PERMISSION_KEYS = ACCESS_PERMISSION_REGISTRY.map((item) => item.key);
