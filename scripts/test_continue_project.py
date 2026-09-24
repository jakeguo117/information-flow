#!/usr/bin/env python3
"""Synthetic tests for continue_project. No live vault, Drive, or private prose."""

from __future__ import annotations

import unittest

import continue_project as cp


def _ok_inputs(**overrides):
    base = {
        "governance": {"availability": "present", "id": "gov-fixture"},
        "project_control": {"availability": "present"},
        "milestone_map": {"availability": "present"},
        "frozen_authority_or_manifest": {
            "availability": "present",
            "approved": True,
        },
        "repo_verification": {
            "status": "verified",
            "sha": "b069358b879c1d70af565fe0dd65939d73de43f7",
        },
        "vault_access": {
            "availability": "available",
            "minimum_context": {
                "relevant_ids": ["cog-1"],
                "status": "active",
            },
        },
    }
    base.update(overrides)
    return base


class ContinueProjectTests(unittest.TestCase):
    def test_successful_continue_project(self) -> None:
        result = cp.continue_project(**_ok_inputs())
        self.assertEqual(result["status"], "found")
        self.assertEqual(result["gaps"], [])
        states = {s["step"]: s["state"] for s in result["steps_checked"]}
        for step in cp.STEP_ORDER:
            self.assertEqual(states[step], "present", msg=step)
        self.assertEqual(
            result["verified_sha"],
            "b069358b879c1d70af565fe0dd65939d73de43f7",
        )
        self.assertIn(
            "b069358b879c1d70af565fe0dd65939d73de43f7",
            result["bounded_next_action"],
        )

    def test_missing_governance(self) -> None:
        result = cp.continue_project(
            **_ok_inputs(governance={"availability": "absent"})
        )
        self.assertEqual(result["status"], "unavailable")
        self.assertTrue(
            any(g["step"] == "governance" for g in result["gaps"])
        )
        self.assertIn("Governance", result["bounded_next_action"])

    def test_unreadable_governance(self) -> None:
        result = cp.continue_project(
            **_ok_inputs(governance={"availability": "unreadable"})
        )
        self.assertEqual(result["status"], "unavailable")
        self.assertTrue(
            any(
                g["step"] == "governance" and g["severity"] == "unavailable"
                for g in result["gaps"]
            )
        )

    def test_missing_manifest(self) -> None:
        result = cp.continue_project(
            **_ok_inputs(
                frozen_authority_or_manifest={
                    "availability": "absent",
                    "approved": False,
                }
            )
        )
        self.assertEqual(result["status"], "blocked")
        self.assertTrue(
            any(
                g["step"] == "frozen_authority_or_manifest"
                for g in result["gaps"]
            )
        )
        self.assertIn("Manifest", result["bounded_next_action"])

    def test_manifest_present_but_not_approved(self) -> None:
        result = cp.continue_project(
            **_ok_inputs(
                frozen_authority_or_manifest={
                    "availability": "present",
                    "approved": False,
                }
            )
        )
        self.assertEqual(result["status"], "blocked")
        self.assertIn("Manifest", result["bounded_next_action"])

    def test_unavailable_vault(self) -> None:
        result = cp.continue_project(
            **_ok_inputs(
                vault_access={"availability": "unavailable"},
            )
        )
        self.assertEqual(result["status"], "unavailable")
        self.assertTrue(
            any(
                g["step"] == "digitalbrain_context"
                and g["severity"] == "unavailable"
                for g in result["gaps"]
            )
        )
        self.assertIn("vault", result["bounded_next_action"].lower())

    def test_unverified_repo(self) -> None:
        result = cp.continue_project(
            **_ok_inputs(
                repo_verification={"status": "unverified"},
            )
        )
        self.assertEqual(result["status"], "blocked")
        self.assertTrue(
            any(g["step"] == "repo_verification" for g in result["gaps"])
        )
        self.assertNotIn("verified_sha", result)
        self.assertIn("SHA", result["bounded_next_action"])

    def test_bounded_next_action_success_is_short_no_body(self) -> None:
        prose_body = (
            "FIXTURE_PROSE_BODY_MUST_NOT_APPEAR_IN_ACTION "
            "long private journal text placeholder"
        )
        result = cp.continue_project(
            **_ok_inputs(
                vault_access={
                    "availability": "available",
                    "minimum_context": {
                        "relevant_ids": ["cog-1"],
                        "status": "active",
                        # Callers must not pass bodies; if they do, action
                        # still must not echo them.
                        "body": prose_body,
                    },
                }
            )
        )
        self.assertEqual(result["status"], "found")
        action = result["bounded_next_action"]
        self.assertLessEqual(len(action), 160)
        self.assertNotIn(prose_body, action)
        self.assertNotIn("FIXTURE_PROSE_BODY", action)
        self.assertIn("b069358b879c1d70af565fe0dd65939d73de43f7", action)

    def test_bounded_next_action_failure_names_gap(self) -> None:
        result = cp.continue_project(
            **_ok_inputs(
                project_control={"availability": "absent"},
                milestone_map={"availability": "absent"},
            )
        )
        self.assertEqual(result["status"], "partial")
        action = result["bounded_next_action"]
        self.assertTrue(
            "PROJECT_CONTROL" in action or "PROJECT_MILESTONE_MAP" in action
        )

    def test_no_invented_milestone_when_map_missing(self) -> None:
        result = cp.continue_project(
            **_ok_inputs(milestone_map={"availability": "absent"})
        )
        self.assertEqual(result["status"], "partial")
        self.assertNotIn("current_milestone", result)
        self.assertNotIn("milestone", result)
        # gaps name the missing map; do not fabricate a milestone id/title
        joined = " ".join(
            f"{g['step']}:{g['reason']}" for g in result["gaps"]
        )
        self.assertIn("milestone_map", joined)
        self.assertNotRegex(joined, r"current milestone|M-\d+|milestone-id")
        self.assertIn("PROJECT_MILESTONE_MAP", result["bounded_next_action"])

    def test_blocked_outranks_unavailable(self) -> None:
        result = cp.continue_project(
            **_ok_inputs(
                governance={"availability": "absent"},
                frozen_authority_or_manifest={
                    "availability": "absent",
                    "approved": False,
                },
            )
        )
        self.assertEqual(result["status"], "blocked")
        self.assertIn("Manifest", result["bounded_next_action"])

    def test_steps_checked_order(self) -> None:
        result = cp.continue_project(**_ok_inputs())
        names = [s["step"] for s in result["steps_checked"]]
        self.assertEqual(names, list(cp.STEP_ORDER))


if __name__ == "__main__":
    unittest.main()
