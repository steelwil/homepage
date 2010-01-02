<?

/*
 * Project:	Auto RSS Importer (for WordPress >= 2.0)
 *
 * Written by:	Anthony Colacchio
 * Support:	http://www.crwebtools.com/auto_rss_importer.php
 * Date: 	11-11-06
 * Version	1.1
 *
 * Release:	- Fixed bug that ignored per feed maximum
 *
 * Terms:	This and associated scripts are released under the
 *		GPL (http://www.gnu.org/copyleft/gpl.html). All that
 *		I ask is that you give me credit when using all or
 *		parts of my code in other projects.
 *
 * Description:	This script (along with 'ari-config.php') will import
 *		items from various RSS feeds containing specified
 *		keywords into WordPress entries at a specified time
 *		interval automatically when included at the top of
 *		your wordpress 'index.php' as detailed in 'readme.txt'.
 *
 * Summary:	In short, set it up once and it will keep your WordPress
 *		site updated with fresh content.
 *
 * Notes:	Most of the RSS parsing code is based on the original
 *		WordPress RSS import code. Those WordPress guys/girls
 *		have written a great application (http://wordpress.org)
 */

class Auto_RSS_Importer {

   var $interval;
   var $rss_feeds;
   var $max_imports;
   var $author_id;
   var $site_url;
   var $db_host;
   var $db_name;
   var $db_user;
   var $db_pass;
   var $db_prefix;
   var $email_summary;
   var $items;
   var $start_time;
   var $conn;


   function Auto_RSS_Importer() {

      $this->start_time = explode( ' ', microtime() );
      $this->start_time = $this->start_time[1] + $this->start_time[0];

      include(dirname(__FILE__).'/ari-config.php');

      $this->interval = $interval;
      $this->rss_feeds = $rss_feeds;
      $this->max_imports = $max_imports;
      $this->site_url = $site_url;
      $this->db_host = $db_host;
      $this->db_name = $db_name;
      $this->db_user = $db_user;
      $this->db_pass = $db_pass;
      $this->db_prefix = $db_prefix;
      $this->email_summary = $email_summary;
      $this->author_id = $this->get_user_id($username);

      if( $this->interval_reached() )
         $this->fetch_rss_feeds();

   }


   function connect_to_mysql() {

      if(!$this->conn) {

         if($this->conn = @mysql_connect($this->db_host, $this->db_user, $this->db_pass)) {

            if(!@mysql_select_db($this->db_name)) {

               $this->send_summary('Failed to select database');

            }

         } else {

            $this->send_summary('Failed to connect to mysql');

         }

      }

   }


   function get_user_id($username) {

      $this->connect_to_mysql();

      $query = "SELECT 
                 ID 
                FROM 
                 ".$this->db_prefix."users 
                WHERE 
                 user_login = '".$username."'";

      $result = mysql_query($query);

      if( !mysql_num_rows($result) )
         $this->send_summary('Specified username not found');

      $arr = mysql_fetch_array($result, MYSQL_NUM);

      return $arr[0];

   }


   function interval_reached() {

      $tspath = dirname(__FILE__).'/ari-timestamp.php';

      $tsfile = file($tspath); // load timestamp from last import

      if( (date('U') - $tsfile[0]) > $this->interval) { // if interval reached

         if( is_writable($tspath) ) {

            $fh = fopen($tspath, 'w');
            fwrite($fh, date('U') ); // save new timestamp
            fclose($fh);

         } else {

            $this->send_summary("Timestamp file (".$tspath.") is not writable");

         }

         return TRUE;

      }

      return FALSE;

   }


   function fetch_rss_feeds() {

      for($x=0; $x<count($this->rss_feeds); $x++) {

         $this->extract_items($this->rss_feeds[$x]); // extract qualified items from feed

         if( count($this->items) >= $this->max_imports) { // if max_imports reached or exceeded

            $this->items = array_slice($this->items, 0, $this->max_imports); // reduce to max_imports
            break; // don't fetch anymore feeds

         }

      }

      $this->import_items(); // import extract items

   }


   function decode_htmlchars($text) {

       return strtr($text, array_flip(get_html_translation_table(HTML_SPECIALCHARS)));

   }


   function clean_value($val) {

      return addslashes(strip_tags($this->decode_htmlchars($val), '<!>')); // improve this

   }


   function extract_items($feed) {

      $importdata = file_get_contents($feed['url']);      $importdata = str_replace(array("\r\n", "\r"), "\n", $importdata);

      preg_match_all('|<item[^>]*>(.*?)</item>|is', $importdata, $rawitems);
      $rawitems = $rawitems[1];

      $feed_import_count = 0;

      foreach($rawitems as $rawitem) {

         $item = array();

         preg_match('|<title[^>]*>(.*?)</title>|is', $rawitem, $item_title);
         $item['title'] = $this->clean_value($item_title[1]); // set item title

         preg_match('|<pubdate[^>]*>(.*?)</pubdate>|is', $rawitem, $item_date);

         if ($item_date) {
            $item_date = strtotime($item_date[1]);
         } else {
            // if we don't already have something from pubDate
            preg_match('|<dc:date>(.*?)</dc:date>|is', $rawitem, $item_date);
            $item_date = preg_replace('|([-+])([0-9]+):([0-9]+)$|', '\1\2\3', $item_date[1]);
            $item_date = str_replace('T', ' ', $item_date);
            $item_date = strtotime($item_date);
         }

         $item['date'] = gmdate('Y-m-d H:i:s', $item_date); // set item date

         preg_match('|<guid.+?>(.*?)</guid>|is', $rawitem, $link);
         if ( ereg('http://', $link[1]) ) {
            $link = $this->clean_value($link[1]);
         } else {
            // This is for feeds that put the link in 'link'
            preg_match('|<link[^>]*>(.*?)</link>|is', $rawitem, $link);
            $link = $this->clean_value($link[1]);
         }
         $item['link'] = $link; // set item link

         preg_match('|<content:encoded>(.*?)</content:encoded>|is', $rawitem, $item_content);
         $item_content = str_replace(array ('<![CDATA[', ']]>'), '', $this->clean_value($item_content[1]) );

         if (!$item_content) {
            // This is for feeds that put content in description
            preg_match('|<description[^>]*>(.*?)</description>|is', $rawitem, $item_content);
            $item_content = $this->clean_value($item_content[1]);
         }

         // Clean up content
         $item_content = preg_replace('|<(/?[A-Z]+)|e', "'<' . strtolower('$1')", $item_content);
         $item_content = str_replace('<br>', '<br />', $item_content);
         $item_content = str_replace('<hr>', '<hr />', $item_content);
         $item['content'] = $item_content; // set item content

         // Add link to content
         if ($feed['link_text'])
            $item['content'] .= '<br /><br /><a href="'.$item['link'].'" target="_blank">'.$feed['link_text'].'</a>';

         // Additional specs
         $item['status'] = $feed['status'];
         $item['category'] = $feed['category'];

         // Does item contain keywords?
         $iwords = explode(' ', strtolower($item['title']).' '.strtolower($item['content']) );
         $kwords = explode(' ', strtolower($feed['kwords']) );
         if( !$feed['kwords'] || array_intersect($iwords, $kwords) ) {

            if( !$this->item_exists($item['title']) ) { // if not already imported

               $this->items[] = $item; // add item to be imported

               ++$feed_import_count;

            }

         }

         if($feed_import_count >= $feed['max_imports']) // don't exceed this feeds max_imports
            break;

      }

   }


   function item_exists($title) {

      $this->connect_to_mysql();

      $query = "SELECT 
                 ID 
                FROM 
                 ".$this->db_prefix."posts 
                WHERE 
                 post_title = '".$title."'";

      $result = mysql_query($query);

      if( mysql_num_rows($result) )
         return TRUE;

      return FALSE;

   }


   function import_items() {

      $this->connect_to_mysql();

      for($x=0; $x<count($this->items); $x++) {

         $item = $this->items[$x];
         $item['name'] = preg_replace(
                                      array("![^a-zA-Z0-9]!", "!\s!"),
                                      array('', '+'),
                                      strtolower($item['title'])
                                     );

         $query = "INSERT INTO 
                  ".$this->db_prefix."posts 
                   (
                    post_author,
                    post_date,
                    post_date_gmt,
                    post_content,
                    post_title,
                    post_category,
                    post_excerpt,
                    post_status,
                    comment_status,
                    ping_status,
                    post_password,
                    post_name,
                    to_ping,
                    pinged,
                    post_modified,
                    post_modified_gmt,
                    post_content_filtered,
                    post_parent,
                    guid,
                    menu_order,
                    post_type,
                    post_mime_type,
                    comment_count
                   )
                   VALUES
                   (
                    '".$this->author_id."',
                    '".$item['date']."',
                    '".$item['date']."',
                    '".$item['content']."',
                    '".$item['title']."',
                    '0',
                    '',
                    '".$item['status']."',
                    'open',
                    'open',
                    '',
                    '".$item['name']."',
                    '',
                    '',
                    '".$item['date']."',
                    '".$item['date']."',
                    '',
                    '0',
                    CONCAT('".$this->site_url.'?p='."',ID),
                    '0',
                    '',
                    '',
                    '0'
                   )";

         $result = @mysql_query($query);

         if(!$result)
            $this->send_summary("Failed to import '".$item['title']."'");

         $post_id = mysql_insert_id();

         $query = "INSERT INTO 
                  ".$this->db_prefix."post2cat 
                   (
                    post_id,
                    category_id
                   )
                   VALUES
                   (
                    '".$post_id."',
                    '".$item['category']."'
                   )";

         $result = mysql_query($query);

         if(!$result)
            $this->send_summary("Failed to create post2cat for '".$item['title']."'");

      }

      $this->send_summary();

   }


   function send_summary($err=FALSE) {

      if($this->email_summary) {

         $end_time = explode( ' ', microtime() );
         $end_time = $end_time[1] + $end_time[0];
         $duration = ( $end_time - $this->start_time );

         $email  = "Imported ".count($this->items)." items successfully "; 
         $email .= "in ".$duration." seconds.\n\n";

         if($err)
            $email .= "ERROR: ".$err."\n\n";

         if($this->items)
            $email .= "Item Titles:\n";

         for($x=0; $x<count($this->items); $x++) {

            $email .= $this->items[$x]['title']."\n";

         }

         mail(
              $this->email_summary,
              'Import Summary for '.$_SERVER['HTTP_HOST'],
              $email,
              "From: ari_script@".$_SERVER['HTTP_HOST']."\n"
             );

      }

      if($err)
         exit(0);

   }

}

$ari = new Auto_RSS_Importer();

?>
