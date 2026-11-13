-- play.lua - start Reaper playback from 0:00.  (python reaper_load.py play)
reaper.SetEditCurPos(0, false, false); reaper.OnPlayButton()
