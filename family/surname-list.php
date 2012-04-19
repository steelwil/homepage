<?php
  require_once 'template.php';
  echo head('Surnames', '');
  try
  {
    //open the database
    $db = new PDO('sqlite:../../.sqlite/gramps.db');

    //now output the data to a simple html table...

    $result = $db->query('SELECT surname, count(1) as Number from name group by surname');
    foreach($result as $row)
    {
		print("<p><span class=\"name\"><a href=\"surname.php?surname=".$row['surname']."\">".$row['surname']."</a></span> <span class=\"value\">".$row['Number']."</span></p>\n");
    }

    // close the database connection
    $db = NULL;
  }
  catch(PDOException $e)
  {
    print 'Exception : '.$e->getMessage();
  }
  echo foot();
?>