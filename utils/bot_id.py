SLACK_BOT_TOKEN=""  #StashPop Slack

import os
from slackclient import SlackClient

BOT_NAME = 'chomps'

slack_client = SlackClient(SLACK_BOT_TOKEN)
if __name__ == "__main__":
    api_call = slack_client.api_call("users.list")
    if api_call.get('ok'):
        # retrieve all users so we can find our bot
        users = api_call.get('members')
        for user in users:
            if 'name' in user and user.get('name') == BOT_NAME:
                print("Bot ID for '" + user['name'] + "' is " + user.get('id'))
    else:
        print("could not find bot user with the name " + BOT_NAME)

    api_call = slack_client.api_call('users.info', user="U0FJ4G709")
    from pprint import pprint
    pprint(api_call)