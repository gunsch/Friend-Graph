<?php

include("config.php");

$config = array();
$config[‘appId’] = $api_key
$config[‘secret’] = $app_secret;
$config[‘fileUpload’] = false; // optional

$facebook = new Facebook($config);

?>
