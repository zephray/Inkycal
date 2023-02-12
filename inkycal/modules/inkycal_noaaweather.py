#!python3

"""
Inkycal weather module
Copyright by aceisace
"""

from inkycal.modules.template import inkycal_module
from inkycal.custom import *

import math
import decimal
import arrow

from noaa_sdk import NOAA

logger = logging.getLogger(__name__)


class NOAAWeather(inkycal_module):
    """NOAAWeather class
    parses weather details from NOAA
    """
    name = "NOAAWeather (NOAA) - Get weather forecasts from NOAA"

    requires = {

        "zipcode": {
            "label": "",
        },

        "country": {
            "label": ""
        }
    }

    optional = {

        "round_temperature": {
            "label": "Round temperature to the nearest degree?",
            "options": [True, False],
        },

        "round_windspeed": {
            "label": "Round windspeed?",
            "options": [True, False],
        },

        "forecast_interval": {
            "label": "Please select the forecast interval",
            "options": ["daily", "hourly"],
        },

        "units": {
            "label": "Which units should be used?",
            "options": ["metric", "imperial"],
        },

        "hour_format": {
            "label": "Which hour format do you prefer?",
            "options": [24, 12],
        },

        "use_beaufort": {
            "label": "Use beaufort scale for windspeed?",
            "options": [True, False],
        },

    }

    def __init__(self, config):
        """Initialize inkycal_weather module"""

        super().__init__(config)

        config = config['config']

        # Check if all required parameters are present
        for param in self.requires:
            if not param in config:
                raise Exception(f'config is missing {param}')

        # required parameters
        self.zipcode = config['zipcode']
        self.country = config['country']

        # optional parameters
        self.round_temperature = config['round_temperature']
        self.round_windspeed = config['round_windspeed']
        self.forecast_interval = config['forecast_interval']
        self.units = config['units']
        self.hour_format = int(config['hour_format'])
        self.use_beaufort = config['use_beaufort']

        # additional configuration
        self.noaa = NOAA()
        self.timezone = get_system_tz()
        self.locale = config['language']
        self.weatherfont = ImageFont.truetype(
            fonts['weathericons-regular-webfont'], size=self.fontsize)

        # give an OK message
        print(f"{__name__} loaded")

    def generate_image(self):
        """Generate image for this module"""

        # Define new image size with respect to padding
        im_width = int(self.width - (2 * self.padding_left))
        im_height = int(self.height - (2 * self.padding_top))
        im_size = im_width, im_height
        logger.info(f'Image size: {im_size}')

        # Create an image for black pixels and one for coloured pixels
        im_black = Image.new('RGB', size=im_size, color='white')
        im_colour = Image.new('RGB', size=im_size, color='white')

        # Check if internet is available
        if internet_available():
            logger.info('Connection test passed')
        else:
            raise NetworkNotReachableError

        def get_moon_phase():
            """Calculate the current (approximate) moon phase"""

            dec = decimal.Decimal
            diff = now - arrow.get(2001, 1, 1)
            days = dec(diff.days) + (dec(diff.seconds) / dec(86400))
            lunations = dec("0.20439731") + (days * dec("0.03386319269"))
            position = lunations % dec(1)
            index = math.floor((position * dec(8)) + dec("0.5"))
            return {0: '\uf095', 1: '\uf099', 2: '\uf09c', 3: '\uf0a0',
                    4: '\uf0a3', 5: '\uf0a7', 6: '\uf0aa', 7: '\uf0ae'}[int(index) & 7]

        def is_negative(temp):
            """Check if temp is below freezing point of water (0°C/30°F)
            returns True if temp below freezing point, else False"""
            answer = False

            if temp_unit == 'celsius' and round(float(temp.split('°')[0])) <= 0:
                answer = True
            elif temp_unit == 'fahrenheit' and round(float(temp.split('°')[0])) <= 0:
                answer = True
            return answer

        # Lookup-table for weather icons and weather codes
        weathericons = {
            '01d': '\uf00d', '02d': '\uf002', '03d': '\uf013',
            '04d': '\uf012', '09d': '\uf01a ', '10d': '\uf019',
            '11d': '\uf01e', '13d': '\uf01b', '50d': '\uf014',
            '01n': '\uf02e', '02n': '\uf013', '03n': '\uf013',
            '04n': '\uf013', '09n': '\uf037', '10n': '\uf036',
            '11n': '\uf03b', '13n': '\uf038', '50n': '\uf023'
        }
        
        def get_weather_at(forecasts, datetime):
            for forecast in forecasts:
                start_time = arrow.get(forecast["startTime"])
                end_time = arrow.get(forecast["endTime"])
                if ((datetime >= start_time) and (datetime < end_time)):
                    return forecast
            return None
        
        def get_temperature(forecast, unit):
            temp = forecast["temperature"]
            forecast_unit = forecast["temperatureUnit"]
            if ((unit == "imperial") and (forecast_unit == "C")):
                # Convert from C to F
                temp = temp * 1.8 + 32
            elif ((unit == "metric") and (forecast_unit == "F")):
                temp = (temp - 32) / 1.8
            return temp

        def get_weather_icon(forecast):
            desc = forecast["shortForecast"]
            icon = ""
            mapping = {
                'Sunny': '',
                'Mostly Sunny': '',
                'Partly Sunny': '',
                'Mostly Cloudy': '',
                'Slight Chance Light Rain': '',
                'Chance Rain Showers': '',
                'Mostly Clear': ''
            }
            if ("Sunny" in desc) or ("Clear" in desc):
                icon = "01"
            elif ("Partily Cloudy" in desc):
                icon = "02"
            elif ("Mostly Cloudy" in desc):
                icon = "03"
            elif ("Cloudy" in desc):
                icon = "04"
            elif ("Shower" in desc):
                icon = "09"
            elif ("Rain" in desc):
                icon = "10"
            elif ("Thunder" in desc):
                icon = "11"
            elif ("Snow" in desc):
                icon = "13"
            elif ("Mist" in desc):
                icon = "50"
            else:
                icon = "01" ## TODO
            
            # TODO: Detect night
            icon = icon + "d"

            return icon

        def draw_icon(image, xy, box_size, icon, rotation=None):
            """Custom function to add icons of weather font on image
            image = on which image should the text be added?
            xy = xy-coordinates as tuple -> (x,y)
            box_size = size of text-box -> (width,height)
            icon = icon-unicode, looks this up in weathericons dictionary
            """
            x, y = xy
            box_width, box_height = box_size
            text = icon
            font = self.weatherfont

            # Increase fontsize to fit specified height and width of text box
            size = 8
            font = ImageFont.truetype(font.path, size)
            text_width, text_height = font.getsize(text)

            while (text_width < int(box_width * 0.9) and
                   text_height < int(box_height * 0.9)):
                size += 1
                font = ImageFont.truetype(font.path, size)
                text_width, text_height = font.getsize(text)

            text_width, text_height = font.getsize(text)

            # Align text to desired position
            x = int((box_width / 2) - (text_width / 2))
            y = int((box_height / 2) - (text_height / 2))

            # Draw the text in the text-box
            draw = ImageDraw.Draw(image)
            space = Image.new('RGBA', (box_width, box_height))
            ImageDraw.Draw(space).text((x, y), text, fill='black', font=font)

            if rotation != None:
                space.rotate(rotation, expand=True)

            # Update only region with text (add text with transparent background)
            image.paste(space, xy, space)

        #   column1    column2    column3    column4    column5    column6    column7
        # |----------|----------|----------|----------|----------|----------|----------|
        # |  time    | temperat.| moonphase| forecast1| forecast2| forecast3| forecast4|
        # | current  |----------|----------|----------|----------|----------|----------|
        # | weather  | humidity |  sunrise |  icon1   |  icon2   |  icon3   |  icon4   |
        # |  icon    |----------|----------|----------|----------|----------|----------|
        # |          | windspeed|  sunset  | temperat.| temperat.| temperat.| temperat.|
        # |----------|----------|----------|----------|----------|----------|----------|

        # Calculate size rows and columns
        col_width = im_width // 7

        # Ratio width height
        image_ratio = im_width / im_height

        if image_ratio >= 4:
            row_height = im_height // 3
        else:
            logger.info('Please consider decreasing the height.')
            row_height = int((im_height * (1 - im_height / im_width)) / 3)

        logger.debug(f"row_height: {row_height} | col_width: {col_width}")

        # Calculate spacings for better centering
        spacing_top = int((im_width % col_width) / 2)
        spacing_left = int((im_height % row_height) / 2)

        # Define sizes for weather icons
        icon_small = int(col_width / 3)
        icon_medium = icon_small * 2
        icon_large = icon_small * 3

        # Calculate the x-axis position of each col
        col1 = spacing_top
        col2 = col1 + col_width
        col3 = col2 + col_width
        col4 = col3 + col_width
        col5 = col4 + col_width
        col6 = col5 + col_width
        col7 = col6 + col_width

        # Calculate the y-axis position of each row
        line_gap = int((im_height - spacing_top - 3 * row_height) // 4)

        row1 = line_gap
        row2 = row1 + line_gap + row_height
        row3 = row2 + line_gap + row_height

        # Draw lines on each row and border
        ############################################################################
        ##    draw = ImageDraw.Draw(im_black)
        ##    draw.line((0, 0, im_width, 0), fill='red')
        ##    draw.line((0, im_height-1, im_width, im_height-1), fill='red')
        ##    draw.line((0, row1, im_width, row1), fill='black')
        ##    draw.line((0, row1+row_height, im_width, row1+row_height), fill='black')
        ##    draw.line((0, row2, im_width, row2), fill='black')
        ##    draw.line((0, row2+row_height, im_width, row2+row_height), fill='black')
        ##    draw.line((0, row3, im_width, row3), fill='black')
        ##    draw.line((0, row3+row_height, im_width, row3+row_height), fill='black')
        ############################################################################

        # Positions for current weather details
        weather_icon_pos = (col1, 0)
        temperature_icon_pos = (col2, row1)
        temperature_pos = (col2 + icon_small, row1)
        humidity_icon_pos = (col2, row2)
        humidity_pos = (col2 + icon_small, row2)
        windspeed_icon_pos = (col2, row3)
        windspeed_pos = (col2 + icon_small, row3)

        # Positions for sunrise, sunset, moonphase
        moonphase_pos = (col3, row1)
        sunrise_icon_pos = (col3, row2)
        sunrise_time_pos = (col3 + icon_small, row2)
        sunset_icon_pos = (col3, row3)
        sunset_time_pos = (col3 + icon_small, row3)

        # Positions for forecast 1
        stamp_fc1 = (col4, row1)
        icon_fc1 = (col4, row1 + row_height)
        temp_fc1 = (col4, row3)

        # Positions for forecast 2
        stamp_fc2 = (col5, row1)
        icon_fc2 = (col5, row1 + row_height)
        temp_fc2 = (col5, row3)

        # Positions for forecast 3
        stamp_fc3 = (col6, row1)
        icon_fc3 = (col6, row1 + row_height)
        temp_fc3 = (col6, row3)

        # Positions for forecast 4
        stamp_fc4 = (col7, row1)
        icon_fc4 = (col7, row1 + row_height)
        temp_fc4 = (col7, row3)

        # Create current-weather and weather-forecast objects
        forecast = self.noaa.get_forecasts(self.zipcode, self.country)
        weather = forecast[0]

        # Set decimals
        dec_temp = None if self.round_temperature == True else 1
        dec_wind = None if self.round_windspeed == True else 1

        # Set correct temperature units
        if self.units == 'metric':
            temp_unit = 'celsius'
        elif self.units == 'imperial':
            temp_unit = 'fahrenheit'

        logging.debug(f'temperature unit: {temp_unit}')
        logging.debug(f'decimals temperature: {dec_temp} | decimals wind: {dec_wind}')

        # Get current time
        now = arrow.utcnow()

        if self.forecast_interval == 'hourly':

            logger.debug("getting hourly forecasts")

            # Forecasts are provided for every 3rd full hour
            # find out how many hours there are until the next 3rd full hour
            if (now.hour % 3) != 0:
                hour_gap = 3 - (now.hour % 3)
            else:
                hour_gap = 3

            # Create timings for hourly forcasts
            forecast_timings = [now.shift(hours=+ hour_gap + _).floor('hour')
                                for _ in range(0, 12, 3)]

            # Create forecast objects for given timings
            forecasts = [get_weather_at(forecast, forecast_time) for
                         forecast_time in forecast_timings]

            # Add forecast-data to fc_data dictionary
            fc_data = {}
            for forecast in forecasts:
                temp = '{}°'.format(round(
                    get_temperature(forecast, unit=temp_unit), ndigits=dec_temp))

                icon = get_weather_icon(forecast)
                fc_data['fc' + str(forecasts.index(forecast) + 1)] = {
                    'temp': temp,
                    'icon': icon,
                    'stamp': forecast_timings[forecasts.index(forecast)].to(
                        get_system_tz()).format('H.00' if self.hour_format == 24 else 'h a')
                }

        elif self.forecast_interval == 'daily':

            logger.debug("getting daily forecasts")

            def calculate_forecast(days_from_today):
                """Get temperature range and most frequent icon code for forecast
                days_from_today should be int from 1-4: e.g. 2 -> 2 days from today
                """

                # Create a list containing time-objects for every 3rd hour of the day
                time_range = list(arrow.Arrow.range('hour',
                                                    now.shift(days=days_from_today).floor('day'),
                                                    now.shift(days=days_from_today).ceil('day')
                                                    ))[::3]

                # Get forecasts for each time-object
                forecasts = [get_weather_at(forecast, _) for _ in time_range]

                # Get all temperatures for this day
                daily_temp = [round(get_temperature(_, unit=temp_unit),
                                    ndigits=dec_temp) for _ in forecasts]
                # Calculate min. and max. temp for this day
                temp_range = f'{max(daily_temp)}°/{min(daily_temp)}°'

                # Get all weather icon codes for this day
                daily_icons = [get_weather_icon(_) for _ in forecasts]
                # Find most common element from all weather icon codes
                status = max(set(daily_icons), key=daily_icons.count)

                weekday = now.shift(days=days_from_today).format('ddd', locale=
                self.locale)
                return {'temp': temp_range, 'icon': status, 'stamp': weekday}

            forecasts = [calculate_forecast(days) for days in range(1, 5)]

            fc_data = {}
            for forecast in forecasts:
                fc_data['fc' + str(forecasts.index(forecast) + 1)] = {
                    'temp': forecast['temp'],
                    'icon': forecast['icon'],
                    'stamp': forecast['stamp']
                }

        for key, val in fc_data.items():
            logger.debug((key, val))

        # Get some current weather details
        temperature = '{}°'.format(round(
            get_temperature(weather, unit=temp_unit), ndigits=dec_temp))

        weather_icon = get_weather_icon(weather)
        humidity = str(weather["relativeHumidity"]["value"])

        logger.debug(f'weather_icon: {weather_icon}')

        # Format the windspeed to user preference
        # TODO: Metric version
        wind = weather["windSpeed"]

        pop = str(weather["probabilityOfPrecipitation"]["value"]) + "% PoP"
        winddir = weather["windDirection"]

        dec = decimal.Decimal
        moonphase = get_moon_phase()

        # Fill weather details in col 1 (current weather icon)
        draw_icon(im_colour, weather_icon_pos, (col_width, im_height),
                  weathericons[weather_icon])

        # Fill weather details in col 2 (temp, humidity, wind)
        draw_icon(im_colour, temperature_icon_pos, (icon_small, row_height),
                  '\uf053')

        if is_negative(temperature):
            write(im_black, temperature_pos, (col_width - icon_small, row_height),
                  temperature, font=self.font)
        else:
            write(im_black, temperature_pos, (col_width - icon_small, row_height),
                  temperature, font=self.font)

        draw_icon(im_colour, humidity_icon_pos, (icon_small, row_height),
                  '\uf07a')

        write(im_black, humidity_pos, (col_width - icon_small, row_height),
              humidity + '%', font=self.font)

        draw_icon(im_colour, windspeed_icon_pos, (icon_small, icon_small),
                  '\uf050')

        write(im_black, windspeed_pos, (col_width - icon_small, row_height),
              wind, font=self.font)

        # Fill weather details in col 3 (moonphase, sunrise, sunset)
        draw_icon(im_colour, moonphase_pos, (col_width, row_height), moonphase)

        write(im_black, sunrise_icon_pos, (col_width, row_height),
              pop, font=self.font)

        write(im_black, sunset_icon_pos, (col_width, row_height), winddir,
              font=self.font)

        # Add the forecast data to the correct places
        for pos in range(1, len(fc_data) + 1):
            stamp = fc_data[f'fc{pos}']['stamp']

            icon = weathericons[fc_data[f'fc{pos}']['icon']]
            temp = fc_data[f'fc{pos}']['temp']

            write(im_black, eval(f'stamp_fc{pos}'), (col_width, row_height),
                  stamp, font=self.font)
            draw_icon(im_colour, eval(f'icon_fc{pos}'), (col_width, row_height + line_gap * 2),
                      icon)
            write(im_black, eval(f'temp_fc{pos}'), (col_width, row_height),
                  temp, font=self.font)

        border_h = row3 + row_height
        border_w = col_width - 3  # leave 3 pixels gap

        # Add borders around each sub-section
        draw_border(im_black, (col1, row1), (col_width * 3 - 3, border_h),
                    shrinkage=(0, 0))

        for _ in range(4, 8):
            draw_border(im_black, (eval(f'col{_}'), row1), (border_w, border_h),
                        shrinkage=(0, 0))

        # return the images ready for the display
        return im_black, im_colour


if __name__ == '__main__':
    print(f'running {__name__} in standalone mode')
