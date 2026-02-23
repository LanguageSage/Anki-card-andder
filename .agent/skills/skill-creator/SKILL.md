---
name: skill-creator
description: Guide for creating, updating, and documenting new agent skills.
---

# Skill Creator
This skill provides instructions on how to package procedural knowledge into a format that other agents can use.

## Instructions
- When tasked with creating a new skill, follow these steps:
  1. Define the goal of the skill (e.g., "SQL Expert", "React Component Generator").
  2. Create a folder in `.agent/skills/<skill-name>`.
  3. Create a `SKILL.md` file with YAML frontmatter (name, description).
  4. Outline clear, actionable instructions in `SKILL.md`.
  5. Include helper scripts if necessary in a `scripts/` subfolder.
- Ensure all skills are documented clearly so other agents can discover their capabilities.
- Prioritize reusable, modular logic.
