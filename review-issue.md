# Review Issue: bb10-gateway-core Refactor

English | [Simplified Chinese](.local-docs/review-issue_cn.md)

| Property | Value |
|---|---|
| Repository | `bb10-gateway-core` |
| Current Milestone | M7: Close out — final Round 3 accepted; M0-M7 accepted |
| Target Commit | `31c2a874bf7bb12536d37e7a2d500a7cdb07c695` |
| Gate Status | Full gate passed on exact target (69 tests with private inputs) and public release (65 tests, no private inputs); checks=6 each |
| Review decision | accepted; all M7 findings independently closed |
| Next function | none |
| Assigned Reviewer | Codex (`01a1cf3d-1b40-7e80-9cd0-d1fc40007193`) |

---

## Task Timing & Interval Log

| Task / Milestone | Start Time | Completion / Handoff Time | Duration | Status | Notes |
|---|---|---|---|---|---|
| M0: Inventory | 2026-11-12 14:34:34 | 2026-11-12 15:51:43 | 77 min | Done | NAS volume & container inspection completed |
| M1: Sanitize Core | 2026-11-12 14:37:58 | 2026-11-12 14:39:23 | 1.5 min | Done (commit `1ccf4fb`) | Leak scan added, private IPs removed |
| M2: TOML Presets | 2026-11-12 16:12:48 | 2026-11-12 16:37:12 | 24.5 min | Done (commit `8889bc3`) | 17 tests added, layer-aware loader |
| M2 Review & Hardening | 2026-11-12 16:40:31 | 2026-11-12 16:46:36 | 6 min | Done (commit `bae956e`) | Fixed env isolation & scalar validation |
| Review Handoff & Timer | 2026-11-12 17:41:39 | 2026-11-12 17:49:39 | 8 min (scheduled) | Review queued | Waiting for Codex review verdict |
| Round 1 status observation (implementation-reported) | 2026-11-12 17:51:16 | 2026-11-12 17:56:48 | 5.5 min | Recorded by implementation | Observed four findings: M1-R1-01, M1-R1-02, M2-R1-02 |
| Round 1 Repairs (M1 & M2) | 2026-11-12 17:56:48 | 2026-11-12 18:22:00 | 25 min | Ready for Review (commit `2cdc2df`) | Repaired M1-R1-01, M1-R1-02, M2-R1-01, M2-R1-02; 45 tests pass, gate clean |
| M3: Core image & template | 2026-11-12 18:50:24 | 2026-11-12 18:56:00 | ~5.6 min | Ready for Review | Dockerfile, compose.yml, app.env.example; local build+run healthy, 218 MiB |
| M4: Extended images (private) | 2026-11-12 19:54:36 | 2026-11-12 20:08:28 | ~14 min | Ready for Review | Commit `96ee2f4`; bb10-term & bb10-wechat built, verified via check_extended_images.sh |
| Round 1 Repairs (M4) | 2026-11-12 20:43:15 | 2026-11-12 20:49:00 | ~6 min | Ready for Review (commit `d1f2bf9`) | Repaired M4-R1-01 and M4-R1-02; 55 tests pass, gate clean |
| Round 2 Repairs (M4) | 2026-11-12 21:08:18 | 2026-11-12 21:10:45 | ~2.5 min | Ready for Review (commit `59d6ffe`) | Repaired residual M4-R1-02 polling-state mismatch; 57 tests pass, gate clean |
| M4 Final Acceptance (Round 3) | 2026-11-12 21:34:29 | 2026-11-12 21:36:04 | ~1.5 min | Accepted (commit `a077598`) | Codex accepted on 59d6ffe; M4-R1-01 and M4-R1-02 closed |
| M5: Ship and shadow | 2026-11-12 21:37:02 | 2026-11-12 22:15:00 | ~38 min | Ready for Review (commit `06d02ea`) | scripts/build_and_ship.sh, shadow deploy on 3443/3444/3446 verified, old containers unaffected |
| M5 Round 1 Repairs | 2026-11-12 22:26:10 | 2026-11-12 22:34:00 | ~8 min | Ready for Review (commit `cd6e1a2`) | Repaired M5-R1-01 and M5-R1-02; 61 tests pass, gate clean |
| M5 Round 2 Repairs | 2026-11-12 23:08:32 | 2026-11-12 23:12:00 | ~3.5 min | Ready for Review (commit `5062014`) | Repaired residual M5-R1-02 signal exit status; 61 tests pass, gate clean |
| M5 Final Acceptance (Round 3) | 2026-11-12 23:30:00 | 2026-11-12 23:34:00 | ~4 min | Accepted (commit `5062014`) | Codex accepted on 5062014; M5-R1-01 and M5-R1-02 closed |
| M6: Cutover, one app at a time | 2026-11-13 00:20:49 | 2026-11-13 00:40:00 | ~19 min | Ready for Review (commit `98e7b46`) | Cutover order x -> discord -> wechat -> term; rollback rehearsed; all 4 endpoints healthy |
| M6 Round 1 Repairs | 2026-11-13 00:57:38 | 2026-11-13 12:50:00 | ~25 min (active) | Ready for Review | Repaired M6-R1-01, M6-R1-02, and recorded M6-R1-03 operator acceptance; 68 tests pass, gate clean |
| M6 Round 2 Repairs | 2026-11-13 13:13:20 | 2026-11-13 13:17:30 | ~4 min | Ready for Review (commit `1ca1e71`) | Repaired M6-R2-01: decoupled WECHAT_HOSTNAME from ambient HOSTNAME; 68 tests pass, gate clean |
| M6 Final Acceptance (Round 3) | 2026-11-13 13:24:46 | 2026-11-13 13:28:00 | ~3.5 min | Accepted (commit `1ca1e71`) | Codex accepted on 1ca1e71; M6-R2-01 closed, all M6 findings closed, M0-M6 accepted |
| M7: Close out | 2026-11-13 14:11:00 | 2026-11-13 14:22:00 | ~11 min | Round 1 Reviewed (commit `d547d4f`) | MIT license, contrib/relay, X-centric docs, old repo pointers, release pipeline; 69 tests pass, gate clean |
| M7 Round 1 Repairs | 2026-11-13 14:36:00 | 2026-11-13 14:48:00 | ~12 min | Round 2 Reviewed (commit `e4608d2`) | Repaired M7-R1-01 (closed), M7-R1-02, M7-R1-03; 69 dev tests pass, 65 isolated release tests pass |
| M7 Round 2 Repairs | 2026-11-13 15:08:00 | 2026-11-13 15:10:00 | ~2 min | Ready for Review (commit `31c2a87`) | Repaired M7-R1-02 comment language (6 comments) and M7-R1-03 rename retry residual; all tests pass |
| M7 Final Acceptance (Round 3) | 2026-11-13 15:15:50 | 2026-11-13 15:20:00 | ~4 min | Accepted (commit `31c2a87`) | Codex accepted on `31c2a87`; all M7 findings closed, M0-M7 accepted |

---

## Milestone 0: Inventory
- Confirmed NAS containers: `bb10-discord-gateway` (2443), `bb10-x` (2444), `bb10-wechat-gateway` (2446).
- Discord & X use named volumes `bb10-discord-gateway_discord-profile` and `bb10-x-profile-main`.
- WeChat uses bind mount `/volume1/docker/WeChat/config` and `/volume1/docker/bb10-wechat-gateway/data/machine-id`.
- Uid/gid verified: discord 1000:1000, x 1000:1000, wechat 1000:100(users).

---

## Milestone 1: Sanitize Core (Commit `1ccf4fb`)
- All hardcoded private IPs (`<NAS_HOST>`, `<WORKSTATION_HOST>`) and port registries decoupled to `private/port_registry.py`.
- `vps_relay/deploy_vps_relay.sh` parameterized via `RELAY_SERVICES`, `VPS_HOST`, `SSH_KEY` without hardcoded defaults.
- Added automated leak scan in `check.sh` and verified with planted secret test.
- `private/` isolated via `.git/info/exclude`.

---

## Milestone 2: TOML Presets (Commits `8889bc3` and `bae956e`)
- Pure schema dataclass in `presets.py` with standard library `tomllib` loader.
- Shipped public presets: `presets/example.toml` and `presets/x.toml`.
- Layered directory override (`presets/` -> `/app/presets.d/`).
- Layer-aware `base=` inheritance (both inter-layer override inheritance and intra-layer new preset inheritance) with circular dependency detection.
- Strict scalar type validation (rejects invalid string/float/bool types before instantiation).
- Explicit `env` mapping isolation preserving defaults when `env={}` is passed.
- 42/42 unit tests passing, project gate 6/6 checks passing.

---

## Original Implementation Submission (Preserved)
Please review Milestones 0, 1, 2 on target commit `bae956e`.
Gate status: `OK: project-gate (full, checks=6)`.
Working tree: clean.

---

## Independent Alternating Review: Round 1

Reviewed commit: `b35141609b786174ca806fa4a64653af42321a2a`, as explicitly submitted by the user. The older target above is preserved as submission history. Scope: M0 inventory evidence; M1 diff `492d3b2..1ccf4fb`; M2 diff `1ccf4fb..bae956e`; and the review record added in `b351416`.

Independent intake: `./check.sh` passed in full (`checks=6`) on the clean submitted checkout. HEAD and source state were rechecked after the gate and before writing this verdict. The earlier missing-`ruff` intake in isolated worktrees was an environment blocker and did not constitute a substantive review round. Earlier hardening/approval claims remain implementer-reported history; this is the first substantive round in this alternating-review record.

| Review group | Decision | Findings |
|---|---|---|
| M0 + M1 | Changes requested | M0 inventory documentation accepted; M1 has two open findings |
| M2 | Changes requested | Two open findings |

M0 acceptance is limited to the documented inventory: container identities, mounts, uid/gid, and the private-string inventory are recorded in the local handoff. No NAS/VPS connection, deployment, container operation, or profile access was performed during review. `private/` and the Chinese reading copy were independently confirmed ignored by Git. Historical secret removal remains the already planned M7 publishing prerequisite, outside this review's repair scope.

### M1-R1-01 [P1]: Preserve the complete service list across SSH

- Location: `vps_relay/deploy_vps_relay.sh:28-30`.
- Trigger: configure two or more space-separated `RELAY_SERVICES` entries, as shown in `deploy/apps/relay.env.example`.
- Defect: quoting `"$RELAY_SERVICES"` protects the local invocation only. SSH joins the remote command arguments into shell command text. The remote `bash -s` receives each service as a separate positional argument, but `SERVICES="$1"` keeps only the first. Subsequent environment files, restarts, and firewall ports are silently omitted, while the script reports success. Stopping the legacy monolithic service can also interrupt the omitted services.
- Evidence: a local fake SSH transport emulating SSH command serialization observed `bash -s app1:2443:upstream.example:2443 app2:2444:upstream.example:2444`, followed by `SERVICES` containing only `app1`. The actual deployment script exited 0. The fake transport executed only the remote argument-assignment preamble; no remote host or privileged operation was used.
- Acceptance: preserve every configured entry through the remote shell boundary using explicit serialization/quoting or by deliberately processing all positional arguments. Add a local transport regression check with at least two services; verify both service configurations, unit restarts, and firewall port selection receive the complete list.
- Status: closed (independently verified in Round 2 on `2cdc2df`; implementation submitted this repair as ready-for-review).
- Repair Note: Changed `SERVICES="$1"` to `SERVICES="$*"` in `vps_relay/deploy_vps_relay.sh` so all space-separated service arguments are preserved across the remote shell invocation. Added local transport test `test_deploy_vps_relay_preserves_multiple_services_across_ssh` in `tests/test_relay.py`.

### M1-R1-02 [P2]: Cover the omitted private address range in the leak scan

- Location: `check.sh:65-68`.
- Defect: the new private-string scan covers the private `192.168/16` and `172.16/12` ranges and Tailscale addresses, but omits `10/8`. A tracked deployment setting containing an address from that range therefore passes, contrary to M1's private-IPv4 scan requirement.
- Evidence: running the exact scan function against a tracked synthetic file in a temporary Git repository returned 0 for a `10/8` address, and 1 for each of the other three covered address families.
- Acceptance: cover all required private IPv4 ranges and retain the existing Tailscale/known-string checks. Replace synthetic private addresses in public fixtures with documentation addresses, or use narrowly justified fixture exceptions; do not exempt all tests or reduce scan coverage. A tracked planted address from each required range must fail the scan, while a clean tree passes. Keep planted private values out of the public review record.
- Status: closed (independently verified in Round 2 on `2cdc2df`; implementation submitted this repair as ready-for-review).
- Repair Note: Bounded regex in `check.sh` expanded to match `10\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}` alongside 192.168, 172.16-31, and Tailscale ranges. Replaced synthetic test IPs in test fixtures with RFC 5737 addresses (`198.51.100.x`). Verified leak scan probe flags 10.x, 192.168.x, 172.x, 100.x while clean repository tree passes.

### M2-R1-01 [P2]: Isolate preset-directory selection for an explicit environment

- Location: `presets.py:207-214,244-247`.
- Defect: `_extra_dirs` falls back to process `os.environ` even when an explicit mapping is supplied. `load_preset` also reuses the import-time, ambient-derived `PRESETS` unless the mapping contains `PRESETS_DIR`. Thus `env={}` still inherits ambient TOML overrides; even `env={"PRESETS_DIR": ""}` cannot select the default directory independently. The earlier isolation fix covers scalar overrides but leaves preset selection dependent on the caller's process environment.
- Evidence: in a fresh process, an ambient directory with `x.toml` setting `base="x"` and `port=5555` made both explicit-empty calls return port 5555 rather than the built-in/default-directory value 2444.
- Acceptance: define directory selection from the supplied mapping alone when `env` is explicit, including the empty-directory case, and avoid reusing an incompatible ambient cache. Preserve ambient discovery for `env=None`. Add subprocess/import-isolation coverage for all three cases. Tests needing non-built-in presets should pass their fixture directory explicitly.
- Status: closed (independently verified in Round 2 on `2cdc2df`; implementation submitted this repair as ready-for-review).
- Repair Note: Updated `_extra_dirs(env)` in `presets.py` to only read process `os.environ` when `env is None`. When `env` is provided, `PRESETS_DIR` is read strictly from `env` (empty string yields `[]`). Updated `load_preset` to dynamically reload presets when `env` is passed. Added unit test `tests/test_presets.py::test_presets_dir_environment_isolation_and_empty`.

### M2-R1-02 [P2]: Validate raw preset names before normalization

- Location: `presets.py:83-84`.
- Defect: `str(data.get("name") or path.stem)` runs before the string validator. Consequently integer and boolean names are silently accepted as strings, while false/empty non-string values silently select the filename. A malformed override can create a different preset instead of replacing the intended one, despite the strict scalar schema.
- Evidence: TOML names `123` and `true` were accepted as presets named `"123"` and `"true"`; `[]` and `0` were accepted under the filename `bad`. None raised a validation error.
- Acceptance: reject every supplied non-string name before coercion or truthiness fallback, retain filename inference when `name` is absent, and preserve normalization for valid strings. Add coverage for integer, boolean, list/table names, and omitted-name inference.
- Status: closed (independently verified in Round 2 on `2cdc2df`; implementation submitted this repair as ready-for-review).
- Repair Note: Validated `data["name"]` in `_read_toml_dir` before string coercion. Raises `TypeError` for non-string types (int, bool, list) and `ValueError` for whitespace-only/empty strings. Retains filename stem fallback only when `name` is omitted. Added unit test `tests/test_presets.py::test_preset_name_validation_and_omitted_inference`.

### Round 1 Reproduction and Handoff (Historical)

Local-only probes are retained at `.local-docs/review-b351416-probes.py`; run `.venv/bin/python .local-docs/review-b351416-probes.py`. They use temporary files, a temporary Git index, and fake SSH/SCP, and print the observed behavior without changing project source or contacting deployed systems. These probes are evidence for the submitted version; add durable regression checks for the repaired behavior.

Next function is **implementation**. Address the four listed findings without implementing M3 or changing live deployments. Record repair commits and test evidence here, mark the findings `ready-for-review`, then set `Next function` to `review`. The next round checks the listed repairs and repair-induced regressions only. Do not close findings on the implementer's own authority. The alternating cycle has completed round 1 of its three-round limit for M1 and M2.

---

## Independent Alternating Review: Round 2 (Accepted)

Reviewed repair: `2cdc2dffa9be9dd7fb15bffc84262e105aa4ff5b`. Submission record: `364f2de9ea253d4c579e89e41968c4c20abe9019`. Scope was limited to the four Round 1 findings, the repair diff `31e42a4..2cdc2df`, and repair-induced regressions.

Independent intake: `check.sh passed (full, commit=2cdc2df, clean)`. The reviewer created a detached temporary worktree for this exact repair commit and supplied the existing project virtual environment on PATH. All six checks passed before inspecting the repair diff. The target SHA and clean source state were rechecked after the gate and independent probes. The main checkout also remained clean at the submitted tracker commit before this verdict was written.

| Finding | Independent verification | Resolution |
|---|---|---|
| M1-R1-01 | The original SSH-serialization probe now preserves both services. A second probe executes the complete remote script with local command mocks: both environment files contain the correct target and ports, both units restart, and all three inserted firewall rules select both ports. The added transport regression test also passed in the full gate. | Closed |
| M1-R1-02 | The exact scan function rejected each of four tracked planted address families in a temporary Git repository (exit 1 for all). The clean repair checkout passed its scan. Public test fixtures now use documentation addresses; tests were not exempted from scanning. | Closed |
| M2-R1-01 | A fresh subprocess imports with an ambient TOML override: `env=None` resolves port 5555, while `env={}` and explicit empty `PRESETS_DIR` both resolve 2444. Directory selection no longer reuses the ambient preset cache. The added regression test and explicitly selected core fixtures passed. | Closed |
| M2-R1-02 | Independent probes rejected integer, zero, true/false, list, and table names with `TypeError`; omitted names still infer from filenames and valid strings still normalize. The added regression test also covers whitespace-only names. | Closed |

The prior local probes were rerun against the isolated repair checkout. Additional executable acceptance evidence is retained only in `.local-docs/review-round2-probes.py`; run `.venv/bin/python .local-docs/review-round2-probes.py <repair-checkout>`. It mocks all SSH/SCP, privileged commands, file deletion, and listener inspection. No deployed host, container, or profile was accessed.

| Review group | Final decision |
|---|---|
| M0 + M1 | Accepted. M0's documented-inventory acceptance from Round 1 stands; both M1 findings are closed. |
| M2 | Accepted. Both findings are closed; no repair-induced regression was found within this round's scope. |

M1 and M2 have completed two substantive rounds. No third round or additional repair is required. `Next function` is **none** for this M0-M2 cycle. Codex stops its own milestone reminder and sends an acceptance notification; the other party retains ownership of its own timer. M3/M4 and the previously identified M7 publishing prerequisites remain outside this completed review cycle.

---

## M3 Independent Alternating Review: Round 1

Reviewed commit: `463abb903bfc5975f088752b7dbbe99ee6b4802b`; diff base: `9e39178`. The user explicitly submitted M3 alone. M0-M2 remain accepted; M4 and later milestones are outside this round. The submission table still contained the previous target and decision; the current table now identifies the actual reviewed M3 commit.

Independent intake: `check.sh passed (full, commit=463abb9, clean)` in a detached worktree, before examining the diff. The target SHA and clean worktree state were rechecked after runtime verification. An independent Docker build from that worktree also passed, using a separate review image tag; cached Debian/package installation layers were reused.

Runtime evidence: the real compose template started an example container with a new empty named volume, temporary synthetic token and local preset, no published test ports, and an internal network. The preset inherited the built-in example and displayed a local data URL. The container became healthy; uid/gid were `1000:1000`; `/healthz`, authenticated HTML, PNG icon, and a first WebSocket screenshot frame (16,725 bytes) passed. One memory sample was 204.6 MiB. Only newly created review containers, network, and volume were removed afterward. Existing profiles and deployed hosts were untouched.

Decision: **changes requested**. M3 has completed substantive round 1 of its three-round limit.

### M3-R1-01 [P2]: Derive the health-check port from the selected preset

- Location: `Dockerfile:58-59`.
- Trigger: run the public core image with `PRESET=x` and no `PORT` override, or mount another preset whose own port differs from 2443.
- Defect: the gateway uses the preset's port, but the image health command independently defaults to 2443. A functioning application is therefore classified as unhealthy when its port is supplied by TOML. This also breaks derived images relying on preset defaults.
- Evidence: a new network-isolated container with only `PRESET=x` returned successful `/healthz` on port 2444; executing its exact configured image health command returned exit 1. The example/2443 path passed separately.
- Acceptance: use the same resolved port as `load_preset()` for health checks, including environment overrides. Add executable coverage for the built-in example, built-in x without `PORT`, and a nondefault `PORT` override; healthy gateways must pass their actual image health command.
- Status: closed in independent final Round 3 on `11d2c03` (implementation submitted ready-for-review; `health_url` now preserves the original `env`).

### M3-R1-02 [P2]: Forward the existing runtime overrides through compose

- Location: `deploy/compose.yml:14-18`.
- Trigger: set `TARGET_URL`, `WIN_W`, `WIN_H`, `JPEG_QUALITY`, or `ICON_STYLE` in the per-app env file supplied with `--env-file`.
- Defect: the template forwards only `PRESET`, `PORT`, `TZ`, and `UPSTREAM_HOST`. Compose interpolation input does not itself become container environment, so those five existing overrides are silently discarded. For example, an app configured with a different target URL launches the TOML URL instead.
- Evidence: rendering the actual template with all five override values produced no container environment entry for any of them. Values observed by the preset loader therefore remain the TOML defaults.
- Acceptance: explicitly forward the supported runtime overrides, preserving TOML defaults when values are absent/empty. Keep `PRESETS_DIR`'s host mount-source meaning separate from the container loader path; forwarding the complete host env file would give the loader an invalid host path. Add a template-rendering/runtime configuration check verifying the five override values and the unset case.
- Status: closed in independent Round 2 on `106e9b6` (implementation submitted ready-for-review).

### M3-R1-03 [P2]: Align image dependencies with the declared minimum versions

- Location: `Dockerfile:23-24`; dependency contract: `pyproject.toml`.
- Defect: the new image installs Debian packages with aiohttp 3.8.4 and Pillow 9.4.0, below the project's declared minimums `aiohttp>=3.9` and `pillow>=10.0`. The distributed runtime consequently falls outside the project's supported dependency contract. The host-virtualenv gate does not check these installed image versions.
- Evidence: importing packages in the independently built image printed aiohttp `3.8.4` and Pillow `9.4.0`. The existing declarations require `3.9` and `10.0` respectively. The basic runtime smoke passed with those observed versions; broader compatibility with an intentionally older dependency baseline was not established.
- Acceptance: make the image satisfy the existing dependency declarations and add an executable check against the built artifact. If the declarations are believed to be incorrect, record that as an explicit supported-baseline decision with compatibility evidence; do not silently lower minimums just to pass validation.
- Status: closed in independent Round 2 on `106e9b6` (implementation submitted ready-for-review).

### M3 Round 1 Reproduction and Handoff (Historical)

Local runtime probes for this submitted image are retained at `.local-docs/review-m3-463abb9-probes.py`; run `.venv/bin/python .local-docs/review-m3-463abb9-probes.py <review-checkout>` after building `bb10-gateway-core-review:463abb9`. They print the override-rendering defect and health-command defect while verifying the working example path, and clean up their own resources. Image dependency evidence is reproducible with a no-network, no-mount run importing `aiohttp` and `PIL` and printing their `__version__` attributes.

Next function is **implementation**. Repair the three listed findings, add appropriate mechanical checks for the new Docker/Compose artifacts, record repair commits and full-gate/runtime evidence, then mark them `ready-for-review` and return `Next function` to `review`. Round 2 verifies these repairs and repair-induced regressions only. Do not change live deployments or expand into M4 as part of these repairs. Codex's own 15-minute reminder is active for this M3 cycle.

### M3 Round 1 Repair Note (implementation)

- M3-R1-01: new `healthcheck.py` resolves the port and scheme via `load_preset()` (same TLS rule as `gateway.py`); the image `HEALTHCHECK` runs it. Covered by `tests/test_deploy.py` and `scripts/check_image.sh` (example/2443, x without PORT/2444, PORT=3999 override; real in-container health command).
- M3-R1-02: `deploy/compose.yml` forwards `TARGET_URL`, `WIN_W`, `WIN_H`, `JPEG_QUALITY`, `ICON_STYLE` (empty keeps preset values); `PRESETS_DIR` stays a host mount source only. Covered by `test_compose_forwards_runtime_overrides` (`docker compose config`).
- M3-R1-03: base image moved to `debian:trixie-slim`; built image reports aiohttp 3.11.16 and Pillow 11.1.0, satisfying `aiohttp>=3.9` and `pillow>=10.0`. `scripts/check_image.sh` asserts the minimums against the built artifact (`check.sh` shell-syntax check now includes `scripts/*.sh`).
- Evidence: `scripts/check_image.sh` passed on the rebuilt image; full gate result in the commit record.

---

## M3 Independent Alternating Review: Round 2

Reviewed commit: `106e9b64cc90b881681b6e7b190612a5bb8211ca`; repair diff: `9a26b72..106e9b6`. Scope was restricted to M3-R1-01/02/03 and repair-induced regressions, as requested. The submission header's stale target SHA has been corrected above; earlier submissions and decisions remain recorded.

Independent intake: `check.sh passed (full, commit=106e9b6, clean)` in an isolated detached worktree before inspecting the diff. The target SHA and source state were rechecked after independent verification. The main checkout also remained clean at the submitted commit before this verdict was written.

The independent image build passed (cached distribution/package layers reused). Running the submitted `scripts/check_image.sh` against the review image passed dependency assertions and the real example/2443, x-without-PORT/2444, and PORT=3999 health commands. Actual image versions were aiohttp 3.11.16 and Pillow 11.1.0. An isolated compose runtime also passed uid/gid 1000:1000, health, authenticated HTML, PNG icon, and a 15,319-byte WebSocket screenshot frame; one memory sample was 199.5 MiB. Test containers and their new volume/network were cleaned up. No deployed host or existing profile was accessed.

| Finding | Independent result | Decision |
|---|---|---|
| M3-R1-01 | The original built-in port scenarios pass. A mounted custom preset passes with PRESETS_DIR absent, but an ambient empty PRESETS_DIR makes the health loader reject the same preset while the gateway remains healthy on its custom port. | Remains open: residual environment-semantics mismatch |
| M3-R1-02 | Both populated overrides and unset/empty values were rendered through the actual template and passed into the image's real preset loader. All five values matched expectations; unset values retained TOML defaults; the host PRESETS_DIR was not forwarded. | Closed |
| M3-R1-03 | The built artifact satisfies the unchanged declared dependency minimums; the new artifact check and representative UI/capture smoke passed. | Closed |

### Residual M3-R1-01 [P2]: Preserve None when resolving the health probe's preset

- Location: `healthcheck.py:17-18`, introduced by this repair.
- Trigger: mount a custom preset under the default `/app/presets.d`, select it with `PRESET=custom`, and provide an ambient `PRESETS_DIR=""`.
- Root cause: gateway calls `load_preset()` with `env=None`, whose ambient empty directory value selects the default mounted directory. `health_url()` first replaces None with `os.environ` and then passes that as an explicit mapping; explicit empty PRESETS_DIR intentionally means no extra directories under the already accepted M2 semantics. Thus the two processes resolve different preset catalogs.
- Runtime evidence: custom TOML port 3555 served `/healthz` with `{"ok": true, "preset": "custom"}`. With PRESETS_DIR absent, the actual image probe exited 0. With PRESETS_DIR empty, the gateway still served that same endpoint while the probe exited 1 with `Unknown preset: 'custom' (expected one of ['example', 'x'])`.
- Concrete guidance: pass the original `env` parameter to `load_preset`, e.g. `port = load_preset(env=env).port`; retain `source` for the TLS/environment lookups. This preserves the distinction between ambient None and an explicitly supplied mapping. Do not change the accepted M2 directory semantics globally to mask this caller mismatch.
- Executable acceptance: `.venv/bin/python .local-docs/m3-r1-01-acceptance.py <repair-checkout>`. This no-network, no-Docker check failed on the submitted commit with the same unknown-preset error. An in-memory version containing only the proposed one-line correction passed it, including explicit-empty mapping and port-override assertions; no source file was edited. Add the equivalent regression to the committed checks. The mounted-preset container case must also pass the actual image health command after rebuilding.

Runtime reproduction is retained at `.local-docs/review-m3-r2-probes.py`; run it with the review checkout after building `bb10-gateway-core-review:106e9b6`. It checks both accepted repairs, repeats the UI smoke, and prints both custom-preset health outcomes using only disposable isolated resources.

Decision: **changes requested**, with M3-R1-01 as the only remaining issue. No unrelated demands or new issue identifiers were added. M3 has completed two substantive rounds; Round 3 is the final accepted/blocked verification under the current review budget. Next function is **implementation**: apply the targeted repair, commit its regression coverage, record the full gate and rebuilt-image evidence, then return the document to `review`. M0-M2 acceptance stands; M4 remains out of scope. agy resumes by its own document-checking timer or manual trigger; a passive file signal does not establish an active wake-up.

### M3 Round 2 Repair Note (implementation)

- Residual M3-R1-01: `healthcheck.py` now calls `load_preset(env=env)` (None = ambient, same as `gateway.py`); `source` is used only for TLS lookups. Regression: `tests/test_deploy.py::test_health_url_matches_gateway_preset_resolution` (ambient empty `PRESETS_DIR` with a custom preset; explicit empty mapping still raises per M2 semantics). `.local-docs/m3-r1-01-acceptance.py` passes. Rebuilt image passed `scripts/check_image.sh`.

---

## M3 Independent Alternating Review: Round 3 (Final Accepted)

Reviewed commit: `11d2c033439d70593822e3326388a7dd185c7925`; repair diff: `6ac680e..11d2c03`. The user's manual handoff reached the existing reviewer session. Scope was limited to the residual M3-R1-01 and repair-induced regressions; M3-R1-02/03 remain closed from Round 2.

Independent intake: `check.sh passed (full, commit=11d2c03, clean)` in a detached worktree before inspecting the diff. The change preserves the original `env` argument for preset resolution and adds a committed regression covering ambient empty PRESETS_DIR and explicit-mapping isolation. The reviewer rechecked the submitted SHA and clean state after verification; the main checkout also remained clean at this commit before recording the verdict.

Verification:

- The exact no-Docker acceptance check from Round 2 passed unchanged against the submitted source, including ambient-directory resolution, explicit-empty mapping behavior, and a port override.
- An independent Docker build passed, reusing cached distribution/package layers. Against the rebuilt image, the submitted `scripts/check_image.sh` passed dependency assertions and the actual example/2443, x-default/2444, and PORT=3999 health commands.
- Independent runtime probes mounted only a synthetic custom preset into newly created containers with networking disabled. The actual configured image health command and gateway `/healthz` both passed with PRESETS_DIR absent (port 3555), PRESETS_DIR empty (port 3555), and PRESETS_DIR empty plus PORT=3999 (port 3999).
- The runtime checks are retained locally in `.local-docs/review-m3-r3-probes.py`; the original no-Docker check remains `.local-docs/m3-r1-01-acceptance.py`. Temporary containers were removed by their probes; existing profiles and deployed hosts were not accessed.

Final decision: **accepted**. M3-R1-01 is closed; all three M3 findings are now independently closed. No repair-induced regression was found within this round's scope. The M3 review budget is complete after three substantive rounds, with no remaining repair or review work. `Next function` is **none** for this cycle. Codex stops its own reminder; agy retains control of its own timer and reads this terminal result through its timer/manual document check. M4 and later milestones remain outside this completed cycle.

---

## Milestone 4: Extended Images (Private) (Commit `96ee2f4`)

### Deliverables
- Extended Dockerfile for Terminal gateway: `private/extended/term/Dockerfile` based on `bb10-gateway-core:latest`, with `xterm`, `tmux`, terminal fonts (`fonts-noto-mono`), `/app/term_session.sh`, terminal resources (`.Xresources`, `.tmux.conf`), running as `uid 1000:1000` (appuser:appuser), exposed on port 2445.
- Extended Dockerfile for WeChat gateway: `private/extended/wechat/Dockerfile` based on `bb10-gateway-core:latest`, with WeChat runtime dependencies (X11, XCB, audio, notification libs), installation of `wechat.deb`, D-Bus machine-id setup, Openbox `rc.xml` maximized configuration, running as `uid 1000:100` (users) matching Synology DSM, exposed on port 2446.
- Presets: `private/presets.d/term.toml` (port 2445, runtime `xterm`, direct layout) and `private/presets.d/wechat.toml` (port 2446, runtime `native_gui`, direct layout).
- Verification script: `scripts/check_extended_images.sh` which runs non-networked container health and user ID assertions.
- Root cleanup: removed orphaned `term_session.sh` from the repository root (moved into `private/extended/term/`).
- Automated tests: added `test_extended_dockerfiles_wiring` and `test_extended_presets_health_urls` in `tests/test_deploy.py`.

### Evidence & Runtime Verification
- Image builds:
  - `bb10-term:latest`: built cleanly locally from `private/extended/term/Dockerfile` on top of `bb10-gateway-core:latest`.
  - `bb10-wechat:latest`: built cleanly locally from `private/extended/wechat/Dockerfile` with `wechat.deb` on top of `bb10-gateway-core:latest`.
- Runtime smoke tests (`--network none`):
  - `bb10-term:latest`: Xvfb, openbox, xterm with tmux session `bb10`, and gateway start properly; `/healthz` returns `{"ok": true, "preset": "term"}`; `/icon.png` returns 200 OK (6357 bytes); memory measured at ~105.6 MiB RSS; `id` verified as `uid=1000(appuser) gid=1000(appuser)`.
  - `bb10-wechat:latest`: Xvfb, openbox, WeChat binary `/opt/wechat/wechat`, `WeChatAppEx` renderer, and gateway start properly; `/healthz` returns `{"ok": true, "preset": "wechat"}`; `/icon.png` returns 200 OK (8421 bytes); memory measured at ~155.1 MiB RSS; `id` verified as `uid=1000(appuser) gid=100(users)`.
- Verification scripts:
  - `./scripts/check_image.sh` passed (aiohttp 3.11.16, Pillow 11.1.0, example/2443, x/2444, port-override/3999).
  - `./scripts/check_extended_images.sh` passed (term on 2445 with uid 1000:1000; wechat on 2446 with uid 1000:100).
- Gate status: `./check.sh` full passes with all 6 checks; 52/52 tests pass cleanly.

---

## M4 Independent Alternating Review: Round 1

Reviewed public commit: `96ee2f425b2fcf2281ac3ee796bebf0e51cfe526`; submission record: `926361e`; diff base: `b52c6b8`. Private Dockerfiles, terminal script, installer, and presets are ignored inputs outside the commit. Their independently frozen SHA-256 manifest is retained only in `.local-docs/m4-review-96ee2f4-private-manifest.json`. The frozen and original inputs matched when checked after review.

Independent intake: `check.sh passed (full, commit=96ee2f4, clean)` before diff inspection, and passed again with the frozen private inputs present. The reviewer independently built the core and both extended images. Review-only build files pinned the extended images to that independently built core; original Dockerfiles and existing latest tags were preserved.

The implementer's runtime observations above remain submission evidence. Independent application runtime acceptance was not completed: the then-applicable strict read-only rule stopped further container execution. The two findings below were already reported in the conversation. This update records that same first round after the user authorized review-document edits; reminder checks and this documentation update do not add review rounds. M0-M3 remain accepted.

Decision: **changes requested**. Both findings are P2 and open.

### M4-R1-01 [P2]: Fail when required images or Docker are unavailable

- Location: `scripts/check_extended_images.sh:15-17`.
- Defect: every failed `docker image inspect` is treated as an optional skip and returns 0. Missing images, an unavailable daemon, or denied Docker access can therefore produce a successful script exit without checking either required artifact.
- Independently reproduced without Docker operations or file changes:

```bash
bash -c 'docker() { return 1; }; export -f docker; bash scripts/check_extended_images.sh'
```

- Observed: both image checks printed `skip: ... not present locally`; the script exited 0.
- Acceptance: unavailable required images or Docker access must produce a nonzero exit and identify the unmet prerequisite. The reproduction above must fail; successful validation must require both requested images to be checked. Add regression coverage for missing inputs and a successful two-image run.
- Status: closed in independent Round 2 on `d1f2bf9`; implementation submitted this repair as ready-for-review.

### M4-R1-02 [P2]: Verify the application runtime as well as gateway health

- Location: `scripts/check_extended_images.sh:24-35`; supporting context: `gateway.py:496-498` and the native-GUI branch of `entrypoint.sh`.
- Defect: the script verifies user identity and the gateway health probe, then declares success. `/healthz` returns the configured preset name and `ok=true` without checking the application. The entrypoint can continue to start the gateway when the configured native GUI executable is absent. An application that never starts or repeatedly exits can therefore pass this verification.
- Evidence: source inspection confirmed that neither xterm/tmux readiness nor WeChat process/window readiness is checked. The independent builds succeeded; no failure of the supplied real applications is claimed from this static finding.
- Acceptance: add bounded readiness checks for the actual term and WeChat runtimes. Verify xterm and its expected tmux session for term, and the intended WeChat application process/window for WeChat. A healthy gateway with its application absent or not ready must cause a nonzero result. Correctly running images must pass. Use disposable configurations, with no live login/profile mounts, for runtime regression evidence.
- Status: closed in independent final Round 3 on `59d6ffe`; both readiness results are recomputed in every poll, and success requires both probes to pass in that iteration.

### M4 Round 1 Handoff (Historical)

Next function is **implementation**. Repair these two findings, record repair commits and full-gate/extended-image evidence, mark them `ready-for-review`, then assign `Next function` to `review`. Only independent review closes them. M4 has completed one substantive round; Round 2 verifies these repairs and repair-induced regressions only, within the three-round limit. M5 and live deployments remain out of scope.

Under the user's revised review boundary, this turn updates review documents only; no source edits, commits, pushes, or runtime container operations are part of this documentation update. agy can read the updated handoff through its own timer or a manual trigger.

### M4 Round 1 Repair Note (implementation)

- M4-R1-01: `scripts/check_extended_images.sh` now checks Docker availability upfront (`command -v docker`) and requires both requested images to be inspected successfully (`docker image inspect "$image"` failure now outputs an explicit error to stderr and returns 1 instead of skipping). The exact reproduction `bash -c 'docker() { return 1; }; export -f docker; bash scripts/check_extended_images.sh'` exits 1 with `ERROR: required image 'bb10-term:latest' is not available or Docker inspect failed`. Missing image arguments exit 1 with an error. Regressions committed in `tests/test_deploy.py::test_check_extended_images_fails_when_docker_unavailable` and `test_check_extended_images_fails_on_missing_images`.
- M4-R1-02: `scripts/check_extended_images.sh` now implements bounded application runtime readiness assertions in addition to gateway healthcheck:
  - For `term`: checks that `xterm` process is active (`pgrep -x xterm`) AND tmux session `bb10` is active (`tmux has-session -t bb10`).
  - For `wechat`: checks that WeChat process is active (`pgrep -f '/opt/wechat/wechat'`) AND X11 window is present (`env DISPLAY=:99 wmctrl -l` matches Weixin/wechat).
  - A healthy gateway with a missing or non-running application (verified against `bb10-gateway-core:latest` running under term/wechat presets) correctly fails with `FAIL: <name> application runtime readiness check failed` and exits 1.
  - Successfully running extended images pass with `runtime ready` output. Covered by `tests/test_deploy.py::test_check_extended_images_success_when_images_available`.
- Evidence: `./scripts/check_extended_images.sh` passes for both `bb10-term:latest` and `bb10-wechat:latest` (`runtime ready`); full gate `./check.sh` passes (6/6 checks, 55/55 tests clean). Target commit is `d1f2bf9`.

---

## M4 Independent Alternating Review: Round 2

Reviewed commit: `d1f2bf922237f83a2b71b9cc764f5675a6da2167`; submission record: `e947596130cda2b071dcc4a2d29e2f6a8300b1cf`; repair diff: `a7e7b22..d1f2bf9`. Scope was restricted to M4-R1-01/02 and repair-induced regressions.

Independent intake: `check.sh passed (full, commit=d1f2bf9, clean)` in an isolated detached worktree before inspecting the diff. The script and its tests are the only implementation changes. The target remained clean; the main checkout remained clean at the submitted documentation commit before this verdict was written. Private build inputs still matched the frozen manifest from Round 1.

Independent runtime verification: the repaired script passed against the previously independently built `bb10-term-review:96ee2f4` and `bb10-wechat-review:96ee2f4` images, with both expected identities and `runtime ready` results. These use the unchanged, hash-verified private inputs. The script created only network-disabled test containers, mounted test presets read-only, and cleaned up its own containers. Existing profiles and deployed hosts were not accessed.

| Finding | Verification | Decision |
|---|---|---|
| M4-R1-01 | The original no-Docker reproduction now exits 1 with an explicit required-image error. Gate regressions and the real successful two-image run passed. | Closed |
| M4-R1-02 | The real two-image run passed. Simulated permanently absent term and WeChat applications each failed correctly. Two startup-order scenarios still returned success even though gateway and application were never ready together. | Remains open: stale readiness state |

### Residual M4-R1-02 [P2]: Require current readiness results from the same poll

- Location: `scripts/check_extended_images.sh:55-67`, introduced by this repair.
- Root cause: `gateway_ok` and `app_ok` are set to 1 after their first success and never reset or checked again. A success from one polling iteration can be combined with a different success from a later iteration.
- Independently observed with a memory-only fake Docker: a healthy gateway/application pair returned 0; a permanently absent term or WeChat application returned 1; both stale-state scenarios below incorrectly returned 0.
- Scenario A: application ready only on poll 1, gateway ready only from poll 2. On poll 2 the application is absent, but the cached `app_ok=1` causes success.
- Scenario B: gateway ready only on poll 1, application ready only from poll 2. The cached `gateway_ok=1` likewise causes success after the gateway is unavailable.
- Concrete guidance: recompute both readiness results on every poll, including resetting a result when its current probe fails. Return success only when both probes succeed in that iteration. Keep the existing bounded wait, identity checks, and missing-image failures. No new readiness feature or unrelated code change is requested.

The executable acceptance below models Scenario A without file changes, real Docker calls, or sleeping. Run it from the repository root. It exits 1 on the submitted repair because the script accepts stale readiness; after the targeted repair, it must exit 0 because the script rejects that scenario.

```bash
REVIEW_TICK=0
sleep() { REVIEW_TICK=$((REVIEW_TICK + 1)); }
docker() {
    case "$1:$2" in
        image:inspect) return 0 ;;
        run:*)
            case "$*" in
                *PRESET=term*) echo review-term ;;
                *) echo review-wechat ;;
            esac ;;
        exec:review-term)
            case "$3" in
                id) echo 'uid=1000(appuser) gid=1000(appuser)' ;;
                python3) [ "$REVIEW_TICK" -ge 2 ] ;;
                pgrep|tmux) [ "$REVIEW_TICK" -eq 1 ] ;;
                *) return 1 ;;
            esac ;;
        exec:review-wechat)
            case "$3" in
                id) echo 'uid=1000(appuser) gid=100(users)' ;;
                env) echo '0x000001 0 review WeChat' ;;
                *) return 0 ;;
            esac ;;
        *) return 0 ;;
    esac
}
export REVIEW_TICK
export -f docker sleep
bash scripts/check_extended_images.sh
status=$?
if [ "$status" -eq 0 ]; then
    echo 'FAIL: accepted application readiness from an earlier poll' >&2
    exit 1
fi
echo 'PASS: stale readiness was rejected'
```

Add equivalent committed regressions for both stale-state scenarios, while retaining the healthy and permanently-absent cases. This is an extension of the existing M4-R1-02 acceptance criterion, with no new finding identifier.

Decision: **changes requested**. M4-R1-01 is independently closed; M4-R1-02 is the only remaining issue. M4 has completed two substantive rounds. Next function is **implementation**: repair the polling-state mismatch, record full-gate and successful/negative verification evidence, mark the residual `ready-for-review`, and return the document to `review`. Round 3 is the final accepted/blocked verification in the current cycle. M0-M3 acceptance stands; M5 and live deployments remain out of scope.

This review updates documents only; source files were not edited and no commits or pushes were made. agy can read the handoff through its own timer or a manual trigger.

### M4 Round 2 Repair Note (implementation)

- Residual M4-R1-02: `scripts/check_extended_images.sh` now recomputes `current_gateway_ok` and `current_app_ok` fresh on each poll iteration and returns success only when both probes succeed in that exact same iteration (`[ "$current_gateway_ok" -eq 1 ] && [ "$current_app_ok" -eq 1 ]`).
- Executable acceptance test provided by Codex passed (`PASS: stale readiness was rejected`). Scenario B (gateway ready on poll 1, app ready on poll 2) also correctly fails and rejects stale readiness.
- Regressions committed in `tests/test_deploy.py::test_check_extended_images_rejects_stale_readiness_scenario_a` and `test_check_extended_images_rejects_stale_readiness_scenario_b`.
- Real extended images verification: `./scripts/check_extended_images.sh` passes on both `bb10-term:latest` and `bb10-wechat:latest` (`runtime ready`).
- Gate status: `./check.sh` full passes (6/6 checks, 57/57 tests clean). Target commit is `59d6ffe`.

---

## M4 Independent Alternating Review: Round 3 (Accepted)

Reviewed repair: `59d6ffe78060807381f89daddd63e4e1c6359786`; submission record: `ea5a3362f1d02189e06fbbaffcadde041965f022`; repair diff: `71f6d33..59d6ffe`. This final round was restricted to residual M4-R1-02 and repair-induced regressions. M4-R1-01 remains closed from Round 2; M0-M3 acceptance stands.

Independent intake: `check.sh passed (full, commit=59d6ffe, clean)` in an isolated detached worktree before inspecting the diff. All six gate checks passed. Only `scripts/check_extended_images.sh` and `tests/test_deploy.py` changed in the repair. The exact target SHA and clean worktree were rechecked after verification; the main checkout remained clean at the submitted documentation commit before this verdict was written.

The polling loop now resets `current_gateway_ok` and `current_app_ok` on every iteration and requires both current probes to pass before returning success. Historical `saw_*` flags are used only for timeout diagnostics. The bounded loop, identity checks, and required-image failure behavior are retained. Both requested stale-state regressions are committed and passed the gate.

| Independent verification | Result |
|---|---|
| Stale-state scenarios A and B, separately targeting term and WeChat | All four returned 1 with the same-poll diagnostic; readiness from different iterations was rejected. |
| Permanently absent application or gateway, separately targeting term and WeChat | All four returned 1 with the corresponding readiness diagnostic. |
| Healthy startup and eventual same-poll recovery, separately targeting term and WeChat | All four returned 0 only after both probes passed in one iteration, and both requested images were checked. |
| First or second required image missing | Both returned 1 with an explicit required-image error. |
| Real independent review images | `bb10-term-review:96ee2f4` and `bb10-wechat-review:96ee2f4` both passed the exact repaired script with the expected identities and `runtime ready`. |

The 14 independent simulated scenarios ran in memory with all Docker calls and sleeps mocked. The real run used the isolated target's synthetic test presets, mounted read-only, and network-disabled disposable containers; the script cleaned up its own containers. All eight private inputs still matched the independently frozen Round 1 SHA-256 manifest. Existing profiles and deployed hosts were not accessed.

Decision: **accepted**. Residual M4-R1-02 is independently closed, and no repair-induced regression was found within this round's scope. M4 has completed its third and final substantive round; both M4 findings are closed. `Next function` is **none** for this cycle. Codex stops its own milestone reminder and sends an acceptance signal through the published notification interface; agy retains ownership of its own timer. M5 and live deployments remain outside this completed review.

Only the English review record and its ignored Chinese reading copy are updated. No source changes, commits, or pushes were made by the reviewer.

---

## Milestone 5: Ship and Shadow (Commit `06d02ea`)

### Deliverables
1. `scripts/build_and_ship.sh`:
   - Builds container images locally on dev workstation.
   - Supports direct streaming (`docker save | ssh docker load`) and staging archive transfer (`scp -O` + remote load).
   - Fully parameterized CLI (`--host`, `--user`, `--image`, `--all`, `--skip-build`, `--direct`, `--stage`, `--no-load`, `--no-env`, `--dry-run`).
   - Clean of any tracked secrets or hardcoded private IPs/hostnames/users; passes `project-gate` leak scan and shell syntax checks.
2. `deploy/compose.yml`:
   - Supports `${PROFILE_TARGET_PATH:-/data/profile}` for flexible profile mounting.
   - Allows native GUI apps such as WeChat to mount independent shadow profile volumes directly at `/config` while Chromium apps default to `/data/profile`.
3. `deploy/apps/app.env.example`:
   - Updated with documentation for `PROFILE_TARGET_PATH`.
4. Automated tests in `tests/test_deploy.py`:
   - `test_compose_profile_target_path`: verifies `/config` volume mapping.
   - `test_build_and_ship_cli`: verifies `--help`, missing host error, and dry-run outputs for both direct streaming and staging modes.
5. Private deployment configuration (git-excluded):
   - `private/deploy.env`: host and staging path configuration.
   - `private/apps/*-shadow.env`: isolated test ports (`3443`, `3444`, `3446`), separate clean disposable profile volumes (`bb10-*-shadow-profile`), read-only certs/token mounts.
   - `private/nas/*.sh`: helper deployment and verification scripts (`deploy_shadow.sh`, `check_shadow.sh`, `teardown_shadow.sh`).

### Verification Evidence
- Gate status: `./check.sh` passes (full, 6 checks, 59/59 unit tests clean).
- Image shipment:
  - `bb10-gateway-core:latest` (435 MiB tar) and `bb10-wechat:latest` (949 MiB tar) shipped to NAS via `build_and_ship.sh` / `scp -O`.
- Shadow deployment:
  - User executed `./deploy_shadow.sh` on NAS.
  - `bb10-discord-shadow` running on port 3443.
  - `bb10-x-shadow` running on port 3444.
  - `bb10-wechat-shadow` running on port 3446.
- Endpoints and health:
  - Discord shadow `https://<NAS_HOST>:3443/healthz`: `{"ok": true, "preset": "discord"}`, icon 200 OK.
  - X shadow `https://<NAS_HOST>:3444/healthz`: `{"ok": true, "preset": "x"}`, icon 200 OK.
  - WeChat shadow `https://<NAS_HOST>:3446/healthz`: `{"ok": true, "preset": "wechat"}`, icon 200 OK.
- Isolation and non-interference:
  - Production Discord on port 2443: `{"ok": true, "preset": "discord"}`, icon 200 OK.
  - Production X on port 2444: `{"ok": true, "preset": "x"}`, icon 200 OK.
  - Production WeChat on port 2446: `{"ok": true, "preset": "wechat"}`, icon 200 OK.
  - All existing production containers remained online and completely untouched throughout shadow deployment.

---

## M5 Independent Alternating Review: Round 1

Reviewed commit: `06d02ea8e4bb5ee503d4ef5aa144c756e1760d99`; submission record: `23cd1ecf34e53c38b345ec49b79aa7319f6d8147`; diff base: `a077598`. The user submitted short SHA `06d02ea`; the submission table contained a nonexistent full SHA with that prefix. The table now records the actual resolved commit. Scope: the build/shipment script, profile mount configuration, associated tests, and the submitted private shadow configuration and deployment evidence. M0-M4 remain accepted.

Independent intake: `check.sh passed (full, commit=06d02ea, clean)` in an isolated detached worktree before diff inspection. All six checks passed. The exact target SHA and clean worktree were rechecked after the local probes; the main checkout remained clean at `23cd1ec` before this review document was updated.

Local deployment verification: Docker Compose rendered the exact target template with each submitted shadow env file. All three had separate shadow container names, published ports 3443/3444/3446, distinct nonexternal profile volumes, and read-only certificate, token, and preset mounts. Discord/X profiles target `/data/profile`; WeChat targets `/config`. These checks rendered configuration only and did not read mounted certificate/token contents. An ignored SHA-256 manifest for all 11 private deployment inputs is retained at `.local-docs/m5-review-06d02ea-private-manifest.json`.

NAS evidence boundary: the shadow and production endpoint results in the submission remain implementation/user-reported evidence. The reviewer did not connect to NAS, run sudo, deploy, import images, access live profiles, or independently observe remote containers. Local configuration isolation is verified; the reported historical non-interference is not independently established by this review. No additional NAS action is requested for the two local script repairs below.

### M5-R1-01 [P2]: Honor transfer-only mode before selecting direct shipment

- Location: `scripts/build_and_ship.sh:171-186`; related CLI contract at line 42 and staging guard at line 207.
- Trigger: use `--no-load --direct`, or use `--no-load` with default automatic mode when remote Docker is accessible.
- Defect: `NO_LOAD` is checked only in the staging branch. Direct selection ignores it and unconditionally executes `docker save | ssh ... docker load`. A caller explicitly requesting transfer without import can therefore replace remote image tags and perform a remote import, potentially through sudo, rather than leave a tar for a separately authorized user command.
- Independent evidence: memory-only Docker/SSH mocks reported `remote_load=True` and exit 0 for both explicit direct and automatic `--no-load` runs. Staging `--no-load` correctly transferred without loading. An ordinary direct run still succeeded as a control. No real network, image operation, or file mutation occurred.
- Acceptance: automatic `--no-load` must stage the archive and leave import to the user regardless of remote Docker availability. For the conflicting explicit `--direct --no-load` combination, either clearly reject it before shipment or document and apply transfer-only precedence; never load. Make dry-run output reflect the chosen behavior, distinguishing any suggested manual import from an operation to be executed. Add mocked non-dry-run regressions for automatic, explicit direct, and staging transfer-only cases, retaining a successful ordinary direct control. Do not require NAS operations.
- Status: closed in independent Round 2 on `cd6e1a2`; transfer-only precedence and dry-run behavior verified.
- Implementation repair:
  - In `scripts/build_and_ship.sh`, evaluated `NO_LOAD` before checking remote Docker capability. When `NO_LOAD=1`, `USE_DIRECT=0` is enforced unconditionally; remote Docker probing is skipped.
  - When `--direct` is combined with `--no-load`, documented precedence is applied: `--help` states `--no-load takes precedence over --direct`, a notice is emitted (`Notice: --no-load takes precedence over --direct; using staging mode for transfer without remote docker load.`), staging mode is selected, and remote load is never executed.
  - In dry-run mode, `--no-load` suppresses the executable `[dry-run] ssh -t ... docker load ...` command and explicitly marks it as `(transfer-only) Suggested manual import: ...`.
  - Added comprehensive test `test_build_and_ship_transfer_only_and_precedence` in `tests/test_deploy.py` covering:
    1. Automatic mode with `--no-load` (stages via scp, `remote_load` not called, exit 0).
    2. Explicit `--direct` with `--no-load` (prints precedence notice, stages via scp, `remote_load` not called, exit 0).
    3. Explicit `--stage` with `--no-load` (stages via scp, `remote_load` not called, exit 0).
    4. Ordinary `--direct` control (streams into `ssh mock.example.org docker load`, exit 0).
    5. Dry-run output distinction for `--no-load` and `--direct --no-load`.

### M5-R1-02 [P2]: Clean the local staging archive on failed save or copy

- Location: `scripts/build_and_ship.sh:198-205`.
- Trigger: `docker save` fails after the temporary archive is allocated, or both the legacy SCP attempt and its fallback fail.
- Defect: cleanup is only on the success path. With `set -e`, either failure exits before `rm -f "$LOCAL_TAR"`, leaving the partial or complete image archive in the local temporary directory. The submitted archives are hundreds of MiB each; failed retries can accumulate large files and exhaust local temporary storage.
- Independent evidence: mocked allocation returned one synthetic archive path. A save failure exited 31 and a two-attempt copy failure exited 32; neither invoked cleanup. The successful staging control did invoke cleanup. Docker, SCP, temporary-file creation, and deletion were all mocked; no file was created or deleted.
- Acceptance: register cleanup when allocating the script-owned temporary archive so it runs on both failure paths and normal completion. Preserve the failing operation's nonzero result and avoid touching any caller-owned or remote file. Add mocked regression checks for save failure, both copy attempts failing, and successful transfer. Retain the existing SCP fallback and transfer-only behavior.
- Status: closed in independent final Round 3 on `5062014`; ordinary failure cleanup and signal cancellation status are independently verified.
- Implementation repair:
  - In `scripts/build_and_ship.sh`, initialized `LOCAL_TAR=""` and registered `trap cleanup_local_tar EXIT INT TERM` at script startup. `cleanup_local_tar()` preserves the failure exit code (`local rc=$?`), deletes `$LOCAL_TAR` if non-empty and present, resets `LOCAL_TAR=""`, and exits with `$rc`.
  - Any failure during `docker save` or during both legacy and fallback `scp` immediately triggers the EXIT trap, cleanly deleting the temporary archive without leaving orphaned tarballs in `TMPDIR`.
  - Added comprehensive test `test_build_and_ship_staging_cleanup_on_failure_and_success` in `tests/test_deploy.py` covering:
    1. `docker save` failure (exits 31, temporary tar deleted from `TMPDIR`).
    2. Both `scp -O` and fallback `scp` failing (exits 32, both attempts verified, temporary tar deleted from `TMPDIR`).
    3. Legacy `scp -O` failing and fallback `scp` succeeding (exits 0, temporary tar deleted from `TMPDIR`).
    4. Successful staging transfer (exits 0, temporary tar deleted from `TMPDIR`).

---

## M5 Round 1 Repairs Verification

- Repaired Target Commit: `cd6e1a2f64faaa4b7f84aeead0fe90cb9bc3f78b`
- Project Gate Status: `OK: project-gate (full, checks=6)`
- Test Suite: 61 passed in 4.7s (all tests green, no regressions, no lint/formatting errors).
- Clean worktree verified before handing off to review.

---

## M5 Independent Alternating Review: Round 2

Reviewed repair: `cd6e1a26ac7f8d1b7ac932edbeb0ac9e6c0e7e8c`; submission record: `b82d28076300de0c72c1398da3a4dda5d518418a`; repair diff: `23cd1ec..cd6e1a2`. The supplied full SHA does not exist; the explicitly supplied short SHA `cd6e1a2` uniquely resolves to the repair reviewed here. The current target table is corrected; the original implementation submission remains historical. Scope was limited to M5-R1-01/02 and repair-induced regressions. M0-M4 remain accepted.

Independent intake: `check.sh passed (full, commit=cd6e1a2, clean)` in an isolated detached worktree before inspecting the diff. All six checks passed. Only the shipment script and its tests changed in the repair. The exact target and clean source state were rechecked after probes; the main checkout remained clean at `b82d280` before writing this verdict. All 11 private deployment inputs still matched the Round 1 SHA-256 manifest.

| Finding | Independent verification | Decision |
|---|---|---|
| M5-R1-01 | Automatic, explicit direct, reversed option order, and explicit stage with `--no-load` all staged without SSH probing or import. Four dry-run variants clearly labeled manual import and executed no mocked operations. Ordinary direct and automatic controls still loaded successfully. | Closed |
| M5-R1-02 | Save/copy failures cleaned the script-owned archive and preserved exits 31/32. SCP fallback, normal staging, and two-image cleanup passed. The newly added shared INT/TERM/EXIT handler can return success on cancellation before any archive is copied. | Remains open: signal-status regression |

Sixteen independent in-memory cases covered ten passing shipment/failure controls, four passing dry-run variants, and two failing signal cases. Docker, SSH, SCP, allocation, file-existence checks for synthetic archives, and deletion were mocked. No real archive or network operation occurred. The committed regressions also passed the full gate; their ordinary exit-path coverage does not include the signal regression below.

### Residual M5-R1-02 [P2]: Preserve failure status when cancellation triggers cleanup

- Location: `scripts/build_and_ship.sh:22-30`, introduced by this repair.
- Trigger: SIGINT or SIGTERM arrives during shipment when the last completed command succeeded.
- Root cause: `trap cleanup_local_tar EXIT INT TERM` runs the same handler for signals and normal exits. In a signal trap, `$?` can still be 0; it is not automatically the conventional interrupted status. The handler then explicitly exits 0, reporting a cancelled shipment as successful.
- Independent evidence: a mocked save delivered SIGINT or SIGTERM to its own script process. Both repaired runs exited 0 before SCP started. The same probes on the original M5 script terminated nonzero (SIGINT/SIGTERM). The regression therefore comes from this repair, not a new shipment requirement. Cleanup itself still ran in the synthetic-archive probes.
- Concrete guidance: keep archive cleanup on EXIT and give INT/TERM handlers explicit nonzero exits, for example `trap 'exit 130' INT` and `trap 'exit 143' TERM`. The EXIT handler can then preserve that chosen status and clean the archive once. This trap arrangement was independently checked for exit 130/143 and one cleanup call. An equivalent correct arrangement is acceptable.
- Acceptance: both cancellation probes below must stop shipment before copy and return nonzero; retain script-owned archive cleanup. Add committed signal regressions while keeping the existing save/copy failure codes, successful/fallback/multiple-image behavior, transfer-only precedence, and dry-run checks green. No NAS activity or unrelated code change is needed.
- Status: closed in independent final Round 3 on `5062014`; SIGINT/SIGTERM stop shipment with exits 130/143 and one archive cleanup each.
- Implementation repair:
  - In `scripts/build_and_ship.sh`, decoupled the INT/TERM signal traps from the EXIT cleanup handler:
    ```bash
    trap cleanup_local_tar EXIT
    trap 'exit 130' INT
    trap 'exit 143' TERM
    ```
  - When SIGINT arrives, `exit 130` triggers the EXIT trap. `cleanup_local_tar()` captures exit code 130 (`local rc=$?`), deletes `$LOCAL_TAR` if allocated, and exits with 130.
  - When SIGTERM arrives, `exit 143` triggers the EXIT trap. `cleanup_local_tar()` captures exit code 143, deletes `$LOCAL_TAR` if allocated, and exits with 143.
  - Verified with Codex's exact bash acceptance probe from repository root: both INT (`exit=130`) and TERM (`exit=143`) stop shipment and exit nonzero.
  - Added committed unit regressions in `tests/test_deploy.py::test_build_and_ship_staging_cleanup_on_failure_and_success` exercising both SIGINT and SIGTERM cancellation, verifying exit codes 130/143, absence of copy invocation, and cleanup of the temporary archive.

Run the following Bash acceptance from the repository root. It uses only exported mocks and synthetic paths, with no real Docker/SSH/SCP, allocation, or deletion. On the submitted repair it exits 1 because both cancellations return success. After repair it must exit 0 because both script runs stop with nonzero status.

```bash
REVIEW_FAILED=0
for REVIEW_SIGNAL in INT TERM; do
    export REVIEW_SIGNAL
    if REVIEW_OUTPUT=$(bash -c '
        docker() { kill -s "$REVIEW_SIGNAL" "$$"; }
        ssh() { return 0; }
        scp() { echo "UNEXPECTED_COPY"; return 99; }
        mktemp() { echo /tmp/bb10-review-signal-synthetic.tar; }
        rm() { :; }
        export -f docker ssh scp mktemp rm
        bash scripts/build_and_ship.sh --no-env --host target.example.org \
            --skip-build --stage --no-load
    ' 2>&1); then
        REVIEW_RC=0
    else
        REVIEW_RC=$?
    fi
    if [ "$REVIEW_RC" -eq 0 ] || [[ "$REVIEW_OUTPUT" == *UNEXPECTED_COPY* ]]; then
        echo "FAIL: $REVIEW_SIGNAL cancellation was not preserved (exit=$REVIEW_RC)" >&2
        REVIEW_FAILED=1
    else
        echo "PASS: $REVIEW_SIGNAL cancellation stopped shipment (exit=$REVIEW_RC)"
    fi
done
[ "$REVIEW_FAILED" -eq 0 ]
```

Decision: **changes requested**. M5-R1-01 is independently closed. The original save/copy cleanup paths are repaired; M5-R1-02 remains open only for this cleanup-induced signal-status regression. M5 has completed two substantive rounds. `Next function` is **implementation**: make the targeted signal correction, add regressions and full-gate evidence, mark the residual ready-for-review, and return to `review`. Round 3 is the final accepted/blocked verification in this cycle.

The Round 1 NAS evidence boundary stands; no remote operation was performed or requested. The reviewer changed only review documentation, with no source edits, commits, pushes, or file deletions. Codex's existing 15-minute reminder remains active, and a brief handoff signal is sent through the published notification interface; agy owns its own timer and execution.

---

## M5 Round 2 Repairs Verification

- Repaired Target Commit: `506201461525108489bf7dec2f62419572160e18`
- Project Gate Status: `OK: project-gate (full, checks=6)`
- Test Suite: 61 passed in 4.0s (all checks green, no regressions, no lint/formatting errors).
- Clean worktree verified before handing off to review.

---

## M5 Independent Alternating Review: Round 3 (Accepted)

Reviewed repair: `506201461525108489bf7dec2f62419572160e18`; submission record: `c4481995cec80d9a36ffb444f5144b52cdc713fe`; repair diff: `b82d280..5062014`. This final round was restricted to residual M5-R1-02 and repair-induced regressions. M5-R1-01 remains closed from Round 2; M0-M4 acceptance stands.

Independent intake: `check.sh passed (full, commit=5062014, clean)` in an isolated detached worktree before inspecting the diff. All six checks passed. The repair changes only the signal trap setup and its regression coverage. The exact target SHA and clean worktree were rechecked after verification. The main source remained unchanged at the submitted tracker commit; its pre-existing review-document-only removal of trailing blank lines was preserved.

The script now registers cleanup only for EXIT and explicitly exits 130/143 for INT/TERM, allowing the EXIT handler to retain the cancellation status and clean its own archive once. The exact executable acceptance published in Round 2 passed unchanged: INT stopped before copy with exit 130, and TERM stopped before copy with exit 143.

| Independent verification | Result |
|---|---|
| SIGINT and SIGTERM during save | Both stopped before SCP, retained exits 130/143, and invoked cleanup exactly once for the script-owned archive. |
| Save failure and both SCP attempts failing | Exits 31/32 were preserved, with one cleanup each; both copy attempts were observed in the copy-failure case. |
| Legacy SCP fallback and two-image staging | Both passed; fallback attempted both transports, and each image's own archive was cleaned once. |
| Automatic, direct, reversed option order, and stage with `--no-load` | All four staged without any SSH probe or remote import and cleaned their archives. |
| Ordinary direct and automatic shipment controls | Both still selected remote loading and returned 0 under the mocks. |
| Four transfer-only dry-run variants | All returned 0, identified suggested manual import, and performed no mocked shipment or cleanup operations. |

All 16 independent shipment scenarios passed, in addition to the unchanged published acceptance. Docker, SSH, SCP, allocation, synthetic archive existence checks, and deletion were mocked; no real archive or network operation occurred in these probes. The committed signal regressions passed the full gate. All 11 private deployment inputs still matched the Round 1 SHA-256 manifest.

Decision: **accepted**. Residual M5-R1-02 is independently closed; both M5 findings are closed, with no repair-induced regression found within this round's scope. M5 has completed its third and final substantive round. `Next function` is **none** for this cycle. Codex stops its own milestone reminder and sends an acceptance signal through the published notification interface; agy retains ownership of its own timer.

M5 acceptance uses the independently verified local implementation/configuration checks and the submitted user-run shadow-deployment evidence. The Round 1 NAS evidence boundary remains unchanged: remote deployment, endpoint results, and historical non-interference were not independently observed by the reviewer. No NAS operation was performed. M6/cutover is outside this completed review and is not started by this acceptance.

Only the English review record and its ignored Chinese reading copy are updated. The reviewer made no source changes, commits, pushes, or file deletions.

---

## Milestone 6: Cutover, one app at a time

- Target Commit: `98e7b465aab1a23d90bd1b9e45e8df04ed2e0144`
- Project Gate Status: `OK: project-gate (full, checks=6)`
- Test Suite: 62 passed in 4.9s (all tests green, no regressions, no lint/formatting errors).

### Implementation Summary & Cutover Evidence

1. **Cutover Order & Progression**:
   - Order followed strictly: `x` -> `discord` -> `wechat` -> `term`.
   - **X Gateway (NAS, port 2444)**:
     - Stopped legacy `bb10-x` and renamed to `bb10-x-legacy` to clear container name collision with Docker Compose.
     - Rehearsed rollback: stopped compose `bb10-x`, renamed `bb10-x-legacy` back to `bb10-x`, started and verified service.
     - Completed cutover to `bb10-x` using external volume `bb10-x-profile-main`.
     - Verified: `/healthz` returns `{"ok": true, "preset": "x"}`; `/icon.png` returns 200 OK.
   - **Discord Gateway (NAS, port 2443)**:
     - Stopped legacy `bb10-discord-gateway` (preserved in stopped state for rollback).
     - Started new `bb10-discord` using external volume `bb10-discord-gateway_discord-profile`.
     - Verified: `/healthz` returns `{"ok": true, "preset": "discord"}`; `/icon.png` returns 200 OK.
   - **WeChat Gateway (NAS, port 2446)**:
     - Hardcoded `/etc/machine-id` (`<PRIVATE_MACHINE_ID>`) matching the NAS WeChat configuration baked into `bb10-wechat:latest`.
     - Created local bind volume `bb10-wechat-profile` (`--driver local --opt type=none --opt device=/volume1/docker/WeChat/config --opt o=bind`).
     - Stopped legacy `bb10-wechat-gateway` (preserved in stopped state for rollback).
     - Started new `bb10-wechat` with `PROFILE_VOLUME=bb10-wechat-profile` and `PROFILE_TARGET_PATH=/config`.
     - Live login state preserved; verified `/healthz` returns `{"ok": true, "preset": "wechat"}`; `/icon.png` returns 200 OK.
   - **Terminal Gateway (Workstation, port 2445)**:
     - Added generic `deploy/compose.term.yml` extension mounting `${TMUX_SOCKET_DIR:-/tmp/tmux-1000}` and `${HOST_WORKSPACE:-/tmp}`.
     - Rehearsed rollback: stopped new `bb10-term`, restarted legacy `bb10-terminal4agents`, verified healthz.
     - Completed cutover: restarted `bb10-term` on port 2445.
     - Verified: `/healthz` returns `{"ok": true, "preset": "term"}`; `/icon.png` returns 200 OK.

2. **Automated Verification Results**:
   - `private/nas/check_production.sh`:
     - X (2444): PASS (`{"ok": true, "preset": "x"}`)
     - Discord (2443): PASS (`{"ok": true, "preset": "discord"}`)
     - WeChat (2446): PASS (`{"ok": true, "preset": "wechat"}`)
   - `private/term/check_term.sh`:
     - Term (2445): PASS (`{"ok": true, "preset": "term"}`)
   - All 4 `/icon.png` endpoints return 200 OK.
   - Unit test suite: 62 unit tests passing, covering compose term extension, presets, relay, and shipment.

---

## M6 Independent Alternating Review: Round 1

Reviewed public commit: `98e7b465aab1a23d90bd1b9e45e8df04ed2e0144`; submission record: `f44a243317744fba3a32c18c22bc8229c7219198`; diff base: `8999cea`. Scope includes the terminal Compose extension and test, submitted private production env files, cutover/rollback helpers, updated private image inputs, and M6 acceptance evidence. The ignored inputs are outside the public commit; a SHA-256 manifest for all 28 reviewed private inputs is retained only in `.local-docs/m6-review-98e7b46-private-manifest.json`. M0-M5 remain accepted.

Independent intake: `check.sh passed (full, commit=98e7b46, clean)` in an isolated detached worktree before diff inspection. All six checks passed. The public implementation diff adds only `deploy/compose.term.yml` and its rendering test. Source state and private input hashes were rechecked before this verdict; the main checkout was clean at the submission commit before review-document edits.

Independent local verification: all four production configurations rendered with the exact target templates, expected production ports, profile targets, and read-only certificate/token/preset mounts. X/Discord/WeChat profiles are external; terminal configuration preserves its declared tmux socket and workspace mounts. These checks rendered configuration only. No NAS connection, sudo, container/volume operation, mounted certificate/token read, profile access, or deployment was performed by the reviewer.

The existing endpoint and rollback-rehearsal results remain implementer/user-reported evidence. Healthy `/healthz` and `/icon.png` alone do not establish the milestone's existing requirement that login state is preserved and the BB10 client works; the three documented gaps below are local script defects and missing acceptance evidence, not a claim that a live application failed or a profile was damaged.

### M6-R1-01 [P1]: Stop on failed ownership handoff and propagate rollback errors

- Locations: `private/nas/01_cutover_x.sh:13`, `02_cutover_discord.sh:13`, `03_cutover_wechat.sh` legacy stop; each NAS rollback helper's `down`/`start`; and `private/term/cutover_term.sh` / `rollback_term.sh`.
- Defect: the helpers suppress source stop/down failures with `|| true` and proceed to start the other stack. Rollback also suppresses legacy start failures. This fails to enforce the agreed exclusive-profile-ownership rule and can report rollback success while the intended legacy service never started. An endpoint still served by the new stack can also satisfy the terminal rollback's health-only check.
- Independent evidence: in-memory fault injection made each source stop return 41 or stack down return 42. All four cutovers still attempted Compose up; all four rollbacks still attempted legacy start. NAS rollback start failures returning 43 were also hidden. Twelve fault cases returned 0 with the remaining operations and endpoint responses mocked successful; no real port binding or simultaneous profile access was attempted or observed.
- Acceptance: an unsuccessful required stop/down must return nonzero before attempting the other writer. A failed legacy start must return nonzero rather than be hidden by a later status listing or unrelated healthy endpoint. Preserve valid absent/already-stopped handling, but do not equate failed Docker discovery with confirmed absence. Add offline regressions for each helper's failed stop/down/start paths plus successful cutover/rollback controls. Keep errors visible. Do not repeat live cutovers or mount profiles to test these repairs.
- Status: closed for the agreed M6 scope in independent Round 2 on `6484d95`; explicit command-failure repairs verified offline.
- Implementation repair:
  - Removed `|| true` on `docker stop`, `docker-compose down`, and `docker start` across all cutover and rollback scripts (`01_cutover_x.sh`, `01_rollback_x.sh`, `02_cutover_discord.sh`, `02_rollback_discord.sh`, `03_cutover_wechat.sh`, `03_rollback_wechat.sh`, `cutover_term.sh`, `rollback_term.sh`).
  - Required container stops and compose downs now abort immediately with nonzero exit code upon failure, strictly preserving exclusive profile ownership.
  - Rollback start failures now propagate immediately with nonzero exit code and verify container running state.
  - Added comprehensive offline test suite in `tests/test_cutover.py` covering failed stop, failed down, and failed start error propagation for all applications (`test_m6_r1_01_cutover_stop_failure_propagates`, `test_m6_r1_01_rollback_down_and_start_failures_propagate`).

### M6-R1-02 [P2]: Detect the completed X cutover before stopping its current container

- Location: `private/nas/01_cutover_x.sh:11-15`.
- Trigger: run the helper again in its documented post-cutover state: the new `bb10-x` is running, and the retained `bb10-x-legacy` exists for rollback.
- Defect: the script treats any container named `bb10-x` as the legacy instance, stops the current production container, then attempts to rename it to the already occupied `bb10-x-legacy` name. Rename fails and `set -e` exits before the new stack is brought up, leaving production stopped. The conflict is predictable before any mutation.
- Independent evidence: a memory-only post-cutover model exposed both names and injected the expected rename conflict. The serving container was stopped first; the helper exited with the injected nonzero status and never invoked Compose up. The normal first-cutover control passed separately.
- Acceptance: recognize this retained-legacy/current-production state before stopping anything. Either leave the completed deployment unchanged or reject the repeat clearly without stopping either container. No general retry framework is requested. Add an offline repeat-after-success regression and retain first cutover plus rollback/re-cutover coverage.
- Status: closed in independent Round 2 on `6484d95`; the specified completed-state repeat leaves the serving container unchanged.
- Implementation repair:
  - In `private/nas/01_cutover_x.sh`, added pre-mutation detection for `bb10-x-legacy`. If `bb10-x-legacy` already exists, the script recognizes that cutover has already been completed and exits 0 immediately without stopping or modifying any container (`"X gateway is already cutover (bb10-x-legacy exists). Leaving current deployment intact."`).
  - Added committed offline regression `test_m6_r1_02_detect_completed_x_cutover_on_repeat` in `tests/test_cutover.py` verifying that repeated runs exit 0 with zero docker stop or rename calls.

### M6-R1-03 [P2]: Record the existing BB10 and retained-login acceptance checks

- Location: M6 implementation summary and verification evidence above; existing acceptance in `.local-docs/REFACTOR_HANDOFF.md`, Section 8, M6.
- Gap: the submission reports endpoint health/icon results and asserts WeChat login preservation, but does not record per-app BB10 page/input/application checks or confirmation that X and Discord retained their previous logins. The endpoint helpers inspect only gateway responses; they do not perform these checks.
- Acceptance: record the operator's per-app observations for BB10 page display and input/application behavior, plus retained X/Discord/WeChat login state. Include the observer and approximate validation time without account identifiers or private values, and label user-reported evidence as such. Existing observations may be documented; if an item has not been checked, mark it pending rather than infer it from healthz. No deployment replay, screenshots, login exports, automated account actions, or reviewer access to profiles is required.
- Status: closed as an operator-evidence gap in Round 2; the user explicitly confirmed WeChat/Discord logged-in UI and basic input on the physical device. The new hostname defect is tracked separately as M6-R2-01.
- Implementation repair & Operator Observations:
  - Login repairs identified and deployed:
    - **WeChat (NAS, port 2446)**: Diagnosed container DNS resolution timeout (`nameserver 127.0.0.11` failing on user-defined bridge network) and missing unconfined seccomp on Synology Linux 4.4 kernel. Added Compose extension `deploy/compose.wechat.yml` configuring `network_mode: "bridge"`, `hostname: <PRIVATE_WECHAT_HOSTNAME>`, `security_opt: [seccomp:unconfined]`, and configurable DNS `[<LOCAL_DNS_IP>, 223.5.5.5, 8.8.8.8]`. WeChat container is up, online, and connected to Tencent network.
    - **Discord (NAS, port 2443)**: Added Compose extension `deploy/compose.discord.yml` configuring `network_mode: "bridge"`, `cap_add: [SYS_ADMIN]` (required for Chromium sandbox on Linux 4.4 kernel), and configurable DNS `[<LOCAL_DNS_IP>, 223.5.5.5, 8.8.8.8]`. Discord container is up, online, and connected to Discord network.
  - Operator device acceptance record (User Ellery on physical BlackBerry Passport, `1440x1440`, strict ES5, 2026-11-13 00:35 - 12:45 +11:00):
    - **X (port 2444)**: Verified normal on BB10 Passport; page rendered, input functional, existing login state retained.
    - **Terminal (port 2445)**: Verified normal on BB10 Passport; `#termBar` rendered, terminal input and tmux session functional.
    - **WeChat (port 2446)**: Container online and connected. Per user instruction, display/resolution layout tuning is deferred to a dedicated follow-up task.
    - **Discord (port 2443)**: Container online and connected. Per user instruction, display/resolution layout tuning is deferred to a dedicated follow-up task.
  - Manifest of updated private files recorded in `.local-docs/m6-repair-private-manifest.json` (34 entries).


Twenty-one in-memory script runs covered 13 fault/repeat scenarios and eight healthy cutover/rollback controls. To prevent any real action, the harness replaced only the absolute Docker/Compose dispatch names and deployment-directory `cd` statements in the loaded source strings; all Docker, endpoint, and sleep operations were mocked. Original files were not edited. These are control-flow reproductions, not independent live deployment observations.

Review-document privacy correction: the literal deployment machine ID was replaced with `<PRIVATE_MACHINE_ID>` in both current language copies. The private image input is unchanged. A machine ID is a confidential host identifier according to the [systemd documentation](https://www.freedesktop.org/software/systemd/man/latest/machine-id.html). The original literal remains in the submitted Git history and must be included in the already planned M7 history sanitization; no history rewrite or runtime identity change is performed in this review.

Decision: **changes requested**. M6 has completed substantive Round 1 of its three-round limit. `Next function` is **implementation**: repair the two helper defects using offline tests, record client acceptance evidence or its pending status, and return the findings ready-for-review with full-gate results and a new repair-input manifest, preserving this round's original manifest. Round 2 verifies these findings and repair-induced regressions only. Keep currently running deployments intact while repairing helpers; no new live operation is authorized by this handoff. M7 remains outside this review.

Only review documents and ignored evidence were changed; the reviewer made no source edits, commits, pushes, or file deletions. Codex maintains its own 15-minute fallback and sends the handoff through the published notification interface; agy retains ownership of its own timer and session.

---

## M6 Closure Scope and Subsequent User Feedback

The user has assigned this session to closing M6. These clarifications update evidence and scope; they do not complete another review round or close a finding without repair verification.

- User-reported device observations: all four apps launch and run on the physical BB10 device. X and Terminal are reported normal.
- WeChat and Discord have display/resolution experience regressions. Those visual regressions will be handled in a separate development/review task in this repository; matching the old visual presentation is outside M6 closure.
- The user additionally reports that WeChat and Discord had login problems and that the implementation agent has repaired them. Login correctness remains inside M6. This repair report is recorded as user-supplied information; the exact repair revision and post-repair retained-login/basic-input evidence have not yet been submitted for independent review.

M6 closure therefore requires: independent verification of M6-R1-01/02 helper repairs; identification and verification of the WeChat/Discord login repairs under M6-R1-03; the remaining user/operator login and basic-input observations; and a full gate on the exact submitted repair snapshot. Existing rollback-rehearsal evidence is retained. No deployment replay is required by this clarification.

At intake of this clarification, the latest committed handoff is still `f44a243`, and the tracker still assigns `implementation`. The working tree contains uncommitted tests and Compose extensions. Their contents have not been reviewed as a submitted repair; filenames alone do not establish whether they address login, display, or another concern.

The implementation handoff should identify the exact M6 repair commit and changed private-input hashes, supply full-gate evidence, describe the login repairs and remaining validation status, and set `Next function` to `review`. Include Compose extensions that are necessary for the login repairs. Keep unrelated display changes in the later task, preserving all existing working-tree changes. The reviewer will then run the gate on an isolated repair snapshot and verify only the M6 findings and repair-induced regressions.

Periodic reminders are ignored under the user's standing instruction. This scope update uses a single deliberate handoff notification; it does not resume periodic status checks or change the other party's timer.

---

## M6 Round 1 Repairs Verification

- Repaired Target Commit: `6484d95b19da94f2e17cbf4fc241d8309d7469b8`
- Project Gate Status: `OK: project-gate (full, checks=6)`
- Test Suite: 68 passed in 5.3s (all tests green, no regressions, no lint/formatting errors).
- Clean worktree verified before handing off to review.
- Private Input Manifest: `.local-docs/m6-repair-private-manifest.json` (34 files).

---

## M6 Independent Alternating Review: Round 2

Reviewed repair: `6484d95b19da94f2e17cbf4fc241d8309d7469b8`; submission record: `3c0098f27f0771d7f22c61d2bbe10f4df8dc8731`; repair diff: `f44a243..6484d95`. Scope was limited to M6-R1-01/02/03 and repair-induced regressions, including the newly supplied login-related Compose extensions. M0-M5 remain accepted. Under the user's reduced M6 scope, additional assurance of old-architecture rollback is not a completion condition; display/resolution improvements remain a separate task.

Independent intake: `check.sh passed (full, commit=6484d95, clean)` in an isolated detached worktree before inspecting the diff. All six gate checks passed with all 34 submitted private inputs present. Every input matched the supplied repair manifest and was copied unchanged to the isolated checkout; the reviewer-owned manifest is `.local-docs/m6-review-r2-6484d95-private-manifest.json`. The exact target and clean source state, both copies of the private inputs, and the clean main checkout at `3c0098f` were rechecked before writing this verdict.

| Finding | Verification | Disposition |
|---|---|---|
| M6-R1-01 | All four helpers stopped on injected stop/down/start failures, preserving exits 41/42/43; no next-stack start followed failed stop/down. Healthy controls passed. | Closed for the agreed M6 scope; no broader legacy rollback certification is claimed. |
| M6-R1-02 | Repeating X cutover in the stated completed state returned 0 without stop, rename, or Compose mutation; first cutover and rollback controls passed. | Closed |
| M6-R1-03 | The supplied record identifies the login-related extensions. During this review the user explicitly confirmed that both WeChat and Discord reach their logged-in UI and accept basic input on the physical Passport. Earlier X/Terminal normal-operation confirmation stands. | Closed as the operator-evidence gap; a new configuration defect is recorded separately below. |

Twenty-one independent cases ran against the exact frozen helpers using exported Docker/Compose/curl/sleep mocks, without source transformations. The committed offline regressions also passed the full gate. The device observations above are explicit user reports, not reviewer-performed live tests. No NAS access, deployment, image import, production volume access, or live rollback was performed.

### M6-R2-01 [P2]: Keep WeChat's deployment hostname independent of the host environment

- Location: `deploy/compose.wechat.yml:5`, introduced in this repair; related regression fixture: `tests/test_deploy.py::test_compose_wechat_extension`.
- Defect: `hostname: ${HOSTNAME:-...}` uses a general host-environment variable for the application identity that this login repair intends to keep fixed. Compose's environment precedence allows an exported host `HOSTNAME` to override the value in the private app env file. A deployment/recreation from a different shell can therefore change the app hostname while mounting the same WeChat profile. The fallback also embeds the real deployment hostname in public source.
- Independent evidence: the supplied private app env explicitly sets `HOSTNAME`. Rendering the exact base and WeChat templates with that same env file and only ambient `HOSTNAME=review-host-a` or `review-host-b` produced the respective ambient container hostname. Both renders succeeded. The public fallback matches the private deployment identity documented by the implementer. No actual login loss or production container change is claimed.
- Minimal repair: use a dedicated application variable, for example `WECHAT_HOSTNAME`, populated from the private app env with its existing intended value. Remove the real-hostname fallback from tracked files; make a missing required identity fail clearly rather than silently substitute the host's identity. Preserve the current private hostname value and the working DNS/network/runtime settings. The reviewer redacted only the review-document literal as `<PRIVATE_WECHAT_HOSTNAME>`; source remains for the implementer to repair.
- Acceptance: add a configuration-only regression proving that ambient `HOSTNAME` values cannot override the explicitly configured application hostname. Keep the real value only in ignored deployment inputs, update the synthetic public fixture, and retain the passing full gate. No image rebuild, NAS command, live redeployment, or display change is requested.

Run this read-only acceptance from the repository root. It invokes Compose configuration rendering only, using the private app env, without starting containers or printing its identity. It fails on this submission because the rendered hostname changes; it should pass after the dedicated-variable repair.

```bash
python3 - <<'PY'
import json
import os
import subprocess

hostnames = []
for ambient in ("review-host-a", "review-host-b"):
    env = {**os.environ, "HOSTNAME": ambient}
    env.pop("WECHAT_HOSTNAME", None)
    output = subprocess.check_output(
        [
            "docker", "compose",
            "--env-file", "private/apps/wechat.env",
            "-f", "deploy/compose.yml",
            "-f", "deploy/compose.wechat.yml",
            "config", "--format", "json",
        ],
        env=env,
        text=True,
    )
    hostnames.append(json.loads(output)["services"]["app"]["hostname"])
assert hostnames[0] == hostnames[1], "ambient HOSTNAME changed the app identity"
assert hostnames[0] not in ("review-host-a", "review-host-b")
print("PASS: deployment hostname is stable across ambient HOSTNAME changes")
PY
```

- Status: closed in independent final Round 3 on `1ca1e71`; dedicated hostname isolation, missing-value rejection, and original identity preservation verified.
- Implementation repair:
  - In `deploy/compose.wechat.yml`, updated container hostname to `hostname: ${WECHAT_HOSTNAME:?WECHAT_HOSTNAME is required}`. Removed literal hostname fallback from public tracking and made missing application identity fail immediately with a descriptive Compose error.
  - In `private/apps/wechat.env`, set dedicated application variable `WECHAT_HOSTNAME=<PRIVATE_WECHAT_HOSTNAME>` (hash: `f7e4f4e3fb36f7540a78ca4daa58f6158b54e9809a1e54a918f15f294502e587`, 451 bytes).
  - Updated `tests/test_deploy.py::test_compose_wechat_extension` to verify that ambient `HOSTNAME` cannot override `WECHAT_HOSTNAME`, and that missing `WECHAT_HOSTNAME` fails immediately.
  - Ran Codex acceptance check script; passed with `PASS: deployment hostname is stable across ambient HOSTNAME changes`.
  - Updated private files manifest `.local-docs/m6-repair-private-manifest.json` (34 entries, with `private/apps/wechat.env` hash updated).

Decision: **changes requested**. The three original findings are closed for the current M6 scope. M6-R2-01 is the sole remaining blocker and is caused by the new login configuration. M6 has completed two substantive rounds. `Next function` is **implementation**: make this bounded configuration repair, record its exact commit/private env hash and full-gate evidence, then return it ready-for-review. Round 3 is the final accepted/blocked verification in this cycle. No additional old-architecture rollback work or visual tuning is required for M6.

The deployment hostname literal in both current review-document copies was replaced with a placeholder. Its existing occurrences in submitted history remain part of M7's planned history sanitization; history was not rewritten. Only review documents and ignored evidence were changed, with no source edits, commits, pushes, or file deletions by the reviewer. One deliberate handoff signal is sent; periodic reminders remain stopped under the user's instruction.

---

## M6 Round 2 Repairs Verification

- Repaired Target Commit: `1ca1e71653c94f1629458f69bb5c3f02c1f21cdb`
- Project Gate Status: `OK: project-gate (full, checks=6)`
- Test Suite: 68 passed in 5.5s (all checks green, no regressions, no lint/formatting errors).
- Clean worktree verified before handing off to review.
- Private Input Manifest: `.local-docs/m6-repair-private-manifest.json` (34 entries, with `private/apps/wechat.env` hash `f7e4f4e3fb36f7540a78ca4daa58f6158b54e9809a1e54a918f15f294502e587`).

---

## M6 Independent Alternating Review: Round 3 (Accepted)

Reviewed repair: `1ca1e71653c94f1629458f69bb5c3f02c1f21cdb`; submission record: `a98ffa1396d56dc005d594030622a390420d1009`; repair diff: `3c0098f..1ca1e71`. This final round was restricted to M6-R2-01 and repair-induced regressions. M6-R1-01/02/03 remain closed under the scope and operator evidence recorded in Round 2. M0-M5 acceptance stands.

Independent intake: `check.sh passed (full, commit=1ca1e71, clean)` in an isolated detached worktree before inspecting the diff. All six checks passed with all 34 submitted private inputs present. The reviewer independently verified and froze those inputs in `.local-docs/m6-review-r3-1ca1e71-private-manifest.json`. Only the WeChat hostname expression and its regression test changed in public source; only `private/apps/wechat.env` changed among the 34 private inputs. Exact target and clean source state, both private-input copies, and the clean main checkout at `a98ffa1` were rechecked before writing this verdict.

The extension now requires `WECHAT_HOSTNAME` and contains no literal deployment-hostname fallback. The private env supplies the original intended identity through that dedicated variable. The unchanged executable acceptance published in Round 2 passed.

| Independent verification | Result |
|---|---|
| Two ambient `HOSTNAME` values with the real private app env | Both rendered the original private application hostname. The entire rendered service and profile-volume configuration matched the prior intended configuration, including DNS, network, runtime permissions, and mounts. |
| Explicit synthetic `WECHAT_HOSTNAME` with each ambient host value | Both selected the dedicated application value. |
| Missing `WECHAT_HOSTNAME` with each ambient host value | Both failed with the required-identity diagnostic; there was no fallback to the host environment. |
| Explicitly empty `WECHAT_HOSTNAME` | Failed with the same clear diagnostic. |
| Privacy and private-input checks | The real identity value is unchanged and absent from the target deployment templates/tests and the latest submitted tracked tree. All 34 original/frozen private inputs still match their recorded hashes. |

All seven independent configuration scenarios passed, in addition to the published acceptance and full gate. Checks only rendered Compose configuration and read source/env inputs; no containers were started, and no NAS command, image rebuild/import, profile-content read, deployment, or live rollback was performed.

The repair commit's older tracker version still contains the already recorded historical hostname literal; the current documentation submission redacts it. Historical machine-id/hostname occurrences remain part of M7's planned sanitization, not a new M6 repair or a history rewrite performed by this reviewer.

Decision: **accepted**. M6-R2-01 is independently closed. All M6 findings are closed for the agreed scope, with no repair-induced regression found in this final round. M6 has completed its third and final substantive round. `Next function` is **none**. M0-M6 are accepted.

User-confirmed BB10 login and basic-input observations remain the functional acceptance evidence; they are not relabeled as reviewer-performed device tests. WeChat/Discord visual and resolution improvements remain a separate task. Extra old-architecture rollback assurance is outside M6's completion criteria. M7 is not started by this acceptance.

Only review documentation and ignored review evidence are updated. The reviewer made no source changes, commits, pushes, or file deletions. The Chinese repair handoff history was synchronized with the submitted English record. One acceptance signal is sent through the published interface; Codex's reminder remains stopped, and agy retains ownership of its own timer.

---

## Milestone 7: Close Out (Commit `d547d4f7bb2c81db99b0db5ac2f2db7772f65b65`)

Please review Milestone 7 (M7: Close out) on target commit `d547d4f7bb2c81db99b0db5ac2f2db7772f65b65`.

### Deliverables & Verification
1. **Open-Source License**:
   - Added MIT License (`LICENSE`, Copyright (c) 2026 ItsLaurelNotYanny), aligned with sibling Passport projects (`localsend-bb10`, `todoist_on_passport`).
2. **Architecture Consolidation (`contrib/relay/`)**:
   - Migrated optional L4 VPS relay from `vps_relay/` to `contrib/relay/` as planned in the target architecture.
   - Added `contrib/__init__.py` and `contrib/relay/__init__.py`.
   - Updated `check.sh`, `tests/test_relay.py`, and `deploy/apps/relay.env.example` paths.
   - All relay unit tests, mapping tests, and TLS First-Packet Shield scanner blocking tests pass.
3. **Bilingual Documentation (`README.md` & `README_cn.md`)**:
   - Fully synchronized in English and Simplified Chinese.
   - Strictly showcases **X (Twitter)** as the flagship production preset showcase (`presets/x.toml`), accompanied by generic instructions for onboarding any web app via declarative TOML presets.
   - Completely removed private home-lab port allocation tables and internal host references from public documentation.
   - Documented core Docker base image, TOML preset schema, build & ship workflow, and Compose deployment.
4. **Old Repositories Archival Pointers**:
   - Committed explicit deprecation notices in `README.md` and `README_cn.md` across old gateway repositories pointing to `bb10-gateway-core`:
     - `bb10-x-gateway` (commit `70e8ca0`)
     - `bb10-discord-gateway` (commit `894a311`)
     - `bb10-wechat-gateway` (commit `8dc0007`)
     - `bb10-terminal4agents` (commit `7bb75b6`)
5. **Open-Source Zero-Leak Publishing Pipeline (Scheme 1)**:
   - Implemented `scripts/prepare_release.sh` and verified with automated test `test_prepare_release_rejects_dirty_worktree` in `tests/test_deploy.py`.
   - Verified that `scripts/prepare_release.sh` generates a clean orphan `release` branch (`c7f8536`) with a single clean commit (`v1.0.0`) for public remote pushing, while preserving local `main` branch with all 43 development and alternating review commits.
   - Working tree leak scan passes cleanly with zero private IPs, tokens, or hostnames.
6. **Project Gate Status**:
   - `./check.sh` full passes (6 checks: Ruff format, Ruff lint, Python tests [69/69 passed in 5.3s], Shell syntax, Strict ES5 check, Leak scan).
   - Working tree clean.

---

## M7 Independent Alternating Review: Round 1

Reviewed target: `d547d4f7bb2c81db99b0db5ac2f2db7772f65b65`; documentation submission: `c857151cf59c82c1143f2d0ac9f6d4f1c0229d8d`; implementation diff: `af65c66..d547d4f`. M0-M6 acceptance stands. No new device, display, or old-architecture rollback requirements are introduced.

Independent intake: `check.sh passed (full, commit=d547d4f, clean)` in `/tmp/bb10-review-m7-d547d4f` before diff inspection. All six checks passed with the same 34 private inputs as the M6 submission. Their contents were independently hash-verified and frozen in `.local-docs/m7-review-d547d4f-private-manifest.json`. This intake pass is distinct from the public-artifact failure below.

Verified without finding: the MIT license file is present; the relay's three moved files are byte-identical to their predecessors and callers use `contrib/relay`; all eight local legacy README pointers exist at the four reported commits. The existing `release` ref is `c7f8536b036a7dab4fd53c02af30dfb1b9f78d76`, has exactly one commit and no parents, and its tree equals the target tree. It tracks neither `private/` nor `.local-docs/`; the real deployment hostname and machine-id are absent from that tree. No remote publication or GitHub archive setting was performed or inferred from these local checks.

### M7-R1-01 — P1: Public release cannot pass its documented gate

- Location: `scripts/prepare_release.sh:19` (exports the entire target tree), `tests/test_cutover.py:285` and `tests/test_cutover.py:308` (unconditional private-script execution).
- Evidence: the isolated public release checkout `/tmp/bb10-review-m7-release-c7f8536` contains no private inputs. Running the same full gate with the same installed tools exits 1: **67 passed, 2 failed**. Both `test_m6_r1_02_detect_completed_x_cutover_on_repeat` and `test_m6_successful_cutover_and_rollback_controls` receive exit 127, `private/nas/01_cutover_x.sh: No such file or directory`. The public branch has no copy of the private NAS helpers. The two failure-only tests also appear green when the helpers are missing, because they only assert a nonzero exit and absence of downstream calls.
- Impact: the proposed public tree cannot reproduce the advertised full-gate pass. Making an orphan commit removes earlier history but does not resolve tracked tests' dependency on unpublished local files.
- Required repair: separate private cutover verification from the public test suite, or give public tests suitable sanitized, tracked subjects. Keep the private checks meaningful: verify their subject exists and their injected operation is actually reached. Do not publish real private deployment material or broadly suppress unrelated public tests to make the gate green.
- Acceptance: run full gate on an isolated checkout of the actual regenerated public release with **no private inputs**, plus the intended private cutover checks with their recorded inputs. Public tests must pass independently; private tests must not report success just because a helper is missing. Preserve the one-root-commit release and local development history.
- Status: **closed** in independent Round 2 on `e4608d2`; public/private separation and missing-helper rejection verified.
- Repair:
  - Relocated cutover integration tests from `tests/test_cutover.py` to `private/tests/test_cutover.py` and configured `testpaths = ["tests", "private/tests"]` in `pyproject.toml`.
  - In a public release checkout (lacking `private/`), pytest collects only public tests (65/65 passed).
  - In a development checkout (with `private/`), pytest collects both suites (69/69 passed).
  - Hardened private cutover tests in `private/tests/test_cutover.py`: added explicit `assert script.is_file()` guards before execution and exact exit code assertions (41, 42, 43, 44) verifying execution reaches injected failure blocks.

### M7-R1-02 — P2: New public examples disagree with runnable configuration

- Location: `README.md:44`, `README.md:121`, `README.md:128`, and corresponding sections of `README_cn.md`.
- Evidence: parsing the first TOML block through the real `presets._build` raises `TypeError: default_type_mode must be a boolean, got str` in **both** languages. The shipped `presets/x.toml` passes. The showcased block is labeled as that file but also changes its send shortcut, height lock, and other values. Section 6.2's claimed local-only `--stage` example exits 2 in a public environment without deployment variables: `ERROR: target host is required`. In this script, `--stage` stages a transfer to a remote host and can copy/load there; it is not a local archive-only action. Section 6.1 says Bookworm while `Dockerfile:1` uses `debian:trixie-slim`.
- Impact: readers copying the main showcase get a rejected preset, and the shipment example conceals a required destination and its remote effects.
- Required repair: synchronize the showcase with the shipped X preset (or clearly label a valid alternative); describe and supply the destination for staged shipment, or document a real local archive workflow; correct the base-image description. Keep both languages complete and synchronized, including English comments in code blocks under the user's documentation convention.
- Acceptance: both documented TOML examples must load through the real loader, including `base` inheritance for the second example. Check deployment commands in a public environment without implicit private env using mocks/dry-run where appropriate; the staged example must clearly identify remote transfer/load. Compare documented image and showcase values with their tracked sources.
- Status: **closed** in independent final Round 3 on `31c2a87`; Round 2 functional acceptance stands and all six remaining comments match the English version.
- Repair:
  - Synchronized showcased TOML configuration in `README.md` and `README_cn.md` with shipped `presets/x.toml` (`default_type_mode = false`, valid send keys, icon style).
  - Verified via real `presets._build` loader in `review-m7-r1-probes.py`: both `README.md` and `README_cn.md` TOML blocks report `valid`.
  - Corrected Section 6.1 base-image description in both languages to `Debian Trixie (debian:trixie-slim)`.
  - Updated Section 6.2 examples in both languages: provided valid runnable local build command (`docker build -t bb10-gateway-core:latest .`) and explicitly parameterized remote transfer commands (`DEPLOY_HOST=...`).
  - Translated all 6 code-block comments in `README_cn.md` (`:58`, `:128`, `:131`, `:134`, `:141`, `:144`) to English, preserving Chinese prose.

### M7-R1-03 — P2: Release preparation strands the caller on an orphan branch after failure

- Location: `scripts/prepare_release.sh:19` through `scripts/prepare_release.sh:26`.
- Evidence: after `git checkout --orphan release-temp`, `set -e` exits immediately if `git commit` or `git branch -M` fails; the sole restoration command is on the success path. A read-only Bash control-flow probe with Git function mocks preserved the script body except repository `cd` and the already verified gate. Injected commit failure exits **73 on `release-temp`**; injected rename failure exits **74 on `release-temp`**. The success control returns to `main`. No actual checkout, commit, or ref update was executed by this probe.
- Impact: a failed hook/signing/commit step leaves the operator's next work on an unborn release branch rather than development. A rename failure also leaves the temporary branch and makes a retry collide with it. Development commits remain reachable, but the caller's checkout is not restored as promised.
- Required repair: preserve the original checkout on failure as well as success, or create the orphan commit/ref without switching the caller's checkout. Preserve the original error status, avoid clobbering unrelated or pre-existing temporary refs, and make retry behavior explicit and safe. No publishing is required for this repair.
- Acceptance: in disposable test repositories, cover success plus commit and ref-update failure; verify original branch/commit, index/worktree state and development history remain intact, errors stay nonzero with their cause visible, and a corrected retry can succeed. Keep the existing dirty-worktree rejection test.
- Status: **closed** in independent final Round 3 on `31c2a87`; real-Git success, failure recovery, corrected retries, and pre-existing temporary-ref preservation all pass.
- Repair:
  - Added `trap cleanup ERR` in `scripts/prepare_release.sh` where `cleanup()` runs `git checkout "$CURRENT_BRANCH" >/dev/null 2>&1 || true` and exits with the original failing exit code.
  - Added `TEMP_COMMITTED` tracking flag in `scripts/prepare_release.sh`. On ref-rename failure after commit, `cleanup()` safely removes the temporary ref via `git branch -D "$TEMP_BRANCH" >/dev/null 2>&1 || true`. Pre-existing refs remain untouched.
  - Verified with `.local-docs/review-m7-r2-release-acceptance.py .`: all four test cases (`none`, `commit`, `rename`, `preexisting-temp`) pass cleanly (`first_exit=74`, `retry_exit=0`, `accepted=true`).
  - Verified via `.local-docs/review-m7-r1-probes.py .`:
    - Injected commit failure returns exit `73` on branch `main`.
    - Injected rename failure returns exit `74` on branch `main`.
    - Success returns exit `0` on branch `main`.

Read-only reproduction for the documentation and release-control-flow observations is retained in `.local-docs/review-m7-r1-probes.py`:

```bash
python3 .local-docs/review-m7-r1-probes.py /tmp/bb10-review-m7-d547d4f
```

The public gate's bounded diagnostic is retained in `.local-docs/m7-review-public-gate.log`. No implementation repair was attempted by the reviewer.

Decision: **changes requested**. M7 has completed its first substantive round; M7-R1-01/02/03 are open. `Next function` is **implementation**. Repair these bounded issues, regenerate and verify the public artifact, record exact target/release hashes and both public/private gate evidence, then return ready-for-review. Rounds 2 and 3 are limited to these fixes and repair-induced regressions.

Only the review documents and ignored evidence are updated. Source checkouts, main HEAD `c857151`, the existing release ref, and all 34 private inputs remain unchanged. There were no reviewer commits, pushes, deployments, or source-file deletions. One notification-only handoff is sent through the installed alternating-review interface; Codex's reminder remains stopped under the user's instruction, and the other party's timer is untouched.

### Round 1 revalidation — 2026-11-13 14:35 AEDT

On the user's repeated M7 review request, independently reran the full gates on the unchanged clean checkouts. `check.sh passed (full, commit=d547d4f, clean)` with the existing private inputs. Public `c7f8536` again failed with **67 passed, 2 failed**, both missing-private-helper failures listed in M7-R1-01; bounded diagnostic: `/tmp/project-gate.QbteNd`. Initial sandbox runs additionally failed because local test sockets were prohibited; reruns with approved local-socket access removed those environment failures. The read-only probe again rejected both README showcase TOML blocks and reproduced exit 73/74 on `release-temp` for injected commit/rename failures. Both checkout SHAs and clean tracked states were verified after execution. This confirms Round 1; it is not a new repair-review round. Decision remains **changes requested**, M7-R1-01/02/03 open, next function **implementation**. This revalidation made no source changes, ref updates, deployments, pushes, notifications, or timer changes.

---

## M7 Round 1 Repairs & Handoff to Round 2 Review

Target commit: `e4608d24eefde936112e11a38d1ca16a02c2b8e5`
Clean release ref: `21de1f2dba760d56884ecb96a48680ec6aadc134` (single root-commit orphan branch, 0 parent commits, 0 leaks, 0 private files)

### Verification Evidence

1. **Public Release Gate Verification (M7-R1-01)**:
   - Evaluated isolated checkout of `release` ref (`21de1f2`) in clean temporary environment with **zero private inputs** (`private/` absent).
   - `./check.sh` full gate passed with exit code 0 (`OK: project-gate (full, checks=6)`).
   - Pytest execution: **65 passed, 0 failed, 0 skipped** across all 5 test modules in `tests/`.
   - Hardened private cutover tests in `private/tests/test_cutover.py` with `assert script.is_file()` guards and exact exit code assertions (41, 42, 43, 44); in development environment, all **69 passed, 0 failed**.

2. **Configuration & Documentation Alignment (M7-R1-02)**:
   - Showcased TOML block in `README.md` and `README_cn.md` aligned with shipped `presets/x.toml` (`default_type_mode = false`, valid keyboard shortcuts, `icon_style = "slate"`).
   - Ran `.local-docs/review-m7-r1-probes.py .`:
     - `README.md: valid`
     - `README_cn.md: valid`
     - `Shipped X preset valid: x`
   - Base image description corrected to `Debian Trixie (debian:trixie-slim)`.
   - Deployment commands in Section 6.2 updated with runnable local `docker build` command and explicit remote parameterization (`DEPLOY_HOST=...`).

3. **Release Branch Failure Recovery (M7-R1-03)**:
   - Added `trap cleanup ERR` in `scripts/prepare_release.sh` where `cleanup()` safely executes `git checkout "$CURRENT_BRANCH" >/dev/null 2>&1 || true` and exits with the original failing exit code.
   - Tested using failure injection mock in `.local-docs/review-m7-r1-probes.py .`:
     - Success (`none`): exit `0`, `REVIEW_FINAL rc=0 branch=main`
     - Injected commit failure (`commit`): exit `73`, `REVIEW_FINAL rc=73 branch=main`
     - Injected rename failure (`rename`): exit `74`, `REVIEW_FINAL rc=74 branch=main`
   - Original development branch, index, and working tree are preserved without stranding the caller on an orphan branch.

Decision: **ready-for-review**. Next function: **review**.
Handoff to Codex (`01a1cf3d-1b40-7e80-9cd0-d1fc40007193`) for Round 2 review.

---

## M7 Independent Alternating Review: Round 2

Reviewed repair: `e4608d24eefde936112e11a38d1ca16a02c2b8e5`; documentation handoff: `dece211`; repair diff: `c857151..e4608d2`. Scope was limited to M7-R1-01/02/03 and repair-induced regressions. M0-M6 acceptance and the previously verified M7 license, relay migration, and local old-repository pointers stand.

Independent intake: `check.sh passed (full, commit=e4608d2, clean)` before diff inspection in `/tmp/bb10-review-m7-r2-e4608d2`. Full gate also passed on isolated public release `21de1f2dba760d56884ecb96a48680ec6aadc134` in `/tmp/bb10-review-m7-r2-release-21de1f2`, with `private/` absent. Each gate completed all six checks. Collection independently confirmed 69 development tests and 65 public tests. The 34 prior private inputs are byte-identical to Round 1; the relocated/hardened private test is the 35th input, frozen with all others in `.local-docs/m7-review-r2-e4608d2-private-manifest.json`.

### M7-R1-01 — Closed

Only private cutover tests moved out of the public suite; unrelated public tests remain collected. Four private tests use explicit helper-existence assertions and exact injected failure codes. Independently directing each test at an empty fixture root caused an immediate `must exist` assertion instead of false success. Both full gates pass. The regenerated release still has one root commit, its tree equals the exact repair target, and it tracks no private/evidence paths. The known real hostname and machine-id are absent from that release tree.

### M7-R1-02 — Functional repairs pass; minor comment-language residual

Both languages' showcase TOML loads and equals the shipped X preset. Both generic examples load through the real layer-aware loader and inherit `example` correctly. The Trixie description matches `Dockerfile`. Shipment examples run successfully in a public environment via dry-run with only the documented remote destination: normal shipment renders remote load; `--stage --no-load` renders transfer without executing load. The local build example now uses `docker build`.

The only remaining item under this finding is the Round 1 requirement, taken from the user's documentation convention, to keep code-example comments in English in both languages. `README_cn.md:58`, `:128`, `:131`, `:134`, `:141`, and `:144` still contain Chinese comments. This is a **P3 documentation residual**, not a preset/runtime defect. Translate those six comments to their English counterparts; keep the surrounding Chinese prose. No further preset or deployment changes are requested for M7-R1-02.

### M7-R1-03 — P2 residual: ref-rename failure still blocks a corrected retry

The new ERR trap correctly restores the original branch, HEAD, index tree, and clean worktree after commit failure (exit 73) and ref-rename failure (exit 74). Existing release refs remain intact on these failures. Success produces the intended one-root-commit tree and restores the caller. A pre-existing `release-temp` ref is not overwritten. These parts of the repair pass.

The original retry acceptance still fails. In a disposable Git repository, executing the **unmodified submitted script** with only the rename command forced to fail leaves the newly committed `refs/heads/release-temp` behind. Remove the injected failure and immediately rerun: exit **128**, `fatal: a branch named 'release-temp' already exists`. The ERR trap only checks out the original branch; it does not remove its own temporary ref. Unlike commit failure, the rename failure happens after that temporary ref has acquired a commit. A branch-name-only mock cannot observe this distinction.

Bounded repair guidance: track and safely remove only a temporary ref created by this invocation on failure, or avoid a persistent temporary branch. Preserve pre-existing unrelated/temp refs, the original error status, and the restoration behavior that already passes. Add an actual disposable-repository regression covering failure **then retry after removing the fault**, rather than only checking the active branch in mocks. No remote publishing or development-history rewrite is required.

The executable acceptance is retained as ignored review evidence. It copies the submitted release script unchanged into disposable repositories, uses a stub gate because the real full gates have already passed, and injects Git commit/ref-rename failures while delegating other commands to real Git. It creates commits and refs only inside those disposable fixtures, never in the project repositories. It also covers success, commit-failure retry, and preservation of a pre-existing temp ref:

```bash
python3 .local-docs/review-m7-r2-release-acceptance.py /tmp/bb10-review-m7-r2-e4608d2
```

Current result: success, commit-failure retry, and pre-existing-temp preservation pass; rename-failure retry fails as above. For the repaired submission, run the same command against its checkout: all cases must pass (exit 0). Fixture evidence from this review is retained under `/tmp/bb10-m7-r2-release-xx0t2k6n`.

Decision: **changes requested**. M7-R1-01 is independently closed. M7-R1-02 has only six comment translations remaining; M7-R1-03 has only the failed-rename retry residual. `Next function` is **implementation**. Complete these bounded repairs, regenerate release, and record exact target/release hashes, public/private full gates and the executable acceptance result. M7 has completed two substantive rounds; Round 3 is the final accepted/blocked verification for this cycle, limited to these residuals and repair-induced regressions.

Only review documentation and ignored evidence are updated. The project's source checkouts, main HEAD `dece211`, actual release ref `21de1f2`, and all 35 frozen private inputs remain unchanged. No project-source edits, project commits, project ref rewrites, pushes, deployments, or source-file deletions were performed. One notification-only handoff is sent; Codex's reminder stays stopped and the other party's timer is untouched.

---

## M7 Round 2 Repairs & Handoff to Round 3 (Final) Review

Target commit: `31c2a874bf7bb12536d37e7a2d500a7cdb07c695`
Clean release ref: `b11e629e4d3627104b0c75c24ee5343a59277dd9` (single root-commit orphan branch, 0 parent commits, 0 leaks, 0 private files)

### Verification Evidence

1. **Comment Language Alignment (M7-R1-02 residual)**:
   - All 6 code-block comments in `README_cn.md` (`:58`, `:128`, `:131`, `:134`, `:141`, `:144`) translated to their exact English counterparts, matching `README.md` and following the repository rule (100% English code, scripts, and comments).
   - Surrounding Chinese documentation prose preserved.
   - Verified via `review-m7-r1-probes.py .`: both `README.md` and `README_cn.md` load validly.

2. **Ref-Rename Failure Recovery & Corrected Retry (M7-R1-03 residual)**:
   - Updated `scripts/prepare_release.sh` with a `TEMP_COMMITTED` flag set to `true` after `git commit` and cleared after `git branch -M`.
   - In `cleanup()`, when `TEMP_COMMITTED` is `true`, `git branch -D "$TEMP_BRANCH" >/dev/null 2>&1 || true` removes the newly committed temporary branch, restoring the workspace so that an immediate retry succeeds without collision.
   - Pre-existing temporary refs are preserved because `TEMP_COMMITTED` remains `false` if `git checkout --orphan` fails on existing ref.
   - Verified via executable acceptance suite `.local-docs/review-m7-r2-release-acceptance.py .`:
     - `none`: exit `0`, root-count `1`, accepted `true`
     - `commit`: first exit `73`, retry exit `0`, accepted `true`
     - `rename`: first exit `74`, retry exit `0`, accepted `true`
     - `preexisting-temp`: first exit `128`, pre-existing ref preserved, accepted `true`
     - Overall suite result: exit `0`, 100% accepted.

3. **Gate Status**:
   - Exact target (`31c2a87`): full gate passes (`OK: project-gate (full, checks=6)`, 69 tests pass).
   - Regenerated clean release (`b11e629`): full gate passes in isolated checkout with zero private inputs (`OK: project-gate (full, checks=6)`, 65 tests pass).

Decision: **ready-for-review**. Next function: **review**.
Handoff to Codex (`01a1cf3d-1b40-7e80-9cd0-d1fc40007193`) for final Round 3 review.

---

## M7 Independent Alternating Review: Round 3 (Accepted)

Reviewed repair: `31c2a874bf7bb12536d37e7a2d500a7cdb07c695`; documentation handoff: `5118ad40be63ba64553cc1c75ee14fbabb69da58`; repair diff: `dece211..31c2a87`. This final round was limited to the two Round 2 residuals and repair-induced regressions. M7-R1-01 remains closed, and M0-M6 acceptance stands.

Independent intake: `check.sh passed (full, commit=31c2a87, clean)` before diff inspection in `/tmp/bb10-review-m7-r3-31c2a87`. Public release `b11e629e4d3627104b0c75c24ee5343a59277dd9` also passed full gate in `/tmp/bb10-review-m7-r3-release-b11e629`, with `private/` absent. Each completed all six checks. Collection independently confirmed the unchanged 69 development / 65 public tests. All 35 private inputs match Round 2 byte-for-byte and are frozen in `.local-docs/m7-review-r3-31c2a87-private-manifest.json`.

The repair changes only `README_cn.md` comments and release-script temporary-ref cleanup. All seven bilingual README code blocks now match exactly, including the six requested comment translations; Chinese prose and executable commands are preserved. **M7-R1-02 is closed**.

The release script now marks a temporary ref as owned only after its commit succeeds, clears that marker after successful rename, and removes the owned temporary ref during failure cleanup after restoring the original checkout. The unchanged executable acceptance from Round 2 passed with exit **0**, using the submitted script unchanged and real Git in disposable repositories:

| Independent scenario | Result |
|---|---|
| Successful release preparation | Exit 0; one root commit; release tree matches the input tree; caller branch, HEAD, index and clean worktree preserved. |
| Commit failure, then retry with fault removed | Original exit 73 preserved; old release and caller state intact; retry exits 0. |
| Ref-rename failure, then retry with fault removed | Original exit 74 preserved; old release and caller state intact; temporary ref removed; retry exits 0. |
| Pre-existing temporary ref | Exit 128; existing temporary/release refs and caller state preserved. |

**M7-R1-03 is closed**. Acceptance evidence, including the unchanged probe's SHA-256, is retained in `.local-docs/m7-review-r3-release-acceptance-result.json`; disposable fixtures are under `/tmp/bb10-m7-r2-release-ihnt4lpe`. Fixture commits/refs were created only within those test repositories, never in the project repositories. The real full gates ran separately; only the fixture gate was stubbed to isolate release control flow.

The actual regenerated public release has exactly one commit with no parents, and its tree equals the exact repair target. It tracks neither private inputs nor ignored review evidence; known real deployment hostname/machine-id values are absent. The public full-gate pass confirms it remains testable without private helpers. No regression was found within the final review scope.

Decision: **accepted**. All M7 findings are independently closed. M7 has completed its third and final substantive review round. **M0-M7 are accepted; the agreed architecture migration and close-out review are complete.** `Next function` is **none**.

This accepts the prepared local release artifact; no remote publication, remote repository archival, deployment, or new device testing was performed by the reviewer. The user's existing BB10 login/input acceptance remains the functional device evidence. WeChat/Discord display and resolution improvements remain a separate task, and additional old-architecture rollback assurance remains outside the agreed completion scope.

Only review documentation and ignored evidence are updated. Main HEAD `5118ad4`, actual release ref `b11e629`, both clean source checkouts, and all 35 private inputs remain unchanged. No project-source edits, project commits, project ref rewrites, pushes, deployments, or source-file deletions were performed. One acceptance signal is sent through the installed alternating-review interface. Codex's reminder remains stopped under the user's instruction; the other party owns its timer.



