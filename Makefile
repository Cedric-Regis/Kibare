# Kibaré — commandes de l'équipe. Propriétaire : Cédric.
COMPOSE := docker compose --project-directory infra -f infra/docker-compose.yml
# L'API console (Prisca) est ajoutée dès que console/Dockerfile existe.
ifneq ($(wildcard console/Dockerfile),)
COMPOSE += --profile console
endif

.PHONY: up down logs ps init test test-securite test-pile proof-db proof-net proof-clear proof-intrus demo demo-reset hosts export-images

up: infra/.env init ## Démarre toute la pile (une commande)
	$(COMPOSE) up -d
	@echo "Kibaré : https://kibare.internal  (penser à make hosts la première fois)"

infra/.env:
	cp infra/.env.example infra/.env

init: ## Génère les secrets (une fois) et rend les configurations
	$(COMPOSE) run --rm init

down:
	$(COMPOSE) down

logs:
	$(COMPOSE) logs -f --tail=100

ps:
	$(COMPOSE) ps

demo: ## Profil démo : comptes fictifs, secrets TOTP publics
	KIBARE_PROFIL=demo $(MAKE) up

demo-reset: ## Remet la démo à zéro (efface TOUTES les données locales, garde les secrets)
	$(COMPOSE) down -v
	KIBARE_PROFIL=demo $(MAKE) up

hosts: ## Ajoute les noms kibare.internal dans /etc/hosts (sudo)
	grep -q "kibare.internal" /etc/hosts || echo "127.0.0.1 kibare.internal auth.kibare.internal console.kibare.internal" | sudo tee -a /etc/hosts

test: test-securite ## Tous les tests
	@[ -d tests/api ] && python3 -m pytest tests/api || true

test-securite:
	python3 -m unittest discover -s tests/securite -v

test-pile: ## Module zéro clair et Caddy sur la pile démarrée
	sh tests/securite/test_pile.sh

proof-db:
	sh infra/scripts/proof-db.sh
proof-net:
	sh infra/scripts/proof-net.sh
proof-clear:
	sh infra/scripts/proof-clear.sh
proof-intrus:
	sh infra/scripts/proof-intrus.sh

export-images: ## Exporte les images pour une installation hors ligne
	mkdir -p infra/images
	docker save $$($(COMPOSE) config --images | sort -u) nicolaka/netshoot:v0.13 -o infra/images/kibare-images.tar
