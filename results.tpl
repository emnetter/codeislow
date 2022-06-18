<html lang="fr">
	<body>
		<h3 style="color:red"> Textes non trouvés sur Légifrance </h1>
			<ul>
			% for result in articles_not_found:
             <li>{{result}}</li>
          % end
			</ul>

		<h3 style="color:orangered"> Textes modifiés il y a moins de {{user_past}} an(s) </h1>
			<ul>
			% for result in articles_recently_modified:
             <li>{{result}}</li>
          % end
			</ul>

		<h3 style="color:orangered"> Textes dont la version actuelle expire dans moins de {{user_future}} an(s) </h1>
			<ul>
			% for result in articles_changing_soon:
             <li>{{result}}</li>
          % end
			</ul>

		<h3 style="color:green"> Textes détectés mais rien à signaler </h1>
			<ul>
			% for result in articles_without_event:
             <li>{{result}}</li>
          % end
			</ul>