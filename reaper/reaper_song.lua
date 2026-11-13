-- reaper_song.lua - load a show song into the OPEN Reaper project and SAVE it.
-- Run via:  python reaper_load.py load --wav ... --markers ... --expect <project name>
-- (the Python wrapper refuses to run unless the expected project is the one open).
-- Load a show song into the open Reaper project.  Reads its job from reaper_job.txt (key=value):
--   wav=<path>  track=<track name>  take=<take name>  markers=<markers.txt>  log=<log file>
-- Removes old markers, (re)uses track named `track` (or the old "Show Audio - *" track),
-- puts the wav at 0, mutes leftover demo tracks, adds markers, saves the project.
local here = ({reaper.get_action_context()})[2]:match("^(.*)[/\\]")
local job = {}
for line in io.lines(here .. "\\reaper_job.txt") do
  local k, v = line:match("^(%w+)=(.*)$")
  if k then job[k] = v end
end
local log = io.open(job.log, "w")

reaper.Undo_BeginBlock()
local _, nm, nr = reaper.CountProjectMarkers(0)
for i = nm + nr - 1, 0, -1 do
  local _, isrgn = reaper.EnumProjectMarkers(i)
  if not isrgn then reaper.DeleteProjectMarkerByIndex(0, i) end
end

local tr = nil
for i = 0, reaper.CountTracks(0) - 1 do
  local t = reaper.GetTrack(0, i)
  local _, n = reaper.GetTrackName(t)
  if n == job.track or n:find("^Show Audio") then tr = t end
end
if not tr then
  reaper.InsertTrackAtIndex(1, true)
  tr = reaper.GetTrack(0, 1)
end
reaper.GetSetMediaTrackInfo_String(tr, "P_NAME", job.track, true)
reaper.SetMediaTrackInfo_Value(tr, "B_MUTE", 0)
for i = reaper.CountTrackMediaItems(tr) - 1, 0, -1 do
  reaper.DeleteTrackMediaItem(tr, reaper.GetTrackMediaItem(tr, i))
end
local item = reaper.AddMediaItemToTrack(tr)
local take = reaper.AddTakeToMediaItem(item)
local src = reaper.PCM_Source_CreateFromFile(job.wav)
reaper.SetMediaItemTake_Source(take, src)
local len = reaper.GetMediaSourceLength(src)
reaper.SetMediaItemInfo_Value(item, "D_POSITION", 0)
reaper.SetMediaItemInfo_Value(item, "D_LENGTH", len)
reaper.GetSetMediaItemTakeInfo_String(take, "P_NAME", job.take, true)
log:write("audio length ", len, "\n")

for i = 0, reaper.CountTracks(0) - 1 do
  local t = reaper.GetTrack(0, i)
  local _, n = reaper.GetTrackName(t)
  if n:find("10 Second Timer") or n:find("CM Punk") then reaper.SetMediaTrackInfo_Value(t, "B_MUTE", 1) end
end

local f = io.open(job.markers, "r")
if f then
  local n = 1
  for line in f:lines() do
    local t, name = line:match("^([%d%.]+)\t(.*)$")
    if t then reaper.AddProjectMarker2(0, false, tonumber(t), 0, name, n, 0); n = n + 1 end
  end
  f:close()
  log:write("markers ", n - 1, "\n")
end
reaper.SetEditCurPos(0, true, false)
reaper.Undo_EndBlock("Load show audio + markers", -1)
reaper.UpdateArrange()
reaper.Main_SaveProject(0, false)
log:write("saved\n")
log:close()

