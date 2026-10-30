"""Module « zéro clair » de Kibaré (Synapse, callback check_event_allowed).

Synapse appelle check_event_allowed avant d'accepter CHAQUE événement de salon.
Le module ne déchiffre rien et ne lit aucun contenu de message : il vérifie seulement
la forme des événements, pour qu'aucun texte en clair ne soit jamais stocké.

  R1  Liste blanche : seuls m.room.encrypted, m.room.redaction (sans motif) et les
      événements d'état nécessaires sont acceptés. Tout le reste (m.room.message,
      m.reaction en clair, widgets, appels...) est refusé.
  R2  Aucun message dans un salon sans chiffrement Megolm ; le chiffrement d'un salon
      ne peut être ni retiré ni changé d'algorithme.
  R3  Forme du texte chiffré contrôlée : algorithme Megolm, champs attendus uniquement,
      ciphertext en base64 non vide. Aucun champ supplémentaire (ex. « body ») possible.
  R4  Médias uniquement en application/octet-stream : appliqué par Caddy (Caddyfile).
  R5  Salons fermés : entrée sur invitation seulement (les invités sont coupés côté serveur).
  R6  Classification (bf.gov.classification) : valeurs connues, jamais abaissée,
      Confidentiel ou changement de niveau : superviseur seulement.

Refus comptés sans contenu : on journalise la règle et le type d'événement, jamais le contenu.

Limite assumée : un client malveillant peut glisser du texte lisible dans un champ
ciphertext bien formé. Le serveur ne peut pas le voir sans déchiffrer, ce qu'il ne fait pas.
"""

import logging
import re
from collections import Counter
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger("kibare_zero_clair")

MEGOLM = "m.megolm.v1.aes-sha2"

# R1 : événements d'état autorisés (métadonnées nécessaires au fonctionnement d'un salon).
ETATS_AUTORISES = {
    "m.room.create",
    "m.room.member",
    "m.room.power_levels",
    "m.room.join_rules",
    "m.room.history_visibility",
    "m.room.guest_access",
    "m.room.encryption",
    "m.room.name",
    "m.room.topic",
    "m.room.canonical_alias",
    "m.room.pinned_events",
    "m.room.tombstone",
    "m.room.server_acl",
    "m.room.retention",
    "m.space.child",
    "m.space.parent",
    "bf.gov.classification",
}

# R3 : seuls champs permis dans le contenu d'un m.room.encrypted.
CHAMPS_CHIFFRES = {"algorithm", "ciphertext", "session_id", "sender_key", "device_id", "m.relates_to"}
BASE64 = re.compile(r"^[A-Za-z0-9+/]+={0,2}$")

# R6 : ordre des niveaux, du moins au plus protégé.
NIVEAUX = {"nc": 0, "dr": 1, "confidentiel": 2}


class ZeroClair:
    def __init__(self, config: Dict[str, Any], api: Any):
        self._api = api
        self._url_role: Optional[str] = config.get("url_role")
        # Uniquement pour les tests unitaires, quand aucune API console n'est fournie.
        self._superviseurs = set(config.get("superviseurs", []))
        self.refus = Counter()  # R5 : compteur par règle, sans contenu
        api.register_third_party_rules_callbacks(check_event_allowed=self.check_event_allowed)

    @staticmethod
    def parse_config(config: Dict[str, Any]) -> Dict[str, Any]:
        return config

    def _refuser(self, regle: str, event: Any) -> Tuple[bool, None]:
        self.refus[regle] += 1
        logger.info("refus %s type=%s total=%d", regle, event.type, self.refus[regle])
        return False, None

    async def check_event_allowed(self, event: Any, state_events: Dict[Tuple[str, str], Any]) -> Tuple[bool, None]:
        etat = event.is_state()

        # ---- Événements d'état ----------------------------------------------------------
        if etat:
            if event.type not in ETATS_AUTORISES:
                return self._refuser("R1", event)
            if event.type == "m.room.encryption":
                return self._verifier_encryption(event, state_events)
            # Les invités sont coupés pour tout le serveur (allow_guest_access: false), donc
            # m.room.guest_access, que Synapse pose lui-même à la création, reste sans effet.
            if event.type == "m.room.join_rules":
                if event.content.get("join_rule") != "invite":
                    return self._refuser("R5", event)
            if event.type == "bf.gov.classification":
                return await self._verifier_classification(event, state_events)
            return True, None

        # ---- Événements de message (non état) ------------------------------------------
        if event.type == "m.room.redaction":
            # Une suppression ne porte aucun texte : le motif (« reason ») est refusé.
            if set(event.content.keys()) - {"redacts"}:
                return self._refuser("R1", event)
            return True, None

        if event.type != "m.room.encrypted":
            return self._refuser("R1", event)

        # R2 : le salon doit être chiffré en Megolm.
        chiffrement = state_events.get(("m.room.encryption", ""))
        if chiffrement is None or chiffrement.content.get("algorithm") != MEGOLM:
            return self._refuser("R2", event)

        # R3 : forme du texte chiffré.
        contenu = event.content
        if set(contenu.keys()) - CHAMPS_CHIFFRES:
            return self._refuser("R3", event)
        if contenu.get("algorithm") != MEGOLM:
            return self._refuser("R3", event)
        texte = contenu.get("ciphertext")
        if not isinstance(texte, str) or not texte or not BASE64.match(texte):
            return self._refuser("R3", event)
        if not isinstance(contenu.get("session_id"), str):
            return self._refuser("R3", event)
        return True, None

    def _verifier_encryption(self, event: Any, state_events: Dict[Tuple[str, str], Any]) -> Tuple[bool, None]:
        # R2 : seul Megolm est accepté, et une fois posé il ne change plus.
        if event.content.get("algorithm") != MEGOLM:
            return self._refuser("R2", event)
        actuel = state_events.get(("m.room.encryption", ""))
        if actuel is not None and actuel.content != event.content:
            return self._refuser("R2", event)
        return True, None

    async def _verifier_classification(self, event: Any, state_events: Dict[Tuple[str, str], Any]) -> Tuple[bool, None]:
        nouveau = event.content.get("niveau")
        if event.state_key != "" or nouveau not in NIVEAUX or set(event.content.keys()) != {"niveau"}:
            return self._refuser("R6", event)

        precedent = state_events.get(("bf.gov.classification", ""))
        ancien = precedent.content.get("niveau") if precedent is not None else None

        if ancien is not None and NIVEAUX[nouveau] < NIVEAUX.get(ancien, 2):
            return self._refuser("R6", event)  # jamais vers le bas
        if ancien == nouveau:
            return True, None

        # Création en Confidentiel, ou tout changement d'un niveau existant : superviseur.
        if nouveau == "confidentiel" or ancien is not None:
            if not await self._est_superviseur(event.sender):
                return self._refuser("R6", event)
        return True, None

    async def _est_superviseur(self, mxid: str) -> bool:
        if not self._url_role:
            return mxid in self._superviseurs
        try:
            reponse = await self._api.http_client.get_json(self._url_role, args={"mxid": mxid})
        except Exception:
            # Fermé par défaut : sans réponse de l'API console, on refuse.
            logger.warning("API console injoignable : changement de classification refusé")
            return False
        return reponse.get("role") == "superviseur" and reponse.get("statut") == "actif"
