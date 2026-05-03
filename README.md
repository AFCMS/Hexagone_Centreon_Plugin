# Hexagone Centreon Plugin

Plugin Centreon/Nagios en Python permettant de superviser la file d'attente des commandes d'une application e-commerce à partir d'un fichier JSON.

---

## Table des matières

1. [Prérequis](#prérequis)
2. [Installation](#installation)
3. [Description du plugin](#description-du-plugin)
4. [Logique du plugin](#logique-du-plugin)
5. [Options disponibles](#options-disponibles)
6. [Exemples d'exécution](#exemples-dexécution)
7. [Intégration Centreon](#intégration-centreon)
8. [Gestion des erreurs](#gestion-des-erreurs)

---

## Prérequis

- Python 3.6 ou supérieur (inclus dans toutes les distributions Linux modernes)
- Accès en lecture au fichier JSON de l'application (par défaut `/var/www/app/data/orders_queue.json`)

---

## Installation

```bash
# Copier le plugin dans le dossier standard des plugins Centreon/Nagios
sudo cp check_orders_queue.py /usr/lib/centreon/plugins/check_orders_queue.py

# Rendre le script exécutable
sudo chmod +x /usr/lib/centreon/plugins/check_orders_queue.py

# Vérifier que le plugin fonctionne
/usr/lib/centreon/plugins/check_orders_queue.py --help
```

---

## Description du plugin

Le plugin lit un fichier JSON mis à jour par l'application e-commerce et extrait la valeur `pending_orders`. En fonction de cette valeur, il retourne un état Nagios/Centreon avec le code de sortie correspondant et un message au format standard incluant les données de performance (*perfdata*).

### Format du fichier JSON attendu

```json
{
  "pending_orders": 45,
  "processing_orders": 12,
  "failed_orders": 3,
  "last_update": "2026-02-27T10:30:00Z"
}
```

### Format de sortie Nagios/Centreon

```
<STATUT> - <N> commandes en attente | pending_orders=<N>;<warn>;<crit>;0;
```

---

## Logique du plugin

```
Lecture du fichier JSON
        │
        ├─► Fichier introuvable           → UNKNOWN (exit 3)
        ├─► JSON invalide                 → UNKNOWN (exit 3)
        ├─► Clé pending_orders absente    → UNKNOWN (exit 3)
        └─► Valeur non numérique          → UNKNOWN (exit 3)
                │
                ▼
        pending_orders > 100  →  CRITICAL (exit 2)
        pending_orders >= 50  →  WARNING  (exit 1)
        pending_orders < 50   →  OK       (exit 0)
```

| Condition                          | État     | Code de sortie |
|------------------------------------|----------|---------------|
| `pending_orders < 50`              | OK       | 0             |
| `50 <= pending_orders <= 100`      | WARNING  | 1             |
| `pending_orders > 100`             | CRITICAL | 2             |
| Valeur non numérique / autre erreur| UNKNOWN  | 3             |

---

## Options disponibles

| Option              | Description                                      | Défaut                                      |
|---------------------|--------------------------------------------------|---------------------------------------------|
| `-f`, `--file`      | Chemin vers le fichier JSON                      | `/var/www/app/data/orders_queue.json`       |
| `-w`, `--warning`   | Seuil WARNING pour `pending_orders` (inclus)     | `50`                                        |
| `-c`, `--critical`  | Seuil CRITICAL — déclenché si `pending_orders > seuil`   | `100`                                       |
| `-t`, `--timeout`   | Timeout en secondes                              | `10`                                        |
| `-h`, `--help`      | Afficher l'aide                                  |                                             |

---

## Exemples d'exécution

### OK — 45 commandes en attente

```
$ echo '{"pending_orders": 45}' > /tmp/orders_queue.json
$ ./check_orders_queue.py -f /tmp/orders_queue.json
OK - 45 commandes en attente | pending_orders=45;50;100;0;
$ echo $?
0
```

### WARNING — 75 commandes en attente

```
$ echo '{"pending_orders": 75}' > /tmp/orders_queue.json
$ ./check_orders_queue.py -f /tmp/orders_queue.json
WARNING - 75 commandes en attente | pending_orders=75;50;100;0;
$ echo $?
1
```

### CRITICAL — 150 commandes en attente

```
$ echo '{"pending_orders": 150}' > /tmp/orders_queue.json
$ ./check_orders_queue.py -f /tmp/orders_queue.json
CRITICAL - 150 commandes en attente | pending_orders=150;50;100;0;
$ echo $?
2
```

### UNKNOWN — valeur non numérique

```
$ echo '{"pending_orders": "N/A"}' > /tmp/orders_queue.json
$ ./check_orders_queue.py -f /tmp/orders_queue.json
UNKNOWN - Valeur non numérique pour pending_orders : 'N/A'
$ echo $?
3
```

### UNKNOWN — fichier introuvable

```
$ ./check_orders_queue.py -f /tmp/fichier_inexistant.json
UNKNOWN - Fichier introuvable : /tmp/fichier_inexistant.json
$ echo $?
3
```

### UNKNOWN — JSON invalide

```
$ echo 'ceci nest pas du json' > /tmp/orders_queue.json
$ ./check_orders_queue.py -f /tmp/orders_queue.json
UNKNOWN - Fichier JSON invalide (Expecting value: line 1 column 1 (char 0))
$ echo $?
3
```

### Seuils personnalisés

```
$ echo '{"pending_orders": 80}' > /tmp/orders_queue.json
$ ./check_orders_queue.py -f /tmp/orders_queue.json -w 70 -c 150
WARNING - 80 commandes en attente | pending_orders=80;70;150;0;
```

---

## Intégration Centreon

### Étape 1 — Déployer le plugin sur le serveur CMA

```bash
sudo cp check_orders_queue.py /usr/lib/centreon/plugins/check_orders_queue.py
sudo chmod +x /usr/lib/centreon/plugins/check_orders_queue.py
```

### Étape 2 — Créer la commande Centreon

Dans **Configuration → Commandes → Contrôles**, créer une nouvelle commande :

| Champ              | Valeur                                                                                     |
|--------------------|--------------------------------------------------------------------------------------------|
| Nom de la commande | `check_orders_queue`                                                                       |
| Type               | `Check`                                                                                    |
| Ligne de commande  | `$USER1$/check_orders_queue.py -f $_SERVICEORDERS_FILE$ -w $_SERVICEWARNING$ -c $_SERVICECRITICAL$ -t $_SERVICETIMEOUT$` |
| Connecteur         | `Centreon Monitoring Agent`                                                                |

> **Important** : sélectionner **Centreon Monitoring Agent** dans le champ *Connectors* pour que la commande soit exécutée via le CMA.

Macros de service suggérées :

| Macro                | Valeur par défaut                         |
|----------------------|-------------------------------------------|
| `ORDERS_FILE`        | `/var/www/app/data/orders_queue.json`     |
| `WARNING`            | `50`                                      |
| `CRITICAL`           | `100`                                     |
| `TIMEOUT`            | `10`                                      |

### Étape 3 — Créer le service Centreon

Dans **Configuration → Services**, créer un nouveau service :

| Champ              | Valeur                      |
|--------------------|-----------------------------|
| Nom du service     | `Orders-Queue`              |
| Commande de check  | `check_orders_queue`        |
| Période de check   | `24x7`                      |
| Intervalle normal  | `1` minute                  |

Exporter la configuration et recharger Centreon.

---

## Gestion des erreurs

| Cas d'erreur                        | Comportement                                      |
|-------------------------------------|---------------------------------------------------|
| Fichier JSON introuvable            | `UNKNOWN` avec message explicite                  |
| Fichier JSON syntaxiquement invalide| `UNKNOWN` avec détail de l'erreur de parsing      |
| Clé `pending_orders` absente        | `UNKNOWN` avec message explicite                  |
| Valeur non numérique                | `UNKNOWN` avec la valeur incriminée affichée      |
| Timeout dépassé (lecture bloquante) | `UNKNOWN` via signal `SIGALRM` (systèmes Unix)    |
| Erreur de permissions / I/O         | `UNKNOWN` avec le message système                 |
