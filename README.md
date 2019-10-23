# Spotify Argos Extension
For use with [p-e-w/argos](https://github.com/p-e-w/argos). Provides current song, artist and playback status in the taskbar and more detailed information with playback controls and album art in the dropdown.

# Set up
To use this argos extension, simply pull down the git repository somewhere safe and either make a symlink to the argos directory or copy the script over.

# Requirements
The following Python library is needed. To quickly install, a requirements.txt file has been provided. With it you can run `pip install -r requirements.txt` to get the necessary libraries. 


* [pydbus](https://pypi.org/project/pydbus/)
* [requests](https://pypi.org/project/requests/)
* [pycairo](https://pypi.org/project/pycairo/)
* [PyGObject](https://pypi.org/project/PyGObject/)

# Screenshots
![Taskbar](images/taskbar.png?raw=true)

![Menu Open](images/menu_open.png?raw=true)

# #TODO
* Implement cool Spotify features using their API
  * Like button
  * Shuffle
* Make the album art a clickable button to maximize the Spotify window.
* Add virtualenv generation to the requirements script and have the plugin run from it.