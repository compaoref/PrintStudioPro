# PrintStudio Pro 🖨️

Application d'impression professionnelle avec **RIP intégré**.
Grand Format (Vinyle / Bâche) + DTF Textile.

## Installation locale

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Déploiement sur Streamlit Cloud

1. Créez un compte sur [share.streamlit.io](https://share.streamlit.io)
2. Créez un repo GitHub, copiez `app.py` et `requirements.txt` dedans
3. Sur Streamlit Cloud → "New app" → sélectionnez votre repo → `app.py`
4. Cliquez Deploy — votre app sera accessible en quelques minutes

## Fonctionnalités

### Grand Format (Vinyle / Bâche)
- Charge PDF, PNG, JPG, TIF, AI, EPS, CDR
- Définit la zone d'impression (ex: 1,50 m × 1,00 m)
- Multiplie l'étiquette en grille (colonnes × lignes)
- Règle espacement, marges, fond perdu
- Résolution : 72 / 150 / 300 / 600 DPI
- Rotation : 0° / 90° / 180° / 270°
- Profils ICC : ISOcoated v2, FOGRA39, SWOP...
- **Export direct : TIF CMJN + PMN MainTap en 1 clic**

### DTF (Textile)
- Formats A4, A3, A2, ou personnalisé
- Portrait / Paysage
- Miroir (pour impression face intérieure)
- Canal blanc / White underbase
- Copies multiples
- **Export ZIP : TIF CMJN + PMN + README en 1 clic**

## Stack technique

- Python 3.11+
- Streamlit (interface)
- Pillow (traitement image, conversion CMJN, encodage TIF)
- PyMuPDF (lecture PDF haute résolution)
