---
paths:
  - "docs/**"
---

# Règles pour la documentation

- Langue : français. Identifiants techniques, noms d'entités, statuts et noms d'endpoints en anglais, tels qu'ils apparaîtront dans le code (`RFQ`, `Quotation`, `Trade Confirmed`…).
- Tracer chaque exigence vers sa source : `CdC §N` (cahier des charges), `Planning §N`, `Roadmap J<N>`.
- Ne jamais inventer de règle métier. Une décision absente des sources est marquée `À VALIDER`, avec la question posée et, si utile, une proposition explicitement présentée comme telle.
- Les contradictions entre sources sont signalées avec les deux versions, sans être tranchées en silence.
- Distinguer clairement : V1 active / préparé mais désactivé / intégration externe future.
- Ne pas documenter comme disponible ce qui n'est pas implémenté.
- Exemples avec des données factices marquées comme telles. Aucun secret, aucune donnée réelle de client.
