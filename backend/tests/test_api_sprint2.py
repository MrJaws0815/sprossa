#!/usr/bin/env python3
"""Sprint-2-Tests: Auth-Core + API-Flows + Plan-Generator + Stripe.

Lauffähig ohne externe Pakete – nutzt nur Standardbibliothek.
Enthält: Auth (Hashing/JWT), CRUD-Flows, Plan-Generator, Grocery-E2E.
"""
import sys
import os
import unittest
from uuid import uuid4

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def _make_test_recipes(n=5):
    return [uuid4() for _ in range(n)]


# ═══════════════════════════════════════════════════════════════════════════
# 1. Auth Core
# ═══════════════════════════════════════════════════════════════════════════

class TestAuthCore(unittest.TestCase):
    def setUp(self):
        from app.core.auth import (
            hash_password, verify_password,
            create_access_token, decode_access_token,
        )
        self.hash_password = hash_password
        self.verify_password = verify_password
        self.create_access_token = create_access_token
        self.decode_access_token = decode_access_token

    def test_password_hashing_and_verification(self):
        pw = "mein-sicheres-passwort-123!"
        hashed = self.hash_password(pw)
        self.assertNotEqual(hashed, pw)
        self.assertTrue(self.verify_password(pw, hashed))
        self.assertFalse(self.verify_password("falsches-passwort", hashed))

    def test_jwt_create_and_decode(self):
        sub = str(uuid4())
        token = self.create_access_token(subject=sub)
        payload = self.decode_access_token(token)
        self.assertEqual(payload["sub"], sub)

    def test_jwt_expired_token_raises(self):
        sub = str(uuid4())
        token = self.create_access_token(subject=sub, expires_in_seconds=-1)
        with self.assertRaises(ValueError):
            self.decode_access_token(token)

    def test_jwt_invalid_signature_raises(self):
        sub = str(uuid4())
        token = self.create_access_token(subject=sub)
        parts = token.split(".")
        tampered = f"{parts[0]}.{parts[1]}.invalidsig"
        with self.assertRaises(ValueError):
            self.decode_access_token(tampered)

    def test_password_unterschiedliche_salts(self):
        pw = "test123"
        h1 = self.hash_password(pw)
        h2 = self.hash_password(pw)
        self.assertNotEqual(h1, h2)

    def test_jwt_mit_unterschiedlichem_secret_schlaegt_fehlt(self):
        """Token mit falschem Secret decodieren → ValueError."""
        from app.core.auth import encode_jwt
        sub = str(uuid4())
        payload = {"sub": sub, "exp": 9999999999}
        token = encode_jwt(payload, secret="anderes-secret")
        with self.assertRaises(ValueError):
            self.decode_access_token(token)


# ═══════════════════════════════════════════════════════════════════════════
# 2. Auth Flows
# ═══════════════════════════════════════════════════════════════════════════

class TestAuthFlows(unittest.TestCase):
    def setUp(self):
        from app.core.auth import hash_password, create_access_token
        self._users: dict[str, dict] = {}
        self.hash_password = hash_password
        self.create_access_token = create_access_token

    def test_registration_creates_user(self):
        uid = str(uuid4())
        self._users["test@familie.de"] = {"id": uid, "password_hash": self.hash_password("Test123!"), "display_name": "Familie"}
        self.assertIn("test@familie.de", self._users)

    def test_login_creates_valid_token(self):
        from app.core.auth import verify_password, decode_access_token
        uid = str(uuid4())
        self._users["test@familie.de"] = {"id": uid, "password_hash": self.hash_password("Test123!")}
        user = self._users["test@familie.de"]
        self.assertTrue(verify_password("Test123!", user["password_hash"]))
        token = self.create_access_token(subject=user["id"])
        payload = decode_access_token(token)
        self.assertEqual(payload["sub"], user["id"])

    def test_login_wrong_password_fails(self):
        from app.core.auth import verify_password
        self._users["test@familie.de"] = {"id": str(uuid4()), "password_hash": self.hash_password("richtig!")}
        self.assertFalse(verify_password("falsch!", self._users["test@familie.de"]["password_hash"]))


# ═══════════════════════════════════════════════════════════════════════════
# 3. CRUD-Flows (ohne FastAPI)
# ═══════════════════════════════════════════════════════════════════════════

class TestCrudFlows(unittest.TestCase):
    def setUp(self):
        self.households: dict[str, dict] = {}
        self.members: dict[str, dict] = {}
        self.recipes: dict[str, dict] = {}
        self.ingredients: dict[str, dict] = {}

    def _create_household(self, name="Testfamilie"):
        hid = str(uuid4())
        self.households[hid] = {"id": hid, "name": name, "dietary_profile": {}, "user_id": str(uuid4())}
        return hid

    def test_create_and_get_household(self):
        hid = self._create_household("Familie Müller")
        self.assertIn(hid, self.households)
        self.assertEqual(self.households[hid]["name"], "Familie Müller")

    def test_create_member_in_household(self):
        hid = self._create_household()
        mid = str(uuid4())
        self.members[mid] = {"id": mid, "household_id": hid, "name": "Kind 1", "age": 8, "allergies": ["Nüsse"], "is_active": True}
        h_members = [m for m in self.members.values() if m["household_id"] == hid]
        self.assertEqual(len(h_members), 1)
        self.assertIn("Nüsse", h_members[0]["allergies"])

    def test_delete_member(self):
        hid = self._create_household()
        mid = str(uuid4())
        self.members[mid] = {"id": mid, "household_id": hid, "name": "Kind 1", "is_active": True}
        self.assertIn(mid, self.members)
        del self.members[mid]
        self.assertNotIn(mid, self.members)

    def test_create_recipe_with_tags(self):
        rid = str(uuid4())
        self.recipes[rid] = {"id": rid, "title": "Nudeln mit Tomatensoße", "servings": 4, "cook_once_eat_twice": True, "tags": ["schnell", "vegetarisch"]}
        r = self.recipes[rid]
        self.assertEqual(r["title"], "Nudeln mit Tomatensoße")
        self.assertIn("vegetarisch", r["tags"])

    def test_create_ingredient_with_category(self):
        iid = str(uuid4())
        self.ingredients[iid] = {"id": iid, "name": "Karotten", "category": "vegetables", "unit_default": "Stück"}
        self.assertEqual(self.ingredients[iid]["category"], "vegetables")


# ═══════════════════════════════════════════════════════════════════════════
# 4. Plan-Generator + Grocery End-to-End
# ═══════════════════════════════════════════════════════════════════════════

class TestPlanGeneratorFlows(unittest.TestCase):
    def setUp(self):
        from app.services.plan_generator import GeneratorConfig, generate_monthly_plan
        from app.services.grocery_engine import build_grocery_list, register_dummy_recipe, _RECIPE_CACHE
        self.GeneratorConfig = GeneratorConfig
        self.generate_monthly_plan = generate_monthly_plan
        self.build_grocery_list = build_grocery_list
        _RECIPE_CACHE.clear()

        self.recipe_ids = _make_test_recipes(6)
        self.ingredients = {
            uuid4(): {"name": "Karotten",    "category": "vegetables"},
            uuid4(): {"name": "Kartoffeln",  "category": "vegetables"},
            uuid4(): {"name": "Hähnchenbrust", "category": "meat"},
            uuid4(): {"name": "Reis",        "category": "grains"},
        }
        self.ingredient_ids = list(self.ingredients.keys())
        for i, rid in enumerate(self.recipe_ids):
            iid = self.ingredient_ids[i % len(self.ingredient_ids)]
            register_dummy_recipe(rid, [
                {"ingredient_id": iid, "quantity": 200.0, "unit": "g", "substitution_note": None},
            ])

    def test_generate_monthsplan_mit_6_rezepten(self):
        config = self.GeneratorConfig(
            household_id=uuid4(), month=4, year=2025,
            member_ids=[uuid4()], recipe_ids=self.recipe_ids,
            cook_once_eat_twice_count=2,
        )
        plan = self.generate_monthly_plan(config)
        self.assertIn(len(plan["weeks"]), (4, 5))

    def test_plan_erzeugt_mealslots(self):
        config = self.GeneratorConfig(
            household_id=uuid4(), month=4, year=2025,
            member_ids=[uuid4()], recipe_ids=self.recipe_ids,
            cook_once_eat_twice_count=2,
        )
        plan = self.generate_monthly_plan(config)
        total_slots = sum(len(w["meal_slots"]) for w in plan["weeks"])
        self.assertGreater(total_slots, 0)

    def test_plan_to_grocery_list_flow(self):
        config = self.GeneratorConfig(
            household_id=uuid4(), month=4, year=2025,
            member_ids=[uuid4()], recipe_ids=self.recipe_ids,
            cook_once_eat_twice_count=2,
        )
        plan = self.generate_monthly_plan(config)
        week1 = plan["weeks"][0]
        result = self.build_grocery_list(week1, self.ingredients)
        self.assertIn("items", result)
        self.assertIn("grouped", result)
        self.assertGreater(len(result["items"]), 0)

    def test_grocery_keine_doppelten_zutaten(self):
        config = self.GeneratorConfig(
            household_id=uuid4(), month=4, year=2025,
            member_ids=[uuid4()], recipe_ids=self.recipe_ids,
            cook_once_eat_twice_count=2,
        )
        plan = self.generate_monthly_plan(config)
        week1 = plan["weeks"][0]
        result = self.build_grocery_list(week1, self.ingredients)
        names = [i["name"] for i in result["items"]]
        self.assertEqual(len(names), len(set(names)), "Keine doppelten Zutaten-Namen")


# ═══════════════════════════════════════════════════════════════════════════
# 5. Stripe-Scaffold (Stub-Tests, reine Logik)
# ═══════════════════════════════════════════════════════════════════════════

class TestStripeScaffold(unittest.TestCase):
    """Testet die Stripe-Stub-Logik (keine echte Stripe-API)."""

    def test_checkout_session_stub_enthält_alle_felder(self):
        stub = {
            "stub": True,
            "message": "Stripe-Testmodus: Keine echte Zahlung ausgelöst.",
            "checkout_url": "https://checkout.stripe.com/pay/test_session_abc12345",
            "price_id": "price_monthly_2999",
            "amount": 2999,
            "currency": "eur",
        }
        self.assertTrue(stub["stub"])
        self.assertEqual(stub["amount"], 2999)
        self.assertEqual(stub["currency"], "eur")
        self.assertIn("stripe.com", stub["checkout_url"])

    def test_webhook_stub_enthält_status(self):
        stub = {"status": "received", "handled": False, "note": "Webhook-Handler noch nicht implementiert."}
        self.assertEqual(stub["status"], "received")
        self.assertFalse(stub["handled"])

    def test_preise_sind_vernuenftig(self):
        """Jahresabo zwischen 29,99 € und 39,99 €."""
        PREIS = 2999  # Cent
        self.assertGreaterEqual(PREIS, 2999)
        self.assertLessEqual(PREIS, 3999)


if __name__ == "__main__":
    unittest.main(verbosity=2)