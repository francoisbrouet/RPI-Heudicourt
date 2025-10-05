<html>
<meta charset="utf-8" />

<head>
<title>Heudicourt</title>
</head>

<body>

<h1>Température</h1>

<p style="margin-bottom: 0cm; line-height: 100%">
<img src="./temptail.png" name="temptail" align="left" width="713" height="535" border="0"/>
</p>

<br>
<a href="index.html">Retour</a>
<br>
<br>

<?php
echo exec ('rm temptail.dat -rf');
echo exec ('tail -196 temperature.dat | tac > temptail.dat');
echo exec ('chgrp webserver temptail.dat');
echo exec ('./temptail.plt');
?>

<table width="400" border="1">
    <tr>
        <td width="150" align="center">Heure</td>
        <td width="60" align="center">salon (°C)</td>
        <td width="60" align="center">cour (°C)</td>
        <td width="60" align="center">cellier (°C)</td>
        <td width="60" align="center">grenier (°C)</td>
        <td width="60" align="center">chaufferie (°C)</td>
        <td width="60" align="center">fioul (0/1)</td>
    </tr>
    
<?php
$file_handle = fopen("temptail.dat", "rb");

while (!feof($file_handle) ) {
    $line_of_text = fgets($file_handle);
    $parts = explode("\t", $line_of_text);
    echo "<tr><td height='30' align='center'>$parts[0]</td><td align='center'>$parts[1]</td><td align='center'>$parts[2]</td><td align='center'>$parts[3]</td><td align='center'>$parts[4]</td><td align='center'>$parts[5]</td><td align='center'>$parts[6]</td></tr>";
}
fclose($file_handle);
?>
</table>

</body>
</html>
