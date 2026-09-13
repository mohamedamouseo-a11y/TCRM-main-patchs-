#!/usr/bin/env python3
from pathlib import Path
import shutil
import sys
import time

ROOT = Path.cwd()
TSX = ROOT / "client/src/pages/LeadProfile.tsx"
CSS = ROOT / "client/src/lead-profile-premium-v2-4.css"
BACKUP_DIR = ROOT / ".tcrm-recovery-backups"
V23_MARKER = "TCRM_LEAD_PROFILE_PREMIUM_V2_3_REGRESSION_RECOVERY"
MARKER = "TCRM_LEAD_PROFILE_PREMIUM_V2_4_REFERENCE_FIDELITY_PASS"

if not TSX.exists():
    raise SystemExit("ERROR: client/src/pages/LeadProfile.tsx not found. Run from the live TCRM project root.")

src = TSX.read_text(encoding="utf-8")
required = [
    V23_MARKER,
    'import "../lead-profile-premium-v2-3.css";',
    'tcrm-lead-profile-premium-v2-3',
    'className="tcrm-lp-v22-hero-topline',
    'className="tcrm-lp-v22-identity',
    'className="tcrm-lp-v22-actions',
    'className="tcrm-lp-v2-signals"',
    'className="tcrm-lp-v2-overview-grid"',
    'className="tcrm-lp-v2-overview-center"',
    'className="tcrm-lp-v21-overview-right"',
]
for token in required:
    if token not in src:
        raise SystemExit(f"ERROR: required V2.3 anchor missing: {token}")

if MARKER in src and CSS.exists():
    print("PATCH=ALREADY_APPLIED")
    print("LEAD_PROFILE_PREMIUM_V2_4=YES")
    sys.exit(0)

BACKUP_DIR.mkdir(exist_ok=True)
stamp = time.strftime("%Y%m%d-%H%M%S")
backup = BACKUP_DIR / f"LeadProfile.tsx.{stamp}.lead-profile-v2-4.bak"
shutil.copy2(TSX, backup)

# -----------------------------------------------------------------------------
# 1) Layer V2.4 after V2.3. V2.4 is a reference-fidelity pass only.
# -----------------------------------------------------------------------------
import_anchor = 'import "../lead-profile-premium-v2-3.css";'
if 'import "../lead-profile-premium-v2-4.css";' not in src:
    src = src.replace(import_anchor, import_anchor + '\nimport "../lead-profile-premium-v2-4.css";', 1)

if MARKER not in src:
    src = src.replace(f"// {V23_MARKER}", f"// {V23_MARKER}\n// {MARKER}", 1)

root_old = 'tcrm-lead-profile-premium-v2-1 tcrm-lead-profile-premium-v2-2 tcrm-lead-profile-premium-v2-3 ${activeTab === "info" ? "tcrm-lp-v21-overview-active" : ""} min-h-screen'
root_new = 'tcrm-lead-profile-premium-v2-1 tcrm-lead-profile-premium-v2-2 tcrm-lead-profile-premium-v2-3 tcrm-lead-profile-premium-v2-4 ${activeTab === "info" ? "tcrm-lp-v21-overview-active" : ""} min-h-screen'
if root_old not in src:
    raise SystemExit("ERROR: V2.3 root class anchor missing")
src = src.replace(root_old, root_new, 1)

# -----------------------------------------------------------------------------
# 2) Reference Hero middle cluster.
#    Uses ONLY already-loaded lead data. No invented portrait/data/backend field.
#    If there is no usable context, show a neutral empty-state sentence.
# -----------------------------------------------------------------------------
actions_anchor = '<div className="tcrm-lp-v22-actions flex flex-wrap items-center gap-2 lg:justify-end">'
context_panel = r'''<div className="tcrm-lp-v24-context-panel">
                              <div className="tcrm-lp-v24-context-quote" aria-hidden="true">“</div>
                              <div className="tcrm-lp-v24-context-copy">
                                <span>{isRTL ? "سياق العميل" : "Lead Context"}</span>
                                {((lead as any).interest || lead.serviceIntroduced || lead.notes || lead.businessProfile || lead.campaignName) ? (
                                  <p>{String((lead as any).interest || lead.serviceIntroduced || lead.notes || lead.businessProfile || lead.campaignName)}</p>
                                ) : (
                                  <p className="is-empty">{isRTL ? "لا يوجد سياق إضافي مسجل لهذا العميل بعد." : "No additional lead context has been captured yet."}</p>
                                )}
                                <small>{lead.campaignName || (lead as any).source || (lead as any).leadSource || ""}</small>
                              </div>
                            </div>

                            <div className="tcrm-lp-v22-actions flex flex-wrap items-center gap-2 lg:justify-end">'''
if 'className="tcrm-lp-v24-context-panel"' not in src:
    if actions_anchor not in src:
        raise SystemExit("ERROR: hero actions anchor missing")
    src = src.replace(actions_anchor, context_panel, 1)

TSX.write_text(src, encoding="utf-8")

css = r'''/*
TCRM Lead Profile Premium V2.4 — Reference Fidelity Pass
BASE: V2.3 Regression Recovery
VISUAL BASIS: approved Lead Profile reference composition
COLOR BASIS: Team Dashboard premium palette — PRESERVED

FOCUS:
- Hero = Identity / Context / Actions as three intentional clusters.
- KPI strip = stronger typography and information hierarchy.
- Main command center = ~30 / 40 / 30 distribution.
- Timeline = visually dominant activity surface, content-driven height.
- Overall information density = higher readability, less unused space.

NO backend / queries / mutations / permissions / routes / business logic changes.
*/

.tcrm-lead-profile-premium-v2-4{
  --v24-border:rgba(94,105,211,.23);
  --v24-shadow:0 22px 52px -38px rgba(58,66,155,.42),0 9px 22px -19px rgba(70,78,170,.22),inset 0 1px 0 rgba(255,255,255,.96);
}
.dark .tcrm-lead-profile-premium-v2-4{
  --v24-border:rgba(107,128,222,.36);
  --v24-shadow:0 28px 62px -42px rgba(0,0,0,.96),0 0 25px -23px rgba(100,117,255,.52),inset 0 1px 0 rgba(255,255,255,.06);
}

/* ========================================================================== */
/* HERO — REFERENCE COMPOSITION: IDENTITY / CONTEXT / ACTIONS                 */
/* ========================================================================== */
.tcrm-lead-profile-premium-v2-4 .tcrm-lp-hero{
  min-height:0!important;
  border-radius:20px!important;
  border-color:var(--v24-border)!important;
  overflow:hidden!important;
}
.tcrm-lead-profile-premium-v2-4 .tcrm-lp-hero>.p-3,
.tcrm-lead-profile-premium-v2-4 .tcrm-lp-hero>.md\:p-4{
  padding:17px 20px 15px!important;
}
.tcrm-lead-profile-premium-v2-4 .tcrm-lp-v22-hero-shell{
  display:block!important;
  width:100%!important;
}
.tcrm-lead-profile-premium-v2-4 .tcrm-lp-v22-hero-main{width:100%!important;}
.tcrm-lead-profile-premium-v2-4 .tcrm-lp-v22-hero-topline{
  display:grid!important;
  grid-template-columns:minmax(420px,1.12fr) minmax(300px,.82fr) minmax(390px,1.06fr)!important;
  gap:20px!important;
  align-items:center!important;
  width:100%!important;
}
.tcrm-lead-profile-premium-v2-4 .tcrm-lp-v22-identity{
  min-width:0!important;
  align-self:center!important;
}
.tcrm-lead-profile-premium-v2-4 .tcrm-lp-v22-identity>.flex.flex-wrap.items-center{
  flex-wrap:nowrap!important;
  gap:13px!important;
  align-items:center!important;
}
.tcrm-lead-profile-premium-v2-4 .tcrm-lp-v21-avatar{
  width:78px!important;
  height:78px!important;
  flex:0 0 78px!important;
  font-size:22px!important;
  border-width:3px!important;
}
.tcrm-lead-profile-premium-v2-4 .tcrm-lp-hero h1{
  font-size:29px!important;
  line-height:1.02!important;
  font-weight:900!important;
  letter-spacing:-.045em!important;
}
.tcrm-lead-profile-premium-v2-4 .tcrm-lp-v22-meta{
  margin-top:5px!important;
  gap:7px 12px!important;
  font-size:11px!important;
  line-height:1.35!important;
}
.tcrm-lead-profile-premium-v2-4 .tcrm-lp-v22-meta button{
  min-height:30px!important;
  height:30px!important;
  padding-inline:10px!important;
  font-size:10px!important;
}

/* Middle quote/context cluster, derived from existing lead data only. */
.tcrm-lead-profile-premium-v2-4 .tcrm-lp-v24-context-panel{
  position:relative;
  min-width:0;
  min-height:94px;
  display:grid;
  grid-template-columns:32px minmax(0,1fr);
  gap:9px;
  align-items:start;
  padding:13px 14px;
  border:1px solid rgba(99,102,241,.14);
  border-radius:15px;
  background:linear-gradient(145deg,rgba(255,255,255,.50),rgba(246,248,255,.34));
  box-shadow:inset 0 1px 0 rgba(255,255,255,.72);
  backdrop-filter:blur(8px);
}
.dark .tcrm-lead-profile-premium-v2-4 .tcrm-lp-v24-context-panel{
  border-color:rgba(116,137,255,.24);
  background:linear-gradient(145deg,rgba(12,35,73,.58),rgba(36,27,94,.34));
  box-shadow:inset 0 1px 0 rgba(255,255,255,.045);
}
.tcrm-lead-profile-premium-v2-4 .tcrm-lp-v24-context-quote{
  height:34px;
  display:flex;
  align-items:flex-start;
  justify-content:center;
  font-size:42px;
  line-height:.75;
  font-weight:900;
  color:rgba(99,102,241,.55);
  font-family:Georgia,serif;
}
.dark .tcrm-lead-profile-premium-v2-4 .tcrm-lp-v24-context-quote{color:rgba(145,160,255,.65);}
.tcrm-lead-profile-premium-v2-4 .tcrm-lp-v24-context-copy{min-width:0;}
.tcrm-lead-profile-premium-v2-4 .tcrm-lp-v24-context-copy>span{
  display:block;
  margin-bottom:5px;
  font-size:9px;
  font-weight:850;
  letter-spacing:.06em;
  text-transform:uppercase;
  color:var(--lp2-accent);
}
.tcrm-lead-profile-premium-v2-4 .tcrm-lp-v24-context-copy p{
  margin:0;
  display:-webkit-box;
  -webkit-box-orient:vertical;
  -webkit-line-clamp:3;
  overflow:hidden;
  font-size:11px;
  line-height:1.45;
  font-weight:650;
  color:var(--lp2-text);
}
.tcrm-lead-profile-premium-v2-4 .tcrm-lp-v24-context-copy p.is-empty{
  color:var(--lp2-muted);
  font-weight:550;
}
.tcrm-lead-profile-premium-v2-4 .tcrm-lp-v24-context-copy small{
  display:block;
  margin-top:6px;
  overflow:hidden;
  text-overflow:ellipsis;
  white-space:nowrap;
  font-size:8.5px;
  color:var(--lp2-muted);
}

/* Actions cluster: compact reference-like right zone. */
.tcrm-lead-profile-premium-v2-4 .tcrm-lp-v22-actions{
  width:100%!important;
  max-width:none!important;
  display:flex!important;
  justify-content:flex-end!important;
  align-content:center!important;
  gap:8px!important;
}
.tcrm-lead-profile-premium-v2-4 .tcrm-lp-v22-actions button{
  min-height:36px!important;
  height:36px!important;
  padding-inline:13px!important;
  font-size:10px!important;
  font-weight:750!important;
  border-radius:10px!important;
}
.tcrm-lead-profile-premium-v2-4 .tcrm-lp-v22-context{
  margin-top:10px!important;
  padding-top:9px!important;
  min-height:0!important;
  border-top:1px solid rgba(99,102,241,.11)!important;
  display:flex!important;
  flex-wrap:wrap!important;
  align-items:center!important;
  justify-content:space-between!important;
  gap:8px 12px!important;
}
.dark .tcrm-lead-profile-premium-v2-4 .tcrm-lp-v22-context{border-top-color:rgba(123,143,255,.16)!important;}

/* ========================================================================== */
/* KPI ROW — REFERENCE SCALE AND READABILITY                                  */
/* ========================================================================== */
.tcrm-lead-profile-premium-v2-4 .tcrm-lp-v2-signals{
  grid-template-columns:repeat(5,minmax(0,1fr))!important;
  gap:11px!important;
}
.tcrm-lead-profile-premium-v2-4 .tcrm-lp-v2-signal-card{
  min-height:118px!important;
  padding:15px 15px 14px!important;
  grid-template-columns:48px minmax(0,1fr)!important;
  gap:12px!important;
  border-radius:16px!important;
  border-color:var(--v24-border)!important;
  box-shadow:var(--v24-shadow)!important;
}
.tcrm-lead-profile-premium-v2-4 .tcrm-lp-v2-signal-icon{
  width:48px!important;
  height:48px!important;
  border-radius:15px!important;
}
.tcrm-lead-profile-premium-v2-4 .tcrm-lp-v2-signal-copy>span{
  font-size:10.5px!important;
  line-height:1.25!important;
  font-weight:820!important;
  letter-spacing:.02em!important;
}
.tcrm-lead-profile-premium-v2-4 .tcrm-lp-v2-signal-copy strong{
  margin-top:1px!important;
  font-size:21px!important;
  line-height:1.05!important;
  font-weight:900!important;
}
.tcrm-lead-profile-premium-v2-4 .tcrm-lp-v2-signal-copy strong small{font-size:10px!important;}
.tcrm-lead-profile-premium-v2-4 .tcrm-lp-v2-signal-copy em{
  margin-top:2px!important;
  font-size:9.5px!important;
  line-height:1.3!important;
}

/* ========================================================================== */
/* NAVIGATION — CLEARER, LESS MINIATURE                                        */
/* ========================================================================== */
.tcrm-lead-profile-premium-v2-4 .tcrm-lp-tabs{
  margin-bottom:10px!important;
  border-color:var(--v24-border)!important;
  box-shadow:var(--v24-shadow)!important;
}
.tcrm-lead-profile-premium-v2-4 .tcrm-lp-tabs>div{padding:6px 8px!important;gap:5px!important;}
.tcrm-lead-profile-premium-v2-4 .tcrm-lp-tabs button{
  min-height:36px!important;
  padding-inline:14px!important;
  font-size:10px!important;
  font-weight:760!important;
}

/* ========================================================================== */
/* MAIN COMMAND CENTER — ~30 / 40 / 30 REFERENCE DISTRIBUTION                 */
/* ========================================================================== */
.tcrm-lead-profile-premium-v2-4 .tcrm-lp-v2-overview-grid{
  grid-template-columns:minmax(310px,.93fr) minmax(0,1.25fr) minmax(300px,.92fr)!important;
  gap:12px!important;
  align-items:start!important;
}
.tcrm-lead-profile-premium-v2-4 .tcrm-lp-v2-overview-left,
.tcrm-lead-profile-premium-v2-4 .tcrm-lp-v2-overview-center,
.tcrm-lead-profile-premium-v2-4 .tcrm-lp-v21-overview-right{
  gap:10px!important;
  align-items:stretch!important;
}
.tcrm-lead-profile-premium-v2-4 .tcrm-lp-v2-card{
  border-radius:14px!important;
  border-color:var(--v24-border)!important;
  box-shadow:var(--v24-shadow)!important;
}
.tcrm-lead-profile-premium-v2-4 .tcrm-lp-v2-card-head{
  min-height:47px!important;
  padding:10px 13px!important;
}
.tcrm-lead-profile-premium-v2-4 .tcrm-lp-v2-card-title{
  font-size:12.5px!important;
  line-height:1.2!important;
  font-weight:850!important;
}
.tcrm-lead-profile-premium-v2-4 .tcrm-lp-v2-card-title svg{width:17px!important;height:17px!important;}
.tcrm-lead-profile-premium-v2-4 .tcrm-lp-v2-mini-action{
  min-height:29px!important;
  height:29px!important;
  padding-inline:10px!important;
  font-size:9px!important;
}

/* Contact / additional information: denser but readable. */
.tcrm-lead-profile-premium-v2-4 .tcrm-lp-v2-info-list{
  padding:9px 13px 11px!important;
  gap:0!important;
}
.tcrm-lead-profile-premium-v2-4 .tcrm-lp-v2-info-list>div{
  min-height:32px!important;
  padding:5px 0!important;
  display:grid!important;
  grid-template-columns:minmax(88px,.42fr) minmax(0,.58fr)!important;
  gap:10px!important;
  align-items:center!important;
}
.tcrm-lead-profile-premium-v2-4 .tcrm-lp-v2-info-list>div>*:first-child{
  font-size:9.5px!important;
  color:var(--lp2-muted)!important;
}
.tcrm-lead-profile-premium-v2-4 .tcrm-lp-v2-info-list>div>*:last-child{
  font-size:10.5px!important;
  color:var(--lp2-text)!important;
  font-weight:680!important;
}

/* Timeline = visual center of gravity. Content-driven height, stronger event language. */
.tcrm-lead-profile-premium-v2-4 .tcrm-lp-v2-timeline-card{
  width:100%!important;
  min-height:0!important;
  height:auto!important;
}
.tcrm-lead-profile-premium-v2-4 .tcrm-lp-v2-timeline{
  width:100%!important;
  min-height:0!important;
  height:auto!important;
  padding:7px 13px 10px!important;
}
.tcrm-lead-profile-premium-v2-4 .tcrm-lp-v2-timeline:before{
  top:20px!important;
  bottom:20px!important;
  width:2px!important;
  opacity:.72;
}
.tcrm-lead-profile-premium-v2-4 .tcrm-lp-v2-timeline-item{
  grid-template-columns:42px minmax(0,1fr) auto!important;
  gap:11px!important;
  padding:11px 0!important;
}
.tcrm-lead-profile-premium-v2-4 .tcrm-lp-v2-timeline-icon{
  width:34px!important;
  height:34px!important;
  border-width:1px!important;
}
.tcrm-lead-profile-premium-v2-4 .tcrm-lp-v2-timeline-copy strong{
  font-size:11px!important;
  line-height:1.25!important;
  font-weight:850!important;
}
.tcrm-lead-profile-premium-v2-4 .tcrm-lp-v2-timeline-copy p{
  margin-top:3px!important;
  font-size:9.5px!important;
  line-height:1.45!important;
  -webkit-line-clamp:3!important;
}
.tcrm-lead-profile-premium-v2-4 .tcrm-lp-v2-timeline-item time,
.tcrm-lead-profile-premium-v2-4 .tcrm-lp-v2-timeline-item time small{
  font-size:8.5px!important;
  line-height:1.35!important;
}

/* Notes gets readable preview, not a tiny empty box. */
.tcrm-lead-profile-premium-v2-4 .tcrm-lp-v2-notes-card{
  width:100%!important;
  min-height:0!important;
  height:auto!important;
}
.tcrm-lead-profile-premium-v2-4 .tcrm-lp-v2-notes-card [data-slot="card-content"]{
  padding:11px 13px!important;
}
.tcrm-lead-profile-premium-v2-4 .tcrm-lp-v2-note-preview{padding:10px!important;gap:10px!important;}
.tcrm-lead-profile-premium-v2-4 .tcrm-lp-v2-note-avatar{width:31px!important;height:31px!important;flex-basis:31px!important;font-size:10px!important;}
.tcrm-lead-profile-premium-v2-4 .tcrm-lp-v2-note-preview strong{font-size:10.5px!important;}
.tcrm-lead-profile-premium-v2-4 .tcrm-lp-v2-note-preview p{font-size:9.5px!important;line-height:1.45!important;}
.tcrm-lead-profile-premium-v2-4 .tcrm-lp-v2-empty-inline{
  min-height:66px!important;
  font-size:9.5px!important;
  gap:5px!important;
}

/* Right column: compact stacked executive cards close to reference. */
.tcrm-lead-profile-premium-v2-4 .tcrm-lp-v21-overview-right .tcrm-lp-v2-card{
  width:100%!important;
  min-width:0!important;
}
.tcrm-lead-profile-premium-v2-4 .tcrm-lp-v21-compact-body,
.tcrm-lead-profile-premium-v2-4 .tcrm-lp-v21-owner-body,
.tcrm-lead-profile-premium-v2-4 .tcrm-lp-v21-task-body{
  padding:11px 12px!important;
}
.tcrm-lead-profile-premium-v2-4 .tcrm-lp-v21-compact-empty{
  min-height:104px!important;
  gap:5px!important;
}
.tcrm-lead-profile-premium-v2-4 .tcrm-lp-v21-compact-empty strong{font-size:10.5px!important;}
.tcrm-lead-profile-premium-v2-4 .tcrm-lp-v21-compact-empty p{font-size:9px!important;line-height:1.4!important;max-width:250px!important;}
.tcrm-lead-profile-premium-v2-4 .tcrm-lp-v21-owner-main strong{font-size:10.5px!important;}
.tcrm-lead-profile-premium-v2-4 .tcrm-lp-v21-owner-grid strong{font-size:9px!important;}
.tcrm-lead-profile-premium-v2-4 .tcrm-lp-v21-task-row strong{font-size:9.5px!important;}
.tcrm-lead-profile-premium-v2-4 .tcrm-lp-v21-task-row p{font-size:8.5px!important;line-height:1.4!important;}

/* Light reference has pearl/icy depth — not flat white. */
.tcrm-lead-profile-premium-v2-4:not(.dark) .tcrm-lp-v2-card,
.tcrm-lead-profile-premium-v2-4:not(.dark) .tcrm-lp-v2-signal-card{
  background:linear-gradient(145deg,rgba(255,255,255,.97),rgba(247,249,255,.93))!important;
}

/* Dark reference uses layered navy surfaces, never flat black. */
.dark .tcrm-lead-profile-premium-v2-4 .tcrm-lp-v2-card,
.dark .tcrm-lead-profile-premium-v2-4 .tcrm-lp-v2-signal-card{
  background:linear-gradient(145deg,rgba(13,29,55,.98),rgba(9,24,47,.96))!important;
}

/* ========================================================================== */
/* RESPONSIVE                                                                 */
/* ========================================================================== */
@media (max-width:1500px){
  .tcrm-lead-profile-premium-v2-4 .tcrm-lp-v22-hero-topline{
    grid-template-columns:minmax(350px,1fr) minmax(260px,.76fr) minmax(330px,.96fr)!important;
    gap:14px!important;
  }
  .tcrm-lead-profile-premium-v2-4 .tcrm-lp-v2-overview-grid{
    grid-template-columns:minmax(280px,.92fr) minmax(0,1.22fr) minmax(270px,.86fr)!important;
  }
}
@media (max-width:1220px){
  .tcrm-lead-profile-premium-v2-4 .tcrm-lp-v22-hero-topline{
    grid-template-columns:minmax(0,1fr) minmax(300px,.9fr)!important;
  }
  .tcrm-lead-profile-premium-v2-4 .tcrm-lp-v24-context-panel{grid-column:1/-1;grid-row:2;}
  .tcrm-lead-profile-premium-v2-4 .tcrm-lp-v2-signals{grid-template-columns:repeat(3,minmax(0,1fr))!important;}
}
@media (max-width:820px){
  .tcrm-lead-profile-premium-v2-4 .tcrm-lp-v22-hero-topline{grid-template-columns:1fr!important;}
  .tcrm-lead-profile-premium-v2-4 .tcrm-lp-v24-context-panel{grid-column:auto;grid-row:auto;}
  .tcrm-lead-profile-premium-v2-4 .tcrm-lp-v22-actions{justify-content:flex-start!important;}
  .tcrm-lead-profile-premium-v2-4 .tcrm-lp-v2-signals{grid-template-columns:1fr 1fr!important;}
  .tcrm-lead-profile-premium-v2-4 .tcrm-lp-v2-info-list>div{grid-template-columns:1fr!important;gap:2px!important;}
}
@media (max-width:560px){
  .tcrm-lead-profile-premium-v2-4 .tcrm-lp-v2-signals{grid-template-columns:1fr!important;}
}
'''

CSS.write_text(css, encoding="utf-8")

print("PATCH=YES")
print("V2_3_BASE_PRESERVED=YES")
print("LEAD_PROFILE_PREMIUM_V2_4=YES")
print("REFERENCE_FIDELITY_PASS=YES")
print("HERO_THREE_CLUSTER_COMPOSITION=YES")
print("HERO_CONTEXT_USES_EXISTING_DATA_ONLY=YES")
print("KPI_REFERENCE_SCALE=YES")
print("OVERVIEW_30_40_30=YES")
print("TIMELINE_VISUAL_DENSITY_UPGRADED=YES")
print("INFORMATION_DENSITY_UPGRADED=YES")
print("LIGHT_PEARL_DEPTH_PRESERVED=YES")
print("DARK_NAVY_LAYERING_PRESERVED=YES")
print("TEAM_DASHBOARD_COLOR_SYSTEM_PRESERVED=YES")
print("BACKEND_UNCHANGED=YES")
print("PERMISSIONS_UNCHANGED=YES")
print("BUSINESS_LOGIC_UNCHANGED=YES")
print(f"BACKUP={backup}")
print("FILES_CHANGED=client/src/pages/LeadProfile.tsx,client/src/lead-profile-premium-v2-4.css")