# Code is low

Ce programme est conçu pour rechercher, à l'intérieur d'un fichier texte, des références à des articles de codes de droit français (comme le Code civil, le Code de commerce, le Code général des collectivités territoriales...). Il est écrit en Python 3.

## Formulaire utilisateur

Une page d'accueil est générée en utilisant le [framework Bottle](https://bottlepy.org/docs/dev/). L'utilisateur y indique quel fichier il entend analyser. Les formats actuellement acceptés sont ODT, DOCX et PDF. La taille est limitée à 2 Mo, car le processus d'analyse est gourmand en ressources. 

Cela est suffisant pour soumettre même des thèses de doctorat aux formats ODT/DOCX/DOC. Le PDF doit être utilisé faute d'alternative, par exemple pour soumettre un article de tiers téléchargé en libre accès.

L'utilisateur indique sur quelles périodes passée et future il convient de vérifier si l'article de code a connu ou connaîtra d'autres versions. Le champ demande des années ~mais accepte des nombres décimaux, ce qui permet par exemple une vérification sur les six derniers mois~.

L'utilisateur peut ensuite sélectionner les codes qu'il souhaite voir reconnaitre dans le document soumis. Par défaut, tous les codes supportés sont testés. 
> si un code n'est pas sélectionné mais présent dans le texte: l'attribution des articles au bon code est erronée. Cela  
## Ouverture du fichier

Le fichier est provisoirement enregistré sur le serveur puis passé à différentes libraries selon le format utilisé : [python-docx](https://python-docx.readthedocs.io/en/latest/), [odfpy](https://pypi.org/project/odfpy/) ou [PyPDF2](https://pypi.org/project/PyPDF2/). Dès que le fichier a été transformé en chaîne de caractères, il est [supprimé du serveur](./parsing.py).

## Expressions régulières

Le programme confronte ensuite l'ensemble du texte à une expression régulière par code de droit français. L'ensemble des codes supportés ainsi que les expressions rationnelles associées est listé dans la page [codes](codes.html)

Cette méthode est simple mais brutale et devrait être améliorée à l'avenir afin de consommer moins de ressources.

Le résultat des expressions régulières est nettoyé au fur et à mesure, pour anticiper la requête qui sera envoyée à Légifrance. Par exemple, "L. 112-1" doit devenir "L112-1".

Il ressort une liste des resultats. Chaque resultat consiste dans le nom du code et le nom de l'article normalisé. 
## Interrogation de Légifrance

La base de données [Légifrance](https://www.legifrance.gouv.fr/), gérée par la [DILA](https://www.dila.premier-ministre.gouv.fr/), dispose d'une API que le programme peut interroger, les données étant placées sous [licence ouverte 2.0](https://www.etalab.gouv.fr/wp-content/uploads/2017/04/ETALAB-Licence-Ouverte-v2.0.pdf).

Interroger Légifrance suppose une authentification préalable à l'aide d'identifiants personnels. La [version accessible à tous de code is low](codeislow.enetter.fr) utilise les identifiants du développeur. Exécuter le programme par vos propres moyens implique l'obtention d'identifiants Légifrance (voir plus bas).

Au moment de l'authentification, Légifrance accorde un jeton valable une heure seulement, et qui devra être présenté à chaque requête. Le programme est donc conçu pour demander un nouveau jeton à chaque utilisation.

Pour chaque article de code, son identifiant est récupéré à l'aide d'une première requête. Si l'article existe (il n'y a pas d'erreur dans sa référence et il n'a pas été abrogé), une seconde requête permet de récupérer un vaste ensemble d'informations. On y récupère la date à laquelle a débuté la version de l'article actuellement en vigueur et la date à laquelle elle expire (abrogation avec effet différé, remplacement par une nouvelle version).

## Affichage des résultats

Les articles n'ayant pas renvoyé d'identifiant unique ont un code de status 404 et un message "Indisponible".

Pour les autres, la date de début et la date de fin de version d'article sont confrontées avec les périodes définies par l'utilisateur dans le formulaire initial. 

En fonction du résultat, l'article peut être classé comme ayant connu une version passée dans la période de référence pour le passé. 
Son code de status est 301, et le message indique "Modifié le" avec la date de modification.

Il peut être classé comme ayant vocation à changer dans la période de référence pour le futur. Son code 302 et le message indique "Valable jusqu'au" avec la date d'expiration. 

S'il n'a ni été modifié dans la période passée ni ne sera modifié dans la période future, il est classé dans la catégorie des articles correctements détectés mais ne présentant pas de modification.

A partir de cette liste, une page de résultats est générée dynamiquement. Hormis les articles non trouvés, les articles sont cliquables et le lien conduit vers leur version sur Légifrance. Le lien est construit à partir d'une racine commune suivie de l'identifiant unique rapatrié au moment de la première requête. Le texte de référéence est affiché.

## Exécuter le programme localement

Une version du programme utilisable par tous est mise à disposition sur un serveur Heroku. Cela permet à l'utilisateur de profiter des identifiants du développeur sans qu'ils soient révélés.

En dépit des précautions employées (connexion forcée en HTTPS, fichier supprimé avant la fin du script), il est déconseillé de soumettre à la version collective des fichiers contenant des données sensibles, confidentielles ou soumises à un secret professionnel. Le programme peut être exécuté sur votre machine et générera une page web identique purement locale. Seules les requêtes Légifrance sortiront vers l'extérieur. Cette solution requiert l'installation de Python, le clonage ou le téléchargement du dépôt Github, et [l'obtention d'identifiants pour l'API auprès de PISTE](https://developer.aife.economie.gouv.fr/).

Il vous faudra alors créer un fichier intitulé .env en prenant exemple sur le fichier dotenv.example renommé en .env, que vous placerez dans le même répertoire que ce fichier, avec le contenu ci-dessous, en remplaçant évidemment "XXXX" par les valeurs qui vous auront été fournies par PISTE.

    CLIENT_ID = XXXX
    CLIENT_SECRET = XXXX
