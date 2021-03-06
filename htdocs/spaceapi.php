<?php
$status = substr(file_get_contents("../current_status"),0,1);

// Send header
header('Access-Control-Allow-Origin: *');
header('Cache-Control: no-cache, must-revalidate');
header('Expires: Mon, 19 Jul 1997 00:00:00 GMT');
header('Content-type: application/json; charset=utf-8');

// Fill data
$data = array(
	"api" => "0.13",
	"space" => "Munich Maker Lab",
	"logo" => "https://wiki.munichmakerlab.de/images/mumalab.png",
	"url" => "https://munichmakerlab.de/",
	"location" => array(
		"address" => "Dachauer Str. 112h, 80636 München, Germany",
		"lon" => 11.5482333,
		"lat" => 48.158752
	),
	"spacefed" => array(
		"spacenet" => false,
		"spacesaml" => false,
		"spacephone" => false
	),
	"contact" => array(
		"email" => "info@munichmakerlab.de",
		"irc" => "irc://irc.hackint.eu/munichmakerlab",
		"ml" => "discuss@munichmakerlab.de",
		"twitter" => "@munichmakerlab",
		"phone" => "+498921553954",
		"issue_mail" =>  base64_encode("spaceapi@tiefpunkt.com")
	),
	"issue_report_channels" => array("issue_mail"),
	"feeds" => array(
		"log" => array(
			"type" => "application/rss+xml",
			"url" => "http://log.munichmakerlab.de/rss"
		),
		"calendar" => array(
			"type" => "text/calendar",
			"url" => "https://calendar.google.com/calendar/ical/lbd0aa2rlahecp7juvp35hd0k0%40group.calendar.google.com/public/basic.ics"
		)
	),
	"cache" => array( "schedule" => "m.02" ),
	"state" => array(
		"open" => ($status == 1)
	),
	"projects" => array(
		"https://github.com/munichmakerlab",
		"https://munichmakerlab.de/wiki/Category:Project"
	)
);

echo json_encode($data);

?>
