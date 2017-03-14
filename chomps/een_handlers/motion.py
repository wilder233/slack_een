import re
import random
import gevent
import logging
import requests
import settings
import StringIO
import tempfile
import simplejson
from io import BytesIO
from pprint import pprint, pformat
from iris import EventMonitor, NotificationManager, ImageClassifier
from lib import ChompsHandler


trigger = re.compile("(?:[Ii]ris)(.*)")
log = logging.getLogger("chomps.iris")

BOT_NAME = "Iris for Eagle Eye"
een_icon_url = "https://s3-us-west-2.amazonaws.com/slack-files2/avatars/2015-11-02/13720654866_55504da4bb6fdb6dfa35_68.jpg"

def make_event_attachment(event, upload, region, intel, withdebug=False):
    title = "{} on {}".format(event.name, event.cam_info['name'])

    general = intel.general_concepts['caption'] or "nothing of interest"
    color = "#1aaf51" if not intel.general_concepts['caption'] else "#eaaa20"
    
    # color the attachment red for these
    for concept in [intel.tm.gun, intel.tm.danger, intel.tm.pistol, intel.tm.box, intel.pm.bag, intel.tm.crate, intel.tm.equipment, intel.tm.container]:
        if concept > 85:
            color = "#9b0711"
            break
    
    custom = ""
    if region.model:
        custom = intel.top_tags[region.model]

    ach = dict(
        fallback=title,
        color=color,
        title=title,
        text="_Looks like {} on the {}_".format(general, event.cam_info['name']),
        image_url=upload['permalink'],
        thumb_url=een_icon_url,
        footer_icon=een_icon_url,
        footer="Iris for Eagle Eye",
        fields=[],
        mrkdwn_in=["text", "pretext", "fields"]
    )
    ach['actions'] = []

    # Intel
    if intel.custom_description:
        field = dict(
            value="_*{}*_".format(intel.custom_description),
            short=False,
        )
        ach['fields'].append(field)


    ### SHOW DEBUG TAG
    if withdebug:
        for model, tags in intel.tags.iteritems():
            field = dict(
                title="{} Tags".format(model),
                value="```{}```".format(pformat(tags)),
                short=False,
            )
            ach['fields'].append(field)

    ach['actions'].append({
        'name': "Train",
        'text': 'Not Accurate',
        'value': event.cam_id,
        'style': 'danger',
        'type': 'button'
    })
    ach['actions'].append({
        'name': "Affirm",
        'text': 'Looks Right',
        'value': event.cam_id,
        'style': 'primary',
        'type': 'button'
    })
    return ach

class MotionHandler(ChompsHandler):

    def __init__(self, client, bot_name, bot_id):
        ChompsHandler.__init__(self, client, bot_name, bot_id)
        self.notif_channel = settings.SLACK_NOTIF_CHANNEL
        
        #self.notif_channel = "#general"
        #self.send_notification(">>>Iris is running")

        self.controller = NotificationManager(
            settings.EEN_ALERT_RESET, 
            settings.EEN_ALERT_REGION,
            settings.CUSTOM_MODEL
        )
        self.clarifai = ImageClassifier(settings.CLARIFAI_APP_ID, settings.CLARIFAI_SECRET)

        # Start the Iris event watcher
        self.event_monitor = EventMonitor(
            self.handle_image_event, 
            username=settings.EEN_USERNAME,
            password=settings.EEN_PASSWORD,
            cams=settings.EEN_CAM_IDS
        )
        self.event_monitor.start()

        gevent.spawn_later(10, self.check_devices)

    @property
    def pattern(self):
        return trigger

    def process_message(self, match, message):
        """ Listen for Iris commands """
        
        sentence = match.groups()[0]
        return self.send_notification('>>>At your service - "{}"'.format(sentence), message['channel'])
    
    def handle_image_event(self, event):
        """ Callback method for processing Iris Events """
        log.info("Event {}: {}".format(event.name, event.cam_id))
        
        classify_region = self.controller.handle_event(event)
        if classify_region:
            self.event_monitor.attach_image(event)
            intel = self.clarifai.intel_report(event.image.content, classify_region)
            self.send_event(event, classify_region, intel)
        else:
            log.info("SKIPPING EVENT")
        #self.send_notification(">>> :gear: Handling Event {} for {}".format(event.name, event.cam_id))

    def check_devices(self):
        """ Loads the devices into the controller """
        log.info("Trying to initialize controller")
        devices = self.event_monitor.watched_cams
        self.controller.update_devices(devices)
        if not devices:
            gevent.spawn_later(10, self.check_devices)
        else:
            gevent.spawn_later(600, self.check_devices)

    def send_event(self, event, region, intel):
        esn = event.cam_id
        filename = "{}_{}.jpg".format(esn, event.image.headers['x-ee-timestamp'])

        log.info("Uploading file {}".format(filename))
        _resp = self.client.api_call(
            'files.upload',
            file=StringIO.StringIO(event.image.content),
            filename=filename,
            channels="#general"
        )

        attachment = make_event_attachment(event, _resp['file'], region, intel)
        self.client.api_call(
            "chat.postMessage", 
            icon_url=een_icon_url,
            channel=self.notif_channel, 
            as_user=False,
            username=BOT_NAME,
            attachments=simplejson.dumps([attachment])
        )
        if settings.SHOW_TAGS:
            attachment = make_event_attachment(event, _resp['file'], region, intel, True)
            self.client.api_call(
                "chat.postMessage", 
                icon_url=een_icon_url,
                channel="#iris_debug", 
                as_user=False,
                username=BOT_NAME,
                attachments=simplejson.dumps([attachment])
            )
            _resp = self.client.api_call(
                'files.upload',
                file=StringIO.StringIO(intel.tag_region),
                filename="crop-{}".format(filename),
                channels="#iris_debug"
            )
        

    def send_notification(self, message, channel=None):
        self.client.api_call(
            "chat.postMessage", 
            channel=channel or self.notif_channel, 
            text=message, 
            as_user=False,
            icon_url=een_icon_url,
            username=BOT_NAME,
        )

