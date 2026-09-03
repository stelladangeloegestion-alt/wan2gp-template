---
name: docker-template-maintenance
description: Use when editing this repo — a Dockerized RunPod template that launches Wan2GP (Wan 2.2 Animate) with pre-baked LoRAs. Covers the Dockerfile build, the boot scripts (start-wan2gp.sh, restart-wan2gp.sh, startup.sh), the asset manifest (assets/manifest.json, scripts/bootstrap_assets.py), and how to validate a change without a GPU/RunPod runtime. Trigger on requests to bump the pinned Wan2GP commit, change CUDA/PyTorch/gradio versions, add or update a LoRA, or fix a boot/runtime issue.
---

# Maintaining the Wan2GP RunPod template

This repo builds a single Docker image (no CI, no test suite) that RunPod
boots to run [Wan2GP](https://github.com/deepbeepmeep/Wan2GP)'s Wan 2.2
Animate model. There's no way to actually run the container here (needs a
CUDA GPU + RunPod's `/workspace` volume), so correctness comes from careful
review plus the syntax/static checks below — always run them before
considering a change done.

## Repo structure

- **`Dockerfile`** — builds from `pytorch/pytorch:2.8.0-cuda12.8-cudnn9-runtime`,
  clones Wan2GP at a pinned commit (`ARG WAN2GP_COMMIT`, defaults to `main`),
  patches a deprecated `torch.cuda.amp.autocast` call, installs Python deps
  (gradio is pinned to `4.44.1` — v5+ caused blank-UI regressions, don't bump
  it without checking that upstream issue is actually fixed), and prefetches
  two LoRA files into the image so the first generation doesn't wait on a
  download.
- **`start-wan2gp.sh`** (copied to `/opt/start-wan2gp.sh`) — the container's
  runtime entrypoint target. Sets up a 16 GB swapfile, memory-friendly Gradio
  env vars, ffmpeg NVENC defaults, then launches `wgp.py` and tails the log.
  Keep it `set -Eeuo pipefail` and prefer `|| true` on any step that's
  best-effort (swap setup, sanity prints) so a non-critical failure doesn't
  kill the boot.
- **`restart-wan2gp.sh`** — kills `wgp.py` and re-execs
  `/opt/start-wan2gp.sh`; installed to `/usr/local/bin/`.
- **`startup.sh`** — thin RunPod entry shim that just execs
  `/opt/start-wan2gp.sh`.
- **`scripts/bootstrap_assets.py`** + **`assets/manifest.json`** — a
  general-purpose downloader for large assets (LoRAs) listed in the
  manifest, with size verification and a `urllib`→`curl` fallback. Add a new
  LoRA by adding a `{name, url, dest, size_mb}` entry to the manifest, not by
  hardcoding another `curl` call somewhere else.

## Before considering a change done

There's no GPU here to actually boot the image, so validate what you can
statically:

```bash
bash -n start-wan2gp.sh
bash -n restart-wan2gp.sh
bash -n startup.sh
python3 -m py_compile scripts/bootstrap_assets.py
```

The helper script in this skill runs all of these in one shot:

```bash
python3 .claude/skills/docker-template-maintenance/scripts/check_template.py
```

Also do a manual read-through of any `Dockerfile` edit — a broken instruction
only surfaces at image-build time (there's no `docker build` available in
this environment), so re-check line-by-line: `ARG`s before their first use,
`ENV`/`RUN` ordering (Torch is already in the base image — never add a step
that reinstalls it), and that `COPY`'d scripts still get `chmod +x`'d.

## Version pinning conventions

- `WAN2GP_COMMIT` exists specifically to avoid nightly breakage — don't
  silently change the default away from a pinned SHA to `main` (or vice
  versa) without calling it out in the change description; the whole point
  of this template is a stable, reproducible boot.
- `gradio` is pinned for the same reason (v4, not v5+). Any version bump to
  a pinned dependency (gradio, the base PyTorch/CUDA image, numpy/cython/
  setuptools ceilings) should be called out explicitly, since each pin in
  this Dockerfile exists to work around a specific known issue (see the
  inline comments next to each `RUN` block).
- README's "Challenges Solved" and "System Optimizations" sections describe
  the reasons behind these pins — read them before loosening a constraint,
  and update them if the change affects what they claim.
