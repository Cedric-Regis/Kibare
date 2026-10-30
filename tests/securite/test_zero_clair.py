"""Tests unitaires du module zéro clair (sans Synapse).

Lancer : python3 -m unittest discover -s tests/securite -v
"""

import asyncio
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "infra" / "synapse" / "modules"))
from kibare_zero_clair import MEGOLM, ZeroClair  # noqa: E402

CHIFFRE = {"algorithm": MEGOLM, "ciphertext": "AwgAEpABqOCAaP4w", "session_id": "abc", "device_id": "DEV"}


class Evenement:
    def __init__(self, type, content, state_key=None, sender="@agent:kibare.internal"):
        self.type, self.content, self.state_key, self.sender = type, content, state_key, sender

    def is_state(self):
        return self.state_key is not None


class FausseApi:
    def register_third_party_rules_callbacks(self, **kwargs):
        self.callbacks = kwargs


def salon(chiffre=True, niveau=None):
    etat = {}
    if chiffre:
        etat[("m.room.encryption", "")] = Evenement("m.room.encryption", {"algorithm": MEGOLM}, "")
    if niveau:
        etat[("bf.gov.classification", "")] = Evenement("bf.gov.classification", {"niveau": niveau}, "")
    return etat


class TestZeroClair(unittest.TestCase):
    def setUp(self):
        self.module = ZeroClair({"superviseurs": ["@chef:kibare.internal"]}, FausseApi())

    def verifier(self, evenement, etat=None):
        autorise, _ = asyncio.run(self.module.check_event_allowed(evenement, salon() if etat is None else etat))
        return autorise

    # R1 -------------------------------------------------------------------------------
    def test_message_en_clair_refuse(self):
        self.assertFalse(self.verifier(Evenement("m.room.message", {"msgtype": "m.text", "body": "MARQUEUR"})))

    def test_reaction_en_clair_refusee(self):
        self.assertFalse(self.verifier(Evenement("m.reaction", {"m.relates_to": {"key": "👍"}})))

    def test_type_etat_inconnu_refuse(self):
        self.assertFalse(self.verifier(Evenement("im.vector.modular.widgets", {"url": "x"}, "w")))

    def test_suppression_avec_motif_refusee(self):
        self.assertFalse(self.verifier(Evenement("m.room.redaction", {"redacts": "$e", "reason": "secret"})))
        self.assertTrue(self.verifier(Evenement("m.room.redaction", {"redacts": "$e"})))

    # R2 -------------------------------------------------------------------------------
    def test_message_chiffre_accepte(self):
        self.assertTrue(self.verifier(Evenement("m.room.encrypted", dict(CHIFFRE))))

    def test_message_dans_salon_non_chiffre_refuse(self):
        self.assertFalse(self.verifier(Evenement("m.room.encrypted", dict(CHIFFRE)), salon(chiffre=False)))

    def test_changer_algorithme_refuse(self):
        self.assertFalse(self.verifier(Evenement("m.room.encryption", {"algorithm": "m.olm.v1"}, "")))

    # R3 -------------------------------------------------------------------------------
    def test_champ_body_ajoute_refuse(self):
        self.assertFalse(self.verifier(Evenement("m.room.encrypted", {**CHIFFRE, "body": "MARQUEUR"})))

    def test_ciphertext_non_base64_refuse(self):
        self.assertFalse(self.verifier(Evenement("m.room.encrypted", {**CHIFFRE, "ciphertext": "bonjour tout le monde"})))

    def test_ciphertext_vide_refuse(self):
        self.assertFalse(self.verifier(Evenement("m.room.encrypted", {**CHIFFRE, "ciphertext": ""})))

    # R5 -------------------------------------------------------------------------------
    def test_salon_public_refuse(self):
        self.assertFalse(self.verifier(Evenement("m.room.join_rules", {"join_rule": "public"}, "")))
        self.assertTrue(self.verifier(Evenement("m.room.join_rules", {"join_rule": "invite"}, "")))

    # R6 -------------------------------------------------------------------------------
    def classification(self, niveau, sender="@agent:kibare.internal"):
        return Evenement("bf.gov.classification", {"niveau": niveau}, "", sender)

    def test_agent_cree_salon_dr(self):
        self.assertTrue(self.verifier(self.classification("dr")))

    def test_agent_ne_cree_pas_confidentiel(self):
        self.assertFalse(self.verifier(self.classification("confidentiel")))

    def test_superviseur_cree_confidentiel(self):
        self.assertTrue(self.verifier(self.classification("confidentiel", "@chef:kibare.internal")))

    def test_jamais_vers_le_bas_meme_superviseur(self):
        self.assertFalse(self.verifier(self.classification("nc", "@chef:kibare.internal"), salon(niveau="dr")))

    def test_agent_ne_releve_pas_le_niveau(self):
        self.assertFalse(self.verifier(self.classification("confidentiel"), salon(niveau="dr")))

    def test_niveau_inconnu_refuse(self):
        self.assertFalse(self.verifier(self.classification("secret", "@chef:kibare.internal")))

    # R5 bis : refus comptés, sans contenu ------------------------------------------------
    def test_refus_comptes_sans_contenu(self):
        with self.assertLogs("kibare_zero_clair", "INFO") as journaux:
            self.verifier(Evenement("m.room.message", {"body": "MARQUEUR"}))
        self.assertEqual(self.module.refus["R1"], 1)
        self.assertNotIn("MARQUEUR", "\n".join(journaux.output))


if __name__ == "__main__":
    unittest.main()
