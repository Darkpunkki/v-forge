# WP-0010 — Stack presets + deterministic spec foundation

## VF Tasks Included
- VF-050: Define StackPreset allowlist (MVP: 1 web stack)
- VF-052: Implement DeterministicSeedDeriver (replayable)
- VF-053: Implement IdeaSeedPicker (genre + up to 2 twist cards)
- VF-054: BuildSpec validation + persistence (ArtifactStore)

## Goal
Complete the foundational pieces of BuildSpec generation: define an allowlisted stack preset, derive deterministic seeds and creative twists, validate BuildSpec, and persist it as an artifact for reproducible runs.

## Ordered Execution Steps

### 1. Define stack presets and seeds data
- Add an allowlisted MVP preset (e.g., Vite + React + TypeScript) with build/test/run commands and constraints.
- Capture preset metadata in config (ids, command families, dev server info) and align with command runner/verifier policies.
- Document preset assumptions and expected verification commands.

### 2. Implement deterministic seed derivation
- Add `DeterministicSeedDeriver` that hashes IntentProfile into a reproducible seed.
- Ensure seed is recorded alongside BuildSpec and used by IdeaSeedPicker for twist selection.
- Add tests covering repeatability for identical inputs.

### 3. Implement IdeaSeedPicker
- Choose genre and up to two twist cards from allowlists using the derived seed.
- Enforce constraints (no duplicates, respect budget/scope limits, deterministic ordering).
- Persist chosen seeds/twists into BuildSpec for later phases.

### 4. Validate and persist BuildSpec
- Add schema validation for BuildSpec, including preset id, seed, genre, twists, budgets, and policies.
- Persist BuildSpec to ArtifactStore after validation; reject progression if invalid.
- Update SpecBuilder to use new helpers and emit clear errors when validation fails.

## Done Means...

### Verification Commands
1. `cd apps/api && pytest tests/test_spec_builder.py -v`
2. `cd apps/api && pytest tests/test_artifacts.py -k buildspec -v`
3. `cd apps/api && pytest tests/test_verifiers.py -k preset -v` (preset alignment)
4. Manual: inspect persisted BuildSpec artifact for deterministic seed and twist selection consistency across runs
