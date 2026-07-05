# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
Build des notebooks marimo vers HTML/WebAssembly pour GitHub Pages.

- `notebooks/*.py`  -> exportés en mode ÉDITABLE (l'apprenant voit et modifie le code)
- `apps/*.py`       -> exportés en mode APP (lecture seule, code masqué)  [optionnel]
- `public/`         -> copié tel quel dans `_site/public/` (les données y sont lues
                       à l'exécution via `mo.notebook_location()`)
- `index.html`      -> page d'accueil listant les notebooks

Aucune dépendance externe : on shelle vers `uvx marimo` (installé par le workflow).
Usage :  uv run .github/scripts/build.py [--output _site]
"""
import argparse
import hashlib
import shutil
import subprocess
import sys
from pathlib import Path

# Purge le stockage marimo du navigateur quand le notebook a changé depuis la
# dernière visite : sinon la session sauvegardée marque les cellules modifiées
# « à exécuter » au lieu de relancer l'auto-run. Doit s'exécuter AVANT le JS marimo.
RESET_SCRIPT = """<script>
(function () {
  var v = "__BUILD_VERSION__";
  var cle = "cours-build:" + location.pathname;
  try {
    if (localStorage.getItem(cle) !== v) {
      localStorage.clear();
      sessionStorage.clear();
      try { indexedDB.deleteDatabase("/marimo"); } catch (e) {}
      if (indexedDB.databases) {
        indexedDB.databases().then(function (dbs) {
          dbs.forEach(function (d) { indexedDB.deleteDatabase(d.name); });
        });
      }
      localStorage.setItem(cle, v);
    }
  } catch (e) {}
})();
</script>"""


def post_process(out_file: Path, nb: Path) -> None:
    """Snapshot affiché immédiatement + auto-run + reset de session si nouveau build."""
    html = out_file.read_text(encoding="utf-8")
    # --execute fige les sorties mais désactive l'auto-run : on le réactive.
    html = html.replace('"auto_instantiate": false', '"auto_instantiate": true')
    version = hashlib.sha256(nb.read_bytes()).hexdigest()[:12]
    script = RESET_SCRIPT.replace("__BUILD_VERSION__", version)
    html = html.replace("<head>", "<head>" + script, 1)
    out_file.write_text(html, encoding="utf-8")
    print(f"→ post-process {out_file.name} (version {version})")


def export(nb: Path, out_dir: Path, as_app: bool) -> dict | None:
    out_file = out_dir / nb.with_suffix(".html")
    out_file.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["uvx", "marimo", "export", "html-wasm", "--sandbox",
           "--mode", "run" if as_app else "edit",
           "--execute"]  # pré-exécute : les sorties sont figées dans le HTML
    if as_app:
        cmd.append("--no-show-code")
    cmd += [str(nb), "-o", str(out_file)]
    print("→", " ".join(cmd), flush=True)
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"!! échec export {nb}: {e}", file=sys.stderr)
        return None
    post_process(out_file, nb)
    return {"name": nb.stem.replace("_", " ").title(),
            "path": str(nb.with_suffix(".html"))}


def collect(folder: str, out_dir: Path, as_app: bool) -> list[dict]:
    p = Path(folder)
    if not p.exists():
        return []
    items = [export(nb, out_dir, as_app) for nb in sorted(p.rglob("*.py"))]
    return [i for i in items if i]


def write_index(out_dir: Path, notebooks: list[dict], apps: list[dict]) -> None:
    def li(items):
        return "".join(
            f'<li><a href="{i["path"]}">{i["name"]}</a></li>' for i in items)
    sections = ""
    if notebooks:
        sections += f"<h2>Notebooks (interactifs)</h2><ul>{li(notebooks)}</ul>"
    if apps:
        sections += f"<h2>Apps (lecture seule)</h2><ul>{li(apps)}</ul>"
    html = f"""<!doctype html>
<html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Parcours rapides — Bonus IA Engineering (Deloitte / LIORA)</title>
<style>
  body{{font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;
       max-width:760px;margin:3rem auto;padding:0 1.2rem;color:#1a2b4a;line-height:1.55}}
  h1{{color:#1a2b4a}} h2{{margin-top:2rem;font-size:1.1rem;color:#33465f}}
  a{{color:#e06a2b;text-decoration:none}} a:hover{{text-decoration:underline}}
  li{{margin:.55rem 0;font-size:1.1rem}}
  .note{{background:#f4f1ea;border-left:4px solid #e06a2b;padding:.8rem 1rem;border-radius:6px;font-size:.92rem}}
</style></head><body>
<h1>Parcours « Pour les rapides »</h1>
<p>Cours interactifs marimo, exécutés <b>dans le navigateur</b> (WebAssembly).
Zéro installation : cliquez, lisez, exécutez, modifiez.</p>
{sections}
<p class="note">Données de paie <b>anonymisées et minimisées</b> (aucun nom, matricules
pseudonymes). Contenu pédagogique — extension du parcours no-code Flowise J4→J7.</p>
</body></html>"""
    (out_dir / "index.html").write_text(html, encoding="utf-8")
    print("→ index.html")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", default="_site")
    args = ap.parse_args()
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)

    notebooks = collect("notebooks", out, as_app=False)
    apps = collect("apps", out, as_app=True)

    # Copier les données publiques (lues à l'exécution par les notebooks)
    if Path("public").exists():
        shutil.copytree("public", out / "public", dirs_exist_ok=True)
        print("→ public/ copié")

    if not notebooks and not apps:
        print("!! aucun notebook trouvé", file=sys.stderr)
        sys.exit(1)

    write_index(out, notebooks, apps)
    print(f"OK — build dans {out}/")


if __name__ == "__main__":
    main()
