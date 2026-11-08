<div align="center">

<img src="https://raw.githubusercontent.com/wiki/OpenUserJS/OpenUserJS.org/images/violentmonkey_icon.min.svg?sanitize=true" width="88" alt="Violentmonkey">

<h1>ViolentMonkey — AddDomain Fork</h1>

<p><b>Add any domain to a script's <code>@match</code> rules in one tap — from the popup or the dashboard.</b></p>

[![Build](https://img.shields.io/github/actions/workflow/status/BlazeFTL/ViolentMonkey_AddDomain/BuildFork.yml?branch=master&label=Build&logo=github&style=flat-square)](https://github.com/BlazeFTL/ViolentMonkey_AddDomain/actions)
[![Upstream](https://img.shields.io/badge/upstream-violentmonkey-7c3aed?style=flat-square&logo=github)](https://github.com/violentmonkey/violentmonkey)
[![Platform](https://img.shields.io/badge/Firefox-Android-FF6611?style=flat-square&logo=firefox-browser&logoColor=white)](https://addons.mozilla.org/firefox/addon/violentmonkey/)

</div>

---

## What This Fork Adds

Upstream Violentmonkey has no built-in way to add a domain to a script's `@match` without editing its header by hand. This fork fixes that and adds a lighter, touch-friendly UI.

| Feature | Where |
|---|---|
| **"+" button** — add a domain to any script | Popup, Dashboard |
| **Domain chips** — one-tap `domain`, `*.domain` and `domain.*` for the current tab | Popup, Dashboard |
| **Current tab button** — fills the input with the last popup tab's domain | Dashboard |
| **Table-view modal** — same add-domain flow when the dashboard is in table view | Dashboard |
| **Shorthand expansion** — commas and bare domains expanded to full `@match` lines on save | Editor |
| **Wildcard TLD** — `example.*` accepted without a bad-pattern warning | Matching |
| **Duplicate check** — an existing pattern is never added twice | Popup, Dashboard |
| **Toast feedback** — `<pattern> added to <script>`; script row message auto-clears | Popup, Dashboard |
| **UI redesign** — white theme, rounded cards, indigo accent, larger touch targets, dark mode ([details](#ui-redesign)) | Popup, Dashboard, Settings |
| **Readable build** — code minification disabled | Build |
| **Self-updating** — manifest `update_url` points to this repo's `updates.json` | Install |

---

## Adding a Domain

1. Tap **+** on a script (popup script row, or dashboard script card).
2. The input is pre-filled with `*.domain` of the current tab. Tap a chip to use another form:

   | Chip | Example | Written as |
   |---|---|---|
   | `domain` | `example.com` | `*://example.com/*` |
   | `*.domain` | `*.example.com` | `*://*.example.com/*` |
   | `domain.*` | `example.*` | `*://example.*/*` |

3. Tap **OK**. The line is inserted after the script's last `@match`.

Dashboard extras: **Current tab** re-fills the input from the last tab a popup was opened on. In table view, **+** opens a modal with the same buttons.

If the pattern already exists, a note is shown and nothing is written.

---

## Shorthand Expansion

Type shorthand in the editor. It is expanded when you save, and the editor refreshes to show the result.

```js
// Before saving                 →   After saving
// @match  example.com                // @match  *://*.example.com/*
// @match  example.com,xyz.*          // @match  *://*.example.com/*
                                      // @match  *://xyz.*/*
// @match  https://a.com/path/*       // @match  https://a.com/path/*   (unchanged)
```

Rules:

- Comma-separated values become one `@match` line each.
- A bare host with no scheme and no `*` defaults to the wildcard-subdomain form (`y.com` → `*://*.y.com/*`).
- A host that already contains `*` (`xyz.*`, `*.y.com`) keeps it and is wrapped as `*://host/*`.
- Missing scheme becomes `*://`. Missing path becomes `/*`.
- Already-valid patterns are left exactly as written.
- Only `@match` lines are affected.

---

## UI Redesign

Applied by `apply_patches_material.py`. It adds one stylesheet (`material.css`) and imports it after the upstream styles. Original sizes are kept; only shape, color and spacing change.

**Theme**

- Clean white background with an indigo accent (`#6366f1`; `#a5b4fc` in dark mode).
- Light gray borders and soft shadows instead of heavy outlines.
- Dark mode follows the system setting with matching tokens.

**Controls**

- Inputs, selects and textareas: 10px radius, accent border on focus.
- Buttons: 12px radius. Ghost buttons: 10px radius with hover and pressed states.
- Rounded modals, dropdown menus, tooltips, fieldsets and toasts.

**Popup**

- Script list shown as bordered, rounded cards with a soft shadow.
- Expanded group header stays pinned while scrolling.
- Menu rows and extras menu get rounded corners and hover/pressed feedback.

**Dashboard**

- Single white header, pill-shaped search box.
- Script cards are rounded with a shadow. Disabled and removed scripts get a muted background.
- Table view stays flat (no radius or shadow).

**Settings**

- Each section is a bordered, rounded card with a tinted indigo title bar.
- Collapsible sections use the same style.

**Touch devices only**

- Popup script rows are at least 52px tall.
- Script names wrap to two lines instead of truncating to one.
- Action buttons are 38px round targets with a divider.
- Script commands use taller rows.

---

## Screenshots

<img width="702" height="1560" alt="Screenshot_20260626-151626_Spark Launcher" src="https://github.com/user-attachments/assets/d62fff25-34c4-43f9-ad6a-747c1446253e" />
<img width="702" height="1560" alt="Screenshot_20260626-153758_Spark Launcher" src="https://github.com/user-attachments/assets/43a6e2f1-449d-401c-8e6a-c4f11b890cb2" />
<img width="702" height="1560" alt="Screenshot_20260626-153833_Spark Launcher" src="https://github.com/user-attachments/assets/053938d8-c11f-4fd8-adcd-f7b83ae78d6c" />
<img width="702" height="1560" alt="Screenshot_20260626-153840_Spark Launcher" src="https://github.com/user-attachments/assets/8f332b42-0ec3-4bf7-b4c9-c652060130cd" />

---

## Installation

### Pre-built

1. Open [**Releases**](../../releases) and pick the latest:
   - `V2.x.y` — stable build
   - `V2.x.y-Beta` — beta build (based on upstream beta)
2. Download the `.xpi` (or the `-Unsigned.zip`).
3. Install in Firefox:
   - **Permanent:** open the `.xpi`. Builds are unsigned, so Firefox needs `xpinstall.signatures.required` set to `false` in `about:config` (Nightly, Developer Edition, ESR).
   - **Temporary:** `about:debugging` → **Load Temporary Add-on** → pick any file inside the zip.

Installed builds check this repo for updates through `update_url`.

### Build from source

```bash
git clone https://github.com/BlazeFTL/ViolentMonkey_AddDomain
cd ViolentMonkey_AddDomain
pnpm i
python3 apply_patches_addmatch.py   # add-domain, shorthand, wildcard TLD, toasts
python3 apply_patches_material.py   # white / compact theme
pnpm build                          # output → dist/
```

Both patch scripts expect a clean upstream tree. Each anchor must match exactly once, otherwise the script exits with an error. Run the helper tests with `pnpm run ci`.

---

## Patch Files

| File | Purpose |
|---|---|
| `apply_patches_addmatch.py` | Popup and dashboard add-domain UI, `AddScriptMatch` / `GetTabDomain` / `GetLastPopupDomain` commands, shorthand expansion, wildcard TLD check, toasts, English strings, unit tests, no-minify build, `update_url` injection |
| `apply_patches_material.py` | Adds `material.css`: white theme, rounded cards, touch tap targets |

---

## Workflows

| Workflow | Trigger | Does |
|---|---|---|
| `BuildFork.yml` | Manual (`create_release` option) | Apply patches → install → test → build → upload artifact → optional release + `updates.json` |
| `sync-upstream.yml` | Daily, or manual | Merge upstream `master` (keeps this README on conflict), then trigger `BuildFork.yml` with release |
| `apply-patch-zip.yml` | Manual | Extract a patch bundle zip over a branch and push it |
| `ci.yml` | Push / PR to `master` | Upstream test and build |

Build details:

- **Version:** `<major>.<minor>.<beta>.<commit count>`, e.g. `2.49.6.1234`.
- **Release tag:** `V<package version>` for stable, `V<major.minor.beta>-Beta` for beta.
- **Assets:** `ViolentMonkey_AddDomain-V<version>.xpi` and `ViolentMonkey_AddDomain-V<…>-Unsigned.zip`.
- **Updates:** a release run force-pushes `updates.json` (with SHA-256) to the `updates` branch.

---

## Credits

Built on top of [violentmonkey/violentmonkey](https://github.com/violentmonkey/violentmonkey).
All original license terms apply — see [LICENSE](LICENSE).
