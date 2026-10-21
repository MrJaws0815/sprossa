# Monatsmenue – Datenmodell DRAFT

## Übersicht

```
User ──→ Household ──→ Member
Household ──→ MonthlyPlan ──→ WeeklyPlan ──→ MealSlot ──→ Recipe
Recipe ──→ RecipeIngredient ──→ Ingredient
MonthlyPlan ──→ GroceryList ──→ GroceryItem
Recipe ──→ Substitution (optional)
```

## Entitäten

### User
| Feld | Typ | Zweck |
|------|-----|-------|
| id | UUID | PK |
| email | String | Login, unique |
| password_hash | String | bcrypt |
| display_name | String | Anzeigename |
| stripe_customer_id | String | Stripe-Referenz |
| is_active | Bool | |
| created_at | DateTime | |

### Household (Familie)
| Feld | Typ | Zweck |
|------|-----|-------|
| id | UUID | PK |
| name | String | z.B. "Familie Müller" |
| user_id | UUID | FK -> User (Owner) |
| dietary_profile | JSON | Globale Präferenzen (vegetarisch, keine Milch, etc.) |
| created_at | DateTime | |

### Member (Familienmitglied)
| Feld | Typ | Zweck |
|------|-----|-------|
| id | UUID | PK |
| household_id | UUID | FK -> Household |
| name | String | |
| age | Int | Für Portionsberechnung |
| weight_kg | Float | Falls relevant |
| allergies | String[] | Allergien-Liste |
| dietary_goals | JSON | Ziele: mehr Protein, weniger Kohlenhydrate, etc. |
| notes | String | Freitext |
| is_active | Bool | Im aktuellen Plan berücksichtigen? |

### Recipe
| Feld | Typ | Zweck |
|------|-----|-------|
| id | UUID | PK |
| household_id | UUID | FK -> Household (haushaltseigene Rezepte) |
| title | String | |
| description | String | Kurzbeschreibung |
| servings | Int | Standard-Portionen |
| prep_time_minutes | Int | |
| cook_time_minutes | Int | |
| difficulty | Enum | einfach/mittel/fortgeschritten |
| instructions | Text | Schritt-für-Schritt |
| image_url | String | Optional |
| source | String | "selbst erstellt", "Blog XY", etc. |
| is_public | Bool | Für Community-Sharing (Später) |
| kid_friendly_tip | String | Kinder-Tipp: Variante/Alternativzutat |
| cook_once_eat_twice | Bool | Flag: Dieses Rezept lohnt sich doppelt zu kochen |
| leftover_recipe_id | UUID | FK -> Recipe: Verwertungs-Rezept für Reste |
| tags | String[] | z.B. "schnell", "vegetarisch", "meal-prep" |
| created_at | DateTime | |

### Ingredient (Zutat)
| Feld | Typ | Zweck |
|------|-----|-------|
| id | UUID | PK |
| name | String | z.B. "Karotten" |
| category | Enum | Gemüse, Obst, Fleisch, Milchprodukte, Getreide, Gewürze, Konserven, Tiefkühl, etc. |
| unit_default | String | Standard-Einheit (g, ml, Stück) |
| storage | String | "Kühlschrank", "Vorrat", "Tiefkühler" |

### RecipeIngredient (Brückentabelle)
| Feld | Typ | Zweck |
|------|-----|-------|
| id | UUID | PK |
| recipe_id | UUID | FK -> Recipe |
| ingredient_id | UUID | FK -> Ingredient |
| quantity | Float | |
| unit | String | g, ml, Stück, EL, TL, Prise, etc. |
| is_optional | Bool | Optionale Zutat? |
| substitution_ingredient_id | UUID | FK -> Ingredient (Alternative) |
| substitution_note | String | "Statt Sahne: Hafermilch" |
| pre_processed | Bool | Bereits in der Vorratshaltung? |

### WeeklyPlan
| Feld | Typ | Zweck |
|------|-----|-------|
| id | UUID | PK |
| household_id | UUID | FK -> Household |
| monthly_plan_id | UUID | FK -> MonthlyPlan |
| week_number | Int | 1-4 (bzw. 1-5) |
| start_date | Date | Montag der Woche |
| notes | String | Besondere Hinweise |
| created_at | DateTime | |

### MealSlot
| Feld | Typ | Zweck |
|------|-----|-------|
| id | UUID | PK |
| weekly_plan_id | UUID | FK -> WeeklyPlan |
| day_of_week | Int | 1=Montag ... 7=Sonntag |
| meal_type | Enum | Frühstück, Mittagessen, Abendessen, Snack |
| recipe_id | UUID | FK -> Recipe |
| servings_multiplier | Float | Portionsfaktor (1.0, 1.5, 2.0) |
| is_repeat | Bool | Handelt es sich um ein "Cook Once Eat Twice"-Repeat? |
| original_meal_slot_id | UUID | FK -> MealSlot (Referenz zum Original-Slot) |

### MonthlyPlan
| Feld | Typ | Zweck |
|------|-----|-------|
| id | UUID | PK |
| household_id | UUID | FK -> Household |
| month | Int | 1-12 |
| year | Int | |
| status | Enum | draft, active, archived |
| focus_tags | String[] | "schnell", "proteinreich", "Resteverwertung", etc. |
| generated_at | DateTime | |
| notes | String | Notizen zum Monat |

### GroceryList
| Feld | Typ | Zweck |
|------|-----|-------|
| id | UUID | PK |
| household_id | UUID | FK -> Household |
| monthly_plan_id | UUID | FK -> MonthlyPlan (optional) |
| week_number | Int | 1-4 (auf welche Woche bezogen) |
| generated_at | DateTime | |
| is_master_list | Bool | Monats-Einkaufsliste oder Wochenliste? |

### GroceryItem
| Feld | Typ | Zweck |
|------|-----|-------|
| id | UUID | PK |
| grocery_list_id | UUID | FK -> GroceryList |
| ingredient_id | UUID | FK -> Ingredient |
| quantity_total | Float | Gesamtmenge über alle Rezepte |
| unit | String | |
| quantity_purchased | Float | Tatsächlich eingekauft (Tracking) |
| is_checked | Bool | Erledigt? |
| category_override | String | Gruppierungs-Override für Ausgabe |
| notes | String | "Bio wenn möglich", "im Angebot kaufen" |

## Core-Logik: "Cook Once, Eat Twice"

Der Plan-Generator arbeitet mit folgender Strategie:

1. Für jede Woche werden ~5-7 Hauptgerichte ausgewählt
2. Davon werden 2-3 als "Cook Once, Eat Twice" markiert
3. Diese Gerichte werden einmal gekocht, aber auf 2 Slots verteilt (Tag X + Tag X+2)
4. Die Einkaufsliste skaliert die Zutaten nur für die tatsächliche Koch-Menge
5. Die restlichen Tage sind "echte" Einzelgerichte

Das ergibt: 4-5 Koch-Sessions pro Woche statt 7 + weniger Abwasch + weniger Stress.

## Substitutions-Engine

Jedes RecipeIngredient kann eine Standard-Substitution haben:
- Regional: "Statt Brokkoli: Blumenkohl" (je nach Saison)
- Allergen: "Statt Milch: Hafermilch" (bei Haushalts-Allergien)
- Budget: "Statt Rinderfilet: Hähnchenbrust"

Der Generator wendet Substitutionen an basierend auf:
1. Member-Allergien
2. Haushalts-Präferenzen
3. Saisonale Verfügbarkeit (später)

## Domain-Regeln (zunächst für TDD)

1. Ein MonthlyPlan hat genau 4 oder 5 WeeklyPlans (je nach Monat)
2. Ein WeeklyPlan hat 7 Tage mit je 2-3 MealSlots (Frühstück optional)
3. Ein Recipe muss mindestens 1 RecipeIngredient haben
4. Keine Allergene bei Membern mit entsprechenden Allergien (Validierung)
5. CookOnce-EatTwice: original_meal_slot_id zeigt auf den Slot mit dem Rezept
6. GroceryItem summiert alle RecipeIngredient.Mengen über alle Slots eines Zeitraums