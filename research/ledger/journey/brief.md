# Brief: turn the stage research into a partner journey map dataset

A visual journey map of the partner lifecycle at the card networks will be built from this data. It must show the tasks a partner actually does at each stage, including the recurring business-as-usual work after onboarding, where the friction is, where the Discover family stands, and where design can be a differentiator. The map is design-agnostic: it must not mention or rely on any prototype or on design work already done, and it does not mention Rich by name.

## Inputs
- Stage research: /Users/richhemsley/Desktop/Claude/payment-network-research/research/ledger/teardown/clean/stage-<id>.json for ids 1 (evaluate), 2 (join and contract), 3 (onboard and certify), 4 (build and integrate), 5 (launch), 6a (run: money), 6b (run: disputes and fraud), 6c (run: change, support and incidents), 7 (grow, renew and leave). Each has summary, by_partner (per partner type and network: how_it_works, tools_and_screens, friction, best_pattern, discover_today), design_moves, unseen and evidence. Every statement carries ids: ledger ids or "new:<key>" pointing at that file's evidence rows.
- Cross-stage strategy: research/ledger/teardown/strategy.json (thesis, patterns, discover_position, principles, 16 ranked moves with stage and stage_move_titles).
Use only these files. Do not fetch anything. Copy ids exactly as they appear.

## Output
Write JSON to the path your task gives:
{"tasks": [ {
  "id": "<stage>-<n>, e.g. 6a-1",
  "stage": "<stage id>",
  "title": "short verb phrase naming the partner's task, e.g. Reconcile the daily settlement",
  "cadence": "once | per project | per event | daily | weekly | monthly | quarterly | yearly",
  "partner_types": ["issuer", "acquirer", "payfac", "atm", "fintech", "developer", "merchant"],   // who does it; use only these seven codes
  "does": {"text": "one or two sentences on what the partner does and with whom", "ids": [...]},
  "touchpoints": [ {"name": "named tool, screen, report, form or channel", "network": "visa|mastercard|amex|discover-family|processor|any"} ],   // 2 to 6
  "friction": {"level": "severe | notable | minor | none found",
               "why": {"text": "one sentence saying why that level, grounded in the evidence", "ids": [...]},
               "points": [ {"text": "a specific friction the partner meets", "ids": [...]} ] },   // 1 to 4 points
  "discover": {"position": "ahead | parity | behind | unknown", "text": "one sentence", "ids": [...]},
  "opportunity": {"kind": "differentiator | parity | none",
                  "title": "the design move, short",
                  "text": "one or two sentences on what design would change for the partner",
                  "stage_move": "exact title of the stage design_move it draws on, or empty",
                  "strategy_rank": <rank of the strategy move it serves, or null>,
                  "ids": [...] }
} ]}

## Rules
- Cover the full lifecycle for your stages: 4 to 7 tasks per stage, in the order a partner meets them. For business-as-usual stages, name the recurring tasks and their cadence, such as reconciling settlement, reviewing the network invoice, working the dispute queue, answering retrievals, monitoring fraud and chargeback ratios, triaging a mandate, implementing a release, raising a support case, living through an incident, attesting compliance, and preparing a business review.
- Friction levels: severe means the evidence shows partners losing money, time or control repeatedly, or regulators or courts stepping in. Notable means real, evidenced effort or uncertainty. Minor means small or occasional. None found means the evidence shows no friction. Base the level on the evidence, never on how interesting the task is.
- Opportunity kind: differentiator means no incumbent offers a good version, the evidence shows it matters, and it would be hard to match quickly. Parity means incumbents already do it well and Discover lags or must match. None means nothing worth designing.
- Every factual sentence carries ids. No assumptions: what partners feel or want needs a source, or it is labelled as the study's inference.
- Prose: plain sentences under 30 words, no semicolons, no em or en dashes, no "not X, but Y", no questions. British spellings (programme, centre).
Return a short summary: tasks per stage, levels, differentiators.
