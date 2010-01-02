<?

// set the time interval between imports. this is the number
// of seconds between imports. example: one day = (60*60*24),
// two days would be (60*60*24*2), etc. ARI will run only once
// every [interval].

$interval = (60*60*24);


// define rss feeds by specifying the url, kwords, status,
// link_text, category, and max_imports for each feed. kwords 
// should be seperated by spaces (no phrases). if kwords is
// set to empty then all feeds will be imported. link_text is
// the text to appear in the link added to the end of each
// item's content, leave empty for no link. category should be
// the category ID number under which to place the item. status
// is 'publish', 'draft', 'private', 'static', 'object', or
// 'attachment'. max_imports is the maximum number of items
// to import from that specific feed (per import session).
// remember to remove the comma after the last array in the
// list.

$rss_feeds = array(
                   array(
                         'url'		=> 'http://rss.slashdot.org/Slashdot/slashdot',
                         'kwords'	=> 'to',
                         'status'	=> 'publish',
                         'link_text'	=> 'Full Article',
                         'category'	=> 2,
                         'max_imports'	=> 3
                        )
                  );


// define maximum items imported overall. overrides the per feed
// maximums. this is necessary because each feed may or may not
// provide its [max_imports] of items matching [kwords].

$max_imports = 7;


// url to site directory. this is the url to the directory that
// contains all of your wordpress directories. another way to explain
// it, is the url to your wordpress site without the 'index.php'.
// for most sites it's simply 'http://www.yourdomain.com/' where
// 'yourdomain' would be ahh... your domain, lol. remember to
// include the trailing slash.

$site_url = 'http://www.your_domain_name.com/'; // ends with a slash '/'


// define the database host. this will almost always be 'localhost'.

$db_host = 'localhost';


// define the database name

$db_name = 'your_database_name';


// define the database username

$db_user = 'your_database_username';


// define the database password

$db_pass = 'your_database_password';


// define the database prefix. the default is 'wp_'.

$db_prefix = 'wp_';


// username of author. this user will show as the author of each
// item imported. be sure to enter the 'Username' of the author.

$username = 'admin';


// email address to which summary should be sent. this summary will 
// include the total number of items imported, the execution time of 
// the import script, the titles of each imported item, and any 
// errors that may have occurred. no summary will be sent if empty.

$email_summary = 'your_email_address';


?>
