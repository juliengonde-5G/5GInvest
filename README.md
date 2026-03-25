# 5GInvest - Module d'investissement guidé Revolut

Outil d'aide à la décision pour investir 100€ sur Revolut (crypto, actions, ETF).

## Installation

```bash
pip install -r requirements.txt
```

## Commandes

```bash
python main.py scan          # Scanner toutes les opportunités
python main.py recommend     # Allocation recommandée pour 100€
python main.py monitor       # Surveillance continue (alertes)
python main.py portfolio     # État du portefeuille
python main.py buy SYMBOL    # Enregistrer un achat
python main.py sell SYMBOL   # Enregistrer une vente
```

## Contraintes respectées

- Pas de vente en pleine nuit (fenêtre 07:30 - 22:00 Paris)
- Horaires marchés US (15:30 - 22:00) et EU (09:00 - 17:30)
- Alertes mises en file d'attente hors horaires
- Diversification max 40% par position
- Stop loss -3% / Take profit +5% / Trailing stop 2.5%
