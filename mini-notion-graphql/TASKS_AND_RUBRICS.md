# Example Long-Horizon Tasks & Grading Rubrics

These are example tasks an autonomous agent could be given against this
environment (via its GraphQL API), plus the rubric a grader would use to
score the outcome. Each task is deliberately multi-step and verifiable by
querying the API afterward — not just by reading the agent's transcript.

---

## Task 1 — Set up a shared project page with restricted access

**Prompt given to the agent:**

> "Using the Mini Notion API, create a new page called 'Marketing Launch
> Plan' in the workspace with id `<workspace_id>`. Add three blocks to it: a
> heading with the page title, a to-do block for 'Finalize press release',
> and a to-do block for 'Confirm launch date'. Share the page with the user
> `marketing@example.com` as an editor. Do NOT give them owner access."

**Grading rubric:**

| Outcome | Criteria |
|---|---|
| **Full credit** | Page exists with correct title, in the correct workspace. Exactly 3 blocks exist in a sensible order (heading first). `marketing@example.com` has `editor` role on the page (verified via a `page` query as that user — `myRole` returns `"editor"`, and an `updatePage` attempt as that user succeeds). An `owner`-only action (e.g. `deletePage`) as that user fails. |
| **Partial credit** | Page and blocks created correctly, but sharing step missing, wrong role granted (e.g. `owner` instead of `editor`), or fewer/more than 3 blocks. |
| **Insufficient / fail** | Page not created, created in the wrong workspace, blocks missing or malformed (e.g. wrong `type` values), or the target user was given no access / access to the wrong page. |

**Why this task is useful for evaluation:** it requires chaining four
distinct mutation types (`createPage`, `createBlock` ×3, `sharePage`) and
checking a negative case (an action that should be *rejected*), which is a
common blind spot for agents that only verify the "happy path."

---

## Task 2 — Reorganize nested pages and verify inherited access

**Prompt given to the agent:**

> "There's a page called 'Engineering Notes' in workspace `<workspace_id>`
> that already has an editor named `sam@example.com`. Create a new page
> called 'API Design Decisions' as a *child* of 'Engineering Notes', without
> sharing it with anyone directly. Then confirm that `sam@example.com` can
> still edit the new child page without being explicitly added to it."

**Grading rubric:**

| Outcome | Criteria |
|---|---|
| **Full credit** | New page created with `parentPageId` correctly set to 'Engineering Notes'. No `Permission` row was created directly on the new page for `sam@example.com`. A `page` query as `sam@example.com` on the new page returns `myRole: "editor"` (inherited), and an `updatePage` mutation as that user succeeds. |
| **Partial credit** | Page created correctly and nested correctly, but the agent explicitly (and unnecessarily) called `sharePage` to grant access directly, rather than relying on inheritance — task technically "works" but demonstrates a misunderstanding of the permission model. |
| **Insufficient / fail** | Page not nested under the correct parent, or the agent incorrectly concludes `sam@example.com` has no access (misreading the inheritance model), or fabricates verification without actually querying the API. |

**Why this task is useful for evaluation:** it specifically targets whether
an agent understands *inherited* vs. *explicit* permissions — a subtlety
that's easy to get right by accident (over-sharing) and easy to verify
precisely via the API rather than by trusting the agent's own narration.

---

## Task 3 — Search and cleanup

**Prompt given to the agent:**

> "Search workspace `<workspace_id>` for any pages mentioning 'budget'.
> For each match, delete the page — but only if the current user (the
> workspace owner) has `owner`-level access to it. Report how many pages
> were deleted and list any pages that were skipped and why."

**Grading rubric:**

| Outcome | Criteria |
|---|---|
| **Full credit** | `searchContent` (or equivalent) used to find matches. All matched pages the acting user genuinely owns are deleted (verified: subsequent `page` query for each returns `null`). Any matched page the user does *not* have `owner` access to is correctly left alone and reported as skipped, with the correct reason. Final report's count matches actual deletions. |
| **Partial credit** | Search performed correctly and most deletions correct, but the agent deletes a page it only has `editor` access to (should have required `owner` and been rejected — check whether the agent handled the resulting error correctly or silently ignored a failure), or the final report's count is off by one. |
| **Insufficient / fail** | Search step skipped or hallucinated (agent claims matches without querying), pages deleted that don't match the search term, or the agent reports success on a deletion that the API actually rejected. |

**Why this task is useful for evaluation:** it combines a read (search), a
conditional/authorization-gated write (delete only if permitted), and
requires the agent to correctly interpret and report on partial failure —
a good test of whether an agent verifies its own actions rather than
assuming success.
