# -*- coding: utf-8 -*-

import logging
import os
from colorama import Fore
from TwitchChannelPointsMiner import TwitchChannelPointsMiner
from TwitchChannelPointsMiner.logger import LoggerSettings, ColorPalette
from TwitchChannelPointsMiner.classes.Chat import ChatPresence
from TwitchChannelPointsMiner.classes.Discord import Discord
from TwitchChannelPointsMiner.classes.Telegram import Telegram
from TwitchChannelPointsMiner.classes.Settings import Priority, Events, FollowersOrder
from TwitchChannelPointsMiner.classes.entities.Bet import Strategy, BetSettings, Condition, OutcomeKeys, FilterCondition, DelayMode
from TwitchChannelPointsMiner.classes.entities.Streamer import Streamer, StreamerSettings
from twitchAPI import Twitch  # You might need this to interact with the Twitch API

# Set up Twitch API client (example setup, replace with your client ID and secret)
twitch = Twitch(client_id='your-client-id', client_secret='your-client-secret')

# Function to get streamer's current game
def get_streamer_game(streamer_username):
    user = twitch.get_users(logins=[streamer_username])
    user_id = user['data'][0]['id']
    stream = twitch.get_streams(user_ids=[user_id])
    if stream['data']:
        return stream['data'][0]['game_name']
    return None

# Function to check if a streamer is live and playing Rust
def is_streamer_live_and_playing_rust(streamer_username):
    game_name = get_streamer_game(streamer_username)
    return game_name and game_name.lower() == "rust"

# Function to prompt for a username and list of streamers from a file
def get_username_and_streamers():
    username = input("Enter your Twitch username: ")
    file_path = input("Enter the path to the file containing streamers' usernames: ")

    # Read the list of streamers from the file
    if not os.path.exists(file_path):
        print("Error: The file path does not exist.")
        return None, None

    with open(file_path, 'r') as file:
        streamers = [line.strip() for line in file.readlines()]
    
    return username, streamers

# Main Twitch Channel Points Miner setup
def setup_twitch_miner(username):
    return TwitchChannelPointsMiner(
        username=username,
        password="write-your-secure-psw",  # If no password provided, ask interactively
        claim_drops_startup=False,
        priority=[Priority.STREAK, Priority.DROPS, Priority.ORDER],  # Custom priority
        logger_settings=LoggerSettings(
            save=True,
            console_level=logging.INFO,
            file_level=logging.DEBUG,
            emoji=True,
            less=False,
            colored=True,
            color_palette=ColorPalette(
                STREAMER_online="GREEN",
                streamer_offline="RED",
                BET_wiN=Fore.MAGENTA
            ),
            telegram=Telegram(
                chat_id=123456789,
                token="your-telegram-bot-token",
                events=[Events.STREAMER_ONLINE, Events.STREAMER_OFFLINE, "BET_LOSE"]
            ),
            discord=Discord(
                webhook_api="https://discord.com/api/webhooks/your-webhook-url",
                events=[Events.STREAMER_ONLINE, Events.STREAMER_OFFLINE, Events.BET_LOSE]
            )
        ),
        streamer_settings=StreamerSettings(
            make_predictions=True,
            follow_raid=True,
            claim_drops=True,
            watch_streak=True,
            chat=ChatPresence.ONLINE,
            bet=BetSettings(
                strategy=Strategy.SMART,
                percentage=5,
                percentage_gap=20,
                max_points=50000,
                stealth_mode=True,
                delay_mode=DelayMode.FROM_END,
                delay=6,
                minimum_points=20000,
                filter_condition=FilterCondition(
                    by=OutcomeKeys.TOTAL_USERS,
                    where=Condition.LTE,
                    value=800
                )
            )
        )
    )

# Watch streamers until a drop is awarded, then move to another eligible streamer
def watch_for_drops_and_switch(twitch_miner, streamers):
    for streamer_username in streamers:
        if is_streamer_live_and_playing_rust(streamer_username):
            print(f"Watching {streamer_username} who is live and playing Rust!")
            
            # Create Streamer instance and add it to the miner
            streamer = Streamer(streamer_username, settings=StreamerSettings(claim_drops=True, watch_streak=True))
            twitch_miner.mine([streamer], followers=False, followers_order=FollowersOrder.ASC)
            
            # Once the drop is awarded, stop watching this streamer and move to the next
            print(f"Drop awarded for {streamer_username}! Moving to another streamer.")
            break

# Main script execution
if __name__ == "__main__":
    username, streamers = get_username_and_streamers()

    if username and streamers:
        twitch_miner = setup_twitch_miner(username)
        while True:
            watch_for_drops_and_switch(twitch_miner, streamers)
            print("Waiting for a drop... Moving to the next eligible streamer.")
