#!/usr/bin/env python3
"""Sprint-3-Tests: Repository-Pattern + Waitlist.
Lauffähig ohne externe Pakete.
"""
import sys
import os
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.repositories import (
    InMemoryUserRepo, InMemoryHouseholdRepo, InMemoryRecipeRepo,
    InMemoryIngredientRepo, InMemoryWaitlistRepo,
    UserRecord, HouseholdRecord, MemberRecord, RecipeRecord,
    IngredientRecord, WaitlistEntry,
)


class TestUserRepo(unittest.TestCase):
    def setUp(self):
        self.repo = InMemoryUserRepo()

    def test_save_and_get_by_email(self):
        u = UserRecord(email="test@t.de", password_hash="hash", display_name="Test")
        self.repo.save(u)
        found = self.repo.get_by_email("test@t.de")
        self.assertIsNotNone(found)
        self.assertEqual(found.display_name, "Test")

    def test_get_by_email_not_found(self):
        self.assertIsNone(self.repo.get_by_email("x@y.z"))

    def test_get_by_id(self):
        u = UserRecord(email="a@b.de", password_hash="h", display_name="A")
        self.repo.save(u)
        self.assertEqual(self.repo.get_by_id(u.id).email, "a@b.de")

    def test_save_updates_existing(self):
        u = UserRecord(email="x@y.de", password_hash="h1", display_name="X")
        self.repo.save(u)
        u.display_name = "Y"
        self.repo.save(u)
        self.assertEqual(self.repo.get_by_email("x@y.de").display_name, "Y")


class TestHouseholdRepo(unittest.TestCase):
    def setUp(self):
        self.repo = InMemoryHouseholdRepo()

    def test_create_and_get_household(self):
        h = HouseholdRecord(name="Familie Test", user_id="u1")
        self.repo.save(h)
        found = self.repo.get_by_id(h.id)
        self.assertEqual(found.name, "Familie Test")

    def test_create_member(self):
        h = HouseholdRecord(name="Familie X", user_id="u1")
        self.repo.save(h)
        m = MemberRecord(household_id=h.id, name="Kind 1", age=8, allergies=["Nüsse"])
        self.repo.save_member(m)
        members = self.repo.get_members(h.id)
        self.assertEqual(len(members), 1)
        self.assertIn("Nüsse", members[0].allergies)

    def test_delete_member(self):
        h = HouseholdRecord(name="Fam", user_id="u1")
        self.repo.save(h)
        m = MemberRecord(household_id=h.id, name="Kind")
        self.repo.save_member(m)
        self.assertTrue(self.repo.delete_member(m.id))
        self.assertFalse(self.repo.delete_member("nonexistent"))

    def test_get_members_empty(self):
        self.assertEqual(self.repo.get_members("nix"), [])


class TestRecipeRepo(unittest.TestCase):
    def setUp(self):
        self.repo = InMemoryRecipeRepo()

    def test_save_and_list(self):
        r = RecipeRecord(household_id="h1", title="Nudeln", tags=["schnell"])
        self.repo.save(r)
        all_r = self.repo.list_all()
        self.assertEqual(len(all_r), 1)
        self.assertIn("schnell", all_r[0].tags)

    def test_get_by_id(self):
        r = RecipeRecord(household_id="h1", title="Suppe")
        self.repo.save(r)
        self.assertEqual(self.repo.get_by_id(r.id).title, "Suppe")

    def test_empty_list(self):
        self.assertEqual(self.repo.list_all(), [])


class TestIngredientRepo(unittest.TestCase):
    def setUp(self):
        self.repo = InMemoryIngredientRepo()

    def test_save_and_list(self):
        i = IngredientRecord(name="Karotte", category="vegetables")
        self.repo.save(i)
        items = self.repo.list_all()
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].category, "vegetables")


class TestWaitlistRepo(unittest.TestCase):
    def setUp(self):
        self.repo = InMemoryWaitlistRepo()

    def test_signup_new_email(self):
        entry = WaitlistEntry(email="test@familie.de", name="Familie Müller")
        self.repo.save(entry)
        found = self.repo.get_by_email("test@familie.de")
        self.assertIsNotNone(found)
        self.assertEqual(found.name, "Familie Müller")

    def test_duplicate_email_returns_existing(self):
        e1 = WaitlistEntry(email="a@b.de")
        self.repo.save(e1)
        e2 = WaitlistEntry(email="a@b.de")
        self.repo.save(e2)  # überschreibt
        found = self.repo.get_by_email("a@b.de")
        self.assertEqual(found.id, e2.id)  # letzter Eintrag gewinnt


class TestDataclassDefaults(unittest.TestCase):
    def test_user_defaults(self):
        u = UserRecord(email="x@y.z", password_hash="h", display_name="N")
        self.assertTrue(u.is_active)
        self.assertIsNotNone(u.id)
        self.assertIsNotNone(u.created_at)

    def test_member_defaults(self):
        m = MemberRecord(household_id="h1", name="Kind")
        self.assertEqual(m.allergies, [])
        self.assertTrue(m.is_active)

    def test_recipe_defaults(self):
        r = RecipeRecord(household_id="h1", title="Test")
        self.assertEqual(r.servings, 4)
        self.assertEqual(r.difficulty, "easy")


if __name__ == "__main__":
    unittest.main(verbosity=2)