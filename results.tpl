<!DOCTYPE html>
<html lang=fr>
<head>
    <script> document.body.innerHTML = "" </script>
    <link rel="stylesheet" href="https://www.w3schools.com/w3css/4/w3.css">
</head>
<body>
<div class="w3-container w3-blue-grey">
    <h1> Code is low</h1>
</div>
<p class="w3-margin"> Cliquez sur les numéros d'articles pour les ouvrir directement dans Légifrance et accéder à davantage d'informations (hors textes non trouvés).</p>
	<div class="w3-panel w3-red">
		<h3> Textes non trouvés sur Légifrance </h3>
	</div>
			<ul class="w3-ul w3-border">
			% for result in articles_not_found:
             <li>{{!result}}</li>
          % end
			</ul>
	<div class="w3-panel w3-yellow">
		<h3> Textes modifiés il y a moins de {{user_past}} an(s) </h3>
	</div>
			<ul class="w3-ul w3-border">
			% for result in articles_recently_modified:
             <li>{{!result}}</li>
          % end
			</ul>
	<div class="w3-panel w3-yellow">
		<h3> Textes dont la version actuelle expire dans moins de {{user_future}} an(s) </h3>
	</div>
			<ul class="w3-ul w3-border">
			% for result in articles_changing_soon:
             <li>{{!result}}</li>
          % end
			</ul>
	<div class="w3-panel w3-green">
		<h3> Textes détectés mais rien à signaler </h3>
	</div>
			<ul class="w3-ul w3-border">
			% for result in articles_without_event:
             <li>{{!result}}</li>
          % end
			</ul>
</body>