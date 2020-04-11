from PIL import Image, ImageFont, ImageDraw, ImageSequence
from rgbmatrix import graphics
from time import sleep
from utils import center_text,get_file
import debug

class wxWeather:
    def __init__(self, data, matrix,sleepEvent):
        self.data = data
        
        self.layout = self.data.config.config.layout.get_board_layout('wx_curr_temp')
        self.layout2 = self.data.config.config.layout.get_board_layout('wx_curr_wind')
        self.layout3 = self.data.config.config.layout.get_board_layout('wx_curr_precip')
        self.layout4 = self.data.config.config.layout.get_board_layout('wx_alert')

        self.wxfont = data.config.layout.wxfont

        self.matrix = matrix

        self.sleepEvent = sleepEvent
        self.sleepEvent.clear()
    
        self.duration = data.config.weather_duration
        if self.duration < 30:
            debug.error("Duration is less than 30 seconds, defaulting to 30 seconds")
            self.duration = 30

        display_wx = 0
        display_sleep = self.duration/3
        if self.data.wx_updated:
            #Get size of summary text for looping 
            if len(self.data.wx_current) > 0:
                summary_info = self.matrix.draw_text(["1%", "77%"],self.data.wx_current[2],self.wxfont)
                self.summary_width = summary_info["size"][0]
            else:
                self.summary_width = self.matrix.width

            if self.summary_width > self.matrix.width:
                self.scroll_summary = True
            else:
                self.scroll_summary = False

            while display_wx < self.duration and not self.sleepEvent.is_set():
                self.WxDrawTemp(display_sleep)
                #self.sleepEvent.wait(display_sleep)
                display_wx += display_sleep
                self.WxDrawWind()
                self.sleepEvent.wait(display_sleep)
                display_wx += display_sleep
                if self.data.config.weather_data_feed.lower() == "ds":
                    self.WxDrawPrecip_DS()
                elif self.data.config.weather_data_feed.lower() == "ec":
                    self.WxDrawPrecip_EC()
                else:
                    continue
                self.sleepEvent.wait(display_sleep)

                if len(self.data.wx_alerts) > 0:
                    self.WxDrawAlert()
                    self.sleepEvent.wait(display_sleep)

                display_wx += display_sleep
        else:
            debug.error("Weather feed has not updated yet....")
        
    def WxDrawTemp(self,display_loop):

        x=0
        pos = self.matrix.width
        # If the summary is to scroll, change size of display loop
        if self.scroll_summary:
            display_loop = ((self.summary_width/self.matrix.width)/0.1)*display_loop

        while x < display_loop and not self.sleepEvent.is_set():
            self.matrix.clear()

            # Get the current weather icon
        
            curr_wx_icontext = self.data.wx_current[1]

            self.matrix.draw_text_layout(
                self.layout.condition,
                curr_wx_icontext
            )  

            if not self.scroll_summary:
                self.matrix.draw_text_layout(
                    self.layout.summary,
                    self.data.wx_current[2] 
                )
            else:
                self.matrix.draw_text([pos,"67%"],self.data.wx_current[2],self.wxfont)
                if self.summary_width > pos:
                    pos -= 1
                    if pos + self.summary_width < 0:
                        pos = self.matrix.width


            self.matrix.draw_text_layout(
                self.layout.update,
                self.data.wx_current[0]
            )

            self.matrix.draw_text_layout(
                self.layout.temp,
                self.data.wx_current[3]
            )  

            self.matrix.draw_text_layout(
                self.layout.temp_app,
                self.data.wx_current[4] 
            )

            self.matrix.render()

            if self.data.network_issues:
                self.matrix.network_issue_indicator()

            if not self.scroll_summary:
                self.sleepEvent.wait(1)
            else:
                self.sleepEvent.wait(0.01)
            x+=1
    
    def WxDrawWind(self):
        
        self.matrix.clear()

       #wind_wx_diricon = u'\uf05b'
        self.matrix.draw_text_layout(
            self.layout2.condition,
            #wind_wx_diricon
            self.data.wx_curr_wind[2]
        )  

        self.matrix.draw_text_layout(
            self.layout2.wind,
            self.data.wx_curr_wind[1] + " @ " + self.data.wx_curr_wind[0]
        )  

        self.matrix.draw_text_layout(
            self.layout2.gust,
            "Gusts to:\n" + self.data.wx_curr_wind[3]
        )  

        if self.data.config.weather_data_feed.lower() == "ds":
            self.matrix.draw_text_layout(
                self.layout2.pressure,
                self.data.wx_curr_wind[4]
            )
        
        if self.data.config.weather_data_feed.lower() == "ec":
            self.matrix.draw_text_layout(
                self.layout2.visibility,
                "Vis: " + self.data.wx_curr_wind[6]
            )
          

        self.matrix.render()

        if self.data.network_issues:
            self.matrix.network_issue_indicator()

    def WxDrawPrecip_DS(self):
        
        self.matrix.clear()

        precip_wx_icon = '\uf07b' #N/A

        
        if self.data.wx_curr_precip[0] == None:
            wx_curr_precip = "N/A"
            self.matrix.draw_text_layout(
                self.layout3.preciptype_na,
                precip_wx_icon
            )
        else:
            wx_curr_precip = self.data.wx_curr_precip[0]
            self.matrix.draw_text_layout(
                self.layout3.preciptype,
                precip_wx_icon
            )  
            
        self.matrix.draw_text_layout(
            self.layout3.precipchance,
            "Chance: " + wx_curr_precip + "\n" + self.data.wx_curr_precip[1]
        ) 
        

        self.matrix.draw_text_layout(
             self.layout3.humidity,
              self.data.wx_current[5] + " Humidity"
        )
    
        if len(self.data.wx_alerts) > 0:
            # Draw Alert boxes (warning,watch,advisory) for 64x32 board
            # Only draw the highest 
            #self.matrix.draw.rectangle([60, 25, 64, 32], fill=(255,0,0)) # warning
            if self.data.wx_alerts[1] == "warning": 
                self.matrix.draw.rectangle([58, 10, 64, 20], fill=(255,0,0)) # warning
            elif self.data.wx_alerts[1] == "watch":
                if self.data.wx_units[5] == "us":
                    self.matrix.draw.rectangle([58, 10, 64, 20], fill=(255,165,0)) # watch
                else:
                    self.matrix.draw.rectangle([58, 10, 64, 20], fill=(255,255,0)) # watch canada
            else:
                if self.data.wx_alerts[1] == "advisory":
                    if self.data.wx_units[5] == "us":
                        self.matrix.draw.rectangle([58, 10, 64, 20], fill=(255,255,0)) #advisory
                    else:
                        self.matrix.draw.rectangle([58, 10, 64, 20], fill=(169,169,169)) #advisory canada

        self.matrix.render()

        if self.data.network_issues:
            self.matrix.network_issue_indicator()
    
    def WxDrawPrecip_EC(self):

        self.matrix.clear()

        precip_wx_icon = '\uf07b' #N/A

        self.matrix.draw_text_layout(
            self.layout3.pressure,
            self.data.wx_curr_wind[4]
        )

        self.matrix.draw_text_layout(
            self.layout3.tendency,
            self.data.wx_curr_wind[5]
        )

        self.matrix.draw_text_layout(
            self.layout3.dewpoint,
            "Dew Pt. " + self.data.wx_current[6]
        )

        self.matrix.draw_text_layout(
             self.layout3.humidity,
              self.data.wx_current[5] + " Humidity"
        )

        self.matrix.render()

        if self.data.network_issues:
            self.matrix.network_issue_indicator()
    
    def WxDrawAlert(self):
        
        self.matrix.clear()

        if self.data.wx_alerts[1] == "warning": 
            self.matrix.draw.rectangle([0, 0, 64, 8], fill=(255,0,0)) # warning

            self.matrix.draw_text_layout(
                self.layout4.warning,
                self.data.wx_alerts[0]
            )  
            self.matrix.draw_text_layout(
                self.layout4.warning_date,
                self.data.wx_alerts[2]
            )
            self.matrix.draw.rectangle([0, 24, 64, 32], fill=(255,0,0)) # warning
            self.matrix.draw_text_layout(
                self.layout4.title_top,
                "Weather"
            )  
            self.matrix.draw_text_layout(
                self.layout4.title_bottom,
                "Warning"
            )  
        elif self.data.wx_alerts[1] == "watch":
            if self.data.wx_units[5] == "us":
                self.matrix.draw.rectangle([0, 0, 64, 8], fill=(255,165,0)) # watch
                self.matrix.draw_text_layout(
                    self.layout4.watch_us,
                    self.data.wx_alerts[0]
                )
                self.matrix.draw.rectangle([0, 24, 64, 32], fill=(255,165,0)) # watch
            else:
                self.matrix.draw.rectangle([0, 0, 64, 8], fill=(255,255,0)) # watch canada
                self.matrix.draw_text_layout(
                    self.layout4.watch_ca,
                    self.data.wx_alerts[0]
                )
                self.matrix.draw.rectangle([0, 24, 64, 32], fill=(255,255,0)) # watch canada
            self.matrix.draw_text_layout(
                self.layout4.title_top,
                "Weather"
            )  
            self.matrix.draw_text_layout(
                self.layout4.title_bottom,
                "Watch"
            )  
        else:
            if self.data.wx_alerts[1] == "advisory":
                if self.data.wx_units[5] == "us":
                    self.matrix.draw.rectangle([0, 0, 64, 8], fill=(255,255,0)) #advisory
                    self.matrix.draw_text_layout(
                        self.layout4.advisory_us,
                        self.data.wx_alerts[0]
                    )
                    self.matrix.draw.rectangle([0, 24, 64, 32], fill=(255,255,0)) #advisory
                else:
                    self.matrix.draw.rectangle([0, 0, 64, 8], fill=(169,169,169)) #advisory canada
                    self.matrix.draw_text_layout(
                        self.layout4.advisory_ca,
                        self.data.wx_alerts[0]
                    )
                    self.matrix.draw.rectangle([0, 24, 64, 32], fill=(169,169,169)) #advisory canada
            self.matrix.draw_text_layout(
                self.layout4.title_top,
                "Weather"
            )  
            self.matrix.draw_text_layout(
                self.layout4.title_bottom,
                "Advisory"
            )  

        self.matrix.render()

        if self.data.network_issues:
            self.matrix.network_issue_indicator()



    