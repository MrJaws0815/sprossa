#!/usr/bin/env bash
# Entfernt Testdaten aus der Testinstanz-Datenbank.
#
# Hintergrund: Die pytest-Suite und die E2E-Skripte schreiben in dieselbe
# Datenbank wie die Testinstanz. Ohne Aufraeumen sammeln sich hunderte
# Testkonten an - und Test-Fixtures ("Fixturegericht 1") landen im echten
# Rezeptkatalog, weil der Plan-Generator ohne Haushaltsfilter laedt.
#
# Aufruf:  ./scripts/cleanup_testdata.sh [--dry-run]
#
# Behalten werden: demo@sprossa.de und alle Rezepte (die haengen am
# Demo-Haushalt).
set -euo pipefail

DB=sprossa-test-db
PATTERN="^(auth-test|e2e_|e2e-|swap-test|idtest|revoke|probe|h5_|wait_|chk-|consenttest|dup_)"
DRY="${1:-}"

if [ "$DRY" = "--dry-run" ]; then
  docker exec "$DB" psql -U sprossa -d sprossa_test -t -c \
    "SELECT count(*) FROM users WHERE email ~ '$PATTERN';"
  exit 0
fi

docker exec -i "$DB" psql -U sprossa -d sprossa_test <<SQL
BEGIN;
DELETE FROM meal_slots WHERE recipe_id IN (SELECT id FROM recipes WHERE title LIKE 'Fixturegericht%');
DELETE FROM recipe_ingredients WHERE recipe_id IN (SELECT id FROM recipes WHERE title LIKE 'Fixturegericht%');
DELETE FROM recipes WHERE title LIKE 'Fixturegericht%';
DELETE FROM grocery_items WHERE grocery_list_id IN (SELECT gl.id FROM grocery_lists gl JOIN households h ON h.id=gl.household_id JOIN users u ON u.id=h.user_id WHERE u.email ~ '$PATTERN');
DELETE FROM grocery_lists WHERE household_id IN (SELECT h.id FROM households h JOIN users u ON u.id=h.user_id WHERE u.email ~ '$PATTERN');
DELETE FROM meal_slots WHERE weekly_plan_id IN (SELECT wp.id FROM weekly_plans wp JOIN monthly_plans mp ON mp.id=wp.monthly_plan_id JOIN households h ON h.id=mp.household_id JOIN users u ON u.id=h.user_id WHERE u.email ~ '$PATTERN');
DELETE FROM weekly_plans WHERE monthly_plan_id IN (SELECT mp.id FROM monthly_plans mp JOIN households h ON h.id=mp.household_id JOIN users u ON u.id=h.user_id WHERE u.email ~ '$PATTERN');
DELETE FROM monthly_plans WHERE household_id IN (SELECT h.id FROM households h JOIN users u ON u.id=h.user_id WHERE u.email ~ '$PATTERN');
DELETE FROM members WHERE household_id IN (SELECT h.id FROM households h JOIN users u ON u.id=h.user_id WHERE u.email ~ '$PATTERN');
DELETE FROM households WHERE user_id IN (SELECT id FROM users WHERE email ~ '$PATTERN');
DELETE FROM users WHERE email ~ '$PATTERN';
DELETE FROM ingredients WHERE name ~ '_[0-9a-f]{6}$'
  AND id NOT IN (SELECT ingredient_id FROM grocery_items WHERE ingredient_id IS NOT NULL);
COMMIT;
SQL

docker exec "$DB" psql -U sprossa -d sprossa_test -c \
  "SELECT (SELECT count(*) FROM users) AS user, (SELECT count(*) FROM recipes) AS rezepte, (SELECT count(*) FROM monthly_plans) AS plaene;"
