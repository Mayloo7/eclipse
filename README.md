# Bot de Tickets — Éclipse

Bot Discord de tickets avec panneau à menu déroulant (3 catégories : Payment, Support, Reseller).

## ⚠️ Sécurité

Le token et le secret client partagés lors de la génération de ce bot ont été vus en clair
dans la conversation : considérez-les comme compromis et régénérez-les avant toute mise en ligne.

1. https://discord.com/developers/applications → votre application
2. Onglet **Bot** → **Reset Token** → copiez le nouveau token dans votre `.env` (jamais dans le code)
3. Onglet **OAuth2** → **Reset Secret** (ce bot n'utilise pas le secret client, mais autant le régénérer par précaution)

Ce projet ne contient aucun token ni secret : tout passe par le fichier `.env`, qui n'est jamais envoyé sur GitHub grâce au `.gitignore` fourni.

## Installation

1. Python 3.10 ou plus récent.
2. `pip install -r requirements.txt`
3. Copiez `.env.example` en `.env` et renseignez `DISCORD_TOKEN` avec votre nouveau token.
4. Invitez le bot sur votre serveur depuis le Developer Portal (onglet OAuth2 → URL Generator),
   scopes `bot` + `applications.commands`, permissions : Gérer les salons, Voir les salons,
   Envoyer des messages, Intégrer des liens, Lire l'historique des messages.
5. Lancez le bot : `python bot.py`
6. Sur Discord, exécutez la commande `/panel` (administrateur uniquement) pour envoyer le
   panneau dans le salon configuré.

## Fonctionnement

- Les 3 catégories (Payment / Support / Reseller) et le salon du panneau sont déjà pré-remplis
  dans `.env.example` avec les identifiants que vous avez fournis.
- Un utilisateur choisit une catégorie dans le menu déroulant → un formulaire lui demande la
  raison du ticket → un salon privé est créé dans la bonne catégorie.
- Un utilisateur ne peut pas ouvrir deux tickets dans la même catégorie en même temps.
- Chaque ticket a un bouton **Fermer le ticket** (avec confirmation) qui supprime le salon.
- `STAFF_ROLE_ID` (optionnel, dans `.env`) donne automatiquement accès à un rôle staff sur
  chaque ticket créé.
- Aucune intention privilégiée (privileged intent) n'est nécessaire côté Developer Portal.

## Héberger le bot (au-delà de GitHub)

GitHub stocke et versionne le code, mais ne fait pas tourner le bot en continu. Pour l'héberger :

1. Créez un dépôt GitHub et poussez ce code (GitHub Desktop ou `git`) — `.env` reste local.
2. Créez un compte sur un hébergeur qui se connecte à GitHub, par exemple Railway (railway.app)
   ou Render (render.com).
3. Dans le dashboard de l'hébergeur : nouveau projet → déploiement depuis votre dépôt GitHub.
4. Ajoutez les mêmes variables que dans `.env` (DISCORD_TOKEN, PANEL_CHANNEL_ID, etc.) dans la
   section "Variables d'environnement" de l'hébergeur — jamais en dur dans le code.
5. Déployez, puis vérifiez les logs pour voir apparaître "Connecté en tant que...".

## Personnalisation

- Couleur, nom affiché ("Éclipse") et textes du panneau : fonction `build_panel_embed()` dans `bot.py`.
- Emojis et libellés des catégories : dictionnaire `CATEGORIES` en haut de `bot.py`.
