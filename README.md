# deckbuilder-ai-arena
2D deckbuilder where you duel 5 AI automatons, from rule-based to ISMCTS and RL. Python engine + C# client over gRPC

## Repository structure

| Folder    | Contents |
|-----------|----------|
| `/server` | Python server: game rules, AI automatons, gRPC server |
| `/client` | 2D client in Godot 4 (C#) |
| `/proto`  | gRPC contract (`.proto`), changes approved by Kacper and Oliwier |
| `/data`   | card and deck data (JSON) |
| `/docs`   | documentation: rules, prototype notes, reports |

## Workflow

- Tasks: YouTrack, board **DAA Scrum**
- Branches: `DAA-<number>-<short-description>`, e.g. `DAA-70-legal-actions`
- Commit messages and PR titles start with `DAA-<number>`
- `main` is protected: every change goes through a pull request with a review and green CI
