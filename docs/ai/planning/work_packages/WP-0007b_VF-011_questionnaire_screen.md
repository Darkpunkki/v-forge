# WP-0007b — Questionnaire Screen

**Status:** In Progress
**Started:** 2026-01-05

## VF Tasks Included
- VF-011: Questionnaire screen (single-question flow, no free text)

## Goal
Enhance the existing Questionnaire screen component to properly render different question types (radio, checkbox, select, slider) with structured inputs only. No free-text input fields allowed.

## Ordered Execution Steps

### 1. Review current Questionnaire screen implementation
- Examine `apps/ui/src/screens/Questionnaire.tsx` to understand current structure
- Identify what question type rendering is already present
- Review backend QuestionResponse type structure from `apps/ui/src/types/api.ts`

### 2. Implement question type renderers
- Create individual rendering components or logic for each question type:
  - **radio**: Single-choice radio buttons (existing basic implementation)
  - **checkbox**: Multi-select checkboxes (if backend supports it)
  - **select**: Dropdown select menu
  - **slider**: Numeric slider with min/max values
- Ensure all inputs are structured (no free-text)
- Use proper HTML form elements with accessibility attributes

### 3. Enhance answer submission handling
- Update submit logic to handle different answer formats:
  - Radio/Select: single value
  - Checkbox: array of values (if applicable)
  - Slider: numeric value
- Validate answer format before submission
- Show loading state during submission

### 4. Add question navigation UI
- Display question progress (e.g., "Question 3 of 7")
- Show "Final question" indicator when `is_final` is true
- Consider adding back/forward navigation if backend supports it

### 5. Improve visual design
- Style each question type appropriately
- Add clear labels and descriptions
- Show validation errors if needed
- Ensure responsive design works on mobile

## Done Means...

### Verification Commands
1. `cd apps/ui && npm run build` - TypeScript compilation succeeds
2. Manual: Start backend (`cd apps/api && uvicorn vibeforge_api.main:app --reload`)
3. Manual: Start UI (`cd apps/ui && npm run dev`)
4. Manual: Create session and answer questions
5. Manual: Verify all question types render correctly
6. Manual: Verify no free-text inputs present
7. Manual: Verify answer submission and navigation works

### Task Checklist
- [x] VF-011: Questionnaire screen fully implemented
  - Different question types render correctly (radio, checkbox, select, slider)
  - Answer submission works for all question types
  - Question progress/navigation displayed (final question indicator)
  - No free-text input fields present (verified with grep - zero matches)
  - Visual design is clean and usable (styled labels, visual feedback on selection)
  - **Files changed:** `apps/ui/src/screens/Questionnaire.tsx` (complete rewrite with all question types)
  - **Verify:** `npm run build` (passed - TypeScript compilation succeeds)
  - **Manual testing:** Start backend + UI, create session, answer questions

## Implementation Notes
- Current implementation in `apps/ui/src/screens/Questionnaire.tsx` already has basic radio button rendering
- Need to extend to handle checkbox, select, and slider types
- Backend `QuestionResponse` type already supports all these types with `question_type`, `options`, `min_value`, `max_value` fields
- Focus on structured inputs only - absolutely no `<input type="text">` or `<textarea>` elements
