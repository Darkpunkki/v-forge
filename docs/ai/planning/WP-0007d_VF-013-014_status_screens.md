# WP-0007d — Status Screens (progress + clarification)

## VF Tasks Included
- **VF-013** — Progress screen (timeline + log stream)
- **VF-014** — Clarification screen (multiple-choice answers)

## Goal
Implement two critical status/interaction screens:
1. **Progress Screen** — Display execution progress with timeline, active task, completed tasks, and streaming logs
2. **Clarification Screen** — Handle clarification questions from gates/agents with multiple-choice answers

## Dependencies
- WP-0007a ✓ (UI foundation with routing, API client, and screen components)

## Implementation Order

### Task 1: VF-013 — Progress screen (timeline + log stream)
- [ ] **VF-013** — Progress screen (timeline + log stream)

**Current State:**
- Progress.tsx screen component exists (created in WP-0007a)
- Has basic structure with polling (every 2 seconds)
- Displays phase, active task, completed/failed tasks, and logs
- API client has ProgressResponse type and getProgress function

**What to enhance:**
1. **Visual Timeline:**
   - Add visual timeline showing task progression
   - Use icons/colors to indicate task status (pending/in_progress/completed/failed)
   - Show completion percentage or progress indicator

2. **Active Task Display:**
   - Highlight active task with animation or pulsing effect
   - Show task details if available
   - Display elapsed time for active task

3. **Log Stream Improvements:**
   - Auto-scroll to latest log entry
   - Syntax highlighting for command outputs
   - Collapsible log sections
   - Filter/search logs if needed

4. **Phase Indicator:**
   - Visual phase progress bar or stepper
   - Show current phase prominently
   - Indicate which phases are complete/pending

5. **Auto-navigation:**
   - When phase transitions to COMPLETE, auto-navigate to /result
   - Handle FAILED phase appropriately

**Done means:**
- Progress screen displays clear visual timeline
- Active task is prominently highlighted
- Logs stream with auto-scroll
- Phase transitions handled correctly
- Polished UI with good UX

**Files:**
- `apps/ui/src/screens/Progress.tsx` (enhance)

**Verification:**
- Build succeeds: `cd apps/ui && npm run build`
- Screen renders without errors
- Polling works correctly
- Visual elements display properly

---

### Task 2: VF-014 — Clarification screen (multiple-choice answers)
- [ ] **VF-014** — Clarification screen (multiple-choice answers)

**Current State:**
- Clarification.tsx is a placeholder (created in WP-0007a)
- Shows "not yet implemented" message
- No API endpoint defined yet for clarifications

**What to implement:**
1. **API Integration:**
   - Define ClarificationResponse type in api.ts
   - Add getClarification() and submitClarification() to API client
   - Handle loading and error states

2. **Question Display:**
   - Show clarification question text prominently
   - Display context or reason for clarification
   - Show all available options as radio buttons or buttons

3. **Answer Submission:**
   - Single-select answer (radio buttons or clickable cards)
   - Submit button to send answer
   - Disabled state during submission
   - Navigate back to progress after submission

4. **Visual Design:**
   - Clear, focused layout
   - Highlight selected option
   - Show submission progress
   - Error handling for failed submissions

**Note:** This screen will be used when gates or agents need user input. The exact API contract may evolve, but the UI structure should support:
- Question text
- Array of options (label + value)
- Optional context/description

**Done means:**
- Clarification screen can display a question with multiple-choice options
- User can select and submit an answer
- Screen integrates with API (even if backend isn't fully implemented)
- Graceful error handling
- Clean, focused UI

**Files:**
- `apps/ui/src/screens/Clarification.tsx` (implement)
- `apps/ui/src/types/api.ts` (add ClarificationResponse type)
- `apps/ui/src/api/client.ts` (add clarification endpoints)

**Verification:**
- Build succeeds: `cd apps/ui && npm run build`
- Screen structure is complete
- Type definitions match expected backend contract

---

## Done Means (WP-level)

This WP is complete when:
1. Progress screen displays visual timeline and log stream with auto-scroll
2. Clarification screen can display and submit multiple-choice questions
3. Both screens have polished UI/UX
4. TypeScript build passes
5. VF-013 and VF-014 are checked off in `vibeforge_master_checklist.md`

## Verification Commands

```bash
# Build UI to check TypeScript compilation
cd apps/ui && npm run build

# Manual verification (requires backend):
# 1. Start a session and approve plan to enter EXECUTION phase
# 2. Navigate to /progress/{sessionId}
# 3. Verify timeline, active task, and logs display correctly
# 4. Verify auto-navigation to /result when complete
# 5. Test clarification screen if gates trigger clarifications
```

## Checklist

- [x] VF-013 — Progress screen (timeline + log stream)
  - Enhanced Progress.tsx with visual timeline and polished UI
  - Phase indicator with progress bar and percentage
  - Active task card with spinning animation
  - Task timeline with icons (✅ completed, 🔄 in progress, ❌ failed)
  - Live logs in terminal-style display with auto-scroll
  - Summary stats cards (completed/in progress/failed)
  - Auto-navigation to /result when phase is COMPLETE
  - Files: apps/ui/src/screens/Progress.tsx
  - Verified: TypeScript build passes

- [x] VF-014 — Clarification screen (multiple-choice answers)
  - Implemented complete Clarification.tsx with polished UI
  - Question display with optional context section
  - Clickable option cards with radio button styling
  - Selected option highlighting
  - Submit answer functionality
  - Navigate back to /progress after submission
  - Files: apps/ui/src/screens/Clarification.tsx
  - Files: apps/ui/src/types/api.ts (added ClarificationResponse types)
  - Files: apps/ui/src/api/client.ts (added getClarification/submitClarification)
  - Verified: TypeScript build passes

- [x] TypeScript build passes
  - Command: cd apps/ui && npm run build
  - Result: ✓ built in 991ms, no errors

- [ ] Both screens verified manually (requires backend implementation)
