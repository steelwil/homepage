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

/*
 Plugin Name: Friend Connect Commenting Plugin
 Description: This plgin allows a user to leave comments using his or her Friend Connect (http://www.google.com/friendconnect/) id to signin. More description can be found in the attached README file
 Version: 1.0
 */

include_once(ABSPATH . 'wp-includes/registration.php');
include_once(ABSPATH . 'wp-includes/user.php');

// The wordpress hooks:
// wp_head is where we put all the javascript and css code
add_action( 'wp_head', 'fc_wp_head');

// The comment form action gets called right after the comment block has been rendered
// and before closing the form
add_action( 'comment_form', 'fc_wp_comment_form');

// This filter takes care of pulling out the avatar image for us to be displayed
// beside the comment. For our plugin, the avatar image is the one that
// is obtained from the FC thumbnailUrl function call (see code below)
add_filter('get_avatar', 'fc_wp_get_avatar', 20, 5);

// Please modify the following function to return a value that
// you obtain after registering your site with FriendConnect
function fc_get_site_id () {
  return '14868846668007632003';
}

// The fc_wp_get_avatar function.
// After wordpress renders each comment, it calls the filter get_avatar
// In this plugin, we have implemented this filter to return the FC url
// location that we have stored in the wp_metadata database table. The
// code to put it into the database is in server_code.php that comes
// with this plugin
// All that we are doing here is to get the email, lookup the userid from
// the user database and then get the image_url from the wp_metadata table
function fc_wp_get_avatar($avatar, $id_or_email, $size, $default, $alt) {
  global $wpdb;
  if (!empty($id_or_email->user_id)) {
    $email = $id_or_email->comment_author_email;
    $query = "SELECT * FROM `wp_users` WHERE user_email = '$email' LIMIT 1;";
    $res = $wpdb->get_col($query);

    // We dont know if this user, so return whatever was given to me
    if (count($res) <= 0)
      return $avatar;
    // Do not change the admin's image
    if ($res[0] == 1)
      return $avatar;

    // Get the image and return the altered $avatar
    $image_url = get_usermeta( $res[0], "image_url");
    return "<img alt='' src='{$image_url}' class='avatar avatar-{$size} photo avatar-default' height='{$size}' width='{$size}' />";
  }
}

// The fc_wp_comment_form function
// This just creates a div tag that will be replaced by the javascript code 
// when the page gets loaded
function fc_wp_comment_form() {
 ?>
   <br>
   <div id="profile">
   </div>
 <?
}

// The fc_javascript_calls functions
// This function is called when the page gets loaded. Specifically,
// it resides in the head.
//
// The primary flow of this function is as follows:
// 
// Request FC for user information
// if (valid user) {
//   Send a request to server_code.php to create/login this user
//   Once request comes back, Modify the HTML to show credentials of new user
//   Show the SignOut link  
// } else {
//   Show the SignIn link
// }
function fc_javascript_calls() {
?>
    <!-- Load the Google AJAX API Loader -->
    <script type="text/javascript" src="http://www.google.com/jsapi"></script>

    <!-- Load the Google Friend Connect javascript library. -->
    <script type="text/javascript">
      google.load('friendconnect', '0.8');
    </script>

    <!-- Initialize the Google Friend Connect OpenSocial API. -->
    <script type="text/javascript">
       var SITE_ID = "<?echo fc_get_site_id(); ?>"
       google.friendconnect.container.setParentUrl('/blog/wordpress/' /* location of rpc_relay.html and canvas.html */);
       google.friendconnect.container.initOpenSocialApi({
       site: SITE_ID,
       onload: function(securityToken) { initAllData(securityToken); }
      });
    </script>
   
    <script type="text/javascript">

    // Send request to FC with request for uesr properties
    function initAllData(securityToken) {
      var req = opensocial.newDataRequest();
      var opt_params = {};
      opt_params[opensocial.DataRequest.PeopleRequestFields.PROFILE_DETAILS] =
        [ opensocial.Person.Field.ID, opensocial.Person.Field.THUMBNAIL_URL,
          opensocial.Person.Field.PROFILE_URL, opensocial.Person.Field.URLS, opensocial.Person.Field.NAME ];
      req.add(req.newFetchPersonRequest('VIEWER', opt_params), 'viewer');
      req.send(setupData);
    };   

    // The password is simply the profileId as of now.
    // Modify this to get a new password scheme
    function getPassword(profilestr) {
      var newString = profilestr.split('&');
      if (newString.length < 1) 
        return profilestr;
      return newString[1];
    }

    function setupData(data) {
      viewer = data.get('viewer').getData();

      if (viewer) {
        // We have a valid user. SetUp the display profile. Everything except the
        // SignOut link as we dont yet want the user to click on it. This is because
        // the user is not yet loged in. Create a div instead so that we can come back
        // and replace it with the SignOut link once the user does get logged in.
        document.getElementById('profile').innerHTML =
          '<img align="left" src="' +  viewer.getField("thumbnailUrl") + '">' +
          '<b>Hello ' +  viewer.getField("displayName") + '!</b><br>' +
          '<a href="#" onclick="google.friendconnect.requestSettings()">Settings</a><br>' +   
          '<a href="#" onclick="google.friendconnect.requestInvite()">Invite</a><br>' +
          '<div id="loadprof"></div>';


        profile_id_url = viewer.getField("profileUrl");
        profileurl = viewer.getField(opensocial.Person.Field.URLS)[0].getField('address');

        // Remove spaces in name
        var nameString = viewer.getField("displayName").split(' ');
        username = nameString.join('');

        // If we are logging in for he first time, create an AJAX
        // request to login/create this user in wp
        if (document.getElementById("author") != null) {
          document.getElementById("loadprof").innerHTML=
            "Loading profile...";

          passwd = getPassword(profile_id_url);
          image_url = viewer.getField("thumbnailUrl");
          CreateRequest(username, passwd, profileurl, profile_id_url, image_url);
        } else {
          // If we are already logged in, simply replace the original
          // html with our custom html
          replaceText();
        }
      } else {
        google.friendconnect.renderSignInButton({ 'id': 'profile' });
      }
    };

    // This function will be called on the completion of the user
    // logging AJAX call
    function loadedProfile() {
      replaceText();
      window.location.reload();
    }

    // Remove the logout button around the comment and add our own logout mechanism.
    // We implement a non-recursive DOM tree traversal as recursion seems to
    // be expensive in javascript
    function replaceText() {
      root = document.getElementById('commentform');
      var nodeArray = new Array();
      var parArray = new(Array);
      nodeArray.push(root);
      parArray.push(root.parentNode);
      while(nodeArray.length > 0) {
        curNode = nodeArray.pop();
        parNode = parArray.pop();
        if (curNode.nodeName == "a" || curNode.nodeName == "A") {
          href_comp = curNode.href.split('wp-login.php');
          if (href_comp.length > 1)
            parNode.removeChild(curNode);
        }
        children = curNode.childNodes;
        for (i = 0; i < children.length; i++) {
          nodeArray.push(children[i]);
          parArray.push(curNode);
        }
      }
      document.getElementById("loadprof").innerHTML=
           '<a href="<?php echo wp_logout_url(get_permalink()); ?>" onClick="google.friendconnect.requestSignOut()"> Sign out</a>';
    }
    
    // The call to the SACK library to send an AJAX request to the 
    // server side for user logging/creation
    function CreateRequest(username, passwd, profileurl, profile_id_url, image_url) {
      var mysack = new sack( 
       "<?php bloginfo( 'wpurl' ); ?>/wp-content/plugins/fc_plugin/server_code.php" );         
      mysack.execute = 1;
      mysack.method = 'POST';
      mysack.setVar( "username", username );
      mysack.setVar( "passwd", passwd );
      mysack.setVar( "profileurl", profileurl);
      mysack.setVar( "profile_id_url", profile_id_url);
      mysack.setVar( "image_url", image_url);
      mysack.onError = function() { alert('Ajax error in user' )};
      mysack.onCompletion = function() { loadedProfile(); };
      mysack.runAJAX();
      return true;
    };
   </script>
<?
}

function fc_wp_head() {
?>
    <style type="text/css">
      body {font-family: Arial, Helvetica, sans-serif; font-weight:normal;}

      h2 {color: #3366CC; font-size: 18px; font-weight: normal}
      h3 {font-size: 13px; font-weight: normal}
      h4 {color: grey; font-size: 11px; font-weight: normal}

      .memberPhoto {
        width: 45px;
        height: 45px;
        padding: 7px;
      }

      .leftbar {
        float:left;
        width: 40%;
        border-right: 1px solid grey;
        padding-right: 50px;
      }

      .rightbar {
        float: left;
        padding-left: 50px;
        width: 40%;
      }

      .main {
        width: 700px;
        margin: auto;
        padding: 5px;
      }

      #profile {
        font-size:13px;
        margin: 20px 40px;
        border: 1px solid blue;
        padding: 15px;
        background-color: #E5ECF9;
      }
      
      #profile_back {
        font-size:13px;
        margin: 20px 40px;
        border: 1px solid grey;
        padding: 15px;
        background-color: #FFFFCC;
      }
      
      #members {
        padding: 0px 80px;
        height: 59px;
      }

      #membersText {
        padding: 0px 87px;
        margin-top: -20px;
      }

      #colorTable {
        width: 100%;
      }

      #colorPicker {
        margin: 20px 40px;
        border: 1px solid grey;
        background-color: #E5ECF9;
      }

      .cell {
        width: 20px;
        height: 20px;
        border: 3px solid #E5ECF9;
      }

      .item {
        padding: 5px;
        font-size: smaller;
      }
    </style>
<?
    wp_print_scripts( array( 'sack' ));
    fc_javascript_calls();
}

?>
