# Install the factory on a Mac Mini

The Mini is the execution host. Keep the factory skills, target repositories,
worktrees, tools, test processes, evidence files, and credentials there. Your laptop
controls that host through your chosen remote connection. Run the coding agent
on the Mini as the factory user. A laptop agent operating a local checkout still
runs locally unless its execution environment is explicitly remote.

The Jev client and context preparation run on the Mini. Inference runs at TypeSafe's
hosted API; Jev model weights are not installed on the Mini. Do not copy the
laptop's Python environment or assume its credentials or macOS permissions transfer.

This repository supplies skills and helpers. It does not itself provide a remote
job server, agent runtime, scheduler, or network-access configuration.

## Transfer this local version

The Jev branch has not been pushed to GitHub. Cloning the upstream URL alone will
not install these additions. Transfer the supplied `software-factory-jev.bundle`
to the Mini, then run there:

```bash
git clone -b agent/jev-audit-0922 software-factory-jev.bundle software-factory
cd software-factory
git bundle verify ../software-factory-jev.bundle
git log -1 --oneline
```

The bundle is self-contained Git history. It excludes local `.venv`, `.artifacts`,
credentials, and nested worktree metadata. Its `origin` points at the transferred
bundle, so it is a transfer source, not a remote you can push to. Choose your own
private repository later if you want shared version control; no upstream push is
needed for installation. Use fresh worktrees in each target project as usual.

## Choose a profile and install

Install Apple's command-line developer tools if Git is unavailable. Install
Homebrew from [brew.sh](https://brew.sh/) if it is not already present. Use the
factory account for the commands below, not root.

For browser automation and non-UI work without desktop recording:

```bash
bash scripts/setup-mac.sh --install-system
```

For full desktop evidence recording and before/after captures:

```bash
bash scripts/setup-mac.sh --desktop --install-system --install-browser-tools
```

`--install-system` explicitly permits Homebrew to install Python, Git, Node, GitHub
CLI, and jq. Desktop mode also installs `ffmpeg-full`. `--install-browser-tools`
installs the existing workflow's `@vercel/before-and-after` and `agent-browser`
packages through npm. Browser executable provisioning remains a separate acceptance
step for your chosen automation tool; the presence of a CLI is not a working browser.
The script always creates a local `.venv` if absent and installs pinned Python
runtime/test dependencies. Without those flags it does not install system tools.
It is safe to rerun; it does not replace credentials or rewrite shell profiles.

Configure `git user.name` and `git user.email` for the factory account or each
project. Missing values appear as explicit failed checks. The setup may exit with
code 2 until you resolve the reported prerequisites; read its JSON remedies.

### FFmpeg selection

Homebrew's [ffmpeg-full](https://formulae.brew.sh/formula/ffmpeg-full) is keg-only
and includes libass. Installing it does not guarantee that an earlier `ffmpeg` on
PATH stops being selected. Installing libass alone also does not retrofit a
subtitle filter into an already-built FFmpeg executable.

Use `scripts/factory-python.sh` when launching helpers. It supplies this repo's
Python environment and puts Homebrew's `ffmpeg-full/bin` first, on both Apple
Silicon and Intel Homebrew paths. It works without depending on interactive shell
startup files. If launching the coding agent separately, give that process the
same PATH before it starts so its capture commands also use the correct FFmpeg.
A custom/non-Homebrew FFmpeg build is acceptable if the capability checks pass.

The doctor checks `ffmpeg`, `ffprobe`, `libx264`, the `ass` subtitle filter, and
macOS `avfoundation`. It reports the selected executable paths. It does not infer
readiness merely from package names.

## Verify on the Mini

Run from the installed repository:

```bash
bash scripts/factory-python.sh scripts/factory_doctor.py --profile desktop
bash scripts/factory-python.sh scripts/smoke_video.py
bash scripts/factory-python.sh -m pytest tests/test_jev_gate.py tests/test_factory_doctor.py -q
bash scripts/factory-python.sh jev-gate/examples/demo.py --out .artifacts/mini-demo-001
```

Choose a fresh demo output name on reruns. For headless-only work use
`--profile headless` and omit `smoke_video.py` if FFmpeg is intentionally absent.
The smoke renders a synthetic one-second H.264 video with a subtitle filter and
probes it. It never records your desktop and does not prove GUI permissions.

The doctor returns 0 when its automated requirements pass, and 2 when they fail.
Manual checks remain listed separately. `ready_for_unattended_work` stays false:
a CLI cannot verify your chosen agent, browser session, real task behavior, and
repository integration from dependency availability alone. The baseline recorder
suite also contains Linux-specific tests; use the targeted cross-platform checks
above for this setup and consult `docs/jev-validation.md` before interpreting the
full legacy suite on macOS.

## Credentials and agent installation

Install and authenticate your chosen coding-agent application on the Mini. Copy
all eight skill directories from this local version into that agent's supported
project skill location, or configure it to load them here. Keep each complete
folder with its scripts and references. Adapt `AGENTS.md` into each target project
without overwriting its existing project rules. Record that project's actual
checks, Jev stages, and evidence requirements.

Authenticate GitHub as the factory user with `gh auth login`. Verify Greptile is
installed on the target repositories. Put `TYPESAFE_API_KEY` in the environment of
the actual factory process using your preferred secret store. Do not commit the
key or embed it in a launch command, manifest, or shared configuration file.
An SSH session and a GUI/background process can have different environments.

```bash
bash scripts/factory-python.sh scripts/factory_doctor.py --profile desktop --live-jev --check-auth
```

The credential check reports presence only, never the key. GitHub authentication
checking is opt-in and suppresses raw auth output. Jev key validity and API access
still need a small approved live request using the gate's prepare/run process.
Begin with shadow mode and follow `jev-gate/references/operation.md`.

## Remote and desktop acceptance

Use your existing remote access arrangement. This change does not configure SSH,
Tailscale, firewall rules, DNS, or an externally reachable factory service.
When connecting from the laptop, verify the reported hostname and executable paths
belong to the Mini. Run the doctor from the same account and launch environment
that will execute real tasks, including after a reboot.

For desktop testing, keep a usable logged-in GUI session on the Mini. Grant Screen
Recording and, where required by the UI automation tool, Accessibility permissions
to the actual application hosting the factory. Check the current macOS privacy
settings and restart that app if requested. SSH connectivity or a listed capture
device does not prove these permissions work. A locked or unavailable desktop may
require headless browser capture instead.

Before calling the Mini ready, complete these actual checks:

1. Launch the chosen agent remotely and confirm its commands run on the Mini.
2. Create a test worktree in a disposable project and execute its checks.
3. Launch the configured browser and save a real screenshot on the Mini.
4. For desktop mode, run the recorder's `doctor`, then make and inspect a brief
   real screen recording using `evidence-driven-testing/SKILL.md`.
5. Run an approved small Jev request; retain its pinned model, usage, and result.
6. On an authorized test PR, confirm GitHub/Greptile and evidence publication work.
7. Reconnect after a reboot and repeat the relevant host/environment checks.

The laptop verification is preparation for this installation. It is not evidence
that the other Mac's permissions, credentials, browser, or remote execution work.

## Local Jev key file

For launcher-based runs, save only the raw key on one line in
`.secrets/typesafe-api-key` inside this factory checkout. Do not add quotes,
`export`, or `TYPESAFE_API_KEY=`. Create the directory with mode 700 and the file
with mode 600. The launcher reads it literally; it does not execute its contents.
An existing non-empty TYPESAFE_API_KEY environment value takes precedence.

`.secrets/`, `.env`, and `.env.*` are ignored by Git, and the Jev context packager
rejects `.secrets` sources. Verify with `git check-ignore .secrets/typesafe-api-key`.
Create this file separately on the Mini; Git bundles do not transfer it. Direct
Python commands bypass the launcher and still require an environment variable.

## Optional Supercov measurement

Follow [the Supercov integration guide](supercov-integration.md) to install the
pinned local tool and run its smoke test on the Mini. This is separate from the
base setup and does not require a TypeSafe key.
