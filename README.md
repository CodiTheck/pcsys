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

### État global et local

Un état est une variable, une instance de classe. Ici, cela peut être n'importe quel
objet `Python`. 

#### État local
<p>
Un état local est tous simplement une variable locale à une structure. Pour plus de clarté dans mes propos, je vais donner l'exemple de deux structures de traitement.

```python
# N'oublie pas de mettre la ligne suivante !
import pcsys

# Une première structure A
class A(pcsys.Proc):
    def init_f(self, state):
        print("Initialisation du processus A ...");

        # dans ce processus, on va definir une variable dans l'état local
        # L'état local ici est représenté par la variable `x`.
        x = "Donnée de A";
        return x;
    
    def proc_f(self, state, data):
        print("Traitement de A ...");

		# C'est data qui contient la valeur de la variable 
		# contenu dans l'état local.

        # on affiche donc la valeur de `data`
        print(f"{data}");


# Une seconde structure B
class B(pcsys.Proc):
    def init_f(self, state):
        print("\nInitialisation du processus B ...");
    
    def proc_f(self, state, data):
        print("Traitement de B ...");

        # on affiche les données de `data`
        print(f"{data}");


if __name__ == '__main__':
    """Ne te focalise pas sur ce que je vais écrire ici. Je t'expliquerai tous
    ceci en détail dans les prochaines sections."""

    # on précise qu'on continu le traitement indépendament 
    # des erreurs éventuelles, et on n'affiche pas les messages
    # interne du module
    pcsys.STOPONFE = False;
    pcsys.LOG      = False;

    kernel = pcsys.Kernel();
    procs  = pcsys.ProcSeq(); # séquence de processus

    # declaration des deux processuses A et B
    a = A();
    b = B();

    procs.add_proc(a);
    procs.add_proc(b);

    # on déclare le state
    state = pcsys.State();
    state.initialval = 1000;

    # on démarre la séquence de traitement (processus)
    p, q = kernel.start_proc(procs, state);
    resl = kernel.wait_result(q);

    # on affiche l'état global `state` modifié après tous les traitements
    print(resl[0]);

    # on affiche les messages d'erreurs
    print();
    print("----------------------Liste des erreurs de traitement--------------------");
    print(resl[1]);


```

</p>

<br/>
<br/>
