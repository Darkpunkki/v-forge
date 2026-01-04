"""SpecBuilder: Deterministically converts IntentProfile to BuildSpec."""

import hashlib
from datetime import datetime, timezone
from typing import Any


class SpecBuilder:
    """Converts IntentProfile to BuildSpec deterministically."""

    @staticmethod
    def fromIntent(intent_profile: dict[str, Any]) -> dict[str, Any]:
        """
        Convert IntentProfile to BuildSpec.

        This is deterministic: same IntentProfile always produces the same BuildSpec.
        """
        # Extract values from IntentProfile
        session_id = intent_profile["sessionId"]
        audience_target = intent_profile["audience"]["targetUser"]
        platform_pref = intent_profile["platformPreference"]
        domains = intent_profile["domains"]
        vibe = intent_profile["vibe"]
        constraints = intent_profile["constraints"]
        scope = intent_profile["scope"]

        # Derive deterministic seed from sessionId
        seed = _derive_seed(session_id)

        # Map platform preference to platform
        platform = _map_platform(platform_pref)

        # Pick stack preset based on platform
        stack = _pick_stack(platform)

        # Pick genre and twists based on domains, vibe, and seed
        idea_seed = _pick_idea_seed(domains, vibe, seed)

        # Map scope budget
        scope_budget = _build_scope_budget(scope, vibe["complexity"])

        # Build policies
        policies = _build_policies(constraints, platform)

        # Build acceptance criteria
        acceptance = _build_acceptance(constraints, platform)

        return {
            "version": "1.0",
            "sessionId": session_id,
            "createdAt": datetime.now(timezone.utc).isoformat(),
            "target": {
                "platform": platform,
                "audience": audience_target,
            },
            "stack": stack,
            "ideaSeed": idea_seed,
            "scopeBudget": scope_budget,
            "policies": policies,
            "acceptance": acceptance,
        }


def _derive_seed(session_id: str) -> int:
    """Derive a deterministic numeric seed from session ID."""
    hash_obj = hashlib.sha256(session_id.encode())
    # Use first 8 bytes as seed
    return int.from_bytes(hash_obj.digest()[:8], byteorder="big") % (2**31)


def _map_platform(platform_pref: str) -> str:
    """Map platform preference to BuildSpec platform."""
    mapping = {
        "WEB_APP": "WEB_APP",
        "DESKTOP_APP": "DESKTOP_APP",
        "CLI_APP": "CLI_APP",
        "NO_PREFERENCE": "WEB_APP",  # Default to web
    }
    return mapping.get(platform_pref, "WEB_APP")


def _pick_stack(platform: str) -> dict[str, str]:
    """Pick stack preset based on platform."""
    # MVP: Simple mapping, one stack per platform
    if platform == "WEB_APP":
        return {
            "preset": "WEB_VITE_REACT_TS",
            "runtime": "NODE_20",
            "packageManager": "NPM",
        }
    elif platform == "CLI_APP":
        return {
            "preset": "CLI_PYTHON",
            "runtime": "PYTHON_3_12",
            "packageManager": "PIP",
        }
    else:
        # Default to web
        return {
            "preset": "WEB_VITE_REACT_TS",
            "runtime": "NODE_20",
            "packageManager": "NPM",
        }


def _pick_idea_seed(domains: list[str], vibe: dict, seed: int) -> dict[str, Any]:
    """Pick genre and twists based on domains, vibe, and seed."""
    # Genre mapping based on first domain
    genre_map = {
        "PRODUCTIVITY": "TRACKER",
        "FITNESS": "TRACKER",
        "LEARNING": "COACH",
        "FINANCE": "DASHBOARD",
        "FOOD": "PLANNER",
        "GAMES": "QUIZ",
        "CREATIVITY": "GENERATOR",
        "HEALTH_WELLNESS": "COACH",
        "SOCIAL": "DASHBOARD",
        "TOOLS_UTILITIES": "GENERATOR",
    }

    primary_domain = domains[0] if domains else "PRODUCTIVITY"
    genre = genre_map.get(primary_domain, "TRACKER")

    # Pick twists based on vibe
    available_twists = [
        "DAILY_CHALLENGES",
        "BADGES_ACHIEVEMENTS",
        "RETRO_THEME",
        "PRIVACY_FIRST_LOCAL_ONLY",
        "COZY_UI",
        "RANDOM_PROMPT_OF_THE_DAY",
        "STREAKS",
    ]

    twists = []
    randomness = vibe.get("randomness", "SAFE")
    visual_style = vibe.get("visualStyle", "MODERN")

    # Add visual style twist
    if visual_style == "RETRO":
        twists.append("RETRO_THEME")
    elif visual_style == "PLAYFUL":
        twists.append("COZY_UI")

    # Add randomness-based twist
    if randomness == "MEDIUM" and "RANDOM_PROMPT_OF_THE_DAY" not in twists:
        twists.append("RANDOM_PROMPT_OF_THE_DAY")
    elif randomness == "CHAOTIC" and "DAILY_CHALLENGES" not in twists:
        twists.append("DAILY_CHALLENGES")

    # Limit to 2 twists
    twists = twists[:2]

    return {
        "seed": seed,
        "genre": genre,
        "twists": twists,
    }


def _build_scope_budget(scope: dict, complexity: int) -> dict[str, Any]:
    """Build scope budget from IntentProfile scope."""
    feature_budget = scope.get("featureBudget", "SMALL")

    # Map feature budget to screen/entity limits
    budget_map = {
        "TINY": {"maxScreens": 2, "maxEntities": 2},
        "SMALL": {"maxScreens": 4, "maxEntities": 4},
        "MEDIUM": {"maxScreens": 7, "maxEntities": 6},
    }

    limits = budget_map.get(feature_budget, budget_map["SMALL"])

    # Adjust based on complexity (0-100 scale)
    if complexity > 70:
        limits["maxScreens"] = min(limits["maxScreens"] + 1, 10)
        limits["maxEntities"] = min(limits["maxEntities"] + 1, 8)

    return {
        "featureBudget": feature_budget,
        "maxScreens": limits["maxScreens"],
        "maxEntities": limits["maxEntities"],
        "maxCommandsPerTask": 4,  # Fixed for MVP
    }


def _build_policies(constraints: dict, platform: str) -> dict[str, Any]:
    """Build policies from constraints."""
    network_access = constraints.get("networkAccessDuringBuild", "ALLOW")

    # Pick allowed command families based on platform
    if platform == "WEB_APP":
        allowed_families = ["NODE_BUILD", "NODE_TEST", "GIT", "FORMAT"]
    elif platform == "CLI_APP":
        allowed_families = ["PYTHON_TEST", "GIT", "FORMAT"]
    else:
        allowed_families = ["NODE_BUILD", "NODE_TEST", "GIT", "FORMAT"]

    # Basic forbidden patterns (MVP)
    forbidden_patterns = [
        r"rm\s+-rf\s+/",
        r"curl.*\|.*sh",
        r"wget.*\|.*sh",
        r"eval\s*\(",
        r"__import__\s*\(",
    ]

    return {
        "networkAccess": network_access,
        "allowedCommandFamilies": allowed_families,
        "forbiddenPatterns": forbidden_patterns,
    }


def _build_acceptance(constraints: dict, platform: str) -> dict[str, Any]:
    """Build acceptance criteria."""
    must_build = True  # Always require build for MVP
    must_have_tests = True  # Always require tests for MVP
    must_run_locally = True  # Always require local run for MVP

    # Define smoke routes based on platform
    smoke_routes = []
    if platform == "WEB_APP":
        smoke_routes = ["/", "/health"]
    elif platform == "CLI_APP":
        smoke_routes = ["--help", "--version"]

    return {
        "mustBuild": must_build,
        "mustHaveTests": must_have_tests,
        "mustRunLocally": must_run_locally,
        "smokeRoutes": smoke_routes,
    }


# Global instance
spec_builder = SpecBuilder()
