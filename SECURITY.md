# Security & Responsible-Use Policy

This repository is a **catalog of security research**. It is documentation and
data only, it contains **no runnable model, no attack code, no exploit, no
jailbreak prompts, and no poisoned artifacts**. The Python scripts under
`scripts/` are offline generators that read a local spreadsheet and emit
Markdown/JSON/CSV/YAML; they perform no network calls and execute no untrusted
code.

## If you find a security issue in *this repository*

For any vulnerability in the tooling or generated site (for example, a bug in
`scripts/` that could be abused, or a dependency/tooling problem), please
**do not open a public issue**. Instead:

1. Use GitHub's **private vulnerability reporting** if enabled on this repo
   (*Security → Report a vulnerability*), **or**
2. Contact the maintainers privately through the channel listed in the project's
   profile / the email on file for the repository owner.

Please include a description of the issue, steps to reproduce, and any
potential impact. We aim to acknowledge reports promptly and coordinate
disclosure responsibly.

## Responsible use of the linked benchmarks

Many benchmarks indexed here deliberately contain **adversarial, offensive,
explicit, or otherwise sensitive material**, jailbreak prompts, harmful-request
datasets, toxic text, backdoored models, and attack tooling, that exists purely
for **defensive research and evaluation**.

When you follow a link out of this catalog:

- Access those resources **only** through their official sites, under **their**
  licenses and terms of use.
- Handle any sensitive data in accordance with applicable laws, institutional
  review requirements, and platform policies.
- Use them to **build and evaluate defenses**, not to cause harm.
- Do not re-upload raw harmful payloads into this repository; link to the
  canonical source instead.

## Scope

Nothing in this repository constitutes legal, security, or professional advice.
Descriptions summarize publicly available research and may contain errors; always
verify against the primary source (the linked paper) before relying on or citing
any figure or claim. See the README's
[Provenance & Data Notes](README.md#provenance--data-notes) and
[Responsible-Use Disclaimer](README.md#responsible-use-disclaimer).
