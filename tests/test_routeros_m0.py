from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import tempfile
import unittest

from prototype.routeros_m0 import (
    AtomicJournalStore,
    ConfigRevision,
    InMemoryRuntime,
    JournalError,
    JournalRecord,
    RecoveryRequired,
    ValidationError,
    apply_transaction,
    compile_plan,
    recover_interrupted_transaction,
    validate_config,
)

ROOT = Path(__file__).resolve().parents[1]


def reference_config():
    return json.loads((ROOT / "config/examples/reference-build-0.1.json").read_text(encoding="utf-8"))


def alternate_config(subnet_octet: int = 60):
    config = reference_config()
    config["interfaces"][1]["address"] = f"192.168.{subnet_octet}.1/24"
    config["interfaces"][1]["dhcp"]["start"] = f"192.168.{subnet_octet}.100"
    config["interfaces"][1]["dhcp"]["end"] = f"192.168.{subnet_octet}.199"
    validate_config(config)
    return config


class ValidationTests(unittest.TestCase):
    def test_reference_config_is_valid(self):
        validate_config(reference_config())

    def test_duplicate_interface_names_fail(self):
        config = reference_config()
        config["interfaces"][1]["name"] = config["interfaces"][0]["name"]
        with self.assertRaises(ValidationError):
            validate_config(config)

    def test_management_on_wan_fails(self):
        config = reference_config()
        config["management"]["bind_role"] = "wan"
        with self.assertRaises(ValidationError):
            validate_config(config)

    def test_dhcp_pool_outside_lan_fails(self):
        config = reference_config()
        config["interfaces"][1]["dhcp"]["start"] = "192.168.51.100"
        with self.assertRaises(ValidationError):
            validate_config(config)

    def test_dhcp_pool_must_exclude_router_address(self):
        config = reference_config()
        config["interfaces"][1]["dhcp"]["start"] = "192.168.50.1"
        with self.assertRaises(ValidationError):
            validate_config(config)

    def test_default_forward_must_drop(self):
        config = reference_config()
        config["firewall"]["default_forward"] = "accept"
        with self.assertRaises(ValidationError):
            validate_config(config)


class DeterminismTests(unittest.TestCase):
    def test_revision_digest_ignores_key_order(self):
        config = reference_config()
        reordered = {key: config[key] for key in reversed(list(config.keys()))}
        self.assertEqual(ConfigRevision.from_config(config).digest, ConfigRevision.from_config(reordered).digest)

    def test_plan_is_deterministic(self):
        config = reference_config()
        self.assertEqual(compile_plan(config), compile_plan(deepcopy(config)))

    def test_plan_contains_no_executable_command_field(self):
        encoded = json.dumps(compile_plan(reference_config()))
        self.assertNotIn('"command"', encoded)
        self.assertNotIn('"shell"', encoded)


class TransactionTests(unittest.TestCase):
    def test_successful_apply_is_retained_after_verification(self):
        config = reference_config()
        runtime = InMemoryRuntime()
        result = apply_transaction(config, runtime)
        self.assertTrue(result.retained)
        self.assertFalse(result.rolled_back)
        self.assertEqual(result.desired_revision, result.applied_revision)
        self.assertEqual(result.desired_revision, result.observed_revision)

    def test_failed_verification_rolls_back_to_previous_known_good(self):
        previous = alternate_config(60)
        runtime = InMemoryRuntime(previous)
        runtime.force_verification_failure = True
        candidate = reference_config()
        result = apply_transaction(candidate, runtime)

        self.assertTrue(result.rolled_back)
        self.assertFalse(result.retained)
        self.assertEqual(ConfigRevision.from_config(previous).digest, ConfigRevision.from_config(runtime.snapshot()).digest)

    def test_candidate_does_not_mutate_runtime_before_apply(self):
        previous = reference_config()
        runtime = InMemoryRuntime(previous)
        candidate = alternate_config(70)
        self.assertEqual(ConfigRevision.from_config(previous).digest, ConfigRevision.from_config(runtime.snapshot()).digest)

    def test_successful_journaled_apply_clears_terminal_journal(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            store = AtomicJournalStore(Path(temp_dir) / "transaction.json")
            runtime = InMemoryRuntime(alternate_config(60))
            result = apply_transaction(reference_config(), runtime, journal_store=store)
            self.assertTrue(result.retained)
            self.assertFalse(store.exists())

    def test_failed_journaled_apply_rolls_back_and_clears_terminal_journal(self):
        previous = alternate_config(60)
        with tempfile.TemporaryDirectory() as temp_dir:
            store = AtomicJournalStore(Path(temp_dir) / "transaction.json")
            runtime = InMemoryRuntime(previous)
            runtime.force_verification_failure = True
            result = apply_transaction(reference_config(), runtime, journal_store=store)
            self.assertTrue(result.rolled_back)
            self.assertFalse(store.exists())
            self.assertEqual(ConfigRevision.from_config(previous).digest, ConfigRevision.from_config(runtime.snapshot()).digest)


class JournalTests(unittest.TestCase):
    def test_atomic_journal_round_trip_and_restrictive_mode(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "transaction.json"
            store = AtomicJournalStore(path)
            record = JournalRecord.prepare(reference_config(), alternate_config(60), transaction_id="test-transaction")
            store.write(record)
            self.assertEqual(record, store.read())
            if os.name == "posix":
                self.assertEqual(path.stat().st_mode & 0o777, 0o600)

    def test_corrupted_checksum_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "transaction.json"
            store = AtomicJournalStore(path)
            store.write(JournalRecord.prepare(reference_config(), alternate_config(60)))
            envelope = json.loads(path.read_text(encoding="utf-8"))
            envelope["phase"] = "retained"
            path.write_text(json.dumps(envelope), encoding="utf-8")
            with self.assertRaises(JournalError):
                store.read()

    def test_sensitive_fields_are_refused(self):
        config = reference_config()
        config["management"]["password"] = "must-not-be-written"
        with self.assertRaises(JournalError):
            JournalRecord.prepare(config, None)


class RecoveryTests(unittest.TestCase):
    def test_prepared_journal_with_previous_runtime_is_discarded(self):
        previous = alternate_config(60)
        with tempfile.TemporaryDirectory() as temp_dir:
            store = AtomicJournalStore(Path(temp_dir) / "transaction.json")
            store.write(JournalRecord.prepare(reference_config(), previous))
            result = recover_interrupted_transaction(store, InMemoryRuntime(previous))
            self.assertEqual(result.action, "discarded-unapplied")
            self.assertFalse(store.exists())

    def test_prepared_journal_with_desired_runtime_is_retained(self):
        previous = alternate_config(60)
        desired = reference_config()
        with tempfile.TemporaryDirectory() as temp_dir:
            store = AtomicJournalStore(Path(temp_dir) / "transaction.json")
            store.write(JournalRecord.prepare(desired, previous))
            result = recover_interrupted_transaction(store, InMemoryRuntime(desired))
            self.assertEqual(result.action, "retained-desired")
            self.assertFalse(store.exists())

    def test_applied_journal_with_desired_runtime_is_retained(self):
        previous = alternate_config(60)
        desired = reference_config()
        with tempfile.TemporaryDirectory() as temp_dir:
            store = AtomicJournalStore(Path(temp_dir) / "transaction.json")
            record = JournalRecord.prepare(desired, previous).with_phase("applied")
            store.write(record)
            result = recover_interrupted_transaction(store, InMemoryRuntime(desired))
            self.assertEqual(result.action, "retained-desired")
            self.assertFalse(store.exists())

    def test_applied_journal_with_previous_runtime_confirms_rollback(self):
        previous = alternate_config(60)
        desired = reference_config()
        with tempfile.TemporaryDirectory() as temp_dir:
            store = AtomicJournalStore(Path(temp_dir) / "transaction.json")
            record = JournalRecord.prepare(desired, previous).with_phase("applied")
            store.write(record)
            result = recover_interrupted_transaction(store, InMemoryRuntime(previous))
            self.assertEqual(result.action, "confirmed-rollback")
            self.assertFalse(store.exists())

    def test_unknown_third_state_requires_manual_recovery_and_preserves_journal(self):
        previous = alternate_config(60)
        desired = reference_config()
        third = alternate_config(70)
        with tempfile.TemporaryDirectory() as temp_dir:
            store = AtomicJournalStore(Path(temp_dir) / "transaction.json")
            record = JournalRecord.prepare(desired, previous).with_phase("applied")
            store.write(record)
            with self.assertRaises(RecoveryRequired):
                recover_interrupted_transaction(store, InMemoryRuntime(third))
            self.assertTrue(store.exists())

    def test_corrupt_journal_requires_manual_recovery_and_preserves_evidence(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "transaction.json"
            path.write_text("{not-json", encoding="utf-8")
            store = AtomicJournalStore(path)
            with self.assertRaises(RecoveryRequired):
                recover_interrupted_transaction(store, InMemoryRuntime(reference_config()))
            self.assertTrue(store.exists())


if __name__ == "__main__":
    unittest.main()
