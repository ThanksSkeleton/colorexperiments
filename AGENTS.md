# Agent Instructions

Before working on this project, read `agent_docs/project_goals.md` and keep its scope, priorities, and non-goals in mind.

## Image analysis

Do not use multimodal LLM vision to inspect or judge images. In particular, do not send an image to the model or otherwise consume it through multimodal image analysis.

Programmatic image inspection is allowed and encouraged when useful. This includes examining file metadata, dimensions, formats, color values, alpha channels, and other properties with scripts or deterministic image-processing tools.

The user may override this rule for a specific task by explicitly asking the agent to use multimodal LLM vision.

## Testing and review

For work at this project's current scope, do not perform agent-run testing or visual review. Make the requested changes and pass the resulting page to the user for examination.

The user expects to revise this directive later. Until then, do not infer permission to test from a request to implement or migrate an experiment; test only when the user explicitly overrides this rule.
