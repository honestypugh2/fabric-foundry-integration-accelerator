## Why this matters

Preview features are how Microsoft ships new capabilities early. They are useful for learning and
pilots, but they can change, move or disappear. A demo or a production process that silently
depends on a preview feature can break on the day it matters.

## How this accelerator handles it

- **Off by default.** Every preview feature sits behind a named flag in the customer overlay, and
  every flag starts as `false`.
- **Always labeled.** Anything that relies on a preview capability is marked **PREVIEW** in
  results, screens, diagrams and lessons, even when the call reaches a real service.
- **Never required.** The default demo runs fully offline with no preview feature enabled.
- **Always simulated.** Each preview topic has an offline equivalent, so the lesson still works.

## The question to ask

"Which parts of this solution are preview, and what happens to the business process if one of
them changes next month?"
