# Documentation Standard

Status: active repository convention. Owner: engineering documentation.
Applies to maintained application guides and navigation; historical records
retain their original filenames, language, dates, and evidence.

## Adopted references

- [Diataxis](https://diataxis.fr/): separate tutorials, task guides, reference,
  and explanations by reader need. Existing responsibility directories remain
  stable; classification does not require relocating the whole tree.
- [GitHub README rules](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-readmes):
  the root README is the public introduction. Do not add `.github/README.md`,
  which would take precedence. Use `.github/CI-GUIDE.md` for automation.
- [Conventional Commits 1.0.0](https://www.conventionalcommits.org/en/v1.0.0/):
  commit titles communicate type, scope, and intent; repository-specific body
  requirements are defined in [CONTRIBUTING.md](../../CONTRIBUTING.md).
- [llms.txt](https://llmstxt.org/): proposed link-oriented LLM navigation.
  Our relative-path adaptation helps repository retrieval; it is not an official
  universal LLM standard or a guarantee that any client loads it automatically.

## Filenames and placement

| Kind | Convention | Example |
|---|---|---|
| Public introduction | Root `README.md` | `README.md` |
| Developer rules | Root `AGENTS.md` | `AGENTS.md` |
| Contribution rules | Root `CONTRIBUTING.md` | `CONTRIBUTING.md` |
| Component entry point | Component `README.md` | `ai/rag/README.md` |
| New maintained guide | English `UPPER-KEBAB-CASE.md` in its owning area | `docs/operations/LOCAL-ENVIRONMENT-CONFIGURATION.md` |
| Architecture decision | Existing numbered ADR convention | `docs/architecture/adr/ADR-029-configuration-secrets-identity-boundary.md` |
| New dated evidence | Topic plus `YYYYMMDD` under `history/quality/` | `history/quality/LOCAL-BASELINE-CLOSURE-20260921.md` |
| Machine navigation | Fixed lowercase filenames | `llms.txt`, `project-index.json` |

Use descriptive topic names rather than `final`, `perfect`, `new`, or
`updated`. Existing stable filenames, published ADRs, and historical paths are
compatibility interfaces: do not rename them merely to normalize casing.
If a move is needed, update consumers, links, manifests, and generated indexes
in the same change. Keep a single authoritative document per responsibility.

## Content contract

Maintained guides use English. Preserve language-specific test examples and
historical sources. Start with purpose, scope, and ownership; add a status/date
when a statement depends on execution evidence. Write short sections and
relative Markdown links. Expand an unfamiliar acronym on first use.

Task guides identify prerequisites, working directory, commands, effects,
success criteria, and relevant failure handling. Reference guides identify
contracts and owning source paths. Evidence records include date, Git base,
environment, executed command, result, skips, and remaining limits.
Do not turn historical results into current claims by editing their date.

## Context layers

1. `docs/PROJECT-BRIEF.md`: at most 600 whitespace-separated words; orientation.
2. `README.LLM.md` and `llms.txt`: task selection and links.
3. One owning component guide and relevant source/test symbols: task evidence.
4. `project-index.json` and `docs/DIRECTORY-MAP.md`: path lookup when needed.
5. Selected sections of `llms-full.txt`: optional expanded context.

The word limit is an inspectable size budget, not a token count or a guarantee
of accuracy. Small models benefit from narrower retrieval, concrete contracts,
and explicit unknowns. Never compensate for uncertainty by loading all history,
datasets, runtime reports, or secrets.

## Enforcement and maintenance

`scripts/documentation_index.py --check` rejects stale generated outputs,
broken local inline file links, a GitHub README that shadows the root, and an
oversized project brief. It does not verify remote URLs, anchors, every naming
convention, or application behavior. Review those separately when affected.

Update the source guide and `docs/navigation.json` first; regenerate the four
derived navigation files as described in
[documentation maintenance](DOCUMENTATION-MAINTENANCE.md). Never edit generated
indexes by hand. Follow the [change rules](DOCUMENTATION-SYSTEM.md) and
[contribution workflow](../../CONTRIBUTING.md).
