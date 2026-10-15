# Rapport de TP — Sécuriser un dépôt Python avec pre-commit

Projet : NOVA SERVICES — US-DEVSEC-001
Environnement : Windows 11, Python 3.11.9, pre-commit 4.7.0, Bandit 1.9.4 (hook 1.8.6),
detect-secrets 1.5.0, pytest 9.1.1, pip-audit 2.10.1.

Les sorties brutes sont dans [resultats/](resultats/).

---

## 1. Analyse du code initial (§3)

```python
import os

def get_message():
    password = "demo-secret-123"
    user_input = input("Entrez une expression : ")
    result = eval(user_input)
    return f"Résultat : {result}"
```

**Problèmes de qualité**
- `import os` inutilisé.
- `password` affecté mais jamais utilisé (code mort).
- Fonction qui mélange saisie, calcul et formatage : impossible à tester unitairement.
- Pas de gestion d'erreur (une saisie invalide lève une exception brute), pas de typage, pas de docstring.
- Fichier sans retour à la ligne final (corrigé par `end-of-file-fixer`).

**Risques de sécurité**
- `eval()` sur une entrée utilisateur → exécution de code arbitraire (CWE-95 / CWE-78).
- Mot de passe en dur dans le code source (CWE-259 / CWE-798).

**Pourquoi `eval()` est dangereux** — `eval` exécute n'importe quelle expression Python
avec les droits du processus. Une saisie comme `__import__('os').system('rm -rf ~')` ou
`open('/etc/passwd').read()` est exécutée telle quelle : lecture de fichiers, exécution de
commandes, exfiltration, déni de service (`9**9**9`). Restreindre `globals`/`builtins` ne
suffit pas, des contournements par introspection existent.

**Pourquoi pas de mot de passe dans le code** — le code est copié partout (postes,
forks, CI, sauvegardes, images) et l'historique Git le conserve même après suppression.
Toute personne ayant accès en lecture obtient le secret ; on ne peut pas le changer sans
redéployer, ni avoir des valeurs différentes par environnement.

**Correction proposée** — secret lu depuis l'environnement (`.env` local ignoré par Git,
`.env.example` versionné), `eval` remplacé par une liste blanche d'opérations
(`calculate`), saisie séparée du calcul pour pouvoir tester.

## 2. Problèmes détectés et corrections (livrable optionnel)

Résultat de `pre-commit run --all-files` sur le code initial ([03](resultats/03_pre_commit_code_initial.txt)),
puis tentative de commit refusée ([04](resultats/04_commit_refuse.txt)) :

| Hook | Résultat | Détail |
|---|---|---|
| end-of-file-fixer | Failed (auto-corrigé) | `app.py` sans saut de ligne final |
| bandit | **Failed** | `B307` eval — Medium/High — `app.py:6` |
| detect-secrets | **Failed** | `Secret Keyword` — `app.py:4` |

### Problème 1 — `eval()` sur entrée utilisateur (Bandit B307)
- **Détection** : Bandit, sévérité Medium, confiance High, CWE-78.
- **Correction** : fonction `calculate(a, b, operation)` qui n'accepte que `add`,
  `subtract`, `multiply`, `divide` ; toute autre valeur lève `ValueError`. Les nombres
  sont convertis par `float()`, qui n'exécute rien.
- **Preuve** : Bandit passe ; test `test_expression_injection_is_rejected` vérifie qu'une
  charge `__import__('os').system('id')` est refusée.

### Problème 2 — mot de passe en dur (detect-secrets + Bandit B105)
- **Détection** : detect-secrets (`Secret Keyword`). Bandit le voit aussi (B105, sévérité
  Low), mais le filtre `-ll` ne bloque pas les Low : c'est detect-secrets qui joue le rôle
  de garde-fou ici ([01b](resultats/01b_bandit_tous_niveaux.txt)).
- **Correction** : `get_password()` lit `APP_PASSWORD` via `python-dotenv`, lève une erreur
  s'il est absent, et ne l'affiche jamais. `.env` dans `.gitignore`, `.env.example` vide.
- **Preuve** : detect-secrets passe ; tests `test_get_password_*`.

### Observation sur le baseline
Une première génération avec `detect-secrets scan --exclude-files '^app\.py$'` a fait
**passer** le hook : le filtre d'exclusion est enregistré dans le baseline et le hook
l'applique ensuite. Démonstration concrète qu'un baseline mal construit masque un secret.
Le baseline final ne contient aucun filtre d'exclusion et `results` est vide : la valeur
trouvée n'a pas été acceptée comme faux positif.

### Autres scénarios de validation (§8)

| Scénario | Résultat obtenu | Trace |
|---|---|---|
| Test unitaire modifié pour échouer | `Tests unitaires ... Failed` → commit bloqué | [08](resultats/08_pytest_scenario_echec.txt) |
| Dépendance vulnérable (`requests==2.25.0`) | pip-audit : 24 vulnérabilités sur requests, idna, urllib3, exit 1 | [07](resultats/07_pip_audit_scenario_vulnerable.txt) |
| Dépendances réelles (`python-dotenv==1.2.4`) | No known vulnerabilities found | [06](resultats/06_pip_audit.txt) |
| Code corrigé, tous contrôles | 8/8 Passed, exit 0 | [09](resultats/09_pre_commit_final.txt) |

Exemple de qualification pip-audit (requests 2.25.0) : paquet `requests`, version 2.25.0,
`PYSEC-2023-74` (fuite de l'en-tête `Proxy-Authorization` lors de redirections), corrigé
en 2.31.0 ; impact si l'application passe par un proxy authentifié ; action : monter à la
dernière version corrigée (≥ 2.33.0 pour couvrir tous les identifiants remontés).
