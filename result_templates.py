#!/usr/bin/env python3
# coding: utf-8

start_results="""<!DOCTYPE html>
<html lang="fr">

<head>
  <meta charset="utf-8">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@4.0.0/dist/css/bootstrap.min.css" integrity="sha384-Gn5384xqQ1aoWXA+058RXPxPg6fy4IWvTNh0E263XmFcJlSAwiGgFAW/dAiS6JXm" crossorigin="anonymous">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.2.0/css/all.min.css" integrity="sha512-xh6O/CkQoPOWDdYTDqeRdPCVd1SpvCA9XXcUnZS2FmJNp1coAFzvtCN9BmamE+4aHK8yyUHUSCcJHgXloTyT2A==" crossorigin="anonymous" referrerpolicy="no-referrer" />
    <title>Code is low - Accueil</title>
</head>


<body>
    
        <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
            <a class="navbar-brand" href="/"><h1 style="margin-left:4%">Code is low</h1></a>
            <button class="navbar-toggler" type="button" data-toggle="collapse" data-target="#navbarSupportedContent" aria-controls="navbarSupportedContent" aria-expanded="false" aria-label="Toggle navigation">
              <span class="navbar-toggler-icon"></span>
            </button>
            
            <div class="collapse navbar-collapse" id="navbarSupportedContent">
              <ul class="navbar-nav mr-auto">  
                    <li class="nav_item active">
                    <a class="nav-link" href="/">Accueil</a>
                    </li>
                    <li class="nav_item">
                        <a class="nav-link" href="/cgu">CGU</a>
                    </li>
                    <li class="nav_item">
                        <a class="nav-link" href="/codes">Liste des codes</a>
                    </li>
                    <li class="nav_item">
                        <a class="nav-link" href="/about/">A propos</a>
                    </li>
              </ul>
            </div>
          </nav>
          <div class="main" style="margin-top:2%">
          <div class="container text-center">
            <h2>Resultats de l'analyse </h2>
            <table class="table">
                <thead class="thead-dark">
                  <tr>
                    <th scope="col">Référence <small>(Code - Article)</small></th>
                    <th scope="col">Statut</th>
                    <th scope="col" width="50%">Texte</th>
                    <th scope="col">Période de validité</th>
                </tr>
                </thead>
                <tbody>
"""
end_results="""</tbody>
            </table>
        <a href="/" class="btn btn-primary" role="button">Nouvelle Analyse</a>
        <a href="/" class="btn btn-info disabled"  role="button">Exporter au format csv</a>
        <a href="/" class="btn btn-warning disabled" role="button">Signaler une erreur</a>
        
        
        </div>
        </div>
        <footer style="margin:2%" class="d-flex flex-wrap justify-content-between align-items-center py-3 my-4 border-top">

    <p class="">Un <a href="">programme expérimental</a> par <a href="">E. Netter</a> et <a href="">C. de Quatrebarbes</a></p>
    <p>codeislow[at]email.enetter.fr</p> 
    

    <p>
        Source : <a href="https://www.dila.premier-ministre.gouv.fr/" target="_blank" rel="noopener">DILA</a> - Données <a href="http://legifrance.gouv.fr">Légifrance</a> exploitées en
        temps réel sous <a href="https://www.etalab.gouv.fr/wp-content/uploads/2017/04/ETALAB-Licence-Ouverte-v2.0.pdf" rel="noopener" target="_blank">licence ouverte 2.0</a>   
    </p>
  
        </footer>
    
  
</body>
</html>"""