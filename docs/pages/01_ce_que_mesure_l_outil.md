# Ce que mesure l'outil
Météo et Chaleur analyse des fichiers météo horaires sous l'angle de l'inconfort d'été.

Important : les degrés-heures (DH) sont calculés sur la température fichier, prise comme si c'était la température intérieure. L'outil est fait, en base, pour des fichiers de températures extérieures (fichiers météo) : c'est alors un indicateur de sévérité du climat, pas le DH d'un bâtiment. Il peut aussi s'utiliser avec n'importe quel fichier horaire, y compris des températures intérieures issues d'une simulation.

Le réglage par défaut suit la méthode RE2020 (arrêté du 4 août 2021, annexe III, méthode Th-BCE 2020).

L'onglet Exporter copie les indicateurs (pour un mail, Word ou Excel) ou télécharge un fichier CSV ou Excel : indicateurs et 8 760 heures (température, seuil et DH), pour le fichier en cours ou avec le second fichier de l'onglet Comparer. Le réglage, la version et les sources sont inscrits dans le fichier.
