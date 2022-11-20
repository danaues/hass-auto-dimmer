## To Do List

- Add 2nd check after 5 or 10 seconds to verify if we should change
- Add detection tolerance as a variable (currently set to 2)
- Configure brightness as % in config_flow, and convert to lumens (0-255)
- clean up validation of config flow and schema (remove the loop and just specify?)
- simplify if statement in auto_dimmer asnc_update
- find out how to properly dismantle async_track_time_interval() and async_track_state_change()