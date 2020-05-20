#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Calendar module for Inky-Calendar Project
Copyright by aceisace
"""

from inkycal.custom import *
import calendar as cal
import arrow

size = (400, 520)
config = {'week_starts_on': 'Monday', 'ical_urls': ['https://calendar.google.com/calendar/ical/en.usa%23holiday%40group.v.calendar.google.com/public/basic.ics']}


class calendar:
  """Calendar class
  Create monthly calendar and show events from given icalendars
  """
  logger = logging.getLogger(__name__)
  logging.basicConfig(level=logging.DEBUG)

  def __init__(self, section_size, section_config):
    """Initialize inkycal_calendar module"""

    self.name = os.path.basename(__file__).split('.py')[0]
    self.config = section_config
    self.width, self.height = section_size
    self.fontsize = 12
    self.font = ImageFont.truetype(
      fonts['NotoSans-SemiCondensed'], size = self.fontsize)
    self.padding_x = 0.02
    self.padding_y = 0.05

    self.num_font = ImageFont.truetype(
      fonts['NotoSans-SemiCondensed'], size = self.fontsize)
    self.weekstart = 'Monday'
    self.show_events = True
    self.date_format = 'D MMM' # used for dates 
    self.time_format = "HH:mm" # used for timings
    self.language = 'en' # Grab from settings file?
    
    self.timezone = get_system_tz()
    self.ical_urls = config['ical_urls']
    self.ical_files = []
    print('{0} loaded'.format(self.name))

  def set(self, **kwargs):
    """Manually set some parameters of this module"""

    for key, value in kwargs.items():
      if key in self.__dict__:
        setattr(self, key, value)
      else:
        print('{0} does not exist'.format(key))
        pass

  def get(self, **kwargs):
    """Manually get some parameters of this module"""

    for key, value in kwargs.items():
      if key in self.__dict__:
        getattr(self, key, value)
      else:
        print('{0} does not exist'.format(key))
        pass

  def get_options(self):
    """Get all options which can be changed"""

    return self.__dict__

  def generate_image(self):
    """Generate image for this module"""

    # Define new image size with respect to padding
    im_width = int(self.width - (self.width * 2 * self.padding_x))
    im_height = int(self.height - (self.height * 2 * self.padding_y))
    im_size = im_width, im_height

    logging.info('Image size: {0}'.format(im_size))

    # Create an image for black pixels and one for coloured pixels
    im_black = Image.new('RGB', size = im_size, color = 'white')
    im_colour = Image.new('RGB', size = im_size, color = 'white')

    # Allocate space for month-names, weekdays etc.
    month_name_height = int(self.height*0.1)
    weekdays_height = int(self.height*0.05)

    if self.show_events == True:
      calendar_height = int(self.height*0.6)
      events_height = int(self.height*0.25)
      logging.debug('calendar-section size: {0} x {1} px'.format(
        im_width, calendar_height))
      logging.debug('events-section size: {0} x {1} px'.format(
        im_width, events_height))
    else:
      calendar_height = self.height - month_name_height - weekday_height
      logging.debug('calendar-section size: {0} x {1} px'.format(
        im_width, calendar_height))

    # Create grid and calculate icon sizes
    calendar_rows, calendar_cols = 6, 7
    icon_width = im_width // calendar_cols
    icon_height = calendar_height // calendar_rows

    # Calculate spacings for calendar area
    x_spacing_calendar = int((im_width % calendar_cols) / 2)
    y_spacing_calendar = int((im_height % calendar_rows) / 2)

    # Calculate positions for days of month
    grid_start_y = (month_name_height + weekdays_height + y_spacing_calendar)
    grid_start_x = x_spacing_calendar

    grid = [(grid_start_x + icon_width*x, grid_start_y + icon_height*y)
            for y in range(calendar_rows) for x in range(calendar_cols)]

    weekday_pos = [(grid_start_x + icon_width*_, month_name_height) for _ in
                   range(calendar_cols)]

    now = arrow.now(tz = self.timezone)

    # Set weekstart of calendar to specified weekstart
    if self.weekstart == "Monday":
      cal.setfirstweekday(cal.MONDAY)
      weekstart = now.shift(days = - now.weekday())
    else:
      cal.setfirstweekday(cal.SUNDAY)
      weekstart = now.shift(days = - now.isoweekday())

    # Write the name of current month
    write(
      im_black,
      (x_spacing_calendar,0),
      (self.width, month_name_height),
      str(now.format('MMMM',locale=self.language)),
      font = self.font,
      autofit = True)

    # Set up weeknames in local language and add to main section
    weekday_names = [weekstart.shift(days=+_).format('ddd',locale=self.language)
      for _ in range(7)]
    logging.debug('weekday names: {}'.format(weekday_names))

    for _ in range(len(weekday_pos)):
      write(
        im_black,
        weekday_pos[_],
        (icon_width, weekdays_height),
        weekday_names[_],
        font = self.font,
        autofit = True
        )

    # Create a calendar template and flatten (remove nestings)
    flatten = lambda z: [x for y in z for x in y]
    calendar_flat = flatten(cal.monthcalendar(now.year, now.month))

    # Add the numbers on the correct positions
    for i in range(len(calendar_flat)):
      if calendar_flat[i] not in (0, int(now.day)):
        write(
          im_black,
          grid[i],
          (icon_width,icon_height),
          str(calendar_flat[i]),
          font = self.num_font, fill_height = 0.5
          )

    # Draw a red/black circle with the current day of month in white
    icon = Image.new('RGBA', (icon_width, icon_height))
    current_day_pos = grid[calendar_flat.index(now.day)]
    x_circle,y_circle = int(icon_width/2), int(icon_height/2)
    radius = int(icon_width * 0.3)
    ImageDraw.Draw(icon).ellipse(
      (x_circle-radius, y_circle-radius, x_circle+radius, y_circle+radius),
      fill= 'black', outline=None)
    write(icon, (0,0), (icon_width, icon_height), str(now.day),
          font=self.num_font, fill_height = 0.5, colour='white')
    im_colour.paste(icon, current_day_pos, icon)
    

    # If events should be loaded and shown...
    if self.show_events == True:

      # import the ical-parser
      from inkycal.modules.ical_parser import icalendar

      # find out how many lines can fit at max in the event section
      line_spacing = 0
      max_event_lines = events_height // (self.font.getsize('hg')[1] +
                                          line_spacing)

      # generate list of coordinates for each line
      event_lines = [(0, grid[-1][1] + int(events_height/max_event_lines*_))
                     for _ in range(max_event_lines)]

      # timeline for filtering events within this month
      month_start = arrow.get(now.floor('month'))
      month_end = arrow.get(now.ceil('month'))

      # fetch events from given icalendars
      parser = icalendar()
      if self.ical_urls:
        parser.load_url(self.ical_urls)
      if self.ical_files:
        parser.load_from_file(self.ical_files)

      # Filter events for full month (even past ones) for drawing event icons
      month_events = parser.get_events(month_start, month_end)
      parser.sort()
      self.month_events = month_events

      # find out on which days of this month events are taking place
      days_with_events = [int(events['begin'].format('D')) for events in
                          month_events]

      # remove duplicates (more than one event in a single day)
      list(set(days_with_events)).sort()
      self._days_with_events = days_with_events

      # Draw a border with specified parameters around days with events
      for days in days_with_events:
        draw_border(
          im_colour,
          grid[calendar_flat.index(days)],
          (icon_width, icon_height),
          radius = 6,
          thickness= 1,
          shrinkage = (0.4, 0.4)
          )

      # Filter upcoming events until 4 weeks in the future
      parser.clear_events()
      upcoming_events = parser.get_events(now, now.shift(weeks=4))
      self._upcoming_events = upcoming_events

      # delete events which won't be able to fit (more events than lines)
      upcoming_events[max_event_lines:]


      # Check if any events were found in the given timerange
      if upcoming_events:

        # Find out how much space (width) the date format requires
        lang = self.language

        date_width = int(max([self.font.getsize(
          events['begin'].format(self.date_format,locale=lang))[0]
          for events in upcoming_events]) * 1.1)
        
        time_width = int(max([self.font.getsize(
          events['begin'].format(self.time_format, locale=lang))[0]
          for events in upcoming_events]) * 1.1)

        line_height = self.font.getsize('hg')[1] + line_spacing
        
        event_width_s = im_width - date_width - time_width
        event_width_l = im_width - date_width

        # Display upcoming events below calendar
        tomorrow = now.shift(days=1).floor('day')
        in_two_days = now.shift(days=2).floor('day')

        cursor = 0
        for event in upcoming_events:
          name = event['title']
          date = event['begin'].format(self.date_format, locale=lang)
          time = event['begin'].format(self.time_format, locale=lang)

          if now < event['end']:
            write(im_colour, event_lines[cursor], (date_width, line_height),
                  date, font=self.font, alignment = 'left')

            # Check if event is all day
            if parser.all_day(event) == True:
              write(im_black, (date_width, event_lines[cursor][1]),
                  (event_width_l, line_height), name, font=self.font,
                  alignment = 'left')
            else:
              write(im_black, (time_width, event_lines[cursor][1]),
                  (event_width, line_height), time, font=self.font,
                  alignment = 'left')

              write(im_black, (date_width+time_width,event_lines[cursor][1]),
                  (event_width_s, line_height), name, font=self.font,
                  alignment = 'left')
            cursor += 1
      else:
        symbol = '- '
        while self.font.getsize(symbol)[0] < im_width*0.9:
          symbol += ' -'
        write(im_black, event_lines[0],
              (im_width, self.font.getsize(symbol)[1]), symbol,
              font = self.font)

    # Save image of black and colour channel in image-folder
    im_black.save(images+self.name+'.png')
    im_colour.save(images+self.name+'_colour.png')

if __name__ == '__main__':
  print('running {0} in standalone mode'.format(
    os.path.basename(__file__).split('.py')[0]))

##a = calendar(size, config)
##a.generate_image()
