# AGENTS.md. CX Field Tools Installer 
*Last updated 2025-June-14*

## 0. Purpose
This file provides guidance to AI Assistants (Cursor, Claude, GPT, etc) which are used to help enhance the project. It encodes coding standards, guard-rails, and a clear delineation between what the AI Assistants can do versus activities which must remain exclusively in human hands. (architecture, tests, business domain).

Contents have been inspired by the `agents.md` published by [Julep AI](https://raw.githubusercontent.com/julep-ai/julep/refs/heads/dev/AGENTS.md).

#### WARNINGS
1. It is still unclear to me how much of this guidance will be detected by AI Assistants and what parts are meant to guide humans only. TBD.

2. I've taken the whole content of the Julep AI document and am not deleting sections (_even the ones that are obviously not relevant_) yet. I will modify once I have a few interation cycles under my belt.


---
## 1. Project overview
This project is designed to help clients deploy and configure their [Seqera Platform Enterprise instance](https://docs.seqera.io/platform-enterprise/25.1/platform-enterprise) in AWS. It does so by:

1. Creating necessary AWS infrastructure.
2. Configuring application files.
3. Installating necessary packages to support the running of application containers via Docker Compose.
4. (Optional) deploying resources inside the newly-running Seqera Platform Enterprise instance via [seqerakit](https://github.com/seqeralabs/seqerakit).

The projects utilizes the following key components:

- **`*.tf`**: Terraform files which handle various aspects of the deploy. Each filename has the following characteristics:
    1. Is numbered with a heuristical sequence identifier to help human deployers under action flow.
    2. Bears a text describing the major component / activity contained within.
- **modules**: The folder that contains Terraform modules. Early architectural decisions eschewed modules for reasons that made sense at the time. As the project has grown, it has become apparently that use of Terraform modules could facilitate project efforts and they are slowly being introduced during refactoring efforts.
- **assets**: Contains various scripts, template files, and Ansible playbooks that support the deployment. 
    - `assets/src` contains the starting file representations (_which may be modified, in memory, during deployment_).
    - `assets/target` contains final state files after all relevant update / modification activities are completed. This folder is then copied over to the resulting EC2 instance in AWS and used for all EC2-based activity.
- **scripts**: Contains python3-based scripts used to support project operations including:
    - Validation of related values specified in `terraform.tfvars`.
    - Generation of some Terraform `local` variables that are dependent upon the superior logic branching capabilites of a full-fledged program language rather than via Terraform.
- **templates**: Contains placeholder files for application secrets which must be deployed to AWS Systems Manager Parameter Store (SSM) via offline business process and `terraform.tfvars` which is used to drive the generation of Terraform assets. 


---
## 2. Non-Negotiable Golden Rules
Supreme to all rules specified in the table below:<br />**AI Assistants must ALWAYS ask the developer for clarification rather than making assumptions about unclear implementations details or requirements.

| #: | AI Assistants *must* do  | AI Assistants *must NOT* do  |
|----|--------------------------|------------------------------|
| G-0 | Must always ask the developer for clarification if implementation details or rquirements are unclear.    |  ❌ Write changes or use tools when unclear on activity goals or if context is lacking for a particular feature/decision. |
| G-1 | May touch any files and folders in the repository except if expressly forbidden in the right-adjacent cell. | ❌ May not touch `SPEC.md`, `LICENSE`, `ssh_config`, `.gitignore`, `DONTDELETE/`.
| G-2 | Add/update **`AIDEV-NOTE:` anchor comments** near non-trivial edited code. | ❌ Delete or mangle existing `AIDEV-` comments.                                     |


<!-- | G-1 | Generate code **only inside** relevant source directories (e.g., `agents_api/` for the main API, `cli/src/` for the CLI, `integrations/` for integration-specific code) or explicitly pointed files.    | ❌ Touch `tests/`, `SPEC.md`, or any `*_spec.py` / `*.ward` files (humans own tests & specs). | -->

<!-- | G-3 | Follow lint/style configs (`pyproject.toml`, `.ruff.toml`, `.pre-commit-config.yaml`). Use the project's configured linter, if available, instead of manually re-formatting code. | ❌ Re-format code to any other style.                                               |
| G-4 | For changes >300 LOC or >3 files, **ask for confirmation**.            | ❌ Refactor large modules without human guidance.                                     |
| G-5 | Stay within the current task context. Inform the dev if it'd be better to start afresh.                                  | ❌ Continue work from a prior prompt after "new task" – start a fresh session.      | -->


---
## 3. Directory-Specific AGENTS.md Files

*   **Always check for `AGENTS.md` files in specific directories** before working on code within them. These files contain targeted context.
*   If a directory's `AGENTS.md` is outdated or incorrect, **update it**.
*   If you make significant changes to a directory's structure, patterns, or critical implementation details, **document these in its `AGENTS.md`**.
*   If a directory lacks a `AGENTS.md` but contains complex logic or patterns worth documenting for AI/humans, **suggest creating one**.


----
## 4. Key File & Pattern References
TODO
<!-- This section provides pointers to important files and common patterns within the codebase.

*   **API Route Definitions**:
    *   Location: `agents-api/routers/` (e.g., `agents-api/routers/sessions.py`)
    *   Pattern: FastAPI routers, Pydantic models for request/response, dependency injection.
*   **Typed Exceptions**:
    *   Location: `agents-api/common/exceptions/`
    *   Pattern: Custom exception classes inheriting from base exceptions.
*   **Pydantic Models**:
    *   Location: Used extensively across services, often in `models.py` files within component directories (e.g., `agents_api/common/protocol/`), or directly in router/activity files.
    *   Pattern: Data validation, serialization, and settings management.
*   **Temporal Workflows & Activities**:
    *   Location: `agents-api/workflows/` (workflow definitions) and `agents-api/activities/` (activity implementations).
    *   Pattern: Define complex, stateful operations using Temporal's primitives.
*   **Database Queries & Models (Memory Store)**:
    *   Location: `agents-api/queries/` (for SQL query builders/files) and `memory-store/` (for schema migrations).
    *   Pattern: Asyncpg for database interaction, often with helper functions for CRUD operations. -->


---
## 5. Domain-Specific Terminology
TODO

<!-- *   **Agent**: An AI entity with specific instructions, tools, and capabilities, defined via API. Core model in `typespec/agents/models.tsp`.
*   **Task**: A definition of a workflow composed of multiple steps that an agent can execute. Core model in `typespec/tasks/models.tsp`.
*   **Tool**: A specific capability or integration an agent can use (e.g., web search, API call). Defined in `typespec/tools/`.
*   **Session**: A container for a sequence of interactions (entries) with an agent, maintaining context. Core model in `typespec/sessions/models.tsp`.
*   **Entry**: A single message or event within a session (e.g., user input, agent response). Core model in `typespec/entries/models.tsp`.
*   **Execution**: The runtime instance and state of a task being performed by an agent. Core model in `typespec/executions/models.tsp`.
*   **POE (PoeThePoet)**: The task runner used in this project for development tasks like formatting, linting, testing, and code generation (configured in `pyproject.toml`).
*   **TypeSpec**: The language used to define API schemas. It is the source of truth for API models, which are then generated into Python Pydantic models in `autogen/` directories.
*   **Ward**: The primary Python testing framework used for unit and integration tests in most components (e.g., `agents-api`, `cli`).
*   **Temporal**: The distributed workflow engine used to orchestrate complex, long-running tasks and ensure their reliable execution.
*   **AIDEV-NOTE/TODO/QUESTION**: Specially formatted comments to provide inline context or tasks for AI assistants and developers. -->

---
## 6. Build, test & utility commands
TODO


---
## 7. Coding Standards

- **Terraform**:    1.3.7
- **Python**:       3.9.22

- **Terraform Module**
    - Ensure any created module includes: README.md, and CHANGELOG.md.
    - Ensure newly-created or modified modules are locally version using semantic versioning.
    - If changes are made to an existing module, ensure updates are made to the README.md and CHANGELOG.md

<!-- *   **Python**: 3.12+, FastAPI, `async/await` preferred.
*   **Formatting**: `ruff` enforces 96-char lines, double quotes, sorted imports. Standard `ruff` linter rules.
*   **Typing**: Strict (Pydantic v2 models preferred); `from __future__ import annotations`.
*   **Naming**: `snake_case` (functions/variables), `PascalCase` (classes), `SCREAMING_SNAKE` (constants).
*   **Error Handling**: Typed exceptions; context managers for resources.
*   **Documentation**: Google-style docstrings for public functions/classes.
*   **Testing**: Separate test files matching source file patterns.

**Error handling patterns**:
- Use typed, hierarchical exceptions defined in `exceptions.py`
- Catch specific exceptions, not general `Exception`
- Use context managers for resources (database connections, file handles)
- For async code, use `try/finally` to ensure cleanup

Example:
```python
from agents_api.common.exceptions import ValidationError

async def process_data(data: dict) -> Result:
    try:
        # Process data
        return result
    except KeyError as e:
        raise ValidationError(f"Missing required field: {e}") from e
``` -->


---
## 8. Project layout & Core Components
TODO

<!-- | Directory               | Description                                       |
| ----------------------- | ------------------------------------------------- |
| `agents-api/`           | FastAPI service & Temporal activities             |
| `memory-store/`         | PostgreSQL + TimescaleDB schemas & migrations     |
| `blob-store/`           | S3-compatible object storage for files            |
| `integrations-service/` | Adapters for external services (browsers, APIs)   |
| `scheduler/`            | Temporal workflow engine for execution            |
| `gateway/`              | API gateway (routing, request handling)           |
| `llm-proxy/`            | LiteLLM proxy for language models                 |
| `monitoring/`           | Prometheus & Grafana                              |
| `typespec/`             | **Source-of-truth** API specifications (TypeSpec) |
| `sdks/`                 | Node.js & Python client SDKs                      |

See `CONTRIBUTING.md` for a full architecture diagram.

**Key domain models**:
- **Agents**: AI agent definitions with instructions and tools
- **Tasks**: Workflow definitions with individual steps
- **Tools**: Integrations and capabilities for agents to use 
- **Sessions**: Conversation containers with context
- **Entries**: Message history tracking
- **Executions**: Task execution state tracking -->


---
## 9. Anchor Comments

Add specially formatted comments throughout the codebase, where appropriate, for yourself as inline knowledge that can be easily `grep`ped for. 

### Guidelines:

- Use `AIDEV-NOTE:`, `AIDEV-TODO:`, or `AIDEV-QUESTION:` (all-caps prefix) for comments aimed at AI and developers.
- Keep them concise (≤ 120 chars).
- **Important:** Before scanning files, always first try to **locate existing anchors** `AIDEV-*` in relevant subdirectories.
- **Update relevant anchors** when modifying associated code.
- **Do not remove `AIDEV-NOTE`s** without explicit human instruction.
- Make sure to add relevant anchor comments, whenever a file or piece of code is:
  * too long, or
  * too complex, or
  * very important, or
  * confusing, or
  * could have a bug unrelated to the task you are currently working on.

Example:
```python
# AIDEV-NOTE: perf-hot-path; avoid extra allocations (see ADR-24)
async def render_feed(...):
    ...
```


---
## 10. Commit discipline

*   **Granular commits**: One logical change per commit.
*   **Tag AI-generated commits**: e.g., `feat: optimise feed query [AI]`.
*   **Clear commit messages**: Explain the *why*; link to issues/ADRs if architectural.
*   **Use `git worktree`** for parallel/long-running AI branches (e.g., `git worktree add ../wip-foo -b wip-foo`).
*   **Review AI-generated code**: Never merge code you don't understand.


---
## 11. API models & codegen

TODO

<!-- *   To modify API models (e.g., in `agents_api/autogen/`), **edit TypeSpec files** in `typespec/`.
*   **Regenerate code** after TypeSpec changes: `bash scripts/generate_openapi_code.sh` (from project root).
*   **Do NOT manually edit** generated files (e.g., in `autogen/` directories) as they will be overwritten.

**API pattern examples**:
```python
# Route definition
@router.post("/sessions/{session_id}/entries", response_model=EntryResponse)
async def create_entry(
    session_id: str,
    entry_create: EntryCreate,
    current_user: User = Depends(get_current_user),
) -> EntryResponse:
    """Create a new entry in a session."""
    # Implementation...
``` -->


---
## 12. Python expressions in tasks (agents-api)
TODO
<!-- 
*   Evaluated using `simpleeval` in a sandboxed environment.
*   Use `validate_py_expression()` from `agents_api.activities.task_steps.base_evaluate` for static checks (syntax, undefined names, safety).
*   Expressions have access to `_` (current input) and standard library modules.
*   Test expressions: `PYTHONPATH=$PWD python -c "from agents_api.activities.task_steps.base_evaluate import validate_py_expression; print(validate_py_expression('$ your_expr_here'))"`
*   Task validation handles raw task dictionaries and Pydantic models (after `task_to_spec` conversion).
*   In `task_to_spec` converted tasks, `kind_` field denotes step type. Raw tasks use step type keys.
*   For "if_else" steps, condition is in `if_` field (aliased as "if").

**Expression example**:
```python
# Simple expression example
"$_['customer']['total_orders'] > 5"  # Checks if customer has more than 5 orders

# More complex example with dict access and function calls
"$len([x for x in _['items'] if x['category'] == 'electronics']) > 0"
``` -->


---
## 11. Ward testing framework
TO DO
<!-- *   Use descriptive test names: `@test("Descriptive name of what is being tested")`.
*   Activate virtual environment: `source .venv/bin/activate`.
*   Ensure correct working directory (e.g., `agents-api/`) and `PYTHONPATH=$PWD` for script-based tests.
*   Filter tests: `poe test --search "pattern_to_match"` (do NOT use `-p`).
*   Limit failures for faster feedback: `poe test --fail-limit 1 --search "pattern_to_match"`. -->


---
## 12. Meta: Guidelines for updating AGENTS.md files
TODO

<!-- ### Elements that would be helpful to add:

1. **Decision flowchart**: A simple decision tree for "when to use X vs Y" for key architectural choices would guide my recommendations.
2. **Reference links**: Links to key files or implementation examples that demonstrate best practices.
3. **Domain-specific terminology**: A small glossary of project-specific terms would help me understand domain language correctly.
4. **Versioning conventions**: How the project handles versioning, both for APIs and internal components.

### Format preferences:

1. **Consistent syntax highlighting**: Ensure all code blocks have proper language tags (`python`, `bash`, etc.).
2. **Hierarchical organization**: Consider using hierarchical numbering for subsections to make referencing easier.
3. **Tabular format for key facts**: The tables are very helpful - more structured data in tabular format would be valuable.
4. **Keywords or tags**: Adding semantic markers (like `#performance` or `#security`) to certain sections would help me quickly locate relevant guidance.

[^1]: This principle emphasizes human oversight for critical aspects like architecture, testing, and domain-specific decisions, ensuring AI assists rather than fully dictates development. -->


---
## 13. Files to NOT modify
TODO

<!-- These files control which files should be ignored by AI tools and indexing systems:

*   @.agentignore : Specifies files that should be ignored by the Cursor IDE, including:
    *   Build and distribution directories
    *   Environment and configuration files
    *   Large data files (parquet, arrow, pickle, etc.)
    *   Generated documentation
    *   Package-manager files (lock files)
    *   Logs and cache directories
    *   IDE and editor files
    *   Compiled binaries and media files

*   @.agentindexignore : Controls which files are excluded from Cursor's indexing to improve performance, including:
    *   All files in `.agentignore`
    *   Files that may contain sensitive information
    *   Large JSON data files
    *   Generated TypeSpec outputs
    *   Memory-store migration files
    *   Docker templates and configuration files

**Never modify these ignore files** without explicit permission, as they're carefully configured to optimize IDE performance while ensuring all relevant code is properly indexed.

**When adding new files or directories**, check these ignore patterns to ensure your files will be properly included in the IDE's indexing and AI assistance features. -->


---
## 14. AI Assistant Workflow: Step-by-Step Methodology
TODO

<!-- When responding to user instructions, the AI assistant (Claude, Cursor, GPT, etc.) should follow this process to ensure clarity, correctness, and maintainability:

1. **Consult Relevant Guidance**: When the user gives an instruction, consult the relevant instructions from `AGENTS.md` files (both root and directory-specific) for the request.
2. **Clarify Ambiguities**: Based on what you could gather, see if there's any need for clarifications. If so, ask the user targeted questions before proceeding.
3. **Break Down & Plan**: Break down the task at hand and chalk out a rough plan for carrying it out, referencing project conventions and best practices.
4. **Trivial Tasks**: If the plan/request is trivial, go ahead and get started immediately.
5. **Non-Trivial Tasks**: Otherwise, present the plan to the user for review and iterate based on their feedback.
6. **Track Progress**: Use a to-do list (internally, or optionally in a `TODOS.md` file) to keep track of your progress on multi-step or complex tasks.
7. **If Stuck, Re-plan**: If you get stuck or blocked, return to step 3 to re-evaluate and adjust your plan.
8. **Update Documentation**: Once the user's request is fulfilled, update relevant anchor comments (`AIDEV-NOTE`, etc.) and `AGENTS.md` files in the files and directories you touched.
9. **User Review**: After completing the task, ask the user to review what you've done, and repeat the process as needed.
10. **Session Boundaries**: If the user's request isn't directly related to the current context and can be safely started in a fresh session, suggest starting from scratch to avoid context confusion. -->
