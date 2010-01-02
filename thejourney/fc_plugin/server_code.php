<?

/*
Copyright 2009 Google Inc.
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
 */

if (!function_exists('add_action'))
{
    require_once("../../../wp-config.php");
}

// If there are two users with display names johnsmith, this 
// function can be used to create the usernames johnsmith and 
// johnsmith_904849292483, where the number is the  profileId.
// Modify this when:
// 1. Naming scheme changes for same name users
// 2. If the profileId format changes
function get_prof_key($profile_id_url) {
  $prof_split_first = split("&", $profile_id_url);
  if (count($prof_split_first) < 2) {
    return $profile_id_url;
  }
  $prof_split_second = split("=", $prof_split_first[1]);
  if (count($prof_split_second) < 2) {
    return $prof_split_first[1];
  }
  return $prof = $prof_split_second[1];
}

//
// The Main function
//

if (isset($_POST['username'])) {
  global $wpdb;
  
  // Extract POST into local variables to avoid confusion
  $uname = $_POST['username'];
  $profile_id_url = $_POST['profile_id_url'];
  $profileurl = $_POST['profileurl'];
  $image_url = $_POST['image_url'];
  
  // The usermeta field for each user is of the form:
  // userid    meta_key    meta_value
  // where
  //    userid is the key into the users database
  //    meta_key is of the form: <name>_fc_meta_key
  //    meta_value is the profileId
  // Thus, two users with displayname johnsmith will have the 
  // same meta_key but different meta_value
  $meta_key = $uname."_fc_meta_key";
  
  // Check if a user with this profileId and meta_key exists
  $metas = $wpdb->get_col( $wpdb->prepare("SELECT user_id FROM $wpdb->usermeta WHERE meta_key = '$meta_key' AND meta_value='$profile_id_url';") );   
  
  if (count($metas) > 0) {
    // We found me
    $userid = $metas[0];
  } else {
    // Since this user is not available, we'll create him.
    // First check if a user with the same name is present
    $basev = $wpdb->get_col( $wpdb->prepare("SELECT user_id FROM $wpdb->usermeta WHERE meta_key = '$meta_key';") );
    if (count($basev) > 0) {
      // If yes, create a unique key. See commments for get_prof_key above
      $prof = get_prof_key($profile_id_url);
      $uname = $uname."_".$prof;
    }
    $userid = wp_create_user($uname, $_POST['passwd'], $uname."@friendconnect.google.com"); 
    update_usermeta($userid, $meta_key, $profile_id_url);
  }
  // Log me in
  update_usermeta($userid, "user_url", $profileurl);
  update_usermeta($userid, "image_url", $image_url);
  $cred['user_login'] = $uname;
  $cred['user_password'] = $_POST['passwd'];
  wp_signon($cred);
}
die('200');

?>
