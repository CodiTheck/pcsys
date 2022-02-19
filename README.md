# pcsys
Système de gestion des traitement chaînés.

<br/>

## Installation
Télécharge simplement le fichier `pcsys.py` dans votre projet ou clonner ce dépôt.

```sh
git clone https://github.com/CodiTheck/pcsys.git
```

Fais en bon usage !

## Guide d'utilisation

### La stucture `Proc`
<p>

Il s'agit d'une structure de traitement `mono-thread`. Il permet d'exécuter un programme dans un thread différent du thread du processus appelant. C'est à dire : le thread dans
lequel ton programme sera exécuté, est celui d'un autre processus dédié à l'exécution
d'une séquence de traitement que tu aurais mis en place grâce à la structure 
`prosys.ProcSeq` (Séquence de traitement).

```python
# pour commencer, importe le module `pcsys`
import pcsys
```

Ensuite, tu devra créer une structure (une classe) qui va hériter de la structure 
`pcsys.Proc`.

```python
# Voici un exemple :
class MyProc(pcsys.Proc): # `MyProc` hérite de `pcsys.Proc`
    pass # pour le moment, on passe notre tour !

```
</p>

> Ça y est, c'est finit ?

<p>

Mais, non ! Tu vas maintenant pouvoir définir ton traitement dans deux fonctions. À savoir, la fonction d'initialisation `init_f` et la fonction de traitement `proc_f`.
- La fonction d'initialisation prend un seul paramètre, il s'agit du `state` 
(état global).
- La fonction de traitement prend deux paramètres : l'état global `state` et 
l'état local `data`.

```python
# Toujours dans la structure que t'as déclaré
# tu va définir les deux fonctions que je viens 
# de te présenter.
class MyProc(pcsys.Proc):
    def init_f(self, state):
        """Ici tu peux écrire ton code de pré-traitement."""
        print("Initialisation du processus ...");
    
    def proc_f(self, state, data):
        """Ici, tu pourras écrire ton code de traitement proprement dite."""
        print("Traitement des informations en cour...");

```

Et voilà ! C'est aussi simple que **Yo**. Je peux maintenant passer au chose sérieuse
avec toi.

</p>

> Attend l'amis. Je ne comprend toujours pas cette affaire d'état local et d'état global.
> Peux tu m'en dire plus avant de passer au chose sérieuse.

D'accord, si tu insiste, alors je vais te rafraichir la mémoire. Alors va pour la
section suivante.


