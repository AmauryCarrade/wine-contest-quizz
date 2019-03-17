# Wine Contest Quizz

## Questions

### Types de question

#### Général

- Toutes les questions peuvent être illustrées.
- Chaque question est constituée d'une question (texte libre pouvant être long) et d'un détail de réponse pouvant être affiché, si renseigné, lors de la correction.
- Chaque question dispose de catégories (tags).
- Chaque question dispose d'une langue (Français ou Anglais initialement).
- Chaque question dispose d'une source (typiquement, un concours dans laquelle elle a été posée), qui peut être non-renseignée (pour les questions inventées de toute pièces, par exemple).
- Chaque question a un niveau de difficulté $d$ entre un (facile) et trois (difficile). Le nombre maximal de points que peut rapporter la question est égal à $d$.

#### Questions à choix multiples

- La question est composée de plusieurs réponses, deux ou plus.
- Chaque réponse est composée d'un texte uniquement (pas d'image). Elle est juste ou fausse.
- Les réponses sont présentées dans un ordre aléatoire.
- Qu'il y ait ou non qu'une réponse juste, l'utilisateur verra dans tous les cas des cases à cocher multiples.
- Les questions peuvent disposer d'un champ « Autre » qu'est libre. Ce champ peut être la bonne réponse, ou une des bonnes réponses, ou non. La détermination de la justesse de ce champ est la même que celle pour les questions à réponse libre ci-dessous.
  - Les points $\alpha$ accordés sont de 1 si la réponse est parfaite ($\ell = 0$), ½ si elle est proche ($1 \leq \ell \leq 3$), et 0 sinon.
- Le nombre de points accordé pour la réponse est égal à, où $\zeta$ vaut 1 s'il  y a une réponse ouverte et 0 sinon, $$\max\left(d \times \frac{N_{\text{rép. justes}} - N_{\text{rép. fausses sélectionnées}} + \alpha}{N_{\text{rép.}} + \zeta}\,;\,0\right)$$.

#### Questions à réponse libre

- L'utilisateur dispose d'un champ de texte vide pour répondre à la question.
- Pour la correction, les caractères de ponctuation ainsi que la casse sont ignorés, et le nombre de points accordés dépend de la distance de Levenshtein $\ell$ entre la réponse fournie normalisée et la réponse juste normalisée :
  - si $\ell = 0$ (réponse exacte), l'utilisateur gagne $d$ points ;
  - si $1 \leq \ell \leq 3$ (réponse proche mais potentiellement avec des fautes d'orthographe ou des fautes de frappe), l'utilisateur gagne $d \over 2$ points ;
  - si $\ell \geq 4$, l'utilisateur ne gagne aucun point.
- La bonne réponse est donnée lors de la phase de correction.

#### Questions avec réponses à relier

- La question dispose de deux groupes de réponses.
- Le premier groupe est similaire à celui des questions multiples.
- Le second groupe est similaire mais chaque réponse est reliée à une réponse du premier groupe.
- L'utilisateur doit associer les réponses entre elles.Toutes les réponses ont une associée.
- Pour la correction, une association correcte compte comme réponse juste. Une association erronée ou pas d'association pour une réponse compte comme fausse. Le nombre de points accordé pour la réponse est égal à $$d \times \frac{N_{\text{rép. justes}}}{N_{\text{rép.}}}$$.

### Catégories

- Système arborescent.
- Il est possible de récupérer les questions par catégorie. Dans ce cas, la liste retournée contient toutes les questions ayant cette catégorie ou n'importe quelle catégorie enfant.

### Participations

- N'importe qui, anonymement, peut sur une page demander à générer un quizz avec, selon le desiderata de la personne, des filtres : 
  - un certain nombre de questions ;
  - des questions limitées à certaines catégories (si non spécifié, prendre toutes les catégories) ;
  - des questions limitées à un certain niveau de difficulté (si spécifié, prendre le niveau de difficulté ou les niveaux inférieurs) ;
  - (évolution) si l'utilisateur est connecté, une option permet de privilégier des questions avec lesquelles iel a mal répondu par le passé.
- Les questions sont sélectionnées aléatoirement selon les critères donnés.
- L'utilisateur se voit posées les questions une à une, sur une page web où il répond directement.
- À la fin du quizz, il lui est proposé une correction sur une page, qui contient sa note globale calculée en fonction des points mentionnés dans la section correspondante, ainsi que pour chaque question :
  - le statut de sa réponse (juste / faux) ;
  - le corrigé ;
  - le texte explicatif détaillé s'il est renseigné.
- (Évolution) Si l'utilisateur est connecté (cf. ci-dessous), la participation est enregistrée dans son compte afin qu'il puisse avoir un historique. Sont notés la note globale ainsi que le score pour chaque question.

### Génération de quizz

- Il est également possible de demander à générer un quizz pour usage papier.
- Le système dispose des mêmes filtres que pour la section ci-dessus.
- Il génère deux fichiers PDF : un fichier contenant les questions, vierges, et un fichier contenant les corrections.
- Les fichiers PDF ont idéalement une en-tête.

## Comptes

### Anonymes

- Ils peuvent passer ou générer des quizz.
- L'historique est sauvegardé (sous la mention « anonyme ») mais seuls les administrateurs peuvent le consulter.

### Utilisateurs

- Les mêmes droits que les anonymes.
- Ils peuvent se connecter en utilisant un compte Google.
- Ils peuvent consulter l'historique de leurs participations.
- Ils peuvent mettre des questions en favoris.
- Ils disposent de deux options en plus sur les filtres :
  - _Privilégier les questions auxquelles j'ai eu du mal auparavant_ ;
  - _Limiter aux questions marquées en favoris_.

### Administrateurs

- Les mêmes droits que les utilisateurs.
- Ils peuvent créer ou modifier des questions.
- Ils peuvent consulter l'historique de participation de tout le monde.

