-- open_project.lua - open the project named by `rpp=` in reaper_job.txt, without a save prompt.
-- Run via:  python reaper_load.py open "C:\path\to\project.rpp"
-- Note: "noprompt:" discards unsaved changes in the currently open project.
local here = ({reaper.get_action_context()})[2]:match("^(.*)[/\\]")
local job = {}
for line in io.lines(here .. "\\reaper_job.txt") do
  local k, v = line:match("^(%w+)=(.*)$")
  if k then job[k] = v end
end
reaper.Main_openProject("noprompt:" .. job.rpp)
