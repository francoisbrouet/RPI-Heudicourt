<!DOCTYPE html>
<html>

<head>
    <title>Shelly Power Graph</title>
</head>

<br>
<a href="index.html">Retour</a>
<br>
<br>
¬
<body>
    <h1>Consommation Heudicourt</h1>
    <img src="./solaire_graph.png?<?php echo time(); ?>" alt="">
</body>

<?php
$lines = file("./solaire_print.txt");
echo '<pre style="font-family: monospace; font-size: 13px;">';
echo htmlspecialchars(file_get_contents("./solaire_print.txt"));
echo '</pre>';
?>

</html>
