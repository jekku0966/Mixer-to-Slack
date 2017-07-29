# Mixer-to-Slack

Also known as Twitch to Slack and XBLStatusbot. This combines Mixer streams, Twitch streams and Xbox Live Status checker in one.
Configure the `defaultconfig.py` and rename it to `botconfig.py`and you're good to go.

# MySQL databases and columns

I've used `usernames` for stream usernames and `online` to check online status. The `online` column is a `TINYINT` type.

# Checking the actual Stream status

I suggest using `cron` to fire the `stream_checker.py` so the server which runs the other commands is unaffected.

# Other

Functionality is the same as the older version and the output is the same as the older ones.
