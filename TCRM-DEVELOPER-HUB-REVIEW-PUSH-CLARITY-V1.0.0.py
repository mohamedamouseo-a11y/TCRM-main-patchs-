#!/usr/bin/env python3
from pathlib import Path
import subprocess

ROOT = Path('/var/www/TCRM-MAIN')
BASELINE = '22b81cc477b9ab58869771108b82b686f0035fdf'
VERSION = 'V1.0.0'
WORKFLOW_ID = 'TCRM-DEVELOPER-HUB-REVIEW-PUSH-CLARITY-V1.0.0'


def read(rel: str) -> str:
    path = ROOT / rel
    if not path.exists():
        raise SystemExit(f'MISSING_FILE={rel}')
    return path.read_text(encoding='utf-8')


def write(rel: str, content: str):
    path = ROOT / rel
    before = path.read_text(encoding='utf-8') if path.exists() else None
    if before == content:
        print(f'SKIP={rel}:already_current')
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding='utf-8')
    print(f'UPDATED={rel}')


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'ANCHOR_ERROR={label}:expected=1:actual={count}')
    return text.replace(old, new, 1)


def git(*args: str) -> str:
    return subprocess.check_output(['git', *args], cwd=ROOT, text=True).strip()


head = git('rev-parse', 'HEAD')
if head != BASELINE:
    raise SystemExit(f'BASELINE_MISMATCH=expected:{BASELINE}:actual:{head}')

tracked_diff = git('diff', '--name-only')
if tracked_diff:
    raise SystemExit(f'PREEXISTING_TRACKED_DIFF={tracked_diff.replace(chr(10), ",")}')

print(f'VERSION={VERSION}')
print(f'WORKFLOW_ID={WORKFLOW_ID}')
print(f'BASELINE={BASELINE}')

# 1) Clarify completed-review state so 100% is not mistaken for a hung push.
rel = 'client/src/components/DeveloperHubTab.tsx'
data = read(rel)

old = '''          } else {
            setReviewStatus("success");
            setReviewStep(recoveredPreview.expectedAction === "noop"
              ? isRTL ? "المشروع متزامن بالفعل" : "Project is already synchronized"
              : recoveredOperationMessage(operation));
          }
'''
new = '''          } else {
            setReviewStatus("success");
            const awaitingPushApproval = recoveredPreview.action === "push"
              && recoveredPreview.pushControl?.mode === "review"
              && recoveredPreview.expectedAction !== "noop";
            setReviewStep(recoveredPreview.expectedAction === "noop"
              ? isRTL ? "المشروع متزامن بالفعل" : "Project is already synchronized"
              : awaitingPushApproval
                ? isRTL ? "اكتملت المراجعة — في انتظار موافقتك على الرفع" : "Review complete — waiting for your approval to push"
                : recoveredOperationMessage(operation));
          }
'''
data = replace_once(data, old, new, 'recovered_review_approval_state')

old = '''              const message = result.expectedAction === "noop"
                ? isRTL ? "المشروع متزامن بالفعل" : "Project is already synchronized"
                : isRTL ? `اكتملت مراجعة ${result.fileCount} ملف` : `${result.fileCount} files reviewed successfully`;
'''
new = '''              const awaitingPushApproval = action === "push"
                && result.pushControl?.mode === "review"
                && result.expectedAction !== "noop";
              const message = result.expectedAction === "noop"
                ? isRTL ? "المشروع متزامن بالفعل" : "Project is already synchronized"
                : awaitingPushApproval
                  ? isRTL ? "اكتملت المراجعة — في انتظار موافقتك على الرفع" : "Review complete — waiting for your approval to push"
                  : isRTL ? `اكتملت مراجعة ${result.fileCount} ملف` : `${result.fileCount} files reviewed successfully`;
'''
data = replace_once(data, old, new, 'live_review_approval_state')

old = '''  const progressVisible = operationStatus !== "idle" || reviewStatus !== "idle";
  const displayedProgress = operationStatus !== "idle" ? progress : reviewProgress;
  const displayedStep = operationStatus !== "idle" ? currentStep : reviewStep;
'''
new = '''  const progressVisible = operationStatus !== "idle" || reviewStatus !== "idle";
  const displayedProgress = operationStatus !== "idle" ? progress : reviewProgress;
  const displayedStep = operationStatus !== "idle" ? currentStep : reviewStep;
  const reviewAwaitingPushApproval = operationStatus === "idle"
    && reviewStatus === "success"
    && preview?.action === "push"
    && preview.expectedAction !== "noop"
    && preview.pushControl?.mode === "review";
'''
data = replace_once(data, old, new, 'review_awaiting_approval_derived_state')

old = '''              <div className="flex flex-wrap gap-2"><Button onClick={() => void runSync(preview, "review_approved")} disabled={operationLocked || preview.blocked.length > 0 || !preview.reviewComplete || preview.expectedAction === "noop" || (preview.action === "push" && preview.pushControl?.mode === "auto")} className="gap-2"><ShieldCheck size={16} />{isRTL ? (preview.action === "push" ? "مراجعة ورفع" : "تنفيذ بعد المراجعة") : (preview.action === "push" ? "Review and Push" : "Execute Reviewed Action")}</Button>{operationStatus === "running" && <Button variant="outline" onClick={cancelSync} className="gap-2"><Square size={14} />{isRTL ? "إيقاف المتابعة" : "Stop Monitoring"}</Button>}</div>
'''
new = '''              <div className="flex flex-wrap gap-2"><Button onClick={() => void runSync(preview, "review_approved")} disabled={operationLocked || preview.blocked.length > 0 || !preview.reviewComplete || preview.expectedAction === "noop" || (preview.action === "push" && preview.pushControl?.mode === "auto")} className="gap-2"><ShieldCheck size={16} />{isRTL ? (preview.action === "push" ? "رفع التغييرات المعتمدة" : "تنفيذ بعد المراجعة") : (preview.action === "push" ? "Push Approved Changes" : "Execute Reviewed Action")}</Button>{operationStatus === "running" && <Button variant="outline" onClick={cancelSync} className="gap-2"><Square size={14} />{isRTL ? "إيقاف المتابعة" : "Stop Monitoring"}</Button>}</div>
'''
data = replace_once(data, old, new, 'approved_push_button_label')

old = '''          {progressVisible && (
            <div className="space-y-3 rounded-xl border p-3">
              <div className="flex justify-between gap-3 text-sm">
                <span className="min-w-0 flex-1 break-words">{displayedStep}</span>
                <span className="shrink-0 font-mono">{Math.round(displayedProgress)}%</span>
              </div>
              <Progress value={displayedProgress} className="h-2" />
              {operationStatus === "idle" && (reviewStatus === "blocked" || reviewStatus === "error") && lastReviewAction && (
                <Button variant="outline" size="sm" onClick={() => reviewSync(lastReviewAction)} disabled={previewLoading} className="gap-2">
                  <RefreshCw size={14} className={previewLoading ? "animate-spin" : ""} />
                  {isRTL ? "إعادة المحاولة" : "Retry Review"}
                </Button>
              )}
            </div>
          )}
'''
new = '''          {progressVisible && (
            reviewAwaitingPushApproval ? (
              <div data-developer-hub-review-awaiting-approval="true" className="rounded-xl border border-emerald-200 bg-emerald-50/60 p-3 dark:border-emerald-900 dark:bg-emerald-950/20">
                <div className="flex items-start gap-3">
                  <span className="mt-0.5 grid h-8 w-8 shrink-0 place-items-center rounded-full bg-emerald-100 text-emerald-700 dark:bg-emerald-900/60 dark:text-emerald-300"><ShieldCheck size={16} /></span>
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-semibold text-emerald-800 dark:text-emerald-200">{isRTL ? "اكتملت المراجعة بنجاح" : "Review complete"}</p>
                    <p className="mt-1 text-xs leading-5 text-emerald-700/90 dark:text-emerald-300/90">{isRTL ? "كل الفحوصات انتهت. لم يبدأ الرفع بعد — اضغط «رفع التغييرات المعتمدة» لبدء الـ Commit والـ Push الفعلي." : "All checks are complete. The push has not started yet — click “Push Approved Changes” to begin the actual commit and push."}</p>
                  </div>
                  <Badge variant="outline" className="shrink-0 border-emerald-300 text-emerald-700 dark:border-emerald-800 dark:text-emerald-300">{isRTL ? "بانتظار الموافقة" : "Awaiting approval"}</Badge>
                </div>
              </div>
            ) : (
              <div className="space-y-3 rounded-xl border p-3">
                <div className="flex justify-between gap-3 text-sm">
                  <span className="min-w-0 flex-1 break-words">{displayedStep}</span>
                  <span className="shrink-0 font-mono">{Math.round(displayedProgress)}%</span>
                </div>
                <Progress value={displayedProgress} className="h-2" />
                {operationStatus === "idle" && (reviewStatus === "blocked" || reviewStatus === "error") && lastReviewAction && (
                  <Button variant="outline" size="sm" onClick={() => reviewSync(lastReviewAction)} disabled={previewLoading} className="gap-2">
                    <RefreshCw size={14} className={previewLoading ? "animate-spin" : ""} />
                    {isRTL ? "إعادة المحاولة" : "Retry Review"}
                  </Button>
                )}
              </div>
            )
          )}
'''
data = replace_once(data, old, new, 'review_complete_not_hung_panel')

write(rel, data)

# 2) Static regression contract for the review-vs-push UX without changing Git semantics.
test_rel = 'server/security/developerHubReviewPushUx.test.ts'
test_content = '''import { describe, expect, it } from "vitest";\nimport { readFileSync } from "node:fs";\nimport { fileURLToPath } from "node:url";\nimport path from "node:path";\n\nconst here = path.dirname(fileURLToPath(import.meta.url));\nconst source = readFileSync(path.resolve(here, "../../client/src/components/DeveloperHubTab.tsx"), "utf8");\n\ndescribe("Developer Hub review/push clarity V1.0.0", () => {\n  it("shows review completion as awaiting approval instead of a hung 100 percent push", () => {\n    expect(source).toContain('const reviewAwaitingPushApproval = operationStatus === "idle"');\n    expect(source).toContain('data-developer-hub-review-awaiting-approval="true"');\n    expect(source).toContain('Review complete — waiting for your approval to push');\n    expect(source).toContain('The push has not started yet');\n    expect(source).toContain('Awaiting approval');\n  });\n\n  it("labels the explicit second step as pushing approved changes", () => {\n    expect(source).toContain('Push Approved Changes');\n    expect(source).toContain('رفع التغييرات المعتمدة');\n    expect(source).toContain('runSync(preview, "review_approved")');\n  });\n\n  it("preserves review-mode and auto-mode execution semantics", () => {\n    expect(source).toContain('onClick={() => reviewSync("push")}');\n    expect(source).toContain('result.pushControl?.mode === "auto"');\n    expect(source).toContain('runSync(result, "auto")');\n    expect(source).toContain('preview.pushControl?.mode === "review"');\n  });\n});\n'''
path = ROOT / test_rel
if path.exists() and path.read_text(encoding='utf-8') != test_content:
    raise SystemExit(f'UNEXPECTED_EXISTING_FILE={test_rel}')
write(test_rel, test_content)

# Fail-closed postchecks.
client_after = read(rel)
required = [
    'const reviewAwaitingPushApproval = operationStatus === "idle"',
    'data-developer-hub-review-awaiting-approval="true"',
    'Review complete — waiting for your approval to push',
    'Push Approved Changes',
    'runSync(preview, "review_approved")',
    'result.pushControl?.mode === "auto"',
    'runSync(result, "auto")',
]
missing = [marker for marker in required if marker not in client_after]
if missing:
    raise SystemExit(f'POSTCHECK_FAILED={rel}:{missing}')

expected_dirty = {
    'client/src/components/DeveloperHubTab.tsx',
    'server/security/developerHubReviewPushUx.test.ts',
}
status_lines = git('status', '--porcelain=v1', '--untracked-files=all').splitlines()
dirty = set()
for line in status_lines:
    if not line:
        continue
    candidate = line[3:]
    if ' -> ' in candidate:
        candidate = candidate.split(' -> ', 1)[1]
    dirty.add(candidate)
unexpected = sorted(dirty - expected_dirty)
missing_dirty = sorted(expected_dirty - dirty)
if unexpected or missing_dirty:
    raise SystemExit(f'POSTCHECK_DIRTY_MISMATCH=unexpected:{unexpected}:missing:{missing_dirty}')

print('PATCH_APPLIED=YES')
print('MODULES=developer_hub_review_push_clarity')
print('GIT_PUSH_SEMANTICS_CHANGED=NO')
print('REVIEW_APPROVAL_STATE_CLARIFIED=YES')
print('PUSH_EXECUTION_PROGRESS_PRESERVED=YES')
print('FILES_CHANGED=' + ','.join(sorted(expected_dirty)))
print('READY_FOR_TESTS=YES')
