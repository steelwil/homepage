<?php
  require_once 'template.php';
  echo head('Surname', '');
  try
  {
  	$surname = $_GET["surname"];
    //open the database
    $db = new PDO('sqlite:../../.sqlite/gramps.db');

    //get all names with a specific surname
    $result = $db->query(
	    "select
			P.gid as gid, 
			P.gender as gender,
			first_name,
			max(D.year1) as year1,
			max(D.month1) as month1,
			max(D.day1) as day1,
			max(D.quality) as quality
		from name N
		inner join person P
			on P.gid = N.gid
		left join event_ref ER
			on ER.gid = P.gid
		left join event E
			on ER.event_gid = E.gid
				and E.the_type0 = 12
		left join date D
			on D.gid = E.gid
		where N.surname = '".$surname."'
		group by P.gid, first_name
		order by first_name");
    foreach($result as $row)
    {
    	$gid = $row['gid'];
    	$descrip = '';
    	if ($row['quality'] == 1)
    		$descrip = "estimated ";
    	else 
    		$descrip = "";
    	$descrip = $descrip.$row['year1'];
    	if ($descrip == '')
    		$descrip = "&nbsp;";
    	$first_name = $row['first_name'];
    	$gender = $row['gender'];
    	if ($first_name == '')
    	{
    		if ($gender == 0)
    			$first_name = "Unknown Female";
    		elseif ($gender == 1)
    			$first_name = "Unknown Male";
    		else
				$first_name = "Unknown";
		}
		print("<p><span class=\"name\"><a href=\"person.php?gid=".$gid."\">".$first_name."</a></span> <span class=\"value\">".$descrip."</span></p>\n");
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