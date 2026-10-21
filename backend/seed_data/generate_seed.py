#!/usr/bin/env python3
"""Generate seed data: ingredients.json + recipes.json for Monatsmenü."""
import json, os

SEED_DIR = os.path.dirname(os.path.abspath(__file__))

# ===================== INGREDIENTS =====================
ingredients = [
    # --- vegetables ---
    {"name": "Karotten", "category": "vegetables", "unit_default": "Stück", "storage": "Kühlschrank"},
    {"name": "Zwiebeln", "category": "vegetables", "unit_default": "Stück", "storage": "Vorratsschrank"},
    {"name": "Knoblauchzehen", "category": "vegetables", "unit_default": "Zehe", "storage": "Vorratsschrank"},
    {"name": "Kartoffeln", "category": "vegetables", "unit_default": "Stück", "storage": "Keller"},
    {"name": "Süßkartoffeln", "category": "vegetables", "unit_default": "Stück", "storage": "Kühlschrank"},
    {"name": "Hokkaido-Kürbis", "category": "vegetables", "unit_default": "Stück", "storage": "Kühlschrank"},
    {"name": "Brokkoli", "category": "vegetables", "unit_default": "Stück", "storage": "Kühlschrank"},
    {"name": "Blumenkohl", "category": "vegetables", "unit_default": "Stück", "storage": "Kühlschrank"},
    {"name": "Spinat (Blatt)", "category": "vegetables", "unit_default": "g", "storage": "Kühlschrank"},
    {"name": "Champignons", "category": "vegetables", "unit_default": "g", "storage": "Kühlschrank"},
    {"name": "Rosenkohl", "category": "vegetables", "unit_default": "g", "storage": "Kühlschrank"},
    {"name": "Rotkohl", "category": "vegetables", "unit_default": "Stück", "storage": "Kühlschrank"},
    {"name": "Lauch (Porree)", "category": "vegetables", "unit_default": "Stück", "storage": "Kühlschrank"},
    {"name": "Stangensellerie", "category": "vegetables", "unit_default": "Stück", "storage": "Kühlschrank"},
    {"name": "Rote Paprika", "category": "vegetables", "unit_default": "Stück", "storage": "Kühlschrank"},
    {"name": "Zucchini", "category": "vegetables", "unit_default": "Stück", "storage": "Kühlschrank"},
    {"name": "Tomaten", "category": "vegetables", "unit_default": "Stück", "storage": "Kühlschrank"},
    {"name": "Cherrytomaten", "category": "vegetables", "unit_default": "Stück", "storage": "Kühlschrank"},
    {"name": "Salatgurke", "category": "vegetables", "unit_default": "Stück", "storage": "Kühlschrank"},
    {"name": "Avocado", "category": "vegetables", "unit_default": "Stück", "storage": "Kühlschrank"},
    {"name": "Rucola", "category": "vegetables", "unit_default": "g", "storage": "Kühlschrank"},
    {"name": "Feldsalat", "category": "vegetables", "unit_default": "g", "storage": "Kühlschrank"},
    {"name": "Frische Chilischote", "category": "vegetables", "unit_default": "Stück", "storage": "Kühlschrank"},
    {"name": "Ingwer", "category": "vegetables", "unit_default": "Stück", "storage": "Kühlschrank"},
    {"name": "Pastinaken", "category": "vegetables", "unit_default": "Stück", "storage": "Kühlschrank"},
    {"name": "Grünkohl", "category": "vegetables", "unit_default": "g", "storage": "Kühlschrank"},
    # --- fruit ---
    {"name": "Äpfel", "category": "fruit", "unit_default": "Stück", "storage": "Kühlschrank"},
    {"name": "Zitrone", "category": "fruit", "unit_default": "Stück", "storage": "Kühlschrank"},
    {"name": "Limette", "category": "fruit", "unit_default": "Stück", "storage": "Kühlschrank"},
    {"name": "Granatapfel", "category": "fruit", "unit_default": "Stück", "storage": "Kühlschrank"},
    # --- grains ---
    {"name": "Langkornreis", "category": "grains", "unit_default": "g", "storage": "Vorratsschrank"},
    {"name": "Vollkorn-Spaghetti", "category": "grains", "unit_default": "g", "storage": "Vorratsschrank"},
    {"name": "Pasta (Penne/Fusilli)", "category": "grains", "unit_default": "g", "storage": "Vorratsschrank"},
    {"name": "Lasagneblätter", "category": "grains", "unit_default": "Stück", "storage": "Vorratsschrank"},
    {"name": "Couscous", "category": "grains", "unit_default": "g", "storage": "Vorratsschrank"},
    {"name": "Bulgur", "category": "grains", "unit_default": "g", "storage": "Vorratsschrank"},
    {"name": "Weizenmehl", "category": "grains", "unit_default": "g", "storage": "Vorratsschrank"},
    {"name": "Paniermehl", "category": "grains", "unit_default": "EL", "storage": "Vorratsschrank"},
    {"name": "Vollkornbrot", "category": "grains", "unit_default": "Stück", "storage": "Vorratsschrank"},
    {"name": "Tortilla-Wraps (groß)", "category": "grains", "unit_default": "Stück", "storage": "Kühlschrank"},
    {"name": "Spätzle (Kühlregal)", "category": "grains", "unit_default": "g", "storage": "Kühlschrank"},
    # --- dairy ---
    {"name": "Butter", "category": "dairy", "unit_default": "g", "storage": "Kühlschrank"},
    {"name": "Milch (3,5%)", "category": "dairy", "unit_default": "ml", "storage": "Kühlschrank"},
    {"name": "Schlagsahne", "category": "dairy", "unit_default": "ml", "storage": "Kühlschrank"},
    {"name": "Crème fraîche", "category": "dairy", "unit_default": "g", "storage": "Kühlschrank"},
    {"name": "Naturjoghurt (3,5%)", "category": "dairy", "unit_default": "g", "storage": "Kühlschrank"},
    {"name": "Feta", "category": "dairy", "unit_default": "g", "storage": "Kühlschrank"},
    {"name": "Mozzarella", "category": "dairy", "unit_default": "Stück", "storage": "Kühlschrank"},
    {"name": "Parmesan (gerieben)", "category": "dairy", "unit_default": "g", "storage": "Kühlschrank"},
    {"name": "Gouda (gerieben)", "category": "dairy", "unit_default": "g", "storage": "Kühlschrank"},
    {"name": "Frischkäse (Natur)", "category": "dairy", "unit_default": "g", "storage": "Kühlschrank"},
    {"name": "Eier", "category": "dairy", "unit_default": "Stück", "storage": "Kühlschrank"},
    # --- meat ---
    {"name": "Rinderhackfleisch", "category": "meat", "unit_default": "g", "storage": "Kühlschrank"},
    {"name": "Hähnchenbrustfilet", "category": "meat", "unit_default": "g", "storage": "Kühlschrank"},
    {"name": "Hähnchenkeulen", "category": "meat", "unit_default": "Stück", "storage": "Kühlschrank"},
    {"name": "Schweinefilet", "category": "meat", "unit_default": "g", "storage": "Kühlschrank"},
    {"name": "Lammgulasch", "category": "meat", "unit_default": "g", "storage": "Kühlschrank"},
    {"name": "Wiener Würstchen", "category": "meat", "unit_default": "Stück", "storage": "Kühlschrank"},
    {"name": "Lachsfilet", "category": "meat", "unit_default": "g", "storage": "Kühlschrank"},
    {"name": "Fischstäbchen", "category": "meat", "unit_default": "Stück", "storage": "Gefrierschrank"},
    {"name": "Räuchermakrelenfilet", "category": "meat", "unit_default": "Stück", "storage": "Kühlschrank"},
    {"name": "Frühstücksspeck", "category": "meat", "unit_default": "g", "storage": "Kühlschrank"},
    {"name": "Zimt (gemahlen)", "category": "spices", "unit_default": "TL", "storage": "Vorratsschrank"},
    {"name": "Räuchertofu", "category": "other", "unit_default": "g", "storage": "Kühlschrank"},
    # --- spices ---
    {"name": "Salz", "category": "spices", "unit_default": "Prise", "storage": "Vorratsschrank"},
    {"name": "Schwarzer Pfeffer", "category": "spices", "unit_default": "Prise", "storage": "Vorratsschrank"},
    {"name": "Paprikapulver (edelsüß)", "category": "spices", "unit_default": "TL", "storage": "Vorratsschrank"},
    {"name": "Kurkuma (gemahlen)", "category": "spices", "unit_default": "TL", "storage": "Vorratsschrank"},
    {"name": "Kreuzkümmel (gemahlen)", "category": "spices", "unit_default": "TL", "storage": "Vorratsschrank"},
    {"name": "Koriander (gemahlen)", "category": "spices", "unit_default": "TL", "storage": "Vorratsschrank"},
    {"name": "Chiliflocken", "category": "spices", "unit_default": "TL", "storage": "Vorratsschrank"},
    {"name": "Muskatnuss (gerieben)", "category": "spices", "unit_default": "Prise", "storage": "Vorratsschrank"},
    {"name": "Lorbeerblätter", "category": "spices", "unit_default": "Stück", "storage": "Vorratsschrank"},
    {"name": "Thymian (getrocknet)", "category": "spices", "unit_default": "TL", "storage": "Vorratsschrank"},
    {"name": "Rosmarin (getrocknet)", "category": "spices", "unit_default": "TL", "storage": "Vorratsschrank"},
    {"name": "Majoran", "category": "spices", "unit_default": "TL", "storage": "Vorratsschrank"},
    {"name": "Oregano", "category": "spices", "unit_default": "TL", "storage": "Vorratsschrank"},
    {"name": "Basilikum (getrocknet)", "category": "spices", "unit_default": "TL", "storage": "Vorratsschrank"},
    {"name": "Currypulver (mild)", "category": "spices", "unit_default": "TL", "storage": "Vorratsschrank"},
    {"name": "Garam Masala", "category": "spices", "unit_default": "TL", "storage": "Vorratsschrank"},
    {"name": "Räucherpaprikapulver", "category": "spices", "unit_default": "TL", "storage": "Vorratsschrank"},
    # --- condiments ---
    {"name": "Olivenöl", "category": "condiments", "unit_default": "EL", "storage": "Vorratsschrank"},
    {"name": "Rapsöl", "category": "condiments", "unit_default": "EL", "storage": "Vorratsschrank"},
    {"name": "Sesamöl", "category": "condiments", "unit_default": "EL", "storage": "Vorratsschrank"},
    {"name": "Weißweinessig", "category": "condiments", "unit_default": "EL", "storage": "Vorratsschrank"},
    {"name": "Apfelessig", "category": "condiments", "unit_default": "EL", "storage": "Vorratsschrank"},
    {"name": "Sojasauce", "category": "condiments", "unit_default": "EL", "storage": "Vorratsschrank"},
    {"name": "Senf (mittelscharf)", "category": "condiments", "unit_default": "TL", "storage": "Kühlschrank"},
    {"name": "Honig", "category": "condiments", "unit_default": "EL", "storage": "Vorratsschrank"},
    {"name": "Hefeflocken", "category": "condiments", "unit_default": "EL", "storage": "Vorratsschrank"},
    {"name": "Tahini (Sesammus)", "category": "condiments", "unit_default": "EL", "storage": "Vorratsschrank"},
    # --- canned ---
    {"name": "Tomatenmark", "category": "canned", "unit_default": "EL", "storage": "Vorratsschrank"},
    {"name": "Passierte Tomaten", "category": "canned", "unit_default": "ml", "storage": "Vorratsschrank"},
    {"name": "Stückige Tomaten (Dose)", "category": "canned", "unit_default": "Dose", "storage": "Vorratsschrank"},
    {"name": "Kokosmilch (Dose)", "category": "canned", "unit_default": "ml", "storage": "Vorratsschrank"},
    {"name": "Kichererbsen (Dose)", "category": "canned", "unit_default": "Dose", "storage": "Vorratsschrank"},
    {"name": "Mais (Dose)", "category": "canned", "unit_default": "Dose", "storage": "Vorratsschrank"},
    {"name": "Weiße Bohnen (Dose)", "category": "canned", "unit_default": "Dose", "storage": "Vorratsschrank"},
    {"name": "Gemüsebrühe (Pulver)", "category": "canned", "unit_default": "TL", "storage": "Vorratsschrank"},
    {"name": "Rote Linsen (getrocknet)", "category": "canned", "unit_default": "g", "storage": "Vorratsschrank"},
    {"name": "Braune Linsen (getrocknet)", "category": "canned", "unit_default": "g", "storage": "Vorratsschrank"},
    # --- frozen ---
    {"name": "TK-Erbsen", "category": "frozen", "unit_default": "g", "storage": "Gefrierschrank"},
    {"name": "TK-Blattspinat", "category": "frozen", "unit_default": "g", "storage": "Gefrierschrank"},
    {"name": "TK-Gemüsemischung", "category": "frozen", "unit_default": "g", "storage": "Gefrierschrank"},
    # --- other ---
    {"name": "Kürbiskerne", "category": "other", "unit_default": "EL", "storage": "Vorratsschrank"},
    {"name": "Walnüsse (gehackt)", "category": "other", "unit_default": "g", "storage": "Vorratsschrank"},
    {"name": "Mandeln (geblättert)", "category": "other", "unit_default": "EL", "storage": "Vorratsschrank"},
    {"name": "Pinienkerne", "category": "other", "unit_default": "EL", "storage": "Vorratsschrank"},
    {"name": "Kokosflocken", "category": "other", "unit_default": "EL", "storage": "Vorratsschrank"},
{"name": "TK-Kräutermischung", "category": "frozen", "unit_default": "g", "storage": "Gefrierschrank"},
]

# deduplicate
seen = {}
unique_i = []
for i in ingredients:
    if i["name"] not in seen:
        seen[i["name"]] = True
        unique_i.append(i)
ingredients = unique_i

with open(os.path.join(SEED_DIR, "ingredients.json"), "w", encoding="utf-8") as f:
    json.dump(ingredients, f, ensure_ascii=False, indent=2)
print(f"✓ ingredients.json ({len(ingredients)} Zutaten)")


# ===================== RECIPES =====================
# leftover_key dient als Referenz: Der leftover_recipe eines cook_once-Rezepts
# wird per title referenziert, damit der Importer die IDs später auflösen kann.
# cook_once_eat_twice = True  → leftover_recipe_title = "Titel des Reste-Rezepts"
# cook_once_eat_twice = False → leftover_recipe_title = None

recipes = [
    # ──────────────────────────────────────────────────────
    # 1–2: Linsen-Curry (cook_once) + Reste-Linsen-Bowl
    # ──────────────────────────────────────────────────────
    {
        "title": "Rotes Linsen-Curry mit Reis",
        "description": "Ein mildes, cremiges Linsen-Curry mit Kartoffeln und Karotten, das die ganze Familie liebt. Die doppelte Portion ist bewusst eingeplant – aus den Resten entsteht am nächsten Tag eine frische Linsen-Bowl. Passt perfekt in die Herbst-Winter-Saison.",
        "servings": 4,
        "prep_time_minutes": 15,
        "cook_time_minutes": 35,
        "difficulty": "easy",
        "cook_once_eat_twice": True,
        "leftover_recipe_title": "Reste-Linsen-Bowl mit Apfel und Walnüssen",
        "tags": ["cook_once", "vegetarisch", "veggie", "familie", "saisonal", "meal_prep"],
        "kid_friendly_tip": "Die Kinder können die Linsen durch ein Sieb waschen und die weichen Kartoffelwürfel mit einem Plastikmesser schneiden.",
        "instructions": "1. Linsen in ein Sieb geben, kalt abspülen und abtropfen lassen.\n2. Zwiebel und Knoblauch fein würfeln, Karotten und Kartoffeln in 1-cm-Würfel schneiden.\n3. Rapsöl in einem großen Topf erhitzen. Zwiebeln und Knoblauch darin 3 Min. glasig dünsten.\n4. Karotten- und Kartoffelwürfel zugeben, 2 Min. mitbraten.\n5. Currypulver, Kurkuma und Garam Masala einrühren, 1 Min. anrösten.\n6. Mit Kokosmilch und 300 ml Wasser ablöschen. Linsen einrühren.\n7. Alles 25 Min. bei niedriger Hitze köcheln lassen, gelegentlich umrühren.\n8. Mit Salz, Pfeffer und einem Spritzer Zitronensaft abschmecken.\n9. Parallel den Reis nach Packungsanweisung kochen.\n10. Curry auf 4 Portionen verteilen, Reis dazu. Die Hälfte für die Reste-Bowl beiseitestellen.",
        "ingredient_list": [
            {"name": "Rote Linsen (getrocknet)", "amount": 250, "unit": "g", "category": "canned"},
            {"name": "Karotten", "amount": 3, "unit": "Stück", "category": "vegetables"},
            {"name": "Kartoffeln", "amount": 4, "unit": "Stück", "category": "vegetables"},
            {"name": "Zwiebeln", "amount": 2, "unit": "Stück", "category": "vegetables"},
            {"name": "Knoblauchzehen", "amount": 2, "unit": "Zehe", "category": "vegetables"},
            {"name": "Currypulver (mild)", "amount": 2, "unit": "TL", "category": "spices"},
            {"name": "Kurkuma (gemahlen)", "amount": 1, "unit": "TL", "category": "spices"},
            {"name": "Garam Masala", "amount": 1, "unit": "TL", "category": "spices"},
            {"name": "Kokosmilch (Dose)", "amount": 200, "unit": "ml", "category": "canned"},
            {"name": "Rapsöl", "amount": 2, "unit": "EL", "category": "condiments"},
            {"name": "Langkornreis", "amount": 300, "unit": "g", "category": "grains"},
        ]
    },
    {
        "title": "Reste-Linsen-Bowl mit Apfel und Walnüssen",
        "description": "Die Reste vom Linsen-Curry werden zur kalten Bowl mit frischem Apfel, Feldsalat und karamellisierten Walnüssen. Ein herzhaft-frischer Lunch, der in 10 Minuten steht.",
        "servings": 4,
        "prep_time_minutes": 10,
        "cook_time_minutes": 0,
        "difficulty": "easy",
        "cook_once_eat_twice": False,
        "leftover_recipe_title": None,
        "tags": ["vegetarisch", "veggie", "schnell", "meal_prep"],
        "kid_friendly_tip": "Die Kinder können die Äpfel mit einem Apfelteiler in Spalten schneiden und die Walnüsse mit den Händen zerbröseln.",
        "instructions": "1. Die kalte Linsen-Curry-Reste aus dem Kühlschrank in eine große Schüssel geben.\n2. Apfel waschen, vierteln und in feine Spalten schneiden.\n3. Feldsalat gründlich waschen und trocken schleudern.\n4. Walnüsse in einer trockenen Pfanne kurz anrösten, bis sie duften.\n5. Alles mit der Linsen-Curry-Basis vermischen.\n6. Mit einem Schuss Apfelessig, Salz und Pfeffer abschmecken.\n7. Auf 4 Bowls verteilen und mit den Walnüssen toppen.",
        "ingredient_list": [
            {"name": "Karotten", "amount": 1, "unit": "Stück", "category": "vegetables"},
            {"name": "Äpfel", "amount": 2, "unit": "Stück", "category": "fruit"},
            {"name": "Feldsalat", "amount": 80, "unit": "g", "category": "vegetables"},
            {"name": "Walnüsse (gehackt)", "amount": 40, "unit": "g", "category": "other"},
            {"name": "Apfelessig", "amount": 1, "unit": "EL", "category": "condiments"},
        ]
    },
    # ──────────────────────────────────────────────────────
    # 3–4: Kürbissuppe (cook_once) + Kürbis-Pasta
    # ──────────────────────────────────────────────────────
    {
        "title": "Cremige Hokkaido-Kürbissuppe",
        "description": "Eine samtige Kürbissuppe mit Ingwer und einem Schuss Sahne – Herbst comfort food pur. Dank doppelter Menge bleibt die Hälfte für die Kürbis-Pasta am Folgetag übrig. Dazu gibt es geröstete Kürbiskerne als Topping.",
        "servings": 4,
        "prep_time_minutes": 15,
        "cook_time_minutes": 30,
        "difficulty": "easy",
        "cook_once_eat_twice": True,
        "leftover_recipe_title": "Kürbis-Pasta mit Salbei und Parmesan",
        "tags": ["cook_once", "vegetarisch", "saisonal", "familie", "schnell"],
        "kid_friendly_tip": "Die Kinder können das Kürbisfruchtfleisch mit einem Löffel aus der Schale kratzen – das geht leichter als Schneidern und macht Spass.",
        "instructions": "1. Hokkaido-Kürbis waschen, halbieren, entkernen und in grobe Würfel schneiden (die Schale kann dranbleiben).\n2. Kartoffel schälen und würfeln, Zwiebel und Ingwer fein hacken.\n3. Rapsöl im Topf erhitzen, Zwiebel und Ingwer 2 Min. glasig dünsten.\n4. Kürbis- und Kartoffelwürfel zugeben, 5 Min. mitbraten.\n5. Mit Gemüsebrühe (500 ml Wasser + 2 TL Pulver) ablöschen.\n6. 20 Min. köcheln lassen, bis Kürbis und Kartoffeln weich sind.\n7. Topf vom Herd nehmen, Sahne einrühren und mit dem Stabmixer fein pürieren.\n8. Mit Salz, Pfeffer und einer Prise Muskat abschmecken.\n9. Die Hälfte der Suppe für die Kürbis-Pasta beiseitestellen.\n10. In Schüsseln anrichten, mit gerösteten Kürbiskernen bestreuen.",
        "ingredient_list": [
            {"name": "Hokkaido-Kürbis", "amount": 1, "unit": "Stück", "category": "vegetables"},
            {"name": "Kartoffeln", "amount": 1, "unit": "Stück", "category": "vegetables"},
            {"name": "Zwiebeln", "amount": 1, "unit": "Stück", "category": "vegetables"},
            {"name": "Ingwer", "amount": 1, "unit": "Stück", "category": "vegetables"},
            {"name": "Schlagsahne", "amount": 100, "unit": "ml", "category": "dairy"},
            {"name": "Gemüsebrühe (Pulver)", "amount": 2, "unit": "TL", "category": "canned"},
            {"name": "Rapsöl", "amount": 1, "unit": "EL", "category": "condiments"},
            {"name": "Kürbiskerne", "amount": 2, "unit": "EL", "category": "other"},
        ]
    },
    {
        "title": "Kürbis-Pasta mit Salbei und Parmesan",
        "description": "Die Reste der Kürbissuppe werden zur cremigen Pastasauce – einfach mit gekochten Vollkorn-Spaghetti und Parmesan verfeinert. In 15 Minuten auf dem Tisch.",
        "servings": 4,
        "prep_time_minutes": 5,
        "cook_time_minutes": 10,
        "difficulty": "easy",
        "cook_once_eat_twice": False,
        "leftover_recipe_title": None,
        "tags": ["vegetarisch", "schnell", "saisonal", "familie"],
        "kid_friendly_tip": "Die Kinder können den Parmesan mit einer kleinen Reibe selbst reiben – das trainiert die Feinmotorik.",
        "instructions": "1. Suppenreste aus dem Kühlschrank in einen Topf geben und bei mittlerer Hitze erwärmen.\n2. Spaghetti nach Packungsanweisung in Salzwasser kochen (10 Min.).\n3. 1–2 Kellen Nudelwasser zur Kürbissauce geben, bis sie sämig ist.\n4. Spaghetti abgießen und sofort mit der Sauce vermischen.\n5. Parmesan unterheben, mit Pfeffer und Muskat abschmecken.\n6. Auf Tellern anrichten und mit Parmesan bestreuen.",
        "ingredient_list": [
            {"name": "Vollkorn-Spaghetti", "amount": 400, "unit": "g", "category": "grains"},
            {"name": "Parmesan (gerieben)", "amount": 50, "unit": "g", "category": "dairy"},
            {"name": "Salz", "amount": 1, "unit": "Prise", "category": "spices"},
        ]
    },
    # ──────────────────────────────────────────────────────
    # 5–6: Hähnchen-Curry (cook_once) + Hähnchen-Wrap
    # ──────────────────────────────────────────────────────
    {
        "title": "Hähnchen-Curry mit Basmatireis",
        "description": "Ein mildes, cremiges Hähnchen-Curry mit Paprika und Zwiebeln – nicht zu scharf, genau richtig für Kinder. Das doppelte Hähnchen wird bewusst gebraten, damit am nächsten Tag Wrap-Füllung daraus wird.",
        "servings": 4,
        "prep_time_minutes": 15,
        "cook_time_minutes": 25,
        "difficulty": "medium",
        "cook_once_eat_twice": True,
        "leftover_recipe_title": "Hähnchen-Reste-Wraps mit Gemüsestreifen",
        "tags": ["cook_once", "fleisch", "familie", "meal_prep"],
        "kid_friendly_tip": "Die Kinder können die Paprika entkernen (Handschuhe bei roten Paprika) und den Reis waschen – das ist wie Sandspiel.",
        "instructions": "1. Hähnchenbrustfilet in 2-cm-Stücke schneiden.\n2. Paprika und Zwiebeln in Streifen schneiden, Knoblauch hacken.\n3. Rapsöl in einer großen Pfanne erhitzen. Hähnchenstücke rundum kräftig anbraten (ca. 5 Min.).\n4. Herausnehmen und warm stellen.\n5. Zwiebeln, Paprika und Knoblauch im Bratrückstand 3 Min. braten.\n6. Currypulver, Kurkuma und Kreuzkümmel einrühren, 1 Min. anrösten.\n7. Kokosmilch dazugiessen, aufkochen und 10 Min. köcheln lassen.\n8. Hähnchen wieder zugeben, 5 Min. ziehen lassen.\n9. Reis parallel kochen. Mit Salz, Pfeffer und Zitronensaft abschmecken.\n10. Die Hälfte des Hähnchen-Currys für die Wraps beiseitestellen.",
        "ingredient_list": [
            {"name": "Hähnchenbrustfilet", "amount": 500, "unit": "g", "category": "meat"},
            {"name": "Rote Paprika", "amount": 2, "unit": "Stück", "category": "vegetables"},
            {"name": "Zwiebeln", "amount": 2, "unit": "Stück", "category": "vegetables"},
            {"name": "Knoblauchzehen", "amount": 2, "unit": "Zehe", "category": "vegetables"},
            {"name": "Currypulver (mild)", "amount": 2, "unit": "TL", "category": "spices"},
            {"name": "Kurkuma (gemahlen)", "amount": 1, "unit": "TL", "category": "spices"},
            {"name": "Kreuzkümmel (gemahlen)", "amount": 1, "unit": "TL", "category": "spices"},
            {"name": "Kokosmilch (Dose)", "amount": 200, "unit": "ml", "category": "canned"},
            {"name": "Rapsöl", "amount": 2, "unit": "EL", "category": "condiments"},
            {"name": "Langkornreis", "amount": 300, "unit": "g", "category": "grains"},
        ]
    },
    {
        "title": "Hähnchen-Reste-Wraps mit Gemüsestreifen",
        "description": "Die Reste vom Hähnchen-Curry treffen auf knackiges Rohkost-Gemüse und Frischkäse – gewickelt in Tortilla-Wraps. Ein schnelles, kaltes Mittagessen für die ganze Familie.",
        "servings": 4,
        "prep_time_minutes": 10,
        "cook_time_minutes": 0,
        "difficulty": "easy",
        "cook_once_eat_twice": False,
        "leftover_recipe_title": None,
        "tags": ["fleisch", "schnell", "kinderfreundlich"],
        "kid_friendly_tip": "Die Wraps können die Kinder selbst belegen und zusammenrollen – jeder bereitet seinen eigenen Wrap zu.",
        "instructions": "1. Hähnchen-Curry-Reste aus dem Kühlschrank nehmen, ggf. grobe Stücke klein schneiden.\n2. Gurke längs in feine Streifen hobeln. Karotte schälen und in dünne Stifte schneiden.\n3. Rucola waschen und trocken schleudern.\n4. Tortilla-Wraps auf einem Teller ausbreiten.\n5. Hähnchen-Curry in die Mitte der Wraps geben.\n6. Mit Gurken-, Karottenstreifen und Rucola belegen.\n7. Frischkäse und ein paar Spritzer Sojasauce darübergeben.\n8. Wrap links und rechts einschlagen, dann von unten eng aufrollen.",
        "ingredient_list": [
            {"name": "Tortilla-Wraps (groß)", "amount": 4, "unit": "Stück", "category": "grains"},
            {"name": "Salatgurke", "amount": 0.5, "unit": "Stück", "category": "vegetables"},
            {"name": "Karotten", "amount": 2, "unit": "Stück", "category": "vegetables"},
            {"name": "Rucola", "amount": 40, "unit": "g", "category": "vegetables"},
            {"name": "Frischkäse (Natur)", "amount": 100, "unit": "g", "category": "dairy"},
            {"name": "Sojasauce", "amount": 1, "unit": "EL", "category": "condiments"},
        ]
    },
    # ──────────────────────────────────────────────────────
    # 7–8: Ofen-Gemüse (cook_once) + Gemüse-Frittata
    # ──────────────────────────────────────────────────────
    {
        "title": "Buntes Ofen-Gemüse mit Feta",
        "description": "Ein Blech voller saisonalem Ofengemüse – Kürbis, Brokkoli, Pastinaken und Paprika werden mit Feta überbacken. Die doppelte Menge garantiert Reste für die Frittata am nächsten Morgen oder Mittag.",
        "servings": 4,
        "prep_time_minutes": 20,
        "cook_time_minutes": 30,
        "difficulty": "easy",
        "cook_once_eat_twice": True,
        "leftover_recipe_title": "Gemüse-Frittata aus dem Ofen",
        "tags": ["cook_once", "vegetarisch", "saisonal", "familie", "kinderfreundlich"],
        "kid_friendly_tip": "Die Kinder können das Gemüse auf dem Blech nach Farben sortieren – das macht das Anrichten zum Spiel.",
        "instructions": "1. Backofen auf 200 °C Ober-/Unterhitze vorheizen.\n2. Kürbis, Pastinaken und Brokkoli in mundgerechte Stücke schneiden.\n3. Paprika und Zucchini in breite Streifen schneiden.\n4. Alles Gemüse auf zwei Bleche verteilen, mit Olivenöl beträufeln.\n5. Mit Salz, Pfeffer, Thymian und Rosmarin würzen.\n6. 20 Min. backen, dann Feta in groben Stücken darüberbröseln.\n7. Weitere 10 Min. überbacken.\n8. Ein Blech für die Frittata beiseitestellen, das andere servieren.",
        "ingredient_list": [
            {"name": "Hokkaido-Kürbis", "amount": 0.5, "unit": "Stück", "category": "vegetables"},
            {"name": "Brokkoli", "amount": 1, "unit": "Stück", "category": "vegetables"},
            {"name": "Pastinaken", "amount": 3, "unit": "Stück", "category": "vegetables"},
            {"name": "Rote Paprika", "amount": 2, "unit": "Stück", "category": "vegetables"},
            {"name": "Zucchini", "amount": 2, "unit": "Stück", "category": "vegetables"},
            {"name": "Feta", "amount": 200, "unit": "g", "category": "dairy"},
            {"name": "Olivenöl", "amount": 3, "unit": "EL", "category": "condiments"},
            {"name": "Thymian (getrocknet)", "amount": 1, "unit": "TL", "category": "spices"},
            {"name": "Rosmarin (getrocknet)", "amount": 1, "unit": "TL", "category": "spices"},
        ]
    },
    {
        "title": "Gemüse-Frittata aus dem Ofen",
        "description": "Aus den Ofen-Gemüse-Resten wird eine herzhafte Frittata mit Eiern und Parmesan – auf dem Blech zubereitet, in 20 Minuten fertig. Perfekt für ein schnelles Familien-Abendessen.",
        "servings": 4,
        "prep_time_minutes": 5,
        "cook_time_minutes": 15,
        "difficulty": "easy",
        "cook_once_eat_twice": False,
        "leftover_recipe_title": None,
        "tags": ["vegetarisch", "schnell", "familie"],
        "kid_friendly_tip": "Die Kinder können die Eier aufschlagen und mit einem Schneebesen verquirlen – das macht ihnen immer Spass.",
        "instructions": "1. Backofen auf 180 °C vorheizen.\n2. Reste vom Ofen-Gemüse auf einer ofenfesten Form verteilen.\n3. In einer Schüssel 6 Eier mit 100 ml Milch verquirlen, Salz und Pfeffer zugeben.\n4. Eiermischung gleichmässig über das Gemüse giessen.\n5. Parmesan darüberstreuen.\n6. 15 Min. backen, bis die Frittata gestockt und goldbraun ist.\n7. In Stücke geschnitten servieren. Dazu passt ein grüner Salat.",
        "ingredient_list": [
            {"name": "Eier", "amount": 6, "unit": "Stück", "category": "dairy"},
            {"name": "Milch (3,5%)", "amount": 100, "unit": "ml", "category": "dairy"},
            {"name": "Parmesan (gerieben)", "amount": 40, "unit": "g", "category": "dairy"},
        ]
    },
    # ──────────────────────────────────────────────────────
    # 9–10: Chili sin Carne (cook_once) + Chili-Mais-Pfanne
    # ──────────────────────────────────────────────────────
    {
        "title": "Veganes Chili sin Carne",
        "description": "Ein herzhaft-wärmendes Chili aus Bohnen, Mais, Paprika und Tomaten – mit ordentlich Rauchnote durch Räucherpaprika. Die doppelte Portion liefert die Basis für die Chili-Mais-Pfanne am nächsten Tag.",
        "servings": 4,
        "prep_time_minutes": 15,
        "cook_time_minutes": 35,
        "difficulty": "medium",
        "cook_once_eat_twice": True,
        "leftover_recipe_title": "Chili-Mais-Pfanne mit Avocado",
        "tags": ["cook_once", "vegan", "familie", "meal_prep", "saisonal"],
        "kid_friendly_tip": "Die Kinder können die Bohnen aus der Dose in ein Sieb schütten und abspülen – einfache Küchenarbeit, die Spass macht.",
        "instructions": "1. Zwiebeln, Knoblauch und Paprika fein würfeln.\n2. Rapsöl im Topf erhitzen, Zwiebeln und Knoblauch 3 Min. glasig dünsten.\n3. Paprika und Chilischote (fein gehackt) zugeben, 3 Min. mitbraten.\n4. Tomatenmark und Räucherpaprikapulver einrühren, 1 Min. anrösten.\n5. Mit stückigen Tomaten und 200 ml Wasser ablöschen.\n6. Bohnen und Mais abgiessen, kalt abspülen und unterrühren.\n7. Chili 20 Min. leise köcheln lassen.\n8. Mit Kreuzkümmel, Oregano, Salz, Pfeffer und einem Schuss Apfelessig abschmecken.\n9. Die Hälfte für die Chili-Mais-Pfanne beiseitestellen.",
        "ingredient_list": [
            {"name": "Zwiebeln", "amount": 2, "unit": "Stück", "category": "vegetables"},
            {"name": "Knoblauchzehen", "amount": 3, "unit": "Zehe", "category": "vegetables"},
            {"name": "Rote Paprika", "amount": 3, "unit": "Stück", "category": "vegetables"},
            {"name": "Frische Chilischote", "amount": 1, "unit": "Stück", "category": "vegetables"},
            {"name": "Tomatenmark", "amount": 2, "unit": "EL", "category": "canned"},
            {"name": "Stückige Tomaten (Dose)", "amount": 1, "unit": "Dose", "category": "canned"},
            {"name": "Weiße Bohnen (Dose)", "amount": 1, "unit": "Dose", "category": "canned"},
            {"name": "Mais (Dose)", "amount": 1, "unit": "Dose", "category": "canned"},
            {"name": "Räucherpaprikapulver", "amount": 1, "unit": "EL", "category": "spices"},
            {"name": "Rapsöl", "amount": 2, "unit": "EL", "category": "condiments"},
            {"name": "Apfelessig", "amount": 1, "unit": "EL", "category": "condiments"},
        ]
    },
    {
        "title": "Chili-Mais-Pfanne mit Avocado",
        "description": "Die Chili-Reste treffen auf frische Avocado und Tortilla-Chips – eine schnelle, vegane Pfanne in 10 Minuten. Das Lieblings-Reste-Rezept unserer Testfamilie.",
        "servings": 4,
        "prep_time_minutes": 5,
        "cook_time_minutes": 5,
        "difficulty": "easy",
        "cook_once_eat_twice": False,
        "leftover_recipe_title": None,
        "tags": ["vegan", "schnell", "familie"],
        "kid_friendly_tip": "Die Kinder können die Avocado mit einem Löffel aus der Schale löffeln und zerdrücken.",
        "instructions": "1. Chili-Reste in einer Pfanne bei mittlerer Hitze erwärmen.\n2. Avocado halbieren, Kern entfernen, Fruchtfleisch in Würfel schneiden.\n3. Chili auf Teller verteilen, Avocado-Würfel daraufgeben.\n4. Mit Koriander und einem Spritzer Limettensaft abschmecken.\n5. Dazu Tortilla-Chips oder Brot reichen.",
        "ingredient_list": [
            {"name": "Avocado", "amount": 1, "unit": "Stück", "category": "vegetables"},
            {"name": "Koriander (gemahlen)", "amount": 0.5, "unit": "TL", "category": "spices"},
            {"name": "Limette", "amount": 0.5, "unit": "Stück", "category": "fruit"},
        ]
    },
    # ──────────────────────────────────────────────────────
    # 11: Rinderhack-Bolognese (Fleisch, Familie)
    # ──────────────────────────────────────────────────────
    {
        "title": "Rinderhack-Bolognese mit Vollkorn-Spaghetti",
        "description": "Der Klassiker für den Familienalltag: Eine herzhafte Bolognese-Sauce mit Rinderhack, Karotten und Sellerie, die heimlich viel Gemüse enthält. Die Kinder lieben die ‚Wurst-Sauce‘.",
        "servings": 4,
        "prep_time_minutes": 10,
        "cook_time_minutes": 30,
        "difficulty": "easy",
        "cook_once_eat_twice": True,
        "leftover_recipe_title": None,
        "tags": ["cook_once", "fleisch", "familie", "kinderfreundlich", "schnell"],
        "kid_friendly_tip": "Die Kinder können die Karotten mit einer Kinderreibe in die Sauce raspeln – das Gemüse wird so fein, dass sie es später nicht erkennen.",
        "instructions": "1. Zwiebeln, Knoblauch fein würfeln. Karotte und Stangensellerie fein raspeln.\n2. Olivenöl in einem grossen Topf erhitzen. Hackfleisch darin kräftig anbraten, bis es krümelig ist (ca. 5 Min.).\n3. Zwiebeln, Knoblauch, Karotte und Sellerie zugeben, 3 Min. mitbraten.\n4. Tomatenmark einrühren, 1 Min. anrösten.\n5. Mit passierten Tomaten ablöschen. Oregano, Thymian und Lorbeerblatt zugeben.\n6. Sauce 20 Min. bei niedriger Hitze köcheln lassen.\n7. Spaghetti nach Packungsanweisung kochen.\n8. Sauce mit Salz und Pfeffer abschmecken, Lorbeerblatt entfernen.\n9. Spaghetti mit Sauce servieren, Parmesan darüberstreuen.",
        "ingredient_list": [
            {"name": "Rinderhackfleisch", "amount": 400, "unit": "g", "category": "meat"},
            {"name": "Zwiebeln", "amount": 2, "unit": "Stück", "category": "vegetables"},
            {"name": "Knoblauchzehen", "amount": 2, "unit": "Zehe", "category": "vegetables"},
            {"name": "Karotten", "amount": 1, "unit": "Stück", "category": "vegetables"},
            {"name": "Stangensellerie", "amount": 1, "unit": "Stück", "category": "vegetables"},
            {"name": "Tomatenmark", "amount": 2, "unit": "EL", "category": "canned"},
            {"name": "Passierte Tomaten", "amount": 700, "unit": "ml", "category": "canned"},
            {"name": "Oregano", "amount": 1, "unit": "TL", "category": "spices"},
            {"name": "Thymian (getrocknet)", "amount": 0.5, "unit": "TL", "category": "spices"},
            {"name": "Lorbeerblätter", "amount": 1, "unit": "Stück", "category": "spices"},
            {"name": "Olivenöl", "amount": 2, "unit": "EL", "category": "condiments"},
            {"name": "Vollkorn-Spaghetti", "amount": 400, "unit": "g", "category": "grains"},
            {"name": "Parmesan (gerieben)", "amount": 40, "unit": "g", "category": "dairy"},
        ]
    },
    # ──────────────────────────────────────────────────────
    # 12: Hähnchen-Gemüse-Pfanne (Fleisch, schnell)
    # ──────────────────────────────────────────────────────
    {
        "title": "Hähnchen-Gemüse-Pfanne mit Reis",
        "description": "Eine schnelle, bunte Pfanne mit Hähnchenstreifen, Brokkoli, Paprika und Zuckerschoten – in 20 Minuten auf dem Tisch. Das ideale Feierabend-Rezept für die ganze Familie.",
        "servings": 4,
        "prep_time_minutes": 10,
        "cook_time_minutes": 20,
        "difficulty": "easy",
        "cook_once_eat_twice": False,
        "leftover_recipe_title": None,
        "tags": ["fleisch", "schnell", "familie", "kinderfreundlich"],
        "kid_friendly_tip": "Die Kinder können die Brokkoli-Röschen mit den Fingern vom Strunk zupfen – das geht schnell und macht den Gemüsepicking zum Spiel.",
        "instructions": "1. Hähnchenbrustfilet in dünne Streifen schneiden.\n2. Brokkoli in Röschen teilen. Paprika und Zucchini in Streifen schneiden.\n3. Rapsöl im Wok oder einer grossen Pfanne erhitzen.\n4. Hähnchenstreifen scharf anbraten, dann herausnehmen.\n5. Brokkoli, Paprika und Zucchini 4 Min. im Wok braten.\n6. Hähnchen wieder zugeben, Sojasauce und 2 EL Wasser angiessen.\n7. 3 Min. fertiggaren, mit Salz und Pfeffer abschmecken.\n8. Dazu Reis servieren.",
        "ingredient_list": [
            {"name": "Hähnchenbrustfilet", "amount": 400, "unit": "g", "category": "meat"},
            {"name": "Brokkoli", "amount": 1, "unit": "Stück", "category": "vegetables"},
            {"name": "Rote Paprika", "amount": 2, "unit": "Stück", "category": "vegetables"},
            {"name": "Zucchini", "amount": 1, "unit": "Stück", "category": "vegetables"},
            {"name": "Sojasauce", "amount": 2, "unit": "EL", "category": "condiments"},
            {"name": "Rapsöl", "amount": 2, "unit": "EL", "category": "condiments"},
            {"name": "Langkornreis", "amount": 300, "unit": "g", "category": "grains"},
        ]
    },
    # ──────────────────────────────────────────────────────
    # 13: Schweinefilet mit Apfel-Rotkohl (Fleisch, saisonal)
    # ──────────────────────────────────────────────────────
    {
        "title": "Schweinefilet mit Apfel-Rotkohl und Kartoffelstampf",
        "description": "Ein herbstliches Sonntagsessen: Zartes Schweinefilet mit selbstgemachtem Apfel-Rotkohl und cremigem Kartoffelstampf. Klingt aufwendig, ist aber mit unserem Zeitspar-Trick in 45 Minuten machbar.",
        "servings": 4,
        "prep_time_minutes": 20,
        "cook_time_minutes": 35,
        "difficulty": "medium",
        "cook_once_eat_twice": False,
        "leftover_recipe_title": None,
        "tags": ["fleisch", "saisonal", "familie"],
        "kid_friendly_tip": "Die Kinder können den Rotkohl zu einem Apfel-Rotkohl-Salat umfunktionieren: einfach kalt mit Apfelsaft und Rosinen mischen.",
        "instructions": "1. Rotkohl vierteln, Strunk entfernen, in feine Streifen hobeln oder schneiden.\n2. Apfel schälen, vierteln und in Spalten schneiden.\n3. Rapsöl im Topf erhitzen, Rotkohl und Apfel zugeben.\n4. Mit Apfelessig und 200 ml Wasser ablöschen, Lorbeerblatt zugeben.\n5. Rotkohl 30 Min. bei niedriger Hitze köcheln lassen, gelegentlich umrühren.\n6. Für den Stampf: Kartoffeln schälen, in Salzwasser 20 Min. kochen.\n7. Schweinefilet in 2 cm dicke Medaillons schneiden, salzen und pfeffern.\n8. Butter in Pfanne erhitzen, Filet von jeder Seite 3 Min. braten, dann 10 Min. bei 150 °C im Ofen fertiggaren.\n9. Kartoffeln abgiessen, mit Milch, Butter und Salz stampfen.\n10. Filet in Scheiben schneiden, mit Rotkohl und Stampf anrichten.",
        "ingredient_list": [
            {"name": "Schweinefilet", "amount": 500, "unit": "g", "category": "meat"},
            {"name": "Rotkohl", "amount": 1, "unit": "Stück", "category": "vegetables"},
            {"name": "Äpfel", "amount": 2, "unit": "Stück", "category": "fruit"},
            {"name": "Kartoffeln", "amount": 6, "unit": "Stück", "category": "vegetables"},
            {"name": "Butter", "amount": 50, "unit": "g", "category": "dairy"},
            {"name": "Milch (3,5%)", "amount": 100, "unit": "ml", "category": "dairy"},
            {"name": "Apfelessig", "amount": 2, "unit": "EL", "category": "condiments"},
            {"name": "Lorbeerblätter", "amount": 1, "unit": "Stück", "category": "spices"},
            {"name": "Rapsöl", "amount": 2, "unit": "EL", "category": "condiments"},
        ]
    },
    # ──────────────────────────────────────────────────────
    # 14: Frikadellen mit Kartoffelstampf (Fleisch, Familie)
    # ──────────────────────────────────────────────────────
    {
        "title": "Frikadellen mit Kartoffelstampf und Gurkensalat",
        "description": "Saftige Frikadellen nach Omas Art – mit Majoran, Zwiebeln und einem Schuss Senf. Dazu gibt es cremigen Kartoffelstampf und einen einfachen Gurkensalat. Ein Sonntagsklassiker, den alle lieben.",
        "servings": 4,
        "prep_time_minutes": 15,
        "cook_time_minutes": 25,
        "difficulty": "easy",
        "cook_once_eat_twice": False,
        "leftover_recipe_title": None,
        "tags": ["fleisch", "familie", "kinderfreundlich"],
        "kid_friendly_tip": "Die Kinder können die Frikadellen-Masse mit den Händen zu kleinen Bällchen formen – wie Knete, nur essbar.",
        "instructions": "1. Für den Gurkensalat: Gurke schälen, in dünne Scheiben hobeln.\n2. Mit 2 EL Essig, 1 EL Öl, Salz, Pfeffer und Düll mischen. Ziehen lassen.\n3. Kartoffeln schälen, in Salzwasser 20 Min. kochen.\n4. Für die Frikadellen: Brötchen von gestern in lauwarmem Wasser einweichen.\n5. Hackfleisch, ausgedrücktes Brötchen, Ei, fein gewürfelte Zwiebel, Senf und Majoran in einer Schüssel mischen.\n6. Mit Salz und Pfeffer würzen, alles gut durchkneten.\n7. Aus der Masse 8 flache Frikadellen formen.\n8. Rapsöl in einer Pfanne erhitzen, Frikadellen 5–6 Min. pro Seite goldbraun braten.\n9. Kartoffeln abgiessen, mit Milch, Butter und Salz stampfen.\n10. Frikadellen mit Stampf und Gurkensalat servieren.",
        "ingredient_list": [
            {"name": "Rinderhackfleisch", "amount": 500, "unit": "g", "category": "meat"},
            {"name": "Eier", "amount": 1, "unit": "Stück", "category": "dairy"},
            {"name": "Zwiebeln", "amount": 1, "unit": "Stück", "category": "vegetables"},
            {"name": "Senf (mittelscharf)", "amount": 1, "unit": "TL", "category": "condiments"},
            {"name": "Majoran", "amount": 1, "unit": "TL", "category": "spices"},
            {"name": "Vollkornbrot", "amount": 2, "unit": "Scheibe", "category": "grains"},
            {"name": "Kartoffeln", "amount": 6, "unit": "Stück", "category": "vegetables"},
            {"name": "Butter", "amount": 30, "unit": "g", "category": "dairy"},
            {"name": "Milch (3,5%)", "amount": 80, "unit": "ml", "category": "dairy"},
            {"name": "Salatgurke", "amount": 1, "unit": "Stück", "category": "vegetables"},
            {"name": "Weißweinessig", "amount": 2, "unit": "EL", "category": "condiments"},
            {"name": "Rapsöl", "amount": 3, "unit": "EL", "category": "condiments"},
        ]
    },
    # ──────────────────────────────────────────────────────
    # 15: Lamm-Tajine (Fleisch, Meal-Prep)
    # ──────────────────────────────────────────────────────
    {
        "title": "Lamm-Tajine mit Kichererbsen und Couscous",
        "description": "Eine nordafrikanisch inspirierte Tajine aus Lammgulasch, Kichererbsen und getrockneten Aprikosen – langsam geschmort für maximalen Geschmack. Das perfekte Meal-Prep-Rezept fürs Wochenende.",
        "servings": 4,
        "prep_time_minutes": 20,
        "cook_time_minutes": 60,
        "difficulty": "medium",
        "cook_once_eat_twice": True,
        "leftover_recipe_title": None,
        "tags": ["cook_once", "fleisch", "meal_prep", "familie"],
        "kid_friendly_tip": "Die Kinder können die Kichererbsen aus der Dose spülen und die Couscous-Quellwasser-Menge abmessen.",
        "instructions": "1. Zwiebeln und Knoblauch fein würfeln, Ingwer reiben.\n2. Rapsöl im Tajine oder Schmortopf erhitzen. Lammgulasch portionsweise scharf anbraten.\n3. Zwiebeln, Knoblauch und Ingwer zugeben, 3 Min. dünsten.\n4. Kreuzkümmel, Koriander, Kurkuma und Zimt einrühren, 1 Min. anrösten.\n5. Mit stückigen Tomaten ablöschen, Kichererbsen zugeben.\n6. 45 Min. bei kleiner Flamme köcheln lassen, ab und zu umrühren.\n7. Couscous nach Packungsanweisung zubereiten.\n8. Tajine mit Salz und Pfeffer abschmecken.\n9. Couscous auf tiefen Tellern verteilen, Tajine darauf anrichten.",
        "ingredient_list": [
            {"name": "Lammgulasch", "amount": 600, "unit": "g", "category": "meat"},
            {"name": "Zwiebeln", "amount": 2, "unit": "Stück", "category": "vegetables"},
            {"name": "Knoblauchzehen", "amount": 2, "unit": "Zehe", "category": "vegetables"},
            {"name": "Ingwer", "amount": 1, "unit": "Stück", "category": "vegetables"},
            {"name": "Kreuzkümmel (gemahlen)", "amount": 1, "unit": "TL", "category": "spices"},
            {"name": "Koriander (gemahlen)", "amount": 1, "unit": "TL", "category": "spices"},
            {"name": "Kurkuma (gemahlen)", "amount": 0.5, "unit": "TL", "category": "spices"},
            {"name": "Zimt (gemahlen)", "amount": 0.5, "unit": "TL", "category": "spices"},
            {"name": "Stückige Tomaten (Dose)", "amount": 1, "unit": "Dose", "category": "canned"},
            {"name": "Kichererbsen (Dose)", "amount": 1, "unit": "Dose", "category": "canned"},
            {"name": "Couscous", "amount": 300, "unit": "g", "category": "grains"},
            {"name": "Rapsöl", "amount": 2, "unit": "EL", "category": "condiments"},
        ]
    },
    # ──────────────────────────────────────────────────────
    # 16: Lachs-Buddha-Bowl (Fisch)
    # ──────────────────────────────────────────────────────
    {
        "title": "Lachs-Buddha-Bowl mit Avocado und Sesam",
        "description": "Eine bunte Bowl aus gebratenem Lachs, Avocado, Gurke, Feldsalat und Reis – mit einem Dressing aus Sojasauce, Sesamöl und Limette. Sieht aus wie vom Japaner, geht aber in 20 Minuten.",
        "servings": 4,
        "prep_time_minutes": 15,
        "cook_time_minutes": 10,
        "difficulty": "medium",
        "cook_once_eat_twice": False,
        "leftover_recipe_title": None,
        "tags": ["fisch", "schnell", "familie"],
        "kid_friendly_tip": "Die Kinder können die Bowl zusammenstellen: jede Zutat kommt in eine eigene ‚Ecke' der Schüssel.",
        "instructions": "1. Reis nach Packungsanweisung kochen, abkühlen lassen.\n2. Lachsfilet in 4 Stücke schneiden, mit Salz und Pfeffer würzen.\n3. Sesamöl in einer beschichteten Pfanne erhitzen.\n4. Lachs von jeder Seite 2 Min. scharf anbraten, dann 5 Min. bei reduzierter Hitze fertig garen.\n5. Avocado halbieren, Kern entfernen, in Spalten schneiden.\n6. Gurke in feine Halbmonde hobeln.\n7. Feldsalat waschen und trocken schleudern.\n8. Für das Dressing: Sojasauce, Sesamöl, Limettensaft und Honig verrühren.\n9. Reis in 4 Bowls verteilen. Lachs, Avocado, Gurke und Salat darauf anrichten.\n10. Dressing über die Bowls träufeln und mit Sesam bestreuen.",
        "ingredient_list": [
            {"name": "Lachsfilet", "amount": 400, "unit": "g", "category": "meat"},
            {"name": "Langkornreis", "amount": 300, "unit": "g", "category": "grains"},
            {"name": "Avocado", "amount": 1, "unit": "Stück", "category": "vegetables"},
            {"name": "Salatgurke", "amount": 0.5, "unit": "Stück", "category": "vegetables"},
            {"name": "Feldsalat", "amount": 80, "unit": "g", "category": "vegetables"},
            {"name": "Sojasauce", "amount": 2, "unit": "EL", "category": "condiments"},
            {"name": "Sesamöl", "amount": 1, "unit": "EL", "category": "condiments"},
            {"name": "Limette", "amount": 1, "unit": "Stück", "category": "fruit"},
            {"name": "Honig", "amount": 1, "unit": "TL", "category": "condiments"},
        ]
    },
    # ──────────────────────────────────────────────────────
    # 17: Fischstäbchen-Auflauf (Fisch, kinderkreundlich)
    # ──────────────────────────────────────────────────────
    {
        "title": "Fischstäbchen-Auflauf mit Erbsen und Kartoffelstampf",
        "description": "Der absolute Kinder-Liebling: Fischstäbchen in einer cremigen Sauce, mit Kartoffelstampf und Erbsen aus dem Ofen. Versteckt Spinat in der Sauce – die Kinder merken es nicht!",
        "servings": 4,
        "prep_time_minutes": 15,
        "cook_time_minutes": 25,
        "difficulty": "easy",
        "cook_once_eat_twice": False,
        "leftover_recipe_title": None,
        "tags": ["fisch", "kinderfreundlich", "familie", "schnell"],
        "kid_friendly_tip": "Die Kinder können die Fischstäbchen auf dem Auflauf wie Legosteine anordnen – in Reihen oder im Zickzack.",
        "instructions": "1. Backofen auf 200 °C Ober-/Unterhitze vorheizen.\n2. Kartoffeln schälen, in Salzwasser 20 Min. kochen.\n3. TK-Erbsen in einer Schüssel mit heissem Wasser auftauen lassen.\n4. Für die Sauce: Butter in einem Topf schmelzen. Mehl einrühren, 1 Min. anschwitzen.\n5. Milch unter Rühren angiessen, aufkochen. TK-Spinat unterrühren, bis er schmilzt.\n6. Sauce mit Salz, Pfeffer und Muskat abschmecken.\n7. Kartoffeln abgiessen, mit Butter und Milch stampfen.\n8. Stampf in eine ofenfeste Form geben, Erbsen darauf verteilen.\n9. Fischstäbchen in die Sauce tauchen und auf dem Stampf anordnen.\n10. Restliche Sauce darübergeben. 15 Min. überbacken.",
        "ingredient_list": [
            {"name": "Fischstäbchen", "amount": 16, "unit": "Stück", "category": "meat"},
            {"name": "Kartoffeln", "amount": 6, "unit": "Stück", "category": "vegetables"},
            {"name": "TK-Erbsen", "amount": 200, "unit": "g", "category": "frozen"},
            {"name": "TK-Blattspinat", "amount": 150, "unit": "g", "category": "frozen"},
            {"name": "Butter", "amount": 30, "unit": "g", "category": "dairy"},
            {"name": "Weizenmehl", "amount": 30, "unit": "g", "category": "grains"},
            {"name": "Milch (3,5%)", "amount": 300, "unit": "ml", "category": "dairy"},
        ]
    },
    # ──────────────────────────────────────────────────────
    # 18: Spinat-Lasagne (Vegetarisch)
    # ──────────────────────────────────────────────────────
    {
        "title": "Spinat-Lasagne mit Ricotta und Pinienkernen",
        "description": "Eine vegetarische Lasagne mit saftigem Spinat-Ricotta-Füllung und einer knusprigen Pinienkern-Kruste. Das ideale Sonntagsessen, das sich am nächsten Tag noch besser aufwärmen lässt.",
        "servings": 4,
        "prep_time_minutes": 25,
        "cook_time_minutes": 35,
        "difficulty": "medium",
        "cook_once_eat_twice": True,
        "leftover_recipe_title": None,
        "tags": ["cook_once", "vegetarisch", "familie", "kinderfreundlich", "meal_prep"],
        "kid_friendly_tip": "Die Kinder können beim Schichten der Lasagne helfen: Eine Schicht Nudelblätter, eine Schicht Füllung – wie beim Hausbau.",
        "instructions": "1. Backofen auf 180 °C (Umluft) vorheizen.\n2. Zwiebel und Knoblauch fein würfeln. TK-Spinat auftauen lassen.\n3. Butter in einem Topf erhitzen, Zwiebel und Knoblauch darin glasig dünsten.\n4. Spinat zugeben, 5 Min. dünsten, bis die Flüssigkeit verdampft ist.\n5. Ricotta (oder Quark) und Parmesan unterrühren. Mit Salz, Pfeffer und Muskat würzen.\n6. 200 ml Sahne angiessen und einmal aufkochen.\n7. Eine Auflaufform einfetten. Abwechselnd Lasagneblätter, Spinatfüllung und Sahne schichten.\n8. Abschliessend mit einer Schicht Béchamel: 30 g Butter, 30 g Mehl, 300 ml Milch.\n9. Pinienkerne darüberstreuen. 30 Min. backen, dann 5 Min. ruhen lassen.",
        "ingredient_list": [
            {"name": "Lasagneblätter", "amount": 12, "unit": "Stück", "category": "grains"},
            {"name": "TK-Blattspinat", "amount": 400, "unit": "g", "category": "frozen"},
            {"name": "Knoblauchzehen", "amount": 2, "unit": "Zehe", "category": "vegetables"},
            {"name": "Zwiebeln", "amount": 1, "unit": "Stück", "category": "vegetables"},
            {"name": "Parmesan (gerieben)", "amount": 50, "unit": "g", "category": "dairy"},
            {"name": "Schlagsahne", "amount": 200, "unit": "ml", "category": "dairy"},
            {"name": "Butter", "amount": 60, "unit": "g", "category": "dairy"},
            {"name": "Weizenmehl", "amount": 30, "unit": "g", "category": "grains"},
            {"name": "Milch (3,5%)", "amount": 300, "unit": "ml", "category": "dairy"},
            {"name": "Pinienkerne", "amount": 2, "unit": "EL", "category": "other"},
            {"name": "Frischkäse (Natur)", "amount": 250, "unit": "g", "category": "dairy"},
        ]
    },
    # ──────────────────────────────────────────────────────
    # 19: Brokkoli-Käse-Gratin (Vegetarisch, Kinder)
    # ──────────────────────────────────────────────────────
    {
        "title": "Brokkoli-Käse-Gratin mit Knusperkruste",
        "description": "Brokkoli in einer cremigen Käse-Sahne-Sauce, überbacken mit einer würzigen Knusperkruste aus Paniermehl und Parmesan. Geht auch mit Blumenkohl – je nachdem, was da ist.",
        "servings": 4,
        "prep_time_minutes": 10,
        "cook_time_minutes": 25,
        "difficulty": "easy",
        "cook_once_eat_twice": False,
        "leftover_recipe_title": None,
        "tags": ["vegetarisch", "kinderfreundlich", "familie", "schnell"],
        "kid_friendly_tip": "Die Kinder können die Kruste aus Paniermehl und Parmesan mit den Fingern auf dem Gratin verstreuen.",
        "instructions": "1. Backofen auf 200 °C Ober-/Unterhitze vorheizen.\n2. Brokkoli in Röschen teilen, 3 Min. in Salzwasser blanchieren, abgiessen.\n3. Sahne, Frischkäse und Gouda in einem Topf schmelzen, mit Salz, Pfeffer und Muskat würzen.\n4. Brokkoli in eine ofenfeste Form geben, Sauce darübergiessen.\n5. Paniermehl mit Parmesan mischen, über den Auflauf streuen.\n6. Butter in Flöckchen daraufsetzen.\n7. 20 Min. goldbraun überbacken. Heiss servieren.",
        "ingredient_list": [
            {"name": "Brokkoli", "amount": 2, "unit": "Stück", "category": "vegetables"},
            {"name": "Schlagsahne", "amount": 200, "unit": "ml", "category": "dairy"},
            {"name": "Frischkäse (Natur)", "amount": 100, "unit": "g", "category": "dairy"},
            {"name": "Gouda (gerieben)", "amount": 100, "unit": "g", "category": "dairy"},
            {"name": "Paniermehl", "amount": 3, "unit": "EL", "category": "grains"},
            {"name": "Parmesan (gerieben)", "amount": 30, "unit": "g", "category": "dairy"},
            {"name": "Butter", "amount": 20, "unit": "g", "category": "dairy"},
        ]
    },
    # ──────────────────────────────────────────────────────
    # 20: Pilz-Risotto (Vegetarisch, Herbst)
    # ──────────────────────────────────────────────────────
    {
        "title": "Cremiges Pilz-Risotto mit Parmesan",
        "description": "Ein cremiges Risotto mit Champignons, Porree und einer Prise Thymian. Die langsame Zubereitung mit dem richtigen Reis macht den Unterschied – und Parmesan hebt es aufs nächste Level.",
        "servings": 4,
        "prep_time_minutes": 10,
        "cook_time_minutes": 35,
        "difficulty": "medium",
        "cook_once_eat_twice": False,
        "leftover_recipe_title": None,
        "tags": ["vegetarisch", "saisonal", "familie"],
        "kid_friendly_tip": "Die Kinder können die Champignons mit einem feuchten Tuch putzen – nicht waschen, sonst saugen sie sich voll.",
        "instructions": "1. Champignons putzen und in Scheiben schneiden. Porree in feine Ringe schneiden.\n2. Rapsöl in einer weiten Pfanne erhitzen, Champignons kräftig anbraten.\n3. Porree zugeben, 2 Min. mitbraten. Herausnehmen, warm stellen.\n4. Butter im gleichen Topf schmelzen, Risottoreis darin 2 Min. anschwitzen.\n5. Mit 200 ml Wasser und Gemüsebrühe ablöschen, 25 Min. leise köcheln.\n6. Pilze und Porree wieder unterheben, Parmesan einrühren.\n7. Mit Salz, Pfeffer und Thymian abschmecken.\n8. Mit Parmesan und Kürbiskernen bestreut servieren.",
        "ingredient_list": [
            {"name": "Champignons", "amount": 400, "unit": "g", "category": "vegetables"},
            {"name": "Lauch (Porree)", "amount": 1, "unit": "Stück", "category": "vegetables"},
            {"name": "Langkornreis", "amount": 250, "unit": "g", "category": "grains"},
            {"name": "Butter", "amount": 30, "unit": "g", "category": "dairy"},
            {"name": "Parmesan (gerieben)", "amount": 60, "unit": "g", "category": "dairy"},
            {"name": "Gemüsebrühe (Pulver)", "amount": 1, "unit": "TL", "category": "canned"},
            {"name": "Thymian (getrocknet)", "amount": 0.5, "unit": "TL", "category": "spices"},
            {"name": "Rapsöl", "amount": 2, "unit": "EL", "category": "condiments"},
            {"name": "Kürbiskerne", "amount": 1, "unit": "EL", "category": "other"},
        ]
    },
    # ──────────────────────────────────────────────────────
    # 21: Kartoffel-Gemüse-Auflauf (Vegetarisch, Familie)
    # ──────────────────────────────────────────────────────
    {
        "title": "Kartoffel-Gemüse-Auflauf mit Crème fraîche",
        "description": "Ein einfacher Auflauf aus Kartoffeln, Zucchini, Paprika und Champignons – mit Crème fraîche und Gouda überbacken. Perfekt, um den Kühlschrank zu leeren, ein echter Alltagsretter.",
        "servings": 4,
        "prep_time_minutes": 15,
        "cook_time_minutes": 30,
        "difficulty": "easy",
        "cook_once_eat_twice": True,
        "leftover_recipe_title": None,
        "tags": ["cook_once", "vegetarisch", "familie", "schnell"],
        "kid_friendly_tip": "Die Kinder können nach Belieben weiteres Gemüse in den Auflauf legen – was im Kühlschrank noch übrig ist darf rein.",
        "instructions": "1. Backofen auf 200 °C vorheizen.\n2. Kartoffeln schälen und in 1-cm-Scheiben schneiden. Zucchini und Paprika in Stücke schneiden.\n3. Champignons putzen und halbieren.\n4. Alles Gemüse in eine Auflaufform geben.\n5. Crème fraîche mit 2 EL Wasser, Salz, Pfeffer und einer Prise Muskat verrühren.\n6. Sauce über das Gemüse giessen, Gouda darüberstreuen.\n7. 30 Min. backen. Heiss servieren – ein grüner Salat passt gut dazu.",
        "ingredient_list": [
            {"name": "Kartoffeln", "amount": 6, "unit": "Stück", "category": "vegetables"},
            {"name": "Zucchini", "amount": 2, "unit": "Stück", "category": "vegetables"},
            {"name": "Rote Paprika", "amount": 2, "unit": "Stück", "category": "vegetables"},
            {"name": "Champignons", "amount": 200, "unit": "g", "category": "vegetables"},
            {"name": "Crème fraîche", "amount": 200, "unit": "g", "category": "dairy"},
            {"name": "Gouda (gerieben)", "amount": 100, "unit": "g", "category": "dairy"},
        ]
    },
    # ──────────────────────────────────────────────────────
    # 22: Blumenkohl-Wedges (Vegetarisch, Kinder)
    # ──────────────────────────────────────────────────────
    {
        "title": "Blumenkohl-Wedges mit Kräuterdip",
        "description": "Knusprig gewürzte Blumenkohl-Spalten aus dem Ofen – wie Pommes, aber gesünder. Mit einem cremigen Kräuterdip aus Joghurt und Frischkäse werden selbst Gemüsemuffel satt.",
        "servings": 4,
        "prep_time_minutes": 10,
        "cook_time_minutes": 25,
        "difficulty": "easy",
        "cook_once_eat_twice": False,
        "leftover_recipe_title": None,
        "tags": ["vegetarisch", "kinderfreundlich", "familie", "schnell"],
        "kid_friendly_tip": "Die Kinder können die Blumenkohl-Wedges wie Pommes in den Dip tunken – das macht den Gemüseesser zum Erlebnis.",
        "instructions": "1. Backofen auf 200 °C vorheizen. Blech mit Backpapier belegen.\n2. Blumenkohl in 2-cm-dicke Spalten schneiden (inklusive Strunk).\n3. Olivenöl mit Paprikapulver, Salz, Pfeffer und Chili mischen.\n4. Blumenkohl-Spalten mit der Gewürzmischung beträufeln, gut vermengen.\n5. Auf dem Blech verteilen, 25 Min. backen, nach 15 Min. wenden.\n6. Für den Dip: Joghurt, Frischkäse, Zitronensaft, Salz und gehackte Kräuter verrühren.\n7. Heisse Wedges mit Dip servieren.",
        "ingredient_list": [
            {"name": "Blumenkohl", "amount": 2, "unit": "Stück", "category": "vegetables"},
            {"name": "Olivenöl", "amount": 3, "unit": "EL", "category": "condiments"},
            {"name": "Paprikapulver (edelsüß)", "amount": 1, "unit": "TL", "category": "spices"},
            {"name": "Chiliflocken", "amount": 0.5, "unit": "TL", "category": "spices"},
            {"name": "Naturjoghurt (3,5%)", "amount": 150, "unit": "g", "category": "dairy"},
            {"name": "Frischkäse (Natur)", "amount": 80, "unit": "g", "category": "dairy"},
            {"name": "Zitrone", "amount": 0.5, "unit": "Stück", "category": "fruit"},
            {"name": "TK-Kräutermischung", "amount": 1, "unit": "EL", "category": "frozen"},
        ]
    },
    # ──────────────────────────────────────────────────────
    # 23: Süßkartoffel-Bowl (Vegetarisch)
    # ──────────────────────────────────────────────────────
    {
        "title": "Süßkartoffel-Bowl mit Avocado und Granatapfel",
        "description": "Eine bunte Bowl aus Ofen-Süßkartoffeln, Avocado, Granatapfel und Feldsalat – mit einem Tahini-Zitronen-Dressing. Sieht aus wie ein teures Cafégericht, kostet aber nur einen Bruchteil.",
        "servings": 4,
        "prep_time_minutes": 15,
        "cook_time_minutes": 25,
        "difficulty": "easy",
        "cook_once_eat_twice": False,
        "leftover_recipe_title": None,
        "tags": ["vegetarisch", "schnell", "saisonal", "familie"],
        "kid_friendly_tip": "Die Kinder können die Granatapfel-Kerne aus der Schale pulen – das ist eine feine Fingerübung.",
        "instructions": "1. Backofen auf 200 °C vorheizen.\n2. Süßkartoffeln waschen, in dicke Spalten schneiden, mit Olivenöl beträufeln.\n3. Süßkartoffeln 25 Min. im Ofen backen.\n4. Feldsalat waschen, trocken schleudern.\n5. Avocado halbieren, in Spalten schneiden. Granatapfel vierteln, Kerne herauslösen.\n6. Für das Dressing: Tahini, Zitronensaft, Honig, Salz und 2 EL Wasser verrühren.\n7. Süßkartoffeln auf 4 Bowls verteilen. Feldsalat, Avocado und Granatapfel darauf anrichten.\n8. Dressing darüberträufeln. Mit Kürbiskernen bestreuen.",
        "ingredient_list": [
            {"name": "Süßkartoffeln", "amount": 3, "unit": "Stück", "category": "vegetables"},
            {"name": "Avocado", "amount": 1, "unit": "Stück", "category": "vegetables"},
            {"name": "Feldsalat", "amount": 80, "unit": "g", "category": "vegetables"},
            {"name": "Granatapfel", "amount": 1, "unit": "Stück", "category": "fruit"},
            {"name": "Zitrone", "amount": 0.5, "unit": "Stück", "category": "fruit"},
            {"name": "Tahini (Sesammus)", "amount": 2, "unit": "EL", "category": "condiments"},
            {"name": "Honig", "amount": 1, "unit": "TL", "category": "condiments"},
            {"name": "Olivenöl", "amount": 2, "unit": "EL", "category": "condiments"},
            {"name": "Kürbiskerne", "amount": 1, "unit": "EL", "category": "other"},
        ]
    },
    # ──────────────────────────────────────────────────────
    # 24: Vegane Kartoffelsuppe (Vegan)
    # ──────────────────────────────────────────────────────
    {
        "title": "Vegane Kartoffelsuppe mit Lauch und Räuchertofu",
        "description": "Eine wärmende, vegane Kartoffelsuppe mit Lauch, Karotten und Räuchertofu – geräucherter Tofu gibt den Rauchgeschmack, den man sonst von Würstchen kennt. In 30 Minuten fertig.",
        "servings": 4,
        "prep_time_minutes": 10,
        "cook_time_minutes": 25,
        "difficulty": "easy",
        "cook_once_eat_twice": True,
        "leftover_recipe_title": None,
        "tags": ["cook_once", "vegan", "schnell", "saisonal", "familie"],
        "kid_friendly_tip": "Die Kinder können das Räuchertofu mit den Händen in Stücke bröseln – die brüchige Konsistenz macht Spass.",
        "instructions": "1. Kartoffeln schälen und in kleine Würfel schneiden. Lauch in feine Ringe, Karotten in Scheiben schneiden.\n2. Rapsöl im Topf erhitzen. Lauch und Karotten 2 Min. andünsten.\n3. Kartoffelwürfel zugeben, 2 Min. mitbraten.\n4. Mit 800 ml Wasser und Gemüsebrühe ablöschen. 20 Min. köcheln lassen.\n5. Räuchertofu in kleine Würfel schneiden, in einer Pfanne knusprig braten.\n6. Suppe mit Salz, Pfeffer, Majoran und Prise Muskat abschmecken.\n7. Räuchertofu in die Suppe geben oder als Topping servieren.",
        "ingredient_list": [
            {"name": "Kartoffeln", "amount": 6, "unit": "Stück", "category": "vegetables"},
            {"name": "Lauch (Porree)", "amount": 1, "unit": "Stück", "category": "vegetables"},
            {"name": "Karotten", "amount": 2, "unit": "Stück", "category": "vegetables"},
            {"name": "Gemüsebrühe (Pulver)", "amount": 2, "unit": "TL", "category": "canned"},
            {"name": "Majoran", "amount": 1, "unit": "TL", "category": "spices"},
            {"name": "Rapsöl", "amount": 2, "unit": "EL", "category": "condiments"},
        ]
    },
    # ──────────────────────────────────────────────────────
    # 25: Linsen-Bolognese (Vegan)
    # ──────────────────────────────────────────────────────
    {
        "title": "Linsen-Bolognese mit Vollkorn-Spaghetti",
        "description": "Eine vegane Bolognese auf Linsen-Basis – genau so herzhaft und aromatisch wie das Original. Die braunen Linsen geben die perfekte ‚Hack'-Konsistenz. Ein Familienliebling, den niemand als vegan erkennt.",
        "servings": 4,
        "prep_time_minutes": 10,
        "cook_time_minutes": 30,
        "difficulty": "easy",
        "cook_once_eat_twice": True,
        "leftover_recipe_title": None,
        "tags": ["cook_once", "vegan", "veggie", "familie", "kinderfreundlich", "schnell"],
        "kid_friendly_tip": "Die Kinder können die Linsen vor dem Kochen nach 'schönen und weniger schönen' sortieren – ein einfaches Farberkennungsspiel.",
        "instructions": "1. Linsen in einem Sieb kalt abspülen, abtropfen lassen.\n2. Zwiebeln und Knoblauch fein würfeln. Karotte fein raspeln.\n3. Olivenöl im Topf erhitzen. Zwiebeln und Knoblauch 3 Min. glasig dünsten.\n4. Karotte und Tomatenmark einrühren, 1 Min. anrösten.\n5. Linsen zugeben, mit passierten Tomaten und 200 ml Wasser ablöschen.\n6. Oregano, Thymian und Lorbeerblatt zugeben. 25 Min. köcheln lassen.\n7. Spaghetti nach Packungsanweisung kochen.\n8. Sauce mit Salz, Pfeffer und Hefeflocken abschmecken.\n9. Lorbeerblatt entfernen. Sauce zu den Spaghetti geben.",
        "ingredient_list": [
            {"name": "Braune Linsen (getrocknet)", "amount": 250, "unit": "g", "category": "canned"},
            {"name": "Zwiebeln", "amount": 2, "unit": "Stück", "category": "vegetables"},
            {"name": "Knoblauchzehen", "amount": 2, "unit": "Zehe", "category": "vegetables"},
            {"name": "Karotten", "amount": 1, "unit": "Stück", "category": "vegetables"},
            {"name": "Tomatenmark", "amount": 2, "unit": "EL", "category": "canned"},
            {"name": "Passierte Tomaten", "amount": 500, "unit": "ml", "category": "canned"},
            {"name": "Oregano", "amount": 1, "unit": "TL", "category": "spices"},
            {"name": "Thymian (getrocknet)", "amount": 0.5, "unit": "TL", "category": "spices"},
            {"name": "Lorbeerblätter", "amount": 1, "unit": "Stück", "category": "spices"},
            {"name": "Hefeflocken", "amount": 1, "unit": "EL", "category": "condiments"},
            {"name": "Olivenöl", "amount": 2, "unit": "EL", "category": "condiments"},
            {"name": "Vollkorn-Spaghetti", "amount": 400, "unit": "g", "category": "grains"},
        ]
    },
    # ──────────────────────────────────────────────────────
    # 26: Kichererbsen-Salat (Vegan, schnell)
    # ──────────────────────────────────────────────────────
    {
        "title": "Marokkanischer Kichererbsen-Salat mit Minze",
        "description": "Ein erfrischender, veganer Salat aus Kichererbsen, Gurke, Tomaten und viel frischer Minze. Mit einem Zitronen-Olivenöl-Dressing und Kreuzkümmel – in 10 Minuten fertig, perfekt für warme Tage.",
        "servings": 4,
        "prep_time_minutes": 10,
        "cook_time_minutes": 0,
        "difficulty": "easy",
        "cook_once_eat_twice": False,
        "leftover_recipe_title": None,
        "tags": ["vegan", "schnell", "familie"],
        "kid_friendly_tip": "Die Kinder können die Minzeblätter von den Stielen zupfen – der Duft an den Fingern ist der Lohn.",
        "instructions": "1. Kichererbsen in ein Sieb abgiessen, kalt abspülen, abtropfen lassen.\n2. Gurke schälen und würfeln. Tomaten und Zwiebel fein würfeln.\n3. Petersilie und Minze hacken.\n4. Alles in einer Schüssel mischen.\n5. Dressing: Olivenöl, Zitronensaft, Kreuzkümmel, Salz und Pfeffer verrühren.\n6. Dressing über den Salat giessen, gut vermengen.\n7. 10 Min. ziehen lassen, dann servieren.",
        "ingredient_list": [
            {"name": "Kichererbsen (Dose)", "amount": 2, "unit": "Dose", "category": "canned"},
            {"name": "Salatgurke", "amount": 1, "unit": "Stück", "category": "vegetables"},
            {"name": "Tomaten", "amount": 3, "unit": "Stück", "category": "vegetables"},
            {"name": "Zwiebeln", "amount": 1, "unit": "Stück", "category": "vegetables"},
            {"name": "Olivenöl", "amount": 3, "unit": "EL", "category": "condiments"},
            {"name": "Zitrone", "amount": 1, "unit": "Stück", "category": "fruit"},
            {"name": "Kreuzkümmel (gemahlen)", "amount": 0.5, "unit": "TL", "category": "spices"},
        ]
    },
    # ──────────────────────────────────────────────────────
    # 27: Makrelen-Pasta (Fisch, schnell)
    # ──────────────────────────────────────────────────────
    {
        "title": "Makrelen-Tomatensauce-Pasta",
        "description": "Eine schnelle Pasta mit Räuchermakrele in cremiger Tomatensauce. Das geräucherte Fischfilet gibt der Sauce ein intensives Aroma – und ist in 15 Minuten auf dem Tisch. Lieblingsrezept für stressige Tage.",
        "servings": 4,
        "prep_time_minutes": 5,
        "cook_time_minutes": 12,
        "difficulty": "easy",
        "cook_once_eat_twice": False,
        "leftover_recipe_title": None,
        "tags": ["fisch", "schnell", "familie"],
        "kid_friendly_tip": "Die Kinder können die Haut von den Makrelenfilets abziehen – das geht leicht und fühlt sich an wie ‚Fisch pellen'.",
        "instructions": "1. Pasta in Salzwasser nach Packungsanweisung kochen.\n2. Räuchermakrelenfilets häuten und mit den Fingern in kleine Stücke zupfen.\n3. Olivenöl in einer Pfanne erhitzen, Cherrytomaten halbieren und anbraten.\n4. Crème fraîche einrühren, Makrelenstücke unterheben.\n5. Mit Salz, Pfeffer und etwas Zitronensaft abschmecken.\n6. Pasta abgiessen und mit der Sauce vermischen.",
        "ingredient_list": [
            {"name": "Pasta (Penne/Fusilli)", "amount": 400, "unit": "g", "category": "grains"},
            {"name": "Räuchermakrelenfilet", "amount": 2, "unit": "Stück", "category": "meat"},
            {"name": "Cherrytomaten", "amount": 200, "unit": "g", "category": "vegetables"},
            {"name": "Crème fraîche", "amount": 150, "unit": "g", "category": "dairy"},
            {"name": "Olivenöl", "amount": 2, "unit": "EL", "category": "condiments"},
            {"name": "Zitrone", "amount": 0.5, "unit": "Stück", "category": "fruit"},
        ]
    },
    # ──────────────────────────────────────────────────────
    # 28: Würstchen-Eintopf (Fleisch, schnell, Kinder)
    # ──────────────────────────────────────────────────────
    {
        "title": "Bunter Würstchen-Eintopf mit Wurzelgemüse",
        "description": "Ein wärmender Eintopf mit Wiener Würstchen, Kartoffeln, Karotten, Pastinaken und Lauch. Das Lieblingsrezept der Kinder – weil Würstchen drin sind. In 25 Minuten fertig, perfekt für kalte Tage.",
        "servings": 4,
        "prep_time_minutes": 10,
        "cook_time_minutes": 20,
        "difficulty": "easy",
        "cook_once_eat_twice": True,
        "leftover_recipe_title": None,
        "tags": ["cook_once", "fleisch", "schnell", "kinderfreundlich", "familie", "saisonal"],
        "kid_friendly_tip": "Die Kinder können die Würstchen mit den Händen in Scheiben brechen – das kracht lustig und ist viel einfacher als Schneidern.",
        "instructions": "1. Kartoffeln und Pastinaken schälen, in 1-cm-Würfel schneiden.\n2. Karotten in Scheiben, Lauch in Ringe schneiden.\n3. Rapsöl im Topf erhitzen, das ganze Gemüse 3 Min. dünsten.\n4. Mit 800 ml Wasser ablöschen, Gemüsebrühe einrühren.\n5. 15 Min. leise köcheln lassen.\n6. Würstchen in Scheiben schneiden und in den Eintopf geben.\n7. Mit Salz, Pfeffer, Majoran und einer Prise Muskat abschmecken.\n8. 2 Min. ziehen lassen (nicht mehr kochen, sonst platzen die Würstchen).",
        "ingredient_list": [
            {"name": "Wiener Würstchen", "amount": 8, "unit": "Stück", "category": "meat"},
            {"name": "Kartoffeln", "amount": 4, "unit": "Stück", "category": "vegetables"},
            {"name": "Karotten", "amount": 2, "unit": "Stück", "category": "vegetables"},
            {"name": "Pastinaken", "amount": 2, "unit": "Stück", "category": "vegetables"},
            {"name": "Lauch (Porree)", "amount": 1, "unit": "Stück", "category": "vegetables"},
            {"name": "Gemüsebrühe (Pulver)", "amount": 2, "unit": "TL", "category": "canned"},
            {"name": "Majoran", "amount": 1, "unit": "TL", "category": "spices"},
            {"name": "Rapsöl", "amount": 1, "unit": "EL", "category": "condiments"},
        ]
    },
]

# Validate
print(f"Recipes: {len(recipes)}")

# Count categories
meat_count = sum(1 for r in recipes if "fleisch" in r["tags"] and "fisch" not in r["tags"])
fish_count = sum(1 for r in recipes if "fisch" in r["tags"])
veg_count = sum(1 for r in recipes if "vegetarisch" in r["tags"])
vegan_count = sum(1 for r in recipes if "vegan" in r["tags"])
cook_once = sum(1 for r in recipes if r["cook_once_eat_twice"])
print(f"  Fleisch: {meat_count}, Fisch: {fish_count}, Vegetarisch: {veg_count}, Vegan: {vegan_count}")
print(f"  cook_once_eat_twice: {cook_once} ({cook_once/len(recipes)*100:.0f}%)")

# Collect all ingredient names used in recipes to check against master
used_ingredients = set()
for r in recipes:
    for i in r["ingredient_list"]:
        used_ingredients.add(i["name"])

master_names = set(i["name"] for i in ingredients)
missing = used_ingredients - master_names
if missing:
    print(f"\n⚠️  Missing from ingredients master: {sorted(missing)}")
else:
    print(f"\n✓ All {len(used_ingredients)} used ingredients are in master list")

# Write recipes.json
with open(os.path.join(SEED_DIR, "recipes.json"), "w", encoding="utf-8") as f:
    json.dump(recipes, f, ensure_ascii=False, indent=2)
print("✓ recipes.json written")