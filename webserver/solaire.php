<!DOCTYPE html>
<html>

<head>
    <title>Shelly Power Graph</title>
</head>

<br>
<a href="index.html">Retour</a>
<br>
<br>

<?php
echo exec ('chmod 0775 logdata.db');
echo exec ('rm solaire_graph.png -rf');
echo exec ('./webserver_plot.sh');
echo exec ('chmod 0775 solaire_graph.png');
?>

<body>
    <h1>Consommation Heudicourt</h1>
    <img src="solaire_graph.png?<?php echo time(); ?>" alt="">
</body>

</html>

