<!-- Ported from jakeguo117/workspace-infrastructure-vnext @ c99355daf4889148dc517704bb6423de221d0770 (branch wi-chg-0009-strategy-execution).
Historical VNext material. Not the AIC baseline. Not an AIC acceptance result.
AIC-DOC-REQ@0.1.1, AIC-DOC-WORKFLOW@0.2.0, AIC-DOC-HANDOFF@0.2.0, and AIC-APR-0001 win on conflict.
This port grants no standing Git merge, push, or write permission. -->

# Evidence WI-CHG-0008

Protocol pin: e75af65951711202a6f973d5f7e89239a4b3b2ff
Approved spec commit: e2d527fc25f6de67e4dd5410a64ac95087bc6855
Acceptance run: f40952fe3358c50e458253835c58bf045914a048

| Case | Result | Proof |
| --- | --- | --- |
| 4 Detection, bootstrap, and adopted preflight | PASS | Disposable repositories covered absent, preview, apply, idempotent repeat, partial retention, invalid, unsupported, unreadable, opt-out, and a missing Jake decision. `example/adopted-project` enrolled from a separate protocol checkout. Its preflight exited 0 while `GITHUB_REPOSITORY` named a different repository. |
| 5 Approval before execution | PASS | Chat-only approval, a blank decision, the draft package at 7a9ebbc, a missing successor spec, and an outdated base were rejected. The reconciled package was admitted. |
| 6 Routine repair identity | PASS | Four disposable branches each kept their branch after one recorded repairable failure. |
| 7 Positive predicate | PASS | The predicate gate exited 0 and the expected head matched. |
| 8 Negative predicate | PASS | Removing each required predicate file rejected, and a non-SHA protocol pin rejected with `reason=identity`. |
| 9 Stale head | PASS | A newer head rejected with `reason=stale-review`. A mismatched mutation rejected with `reason=raced-head`. |
| 10 Material stop | PASS | The stop exited 16 and left the approved file unchanged. |
| 11 Retry bound | PASS | The same failure recorded by a second process exited 16. `repair_count` stayed 2. |
| 2 Live reconstruction | PASS | Detect on this checkout returned `VNEXT_INITIALIZED` for the declared repository, and admit exited 0. |
| Preflight | PASS | `bash scripts/wi_preflight.sh --check` exited 0 and reused pull request 21. |
| 1 Fresh GPT session | PASS | Fresh GPT session 008a5a04-a9a5-4f58-ba0c-3d5ca45feb04 read the durable files at ea7266152912b1315d2b140e017e31e2837b7159 and reconstructed the project, protocol pin e75af65951711202a6f973d5f7e89239a4b3b2ff, approved spec 3c35008526bbdefa1ba84016f179867ad950feec, baseline v0.2.0, active change WI-CHG-0008, and the one next action. It did not claim a fresh remote readback. |
| 3 Fresh Grok session | PASS | Fresh Grok session b1152d81-0aa9-4d36-b320-70acccc8a1a7 read the same checkout and reconstructed the same durable facts. Live GitHub in that session stayed NOT_VERIFIED. |
| 12 Final reconstruction after merge | PASS | Fresh session c279f1bb-f2a9-4eef-aa79-d718810d0249 read origin/main 4b8a08362d7ae2417aed244059b6a173311ef6ca and reconstructed the successor spec at b9e339f65a718a00121842e531632c5c2e34e904, project baseline v0.3.0, implementation baseline b9e339f65a718a00121842e531632c5c2e34e904, protocol commit e75af65951711202a6f973d5f7e89239a4b3b2ff, no active change, WI-CHG-0008 CLOSED / CONVERGED, the previous requirements still present, and one next action: none. No deployment was claimed. |
| 13 Native end to end | PASS | Cloud agent bc-fa58a215-90fc-40b3-a206-12383ef0161f implemented the marker at 10bd7cf4c7328f538cd60be3afe7a8024a8f4beb. Defect commit e38b33fdf0eb9710efdfef3633328485b8a64290 failed CI run 36819362255. Cloud agent bc-81651fad-11b9-4af3-a5e1-07a3277b5170 repaired it. repair_count is 1 and failure_identity is native-e2e-marker. Reviewer 9db1542f-0a74-4ff9-85e4-8fd319e2bcb8 returned PASS and verifier 6729dbad-03e5-45af-9f50-1535d6d09d8f returned VERIFIED for ea7266152912b1315d2b140e017e31e2837b7159. Preflight run 36819856708 passed on that SHA. The predicate gate passed, and pull request 22 merged to b9e339f65a718a00121842e531632c5c2e34e904 only while the remote head matched. |
