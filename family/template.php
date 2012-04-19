<?php
function head($title, $surname)
{
   $html = "<!DOCTYPE html PUBLIC \"-//W3C//DTD XHTML 1.0 Strict//EN\"
   \"http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd\">
<html>
<head>
<meta http-equiv=\"content-type\" content=\"text/html; charset=UTF-8\" />
<link rel=\"stylesheet\" type=\"text/css\" href=\"basic.css\" />


<title>" . htmlspecialchars($title) . "</title></head>
<body>";

if ($surname != '')
	$html = $html."<p><a href=\"surname-list.php\">Surnames</a> <a href=\"surname.php?surname=".$surname."\">".$surname."</a></p>\n";
else
	$html = $html."<p><a href=\"surname-list.php\">Surnames</a></p>\n";
   return $html;
}

function foot()
{
	//$html = "<p>Copyright 2010 - " . date('Y') . "</p>
	$html = "</body>
	</html>";
   return $html;
} 