# Human projection fields

Source rule: WI-REQ-019 and WI-REQ-022, rewritten so the projection is Notion.

AIC projection is the Notion project page named by AIC-APR-0001 (`3ef47497-0e40-816e-a7cb-dc602d9110f7`). Editing a Notion badge creates neither approval nor runtime evidence (WORKFLOW “State, evidence and projection”; REQ-003).

A reader who ignores commit SHAs can answer:

- Objective
- Phase
- Completed
- Blocker
- Next action
- Jake decision needed

Machine identifiers are not the headline. Links to the approved Drive documents, the Git revision, and proof may follow. On mismatch, correct the projection from Drive business authority and Git engineering authority. Do not change those authorities to match Notion.

Linear is not the AIC projection. See CONFLICTS C-019.

`scripts/vnext/wi_projection_check.sh` checks that a projection file has these six labels and does not use a SHA as the headline. A successful check is not an AIC acceptance PASS.
