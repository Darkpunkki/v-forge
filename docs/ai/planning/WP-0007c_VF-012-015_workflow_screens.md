# WP-0007c — Workflow Screens (plan review + summary)

## VF Tasks Included
- **VF-012** — Plan review screen (approve/reject)
- **VF-015** — Summary screen (run instructions + open workspace link)

## Goal
Implement two key workflow screens:
1. **Plan Review Screen** — Display proposed concept/plan summary and require explicit user approval before code generation begins
2. **Summary Screen** — Present final run instructions, key features built, and workspace location with actionable links

## Dependencies
- WP-0007a ✓ (UI foundation with routing, API client, and screen components)

## Implementation Order

### Task 1: VF-012 — Plan review screen (approve/reject)
- [ ] **VF-012** — Plan review screen (approve/reject)

**Current State:**
- PlanReview.tsx screen component exists (created in WP-0007a)
- Currently shows placeholder text
- API client has proper typing for plan review endpoints
- React Router configured with `/plan-review` route

**What to implement:**
1. **State Management:**
   - Load session data from sessionStorage
   - Fetch plan/concept summary from API
   - Track approval/rejection state
   - Handle loading and error states

2. **Display Components:**
   - Plan summary section (concept description, key features)
   - Technical details (stack, structure, constraints)
   - Proposed task list or high-level phases
   - Risk/feasibility warnings (if any from gates)

3. **Approval Actions:**
   - "Approve Plan" button → POST to approve endpoint → navigate to /progress
   - "Reject Plan" button → POST to reject endpoint → handle rejection flow
   - Buttons disabled during API calls
   - Visual feedback on action

4. **Error Handling:**
   - Display API errors
   - Handle missing session
   - Redirect if wrong phase

**Done means:**
- Plan review screen displays concept/plan summary
- Approve button advances to execution phase
- Reject button handles rejection gracefully
- Screen is accessible only in PLAN_REVIEW phase

**Files:**
- `apps/ui/src/screens/PlanReview.tsx` (update)

**Verification:**
- Build succeeds: `cd apps/ui && npm run build`
- Screen renders plan details without errors
- Approve/reject buttons trigger correct API calls

---

### Task 2: VF-015 — Summary screen (run instructions + open workspace link)
- [ ] **VF-015** — Summary screen (run instructions + open workspace link)

**Current State:**
- Result.tsx screen component exists (created in WP-0007a)
- Currently has basic structure showing result
- API client includes ResultResponse type
- Result endpoint returns workspace location and run instructions

**What to implement:**
1. **State Management:**
   - Load session data from sessionStorage
   - Fetch result from GET /sessions/{sessionId}/result
   - Handle loading and error states

2. **Display Sections:**
   - **Success Banner** — Congratulations message
   - **Run Instructions** — Step-by-step commands to build and run the app
   - **Workspace Location** — Full path with "Open Folder" button/link
   - **Features Built** — Bullet list of key features/components generated
   - **Stack Info** — Technologies used
   - **Next Steps** — Suggestions for extending the app

3. **Workspace Actions:**
   - "Open Workspace" button that triggers file:// protocol link (if supported)
   - Copy workspace path to clipboard button
   - Visual indication if workspace cannot be opened directly

4. **Error Handling:**
   - Display API errors
   - Handle missing session
   - Show appropriate message if session is not complete

**Done means:**
- Summary screen shows complete run instructions
- Workspace location is clearly displayed with action buttons
- Features and stack info presented clearly
- User has clear path to running their generated app

**Files:**
- `apps/ui/src/screens/Result.tsx` (update)

**Verification:**
- Build succeeds: `cd apps/ui && npm run build`
- Screen displays all required sections
- Workspace path and run instructions are visible
- "Open Workspace" action functions (or shows appropriate alternative)

---

## Done Means (WP-level)

This WP is complete when:
1. Plan review screen displays plan summary and allows approve/reject
2. Summary screen shows run instructions and workspace location
3. Both screens integrate with API correctly
4. TypeScript build passes
5. VF-012 and VF-015 are checked off in `vibeforge_master_checklist.md`

## Verification Commands

```bash
# Build UI to check TypeScript compilation
cd apps/ui && npm run build

# Manual verification:
# 1. Navigate to /plan-review after completing questionnaire
# 2. Verify plan details are displayed
# 3. Test approve/reject actions
# 4. Navigate to /result after completion
# 5. Verify run instructions and workspace location are shown
```

## Checklist

- [x] VF-012 — Plan review screen (approve/reject)
  - Enhanced PlanReview.tsx with improved styling
  - Added submitting state for buttons
  - Proper navigation: approve → /progress, reject → /
  - Files: apps/ui/src/screens/PlanReview.tsx
  - Verified: TypeScript build passes

- [x] VF-015 — Summary screen (run instructions + open workspace link)
  - Completely redesigned Result.tsx with polished UI
  - Added success banner with gradient styling
  - Workspace location with copy-to-clipboard button
  - Run instructions in dark terminal-style code block
  - Generated files list and artifacts display
  - Next steps section for user guidance
  - Files: apps/ui/src/screens/Result.tsx
  - Verified: TypeScript build passes

- [x] TypeScript build passes
  - Command: cd apps/ui && npm run build
  - Result: ✓ built in 745ms, no errors

- [ ] Both screens verified manually (requires backend implementation)
