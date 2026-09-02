-- Darwish Phase 4 — Human feedback + smart matching audit.
-- Audit-only. Does not enable automatic linking, remapping, outbound actions, or model training.
CREATE TABLE IF NOT EXISTS darwish_group_matching_feedback (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  client_id INT UNSIGNED NOT NULL,
  actor_user_id INT UNSIGNED NOT NULL,
  decision_type VARCHAR(40) NOT NULL,
  selected_group_jid VARCHAR(255) NOT NULL,
  selected_evolution_instance VARCHAR(160) NOT NULL,
  recommendation_available BOOLEAN NOT NULL DEFAULT FALSE,
  recommended_group_jid VARCHAR(255) NULL,
  recommended_evolution_instance VARCHAR(160) NULL,
  selected_is_recommended BOOLEAN NOT NULL DEFAULT FALSE,
  selected_confidence DECIMAL(5,2) NULL,
  selected_confidence_level VARCHAR(16) NULL,
  selected_signals JSON NULL,
  recommended_confidence DECIMAL(5,2) NULL,
  recommended_confidence_level VARCHAR(16) NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_darwish_group_feedback_client (client_id, created_at),
  KEY idx_darwish_group_feedback_actor (actor_user_id, created_at),
  KEY idx_darwish_group_feedback_decision (decision_type, created_at),
  KEY idx_darwish_group_feedback_selected (selected_evolution_instance, selected_group_jid),
  KEY idx_darwish_group_feedback_recommended (recommended_evolution_instance, recommended_group_jid)
);
