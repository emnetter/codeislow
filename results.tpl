<!DOCTYPE html>
<html lang=fr>
<head>
 <link rel="stylesheet" href="w3.css"> 
</head>
<body>

	<body>
	<div class="w3-panel w3-red">
		<h3> Textes non trouvés sur Légifrance </h1>
	</div>
			<ul>
			% for result in articles_not_found:
             <li>{{result}}</li>
          % end
			</ul>
	<div class="w3-panel w3-yellow">
		<h3> Textes modifiés il y a moins de {{user_past}} an(s) </h1>
	</div>
			<ul>
			% for result in articles_recently_modified:
             <li>{{result}}</li>
          % end
			</ul>
	<div class="w3-panel w3-yellow">
		<h3> Textes dont la version actuelle expire dans moins de {{user_future}} an(s) </h1>
	</div>
			<ul>
			% for result in articles_changing_soon:
             <li>{{result}}</li>
          % end
			</ul>
	<div class="w3-panel w3-green">
		<h3> Textes détectés mais rien à signaler </h1>
	</div>
			<ul>
			% for result in articles_without_event:
             <li>{{result}}</li>
          % end
			</ul>