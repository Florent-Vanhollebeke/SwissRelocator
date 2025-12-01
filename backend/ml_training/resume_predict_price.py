from predict_price import predire_prix_bureau

# Bureau 307m², Genève, 6e étage, 9 pièces, parking + ascenseur
prix_predit = predire_prix_bureau(
    ville='Genève',
    surface=307,
    latitude=46.218889,  # Coordonnées précises
    longitude=6.137333,
    pieces=9,
    etage=6,
    has_parking=True,
    has_lift=True
)

prix_reel = 10140

print(f"Prix réel    : {prix_reel:,} CHF/mois")
print(f"Prix prédit  : {prix_predit:.0f} CHF/mois")
print(f"Erreur       : {prix_predit - prix_reel:+.0f} CHF ({(prix_predit - prix_reel)/prix_reel*100:+.1f}%)")