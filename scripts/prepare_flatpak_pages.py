#!/usr/bin/env python3

from __future__ import annotations

import argparse
import html
from pathlib import Path


INDEX_TEMPLATE = """<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{app_name} Flatpak Repository</title>
  <style>
    :root {{
      color-scheme: dark;
      --bg: #17192b;
      --panel: #232745;
      --panel-2: #1d213a;
      --text: #f5f7ff;
      --muted: #b3bfdc;
      --accent: #8fa8ff;
      --accent-2: #a4e2ff;
      --border: rgba(255, 255, 255, 0.08);
    }}

    * {{
      box-sizing: border-box;
    }}

    body {{
      margin: 0;
      font-family: "Noto Sans", "Cantarell", system-ui, sans-serif;
      background:
        radial-gradient(circle at top, rgba(143, 168, 255, 0.18), transparent 34%),
        linear-gradient(180deg, #1a1d33 0%, var(--bg) 100%);
      color: var(--text);
    }}

    main {{
      width: min(920px, calc(100% - 32px));
      margin: 0 auto;
      padding: 48px 0 64px;
    }}

    .hero {{
      background: linear-gradient(180deg, rgba(255,255,255,0.04), rgba(255,255,255,0.02));
      border: 1px solid var(--border);
      border-radius: 28px;
      padding: 28px;
      box-shadow: 0 18px 60px rgba(0, 0, 0, 0.28);
    }}

    h1, h2 {{
      margin: 0 0 12px;
      line-height: 1.1;
    }}

    h1 {{
      font-size: clamp(2.2rem, 3vw, 3.2rem);
    }}

    h2 {{
      font-size: 1.15rem;
      color: var(--accent-2);
      margin-top: 28px;
    }}

    p, li {{
      color: var(--muted);
      line-height: 1.6;
    }}

    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
      gap: 16px;
      margin-top: 24px;
    }}

    .card {{
      background: var(--panel-2);
      border: 1px solid var(--border);
      border-radius: 20px;
      padding: 18px;
    }}

    a {{
      color: var(--accent-2);
    }}

    code, pre {{
      font-family: "JetBrains Mono", "Fira Code", monospace;
      font-size: 0.95rem;
    }}

    pre {{
      white-space: pre-wrap;
      overflow-x: auto;
      background: #101221;
      border: 1px solid var(--border);
      border-radius: 18px;
      padding: 16px;
      margin: 12px 0 0;
      color: #ebf1ff;
    }}

    .notes {{
      margin-top: 24px;
      padding: 20px;
      border-radius: 20px;
      border: 1px solid var(--border);
      background: rgba(255, 255, 255, 0.03);
    }}

    .muted {{
      color: var(--muted);
    }}
  </style>
</head>
<body>
  <main>
    <section class="hero">
      <p class="muted">Flatpak Repository</p>
      <h1>{app_name}</h1>
      <p>
        Este sitio publica el repositorio Flatpak estático de <strong>{app_name}</strong>
        generado desde GitHub Actions.
      </p>
      <p>
        Versión actual: <strong>{app_version}</strong>
      </p>

      <div class="grid">
        <div class="card">
          <h2>Añadir el remote</h2>
          <pre>{remote_add_command}</pre>
        </div>
        <div class="card">
          <h2>Instalar la app</h2>
          <pre>{install_command}</pre>
        </div>
      </div>

      <div class="notes">
        <h2>Release Notes</h2>
        {release_notes}
      </div>

      <div class="grid">
        <div class="card">
          <h2>Archivos publicados</h2>
          <ul>
            <li><a href="{flatpakrepo_name}">{flatpakrepo_name}</a></li>
            <li><a href="repo/">Repositorio OSTree</a></li>
          </ul>
        </div>
        <div class="card">
          <h2>Notas</h2>
          <ul>
            <li>{signature_note}</li>
            <li>Runtimes y dependencias se resuelven desde Flathub.</li>
          </ul>
        </div>
      </div>
    </section>
  </main>
</body>
</html>
"""


def build_flatpakrepo(
    *,
    title: str,
    repo_url: str,
    homepage: str,
    default_branch: str,
    gpg_key_base64: str | None,
) -> str:
    lines = [
        "[Flatpak Repo]",
        f"Title={title}",
        f"Url={repo_url}",
        f"Homepage={homepage}",
        "Comment=Official Flatpak repository for KineticSOL",
        "Description=GitHub Pages Flatpak repository for KineticSOL.",
        f"DefaultBranch={default_branch}",
    ]
    if gpg_key_base64:
        lines.append(f"GPGKey={gpg_key_base64}")
    lines.append("")
    return "\n".join(lines)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--app-id", required=True)
    parser.add_argument("--app-name", required=True)
    parser.add_argument("--app-version", required=True)
    parser.add_argument("--release-notes-html", required=True)
    parser.add_argument("--repo-url", required=True)
    parser.add_argument("--homepage-url", required=True)
    parser.add_argument("--remote-name", required=True)
    parser.add_argument("--default-branch", required=True)
    parser.add_argument("--gpg-key-base64")
    parser.add_argument("--flatpakrepo-name", default="kineticsol.flatpakrepo")
    return parser.parse_args()


def main():
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    flatpakrepo_text = build_flatpakrepo(
        title=f"{args.app_name} Flatpak Repository",
        repo_url=args.repo_url,
        homepage=args.homepage_url,
        default_branch=args.default_branch,
        gpg_key_base64=args.gpg_key_base64,
    )
    (output_dir / args.flatpakrepo_name).write_text(flatpakrepo_text, encoding="utf-8")
    (output_dir / ".nojekyll").write_text("", encoding="utf-8")

    remote_add_command = (
        f"flatpak remote-add --if-not-exists "
        f"--from {args.remote_name} {args.repo_url.removesuffix('/repo/')}/{args.flatpakrepo_name}"
    )
    install_command = f"flatpak install {args.remote_name} {args.app_id}//{args.default_branch}"
    signature_note = (
        "Este remote está <strong>firmado con GPG</strong> y puede añadirse sin banderas"
        " especiales."
        if args.gpg_key_base64
        else "Este remote es <strong>unsigned</strong> por ahora y requiere "
        "<code>--no-gpg-verify</code>."
    )
    index_html = INDEX_TEMPLATE.format(
        app_name=html.escape(args.app_name),
        app_version=html.escape(args.app_version),
        remote_add_command=html.escape(remote_add_command),
        install_command=html.escape(install_command),
        release_notes=args.release_notes_html,
        signature_note=signature_note,
        flatpakrepo_name=html.escape(args.flatpakrepo_name),
    )
    (output_dir / "index.html").write_text(index_html, encoding="utf-8")


if __name__ == "__main__":
    main()
