# NOVA SERVICES — Dépôt Python sécurisé par pre-commit

Mise en œuvre de l'US-DEVSEC-001 : contrôles de qualité et de sécurité exécutés
automatiquement avant chaque commit.

## Contrôles en place

| Hook | Outil | Bloquant | Rôle |
|---|---|---|---|
| `trailing-whitespace`, `end-of-file-fixer` | pre-commit-hooks v5.0.0 | oui (auto-corrige) | Hygiène des fichiers |
| `check-added-large-files`, `check-yaml` | pre-commit-hooks v5.0.0 | oui | Gros fichiers, YAML invalide |
| `bandit` (`-ll`) | Bandit 1.8.6 | oui | Pratiques Python dangereuses (sévérité ≥ Medium) |
| `detect-secrets` | detect-secrets v1.5.0 | oui | Secrets potentiels (comparés à `.secrets.baseline`) |
| `pytest` | pytest (local) | oui | Tests unitaires |
| `pip-audit` | pip-audit (local) | oui | Vulnérabilités connues dans `requirements.txt` |

## Installation (reproductible)

Versions de référence : Python 3.11, outils épinglés dans `requirements-dev.txt`.

```bash
python -m venv .venv
# Linux/macOS
source .venv/bin/activate
# Windows PowerShell
.\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
pre-commit install

cp .env.example .env   # puis renseigner APP_PASSWORD localement (jamais commité)
```

> Les hooks `pytest` et `pip-audit` sont en `language: system` : l'environnement
> virtuel doit être **activé** au moment du commit.

## Utilisation

```bash
pre-commit run --all-files        # tous les contrôles sur tout le dépôt
pytest -q                         # tests seuls
pip-audit -r requirements.txt     # audit des dépendances seul
```

Si un hook modifie un fichier (espaces, fin de fichier), vérifier avec `git diff`,
refaire `git add`, puis recommiter.

## Limite

Un hook local peut être contourné (`--no-verify`, `core.hooksPath`) : il doit être
complété par une CI et une protection de `main` côté serveur.

## Documentation

- [docs/RAPPORT_TP.md](docs/RAPPORT_TP.md) — analyse du code et des problèmes détectés
- [docs/resultats/](docs/resultats/) — sorties brutes des exécutions
