# Documentation System and Change Rules

## Reading contract

`README.md` explains the product, current documented baseline, and where to
continue. `README.LLM.md` explains authority, boundaries, and task-based
retrieval. `llms.txt` is a concise link map. `llms-full.txt` is a generated
bundle of explicitly selected guides; it is not the whole codebase or history.
`project-index.json` inventories paths. `DIRECTORY-MAP.md` lists folders and
files by responsibility without reading datasets. No file guarantees that an
LLM client will load it automatically.

## One source per responsibility

Each component README should explain its purpose, inputs and outputs, source
locations, local usage, tests, and limitations. Organize documentation so
tutorials teach, how-to guides help complete a task, reference documents define
interfaces, and explanations describe why the system works as it does. Dated
reports preserve observed results; the main README points to current status.
Do not copy the same metrics into many READMEs. Do not rename folders to match
milestones or remove experiments to hide contradictions.

## When to create or update documentation

| Change | Required documentation | Validation |
|---|---|---|
| New responsibility | Component README, canonical catalog, and ownership map; ADR when needed | Review consumers and tests |
| New internal directory | Add it to the directory map; add a README if it exposes an interface or procedure | Index has no orphan paths |
| API or contract change | Schema, producer, consumer, and usage guide | Contract and error-case tests |
| New configuration variable | Name, purpose, whether required, and a template without real values | Configuration and secret-exclusion checks |
| New script | Working directory, effects, requirements, and outputs | Run the relevant check |
| Architecture change | New ADR and explicit link to the superseded decision | Update catalog and ownership map |
| New report | Date, Git base, environment, command, sample count, skips, and limits | Preserve earlier reports; do not overwrite evidence |
| Release | Changelog or notes plus actual tag and commit evidence | Do not infer a release from a title |
| Moved file | Update links, README files, and indexes in the same change | Deterministic regeneration |

## Git ignore and machine reading

Git ignore rules exclude untracked files; they do not remove already tracked
files or control what an LLM can read. Keep ignore rules at repository roots
unless a component needs a local rule. Version redacted examples, lockfiles,
tests, guides, and reproducible indexes. Exclude real `.env` files, keys, local
databases, environments, caches, runtime reports, and local MLflow data.
Preserve tracked historical reports; do not remove them in bulk. Use an
explicit source list for expanded context instead of concatenating the tree.

## Maintenance cycle

1. Update the owning guide alongside the source or configuration change.
2. Update the navigation manifest when folder responsibilities or the intended
   LLM context bundle change.
3. Regenerate derived indexes and expanded context; review the diff and do not
   hand-edit generated files.
4. Run the generator tests, link and exclusion checks, and checks relevant to
   the changed component.
5. Review recent Git commit messages. Use a descriptive title and a body that
   records purpose, changes, observed validation, and limitations. Stage only
   explicit paths.
6. During milestone review, check source links and evidence dates. During
   release review, verify maturity against actual evidence.

## Applied references — 2026-09-22

- [llms.txt](https://llmstxt.org/): a Markdown map of information and links.
  This repository uses a local adaptation with relative paths. It is a
  proposal for navigation, not an access-control mechanism.
- [Write the Docs beginner's guide](https://www.writethedocs.org/guide/writing/beginners-guide-to-docs/):
  organize around reader needs, examples, and maintenance with the product.
- [Diátaxis](https://diataxis.fr/): distinguish learning, task completion,
  reference, and explanation.
- [Git ignore documentation](https://git-scm.com/docs/gitignore): ignore
  patterns apply to untracked files; they are not a security boundary for
  tracked content.
- [Make a README](https://www.makeareadme.com/): explain purpose, installation,
  usage, and support for the project. Operational instructions stay with their
  owning component here.

These ideas are applied without adding a documentation platform or dependency.
