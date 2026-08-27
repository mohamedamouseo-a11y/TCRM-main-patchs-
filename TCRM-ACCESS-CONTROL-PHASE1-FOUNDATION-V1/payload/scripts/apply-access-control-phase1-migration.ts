import { sql } from "drizzle-orm";
import { ACCESS_PERMISSION_REGISTRY } from "../shared/accessControl";
import { getDb } from "../server/db";

const apply = process.argv.includes("--apply");

const statements = [
  `CREATE TABLE IF NOT EXISTS access_roles (
    id INT NOT NULL AUTO_INCREMENT,
    role_key VARCHAR(64) NOT NULL,
    name VARCHAR(120) NOT NULL,
    description VARCHAR(500) NULL,
    is_system TINYINT NOT NULL DEFAULT 0,
    is_active TINYINT NOT NULL DEFAULT 1,
    version INT NOT NULL DEFAULT 1,
    created_by INT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_access_roles_key (role_key),
    KEY idx_access_roles_active (is_active)
  ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci`,

  `CREATE TABLE IF NOT EXISTS access_permissions (
    id INT NOT NULL AUTO_INCREMENT,
    permission_key VARCHAR(160) NOT NULL,
    module VARCHAR(64) NOT NULL,
    resource VARCHAR(80) NOT NULL,
    action VARCHAR(64) NOT NULL,
    risk_level ENUM('low','medium','high','critical') NOT NULL DEFAULT 'low',
    description VARCHAR(500) NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_access_permissions_key (permission_key),
    KEY idx_access_permissions_module (module,resource)
  ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci`,

  `CREATE TABLE IF NOT EXISTS access_role_permissions (
    role_id INT NOT NULL,
    permission_id INT NOT NULL,
    effect ENUM('allow','deny') NOT NULL DEFAULT 'deny',
    scope ENUM('own','assigned','team','department','branch','custom','all') NOT NULL DEFAULT 'own',
    conditions_json JSON NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (role_id,permission_id),
    KEY idx_access_role_permissions_permission (permission_id),
    CONSTRAINT fk_access_role_permissions_role FOREIGN KEY (role_id) REFERENCES access_roles(id) ON DELETE CASCADE,
    CONSTRAINT fk_access_role_permissions_permission FOREIGN KEY (permission_id) REFERENCES access_permissions(id) ON DELETE CASCADE
  ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci`,

  `CREATE TABLE IF NOT EXISTS access_user_roles (
    user_id INT NOT NULL,
    role_id INT NOT NULL,
    assigned_by INT NULL,
    valid_from DATETIME NULL,
    valid_to DATETIME NULL,
    source VARCHAR(32) NOT NULL DEFAULT 'manual',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id,role_id),
    KEY idx_access_user_roles_role (role_id),
    KEY idx_access_user_roles_validity (user_id,valid_to),
    CONSTRAINT fk_access_user_roles_role FOREIGN KEY (role_id) REFERENCES access_roles(id) ON DELETE CASCADE
  ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci`,

  `CREATE TABLE IF NOT EXISTS access_user_overrides (
    id INT NOT NULL AUTO_INCREMENT,
    user_id INT NOT NULL,
    permission_id INT NOT NULL,
    effect ENUM('allow','deny') NOT NULL DEFAULT 'deny',
    scope ENUM('own','assigned','team','department','branch','custom','all') NOT NULL DEFAULT 'own',
    conditions_json JSON NULL,
    reason VARCHAR(500) NULL,
    expires_at DATETIME NULL,
    created_by INT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_access_user_override (user_id,permission_id),
    KEY idx_access_user_overrides_expiry (user_id,expires_at),
    CONSTRAINT fk_access_user_overrides_permission FOREIGN KEY (permission_id) REFERENCES access_permissions(id) ON DELETE CASCADE
  ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci`,

  `CREATE TABLE IF NOT EXISTS access_temporary_grants (
    id INT NOT NULL AUTO_INCREMENT,
    user_id INT NOT NULL,
    permission_id INT NOT NULL,
    scope ENUM('own','assigned','team','department','branch','custom','all') NOT NULL DEFAULT 'own',
    conditions_json JSON NULL,
    starts_at DATETIME NOT NULL,
    expires_at DATETIME NOT NULL,
    reason VARCHAR(500) NOT NULL,
    approved_by INT NULL,
    created_by INT NULL,
    revoked_at DATETIME NULL,
    revoked_by INT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY idx_access_temporary_grants_active (user_id,starts_at,expires_at,revoked_at),
    KEY idx_access_temporary_grants_permission (permission_id),
    CONSTRAINT fk_access_temporary_grants_permission FOREIGN KEY (permission_id) REFERENCES access_permissions(id) ON DELETE CASCADE
  ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci`,

  `CREATE TABLE IF NOT EXISTS access_org_units (
    id INT NOT NULL AUTO_INCREMENT,
    parent_id INT NULL,
    unit_type ENUM('organization','branch','department','team') NOT NULL,
    unit_key VARCHAR(80) NOT NULL,
    name VARCHAR(160) NOT NULL,
    is_active TINYINT NOT NULL DEFAULT 1,
    metadata_json JSON NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_access_org_units_key (unit_key),
    KEY idx_access_org_units_parent (parent_id),
    CONSTRAINT fk_access_org_units_parent FOREIGN KEY (parent_id) REFERENCES access_org_units(id) ON DELETE SET NULL
  ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci`,

  `CREATE TABLE IF NOT EXISTS access_user_org_units (
    user_id INT NOT NULL,
    org_unit_id INT NOT NULL,
    relation_type ENUM('member','manager','owner') NOT NULL DEFAULT 'member',
    is_primary TINYINT NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id,org_unit_id),
    KEY idx_access_user_org_units_unit (org_unit_id),
    CONSTRAINT fk_access_user_org_units_unit FOREIGN KEY (org_unit_id) REFERENCES access_org_units(id) ON DELETE CASCADE
  ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci`,

  `CREATE TABLE IF NOT EXISTS access_decision_logs (
    id BIGINT NOT NULL AUTO_INCREMENT,
    user_id INT NOT NULL,
    permission_key VARCHAR(160) NOT NULL,
    resource_type VARCHAR(80) NULL,
    resource_id VARCHAR(120) NULL,
    effect ENUM('allow','deny') NOT NULL,
    scope ENUM('own','assigned','team','department','branch','custom','all') NULL,
    source VARCHAR(64) NOT NULL,
    reason VARCHAR(160) NOT NULL,
    matched_policy_json JSON NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY idx_access_decision_logs_user_time (user_id,created_at),
    KEY idx_access_decision_logs_permission_time (permission_key,created_at),
    KEY idx_access_decision_logs_effect_time (effect,created_at)
  ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci`,
];

const systemRoles = [
  ["Admin","Administrator","Full TCRM access-control compatibility role"],
  ["Developer","Developer","Developer compatibility role; starts empty"],
  ["SalesManager","Sales Manager","Sales management compatibility role"],
  ["SalesAgent","Sales Agent","Sales compatibility role"],
  ["ColdSalesAgent","Cold Sales Agent","Outbound sales compatibility role"],
  ["AccountManager","Account Manager","Account-management compatibility role"],
  ["AccountManagerLead","Account Manager Lead","Account-management lead compatibility role"],
  ["MediaBuyer","Media Buyer","Media buying compatibility role"],
  ["Viewer","Viewer","Read-only compatibility role"],
  ["Moderator","Moderator","Moderator compatibility role"],
] as const;

async function run() {
  if (!apply) {
    console.log("[AccessControl] DRY RUN");
    console.log(`Would create/verify ${statements.length} tables.`);
    console.log(`Would seed ${ACCESS_PERMISSION_REGISTRY.length} permission definitions.`);
    console.log("Run with --apply to execute.");
    return;
  }

  const db = await getDb();
  if (!db) throw new Error("DATABASE_URL is not configured or database connection failed");

  for (const statement of statements) await db.execute(sql.raw(statement));

  for (const definition of ACCESS_PERMISSION_REGISTRY) {
    await db.execute(sql`
      INSERT INTO access_permissions (permission_key,module,resource,action,risk_level,description,created_at,updated_at)
      VALUES (${definition.key},${definition.module},${definition.resource},${definition.action},${definition.risk},${definition.description},NOW(),NOW())
      ON DUPLICATE KEY UPDATE module=VALUES(module),resource=VALUES(resource),action=VALUES(action),risk_level=VALUES(risk_level),description=VALUES(description),updated_at=NOW()
    `);
  }

  for (const [roleKey,name,description] of systemRoles) {
    await db.execute(sql`
      INSERT INTO access_roles (role_key,name,description,is_system,is_active,version,created_at,updated_at)
      VALUES (${roleKey},${name},${description},1,1,1,NOW(),NOW())
      ON DUPLICATE KEY UPDATE name=VALUES(name),description=VALUES(description),is_system=1,is_active=1,updated_at=NOW()
    `);
  }

  // Bootstrap only Admin. Every operational role remains empty until reviewed.
  await db.execute(sql`
    INSERT INTO access_role_permissions (role_id,permission_id,effect,scope,conditions_json,created_at,updated_at)
    SELECT r.id,p.id,'allow','all',JSON_ARRAY(),NOW(),NOW()
    FROM access_roles r CROSS JOIN access_permissions p
    WHERE r.role_key='Admin'
    ON DUPLICATE KEY UPDATE effect='allow',scope='all',conditions_json=JSON_ARRAY(),updated_at=NOW()
  `);

  console.log(`[AccessControl] Phase 1 migration complete. ${ACCESS_PERMISSION_REGISTRY.length} permissions are registered.`);
}

run().catch((error) => {
  console.error("[AccessControl] migration failed", error);
  process.exitCode = 1;
});
