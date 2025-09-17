# Projet Algo-distribue dans le cadre du Master 2 à l'USMB

- Evan MEZIERE

1. [Rappel](#rappel-du-sujet)
2. [Installation du projet](#installation-du-projet)
3. [Architecure](#architecture-du-projet)
4. [Fonction](#fonction-ajouter)

## Rappel du Sujet

Dans la prise en main du bus asynchrone, vous avez certainement implémenté l’ensemble des
méthodes d’émissions et réceptions dans la classe Process. Hors ceci est une tâche du middleware et
non du processus.

Repartons donc sur de bonnes bases et enrichissons ce que nous (vous) avons fait précédemment.
Créez une classe « Com » qui sera votre communicateur ; soit la classe qui contient l’ensemble des
méthodes de communication. Ainsi chaque processus pourra instancier un communicateur pour
l’envoi et la réception de message. Votre communicateur implémentera une horloge de Lamport
protégée par un sémaphore et proposera la méthode inc_clock() a votre process afin qu’il puisse
incrémenter l’horloge s’il le souhaite. La gestion de l’horloge concernant les émission et réception
de message se fera naturellement par le communicateur. Le sémaphore évitera que le process et le
communicateur modifient l’horloge en parallèle. Notons que seuls les messages utilisateurs auront
un effet sur l’horloge de Lamport, certains messages ont une vocation système, ils ne doivent pas
avoir d’effet sur l’horloge (ex. : un Token).

Dans notre middleware, nous souhaitons que le communicateur fournisse, à son processus, une
boite aux lettres (B.a.L.) pour tous les messages asynchrones. Ainsi le processus pourra piocher à sa
guise les messages qu’il a reçus dans cette boite.

Concernant les messages, il est conseillé d’avoir une classe abstraite de messages génériques. Cette
dernière contiendra toutes les informations communes à tout message (Payload, stamp…). Tous les
messages supportés par votre communicateur hériteront de cette classe abstraite.
Le communicateur doit fournir aux processus les méthodes de communication asynchrone :

- broadcast(Object o) : qui envoie l’objet « o » dans toutes les B.a.L. des autres processus.
- sendTo(Object o, int dest) : qui envoie l’objet « o » dans la B.a.L. du processus « dest ».
  Note : tous les services suivants sont bloquants, évitez autant que possible les attentes actives en
  utilisant des mutexs ou sémaphores.

Il doit fournir aux processus les services de :

- section critique distribuée avec les méthodes « requestSC() » et « releaseSC() ». La méthode
  « requestSC() » doit bloquer le processus jusqu’à obtention de la section critique.
  L’utilisation d’un jeton sur anneau au sein du communicateur est la méthode la plus simple
  pour répondre à ce problème. Cependant, la gestion du jeton doit être gérée par un thread
  tiers et les messages contenant le jeton ne doivent pas impacter l’horloge du processus, car
  ce sont des messages système,
- synchronisation avec la méthode « synchronize() » qui attend que tous les processus aient
  invoqué cette méthode pour tous les débloquer.

Le communicateur doit fournir aux processus les méthodes de communication synchrone (donc
bloquantes) :

- broadcastSync(Object o, int from) : qui
  - si le processus a l’identifiant « from », il envoie l’objet « o » à tous les autres processus et attend que tous les autres aient reçu le message par invocation de la méthode ;
  - si le processus n’a pas l’identifiant « from », il attend de recevoir le message de « from ».
- sendToSync(Object o, int dest) et recevFromSync(Object o, int from) : qui respectivementenvoie le message à « dest » et bloque jusqu’à ce que « dest », reçoit le message et bloque jusqu’à ce que « from » envoie le message.

Le communicateur doit fournir un système de numérotation automatique et consécutive, quand un
processus se connecte, il reçoit un numéro unique. La numérotation commençant à 0 pour le
premier processus. Contrairement à ce qui a été proposé dans l’exemple fourni, il est interdit
d’utiliser de variable de Classe.

Pour aller plus loin, le système de numérotation sera couplé à un « heartbit », c’est-à-dire un
message système envoyé périodiquement par les processus à tous les autres pour prouver qu’ils sont
encore vivants. Si un des processus ne communique plus, la numérotation de ceux encore vivants
doit être corrigée.

Pour toutes les fonctions que vous avez réalisées, vous rendrez le code Java (ou autre) ainsi que la
JavaDoc associée à ces fonctions. Un exemple d’utilisation de vos fonctions, comme le jeu de dés
proposé dans la prise en main de Guava sera le bienvenu.

## Installation du projet

Tout d'abord clone le repository

```bash
git clone https://github.com/nocxxy/Algo-distribue
```

Une fois le repository clone, il vous faut créer un environement virtuel pour installer les librairies

```bash
python -m venv /path/to/new/virtual/environment
```

Ensuite, pour pouvoir executer le code, il faut d'abord se mettre dans l'environement virtuel.

_Pour windows :_

```bash
/path/to/new/virtual/environment/Script/activate
```

_Pour linux :_

```bash
source /path/to/new/virtual/environment/bin/activate
```

De plus, il vous faudra installer les dépendances :

```bash
pip install -r ./requirements.txt
```

Enfin pour lancer le projet

```bash
py ./Launcher.py
```

## Architecture du projet

## Fonction Ajouter
