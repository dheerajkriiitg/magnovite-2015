import markdown2
import re

from django.db import models
from django.core.urlresolvers import reverse
from django.core.exceptions import ValidationError

from multiselectfield import MultiSelectField


class Event(models.Model):
    TECHNICAL_TAGS = (
        ('cse', 'Computer Science'),
        ('ec', 'Electronics'),
        ('mech', 'Mechanical'),
        ('civil', 'Civil'),
    )

    title = models.CharField(max_length=100)
    slug = models.SlugField(help_text='The event url, use all simple and - as a seperator, Eg: junkyard-wars')

    quote = models.CharField(max_length=70, help_text='Text displayed on the cards in /events/')

    # This is assumed to be a Markdown field
    info = models.TextField(
        help_text='Please write in Markdown (Editor: http://dillinger.io/)'
    )

    cash_prize = models.IntegerField(help_text='Numeric, Eg: 5000')

    # Time and venue are simple text
    date = models.IntegerField(
        max_length=2,
        help_text='Eg: 21',
        blank=True, null=True
    )
    time = models.CharField(
        max_length=30,
        help_text='(Start time), Eg: 9:00 am',
        blank=True
    )
    end_time = models.CharField(
        max_length=30,
        help_text='(End Time), Eg: 4:00 pm',
        blank=True, null=True,
    )
    venue = models.CharField(
        max_length=50,
        help_text='Eg: Room 243, Block 2',
        blank=True
    )

    team_min = models.IntegerField(
        help_text='Minimum number of people in a team (If individual: 1)',
        default=1
    )
    team_max = models.IntegerField(
        help_text='Maximum number of people in a team (If individual: 1)',
        default=1
    )

    # if not technical, then cultural
    technical = models.BooleanField(default=True, help_text='If cultural set to false')

    # This is a comma seperated field
    tags = MultiSelectField(choices=TECHNICAL_TAGS, blank=True, null=True)

    # event heads
    picture_one = models.BooleanField(
        help_text='Does event head 1 have a picture? (name: img/events/[slug]_h1.jpg)',
        default=False
    )

    picture_two = models.BooleanField(
        help_text='Does event head 2 have a picture? (name: img/events/[slug]_h2.jpg)',
        default=False
    )

    # analytics
    views = models.IntegerField(default=0)
    registrations = models.IntegerField(default=0)

    class Meta:
        permissions = (
            ('change_own', 'Change events incharge of'),
        )

    def clean(self):
        if self.title:
            if (self.title.lower() == self.title or
                self.title.upper() == self.title):
                raise ValidationError('Title needs to be in Title Case (eg: Dance Event)')

        if self.slug:
            if not re.match(r'^[-a-z]+$', self.slug):
                raise ValidationError('Slug must contain only lowercase letters and -')

        if self.date:
            if not self.date in [21, 22]:
                raise ValidationError('Date can only be 21 or 22')

        time_re = re.compile(r'^1?\d:\d\d (am|pm)$')
        if self.time:
            if not time_re.match(self.time):
                raise ValidationError('Start Time must be in format "0:00 am" or "0:00 pm" (note spaces)')

        if self.end_time:
            if not time_re.match(self.end_time):
                raise ValidationError('End Time must be in format "0:00 am" or "0:00 pm" (note spaces)')

    def info_as_html(self):
        """
        Returns the rendered html from the markdown
        """
        return markdown2.markdown(self.info)

    def is_complete(self):
        """
        Are all the details of this event complete,
        we only need to verify optional fields
        """
        return bool(self.date and self.time and self.venue)
    is_complete.boolean = True

    def is_team(self):
        return not bool(self.team_min == 1 and self.team_max == 1)

    def type(self):
        if self.technical:
            return 'technical'
        else:
            return 'cultural'

    def tag_assoc(self):
        """
        Returns an array of objects [{tag, name}]
        """
        out = []

        if not self.tags:
            return out

        for tag in self.tags:
            out.append({
                'tag': tag,
                'name': self.get_tag_verbose(tag)
            })

        return out

    def class_string(self):
        """
        Returns all the tags as a string
        """
        if self.tags:
            return ' '.join(self.tags)
        else:
            return ''

    def get_tag_verbose(self, tag):
        for row in self.TECHNICAL_TAGS:
            if row[0] == tag:
                return row[1]

        return ""

    def cover_picture_path(self):
        return 'img/events/' + self.slug + '_cover.jpg'

    def event_head_p1(self):
        if self.picture_one:
            return 'img/events/' + self.slug + '_h1.jpg'
        else:
            return 'img/events/head_default.jpg'

    def event_head_p1(self):
        if self.picture_one:
            return 'img/events/' + self.slug + '_h2.jpg'
        else:
            return 'img/events/head_default.jpg'

    def get_first_head(self):
        return self.heads.first()

    def get_absolute_url(self):
        return reverse('event_details', kwargs={'slug': self.slug})

    def __str__(self):
        return self.title


class Registration(models.Model):
    event = models.ForeignKey(Event)
    profile = models.ForeignKey('main.Profile')

    # If this registration is for a team event
    # then the team id
    team_id = models.CharField(max_length=5, blank=True, null=True)

    class Meta:
        unique_together = ['event', 'profile']
        permissions = (
            ('own_event_registrations', 'View registrations for own event'),
        )
