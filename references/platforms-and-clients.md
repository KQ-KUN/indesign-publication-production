# Operating systems, InDesign versions and desktop agents

The Skill is a portable `SKILL.md` folder. Its scripts do not call a model API,
depend on Codex tools or read client credentials. A client still needs authorized
local file/command access on the computer where InDesign runs. Installing a Skill
does not grant those capabilities or substitute for a licensed Adobe application.

## Capability routing

| Environment | Route | Evidence boundary |
| --- | --- | --- |
| Windows with InDesign | Registry + process discovery; PowerShell 5.1 COM bridge | Real version/path returned by host; content/visual checks still separate |
| macOS with InDesign | `.app` Info.plist + process discovery; AppleScript/Apple Events | Adapter implemented; requires macOS Automation consent and native verification |
| Linux / WSL / container | Python/static/PDF checks; JSX bundle handed to Windows/macOS | No claim of native Linux InDesign; do not silently use Wine or cross into Windows |
| Remote desktop agent | Run adapter on the authorized desktop host, then return receipts/artifacts | A cloud filesystem alone cannot access the user's desktop host |
| GUI-only client | Prepare JSX + data; use InDesign's Scripts panel if GUI operation is available | Record manual/native result; do not invent a shell/MCP tool |

No fixed marketing-year-to-version table is used. Windows enumerates registered
`InDesign.Application.*` ProgIDs and reads their actual executable paths; macOS
reads app bundle versions. Default selection prefers the single already running
installation. Multiple running versions require an explicit discovered `--target`.
Cold launch is opt-in; with none running, the highest discovered numeric version
hint is selected only when `--allow-launch` is given. An explicit target overrides
that choice. Actual `app.version` is returned after attachment. Do not assume that
finding an executable proves licensing, startup readiness or API compatibility.

### Commands

Use `python`/`py -3` on Windows or `python3` on macOS/Linux, selecting an available
Python 3.10+ runtime. The launcher itself uses only Python's standard library.
Optional PDF/image checks retain their separately declared dependencies.

```text
python scripts/indesign_runtime.py detect
python scripts/indesign_runtime.py run scripts/runtime_probe.jsx --expect-prefix "PASS "
python scripts/indesign_runtime.py status <job-directory> --wait-seconds 10
python scripts/indesign_runtime.py run <authorized-build.jsx> --target <discovered-id> --wait-seconds 10
```

`detect` never activates COM or launches an application. It does not probe APIs
inside the application. `runtime_probe.jsx` reads only host version/path/document
count/modal state; it changes no documents or preferences. It is the small native
smoke test, not layout acceptance. Add `--allow-launch` only when starting an
application is within the user's authorization. Do not use that flag as a retry
after a failed attachment with another InDesign process already present.

`run` creates a request hash, job ID, receipt and per-user single-flight lock in the
OS temporary directory. `INDESIGN_SKILL_STATE_DIR` can override that lock directory
for a restricted environment; use the SAME directory for all callers sharing an
InDesign host. Job output defaults to the current project's ignored
`.artifacts/indesign-runtime/`. The worker continues when the short client wait
ends. `QUEUED`/`RUNNING` is not failure, and not permission to dispatch again. Use
`status` on the returned job. Never auto-delete a lock after a tool timeout; inspect
the recorded job, worker, host and logs. These locks do not serialize unrelated
third-party automation: do not operate the same host from another client at once.

`COMPLETED` means the host returned; optional `--expect-prefix` checks the build's
native result contract. It does not establish page count, source preservation or
visual acceptance. `FAILED` contains the original bridge/native error or logs.
Host execution has no destructive timeout: inspect the worker instead of killing
InDesign or clearing preferences. Windows checks executable identity and process
inventory before dispatch. When no Running Object Table attachment exists, it makes one registered COM
class binding only to a single ready matching process, then checks that no extra
process appeared. A mismatch/failure stops dispatch; it never retries activation. Registry discovery can miss a portable/custom
install; use the Scripts panel or add a verified discovery adapter, not a guessed
ProgID. macOS standard discovery searches `/Applications` and `~/Applications`;
custom locations need a verified adapter or the Scripts panel.

## DeepSeek DSH, Kimi and other desktop clients

Use the directory form, with required lowercase kebab-case `name` and a one-line
`description` in YAML frontmatter. Keep supporting scripts/references beside
`SKILL.md`; do not paste only the entrypoint and lose its resources. Relative
references resolve against the loaded Skill directory. `agents/openai.yaml` is
optional Codex UI metadata; the workflow must work without reading that file.

| Client | Install/discover | Execute |
| --- | --- | --- |
| DeepSeek Harness / DSH Desktop | Project `.agents/skills/indesign-publication-production/` or configured DSH Skill root | Authorized local command tool calls the same Python launcher |
| Kimi Code / Code Desktop | Project `.agents/skills/indesign-publication-production/` or configured Kimi Skill root | Invoke the Skill from the client catalog; use available local command tool |
| Kimi Work desktop | Import the complete local Skill folder/package using that version's Skills UI | Check file/command availability first; local execution or manual Scripts-panel handoff |
| Other Agent Skills clients | Use their documented skill root/import mechanism | Same files, standard Python CLI, or manual handoff |

For a shared project installation, put the folder ONE level under `.agents/skills`
at the actual project root, not nested arbitrarily. DSH/Kimi versions can override
discovery roots and duplicate-name precedence. Confirm the client catalog resolves
the intended `SKILL.md`; a folder on disk is not proof that a desktop app loaded
it. Plain web/chat mode without local tools cannot run InDesign. A third-party
desktop shell is not evidence about an official client's capabilities.

An MCP server is optional if the client already provides local command execution.
Do not install or expose a remote arbitrary-code service just for this Skill. When
the user already has an authorized InDesign MCP/remote bridge, validate its tool
schema, execution host, path mapping, result correlation and native version, then
apply the same verification ladder. Do not hardcode client-specific tool names.

An optional distribution helper creates a ZIP with `SKILL.md` at its root:

```text
python scripts/package_skill.py --out .artifacts/indesign-publication-production.zip
```

Only paths explicitly listed in `distribution-files.json` are included; `.git`, `.artifacts`, caches and project
manuscripts are excluded. Import shape and command permissions still need checking
in the particular desktop build. Do not modify client profiles or install plugins
without authorization. Retain the folder import path when ZIP import is unsupported.

## Compatibility claims and sources

Record separately: documentation support, fixture tests, native adapter test,
client load test, client command invocation and visual publication acceptance.
Windows success does not establish macOS execution; CLI success does not prove
DSH/Kimi's desktop catalog/tool permissions. Do not label untested clients PASS.

Primary sources checked 2026-11-10 (client details change):

- [Adobe application DOM: fullName and version](https://developer.adobe.com/indesign/uxp/dom/api/a/application/)
- [Adobe scripting panel and OS paths](https://helpx.adobe.com/indesign/desktop/automation-and-scripting/document-automation/automate-workflows-with-scripts.html)
- [Adobe supported native platforms](https://helpx.adobe.com/indesign/desktop/get-started/system-and-product-info/adobe-indesign-technical-requirements.html)
- [DSH official Skill provider discovery](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/subsystems/skills.md)
- [DSH official Desktop](https://github.com/deepseek-ai/deepseek-harness/blob/master/apps/desktop/README.md)
- [Kimi Code Agent Skills and scan roots](https://moonshotai.github.io/kimi-code/en/customization/skills.html)
- [Kimi Code Desktop](https://www.kimi.com/en/help/kimi-code/desktop-getting-started)
- [Kimi Work local Skills](https://www.kimi.com/en/help/kimi-work/overview)
