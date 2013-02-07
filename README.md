# Overview
This is a small utility I wrote after I realized that my digital assets (mostly pictures, of which I have plenty) are not being tracked properly. We constantly move between photo organizers, tagging apps, cloud services, virtual mounts, backup solutions and folder layouts, and over the past two years I encountered several cases where one or more digital asset suddenly turned out missing. 

I back up my data all of the time, and even have an online backup service. The problem is I don't know if and when I need to activate it. There are thousands of photos in my collection, and it's not really possible to know when and if you delete one of them accidentally.

# Usage
Write the following in ~/.asset_tracker/config:

	# this is useful for locally stored assets
    tracker.add_source(LocalSource("/path/to/your/local/collection"))
	# we also support remote (over ssh) collections
	tracker.add_source(RemoteSource("my.ssh.machine.name", "/path/on/machine"))
	
To scan your collection, run:

	assets scan
	
# License
BSD
