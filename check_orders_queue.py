#!/usr/bin/env python3
"""
Plugin Centreon/Nagios - Supervision de la file d'attente des commandes e-commerce.

Lit un fichier JSON contenant des compteurs de commandes et retourne un état
Nagios/Centreon basé sur le nombre de commandes en attente (pending_orders).

Seuils par défaut :
  OK       : pending_orders < 50   (exit 0)
  WARNING  : 50 <= pending_orders <= 100  (exit 1)
  CRITICAL : pending_orders > 100  (exit 2)
  UNKNOWN  : valeur non numérique ou erreur de lecture (exit 3)

Format de sortie Nagios/Centreon :
  <STATUT> - <message> | pending_orders=<valeur>;<warn>;<crit>;0;

Exemple :
  OK - 45 commandes en attente | pending_orders=45;50;100;0;
"""

import argparse
import json
import os
import signal
import sys

# ---------------------------------------------------------------------------
# Codes de retour Nagios/Centreon
# ---------------------------------------------------------------------------
EXIT_OK = 0
EXIT_WARNING = 1
EXIT_CRITICAL = 2
EXIT_UNKNOWN = 3

STATUS_LABELS = {
    EXIT_OK: "OK",
    EXIT_WARNING: "WARNING",
    EXIT_CRITICAL: "CRITICAL",
    EXIT_UNKNOWN: "UNKNOWN",
}


def timeout_handler(signum, frame):
    """Gestionnaire du signal SIGALRM déclenché si le timeout est dépassé."""
    print("UNKNOWN - Timeout dépassé lors de la lecture du fichier JSON")
    sys.exit(EXIT_UNKNOWN)


def parse_args():
    """Analyse les arguments de la ligne de commande."""
    parser = argparse.ArgumentParser(
        description="Plugin Centreon/Nagios - File d'attente des commandes e-commerce"
    )
    parser.add_argument(
        "-f",
        "--file",
        default="/var/www/app/data/orders_queue.json",
        help="Chemin vers le fichier JSON des commandes (défaut : /var/www/app/data/orders_queue.json)",
    )
    parser.add_argument(
        "-w",
        "--warning",
        type=int,
        default=50,
        help="Seuil WARNING pour pending_orders (défaut : 50)",
    )
    parser.add_argument(
        "-c",
        "--critical",
        type=int,
        default=100,
        help="Seuil CRITICAL pour pending_orders (défaut : 100)",
    )
    parser.add_argument(
        "-t",
        "--timeout",
        type=int,
        default=10,
        help="Timeout en secondes pour la lecture du fichier (défaut : 10)",
    )
    return parser.parse_args()


def read_json_file(filepath):
    """
    Lit et retourne le contenu du fichier JSON.

    Lève FileNotFoundError si le fichier est introuvable.
    Lève json.JSONDecodeError si le contenu n'est pas du JSON valide.
    """
    with open(filepath, "r", encoding="utf-8") as fh:
        return json.load(fh)


def check_orders(filepath, warn_threshold, crit_threshold):
    """
    Vérifie le nombre de commandes en attente et retourne (exit_code, message).

    Paramètres
    ----------
    filepath       : chemin vers le fichier JSON
    warn_threshold : seuil WARNING — déclenché si pending_orders >= warn_threshold
    crit_threshold : seuil CRITICAL — déclenché si pending_orders > crit_threshold

    Retourne
    --------
    tuple (exit_code, output_message)
    """
    # --- Lecture du fichier ---------------------------------------------------
    if not os.path.exists(filepath):
        return (
            EXIT_UNKNOWN,
            f"UNKNOWN - Fichier introuvable : {filepath}",
        )

    try:
        data = read_json_file(filepath)
    except json.JSONDecodeError as exc:
        return (
            EXIT_UNKNOWN,
            f"UNKNOWN - Fichier JSON invalide ({exc})",
        )
    except OSError as exc:
        return (
            EXIT_UNKNOWN,
            f"UNKNOWN - Impossible de lire le fichier : {exc}",
        )

    # --- Extraction de pending_orders ----------------------------------------
    if "pending_orders" not in data:
        return (
            EXIT_UNKNOWN,
            "UNKNOWN - Clé 'pending_orders' absente du fichier JSON",
        )

    raw_value = data["pending_orders"]

    # La valeur doit être un entier (ou un flottant représentant un entier)
    if not isinstance(raw_value, (int, float)) or isinstance(raw_value, bool):
        return (
            EXIT_UNKNOWN,
            f"UNKNOWN - Valeur non numérique pour pending_orders : {raw_value!r}",
        )

    pending = int(raw_value)

    # --- Formatage perfdata ---------------------------------------------------
    perfdata = f"pending_orders={pending};{warn_threshold};{crit_threshold};0;"

    # --- Évaluation des seuils -----------------------------------------------
    if pending > crit_threshold:
        status = EXIT_CRITICAL
        label = STATUS_LABELS[EXIT_CRITICAL]
    elif pending >= warn_threshold:
        status = EXIT_WARNING
        label = STATUS_LABELS[EXIT_WARNING]
    else:
        status = EXIT_OK
        label = STATUS_LABELS[EXIT_OK]

    message = f"{label} - {pending} commandes en attente | {perfdata}"
    return (status, message)


def main():
    args = parse_args()

    # --- Mise en place du timeout via SIGALRM (Unix uniquement) --------------
    if hasattr(signal, "SIGALRM"):
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(args.timeout)

    exit_code, output = check_orders(args.file, args.warning, args.critical)

    # Désarmer le timeout avant de quitter
    if hasattr(signal, "SIGALRM"):
        signal.alarm(0)

    print(output)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
