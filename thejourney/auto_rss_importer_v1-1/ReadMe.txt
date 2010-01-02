
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
 * Terms:	This program is released under the
 *		GPL (http://www.gnu.org/copyleft/gpl.html). It 
 *		comes 'as is' with no guarantees, stated or implied.
 *		All that I ask is that you give me credit when using
 *		all or parts of my code in other projects.
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
 *
 * Install:	This is very easy, so don't overcomplicate it.
 *		Note that this script does require WordPress 2.0 or higher.
 *		
 *		1. Extract the zip or tar.gz archive to a local folder
 *		
 *		2. Edit /wp-ari/ari-config.php -- Each variable is
 *		   explained extensively in this file, it is pretty
 *		   straight-forward. This is where you specify your
 *		   database login info., rss feeds, etc.
 *		
 *		3. Upload the /wp-ari directory to your WordPress
 *		   folder on your server. It's the folder that has
 *		   your /wp-admin, and /wp-content directories in it.
 *		
 *		4. Now just edit your wordpress 'index.php' file as follows:
 *
 *		/* Auto RSS Importer */
 *		include('wp-ari/index.php');
 *		/* Short and sweet */
 *		define('WP_USE_THEMES', true);
 *		require('./wp-blog-header.php');
 *
 * TroubleSho	Make sure that /wp-ari/ari-timestamp.php is chmod 777.
 *		If it's not, you'll see a 'timestamp is not writable'
 *		error in your summary email.
 */

