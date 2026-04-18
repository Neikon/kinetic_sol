# AGENTS.md

## Read First

Before continuing development in this repository, read these files in this order:

1. [docs/agent_memory.md](/var/home/neikon/Projects/KineticSOL/docs/agent_memory.md)
2. [docs/app_spec.md](/var/home/neikon/Projects/KineticSOL/docs/app_spec.md)
3. [docs/roadmap.md](/var/home/neikon/Projects/KineticSOL/docs/roadmap.md)

## Project Operating Rules

- This repository is for a Linux-only companion app for Kinetic WOL.
- The app must be built with GTK4 + libadwaita and packaged as Flatpak.
- Prefer Flatpak-first decisions that fit immutable distros such as Bazzite, Silverblue, and Kinoite.
- Do not design the product around interactive `sudo`.
- The preferred shutdown path is `org.freedesktop.login1` over the system bus, governed by polkit.
- Request only the minimum Flatpak permissions needed, especially for system bus access.
- Assume the product is a single app with UI plus background listening logic unless the documented architecture changes.
- Keep source code and inline code comments in English.
- Keep user-facing project documentation in Spanish unless there is a reason to switch.

## Git Workflow

- Explore the repo before making assumptions.
- Document important decisions first, then implement.
- Create small, coherent commits for each meaningful milestone.
- Push after each relevant commit unless the user explicitly asks to keep work local.
- Prefer a clean, reversible history over large mixed commits.
