#!/usr/bin/env pythonw
# ----------------------------- IMPORTS ----------------------------- #
import wx
import os
from Tuner-main.tune_freq import tune_cols
from Tuner-main.misc_util import *

# ----------------------------- MISCELLANEOUS ----------------------------- #

# Stores supported scales and their notes, with C being 1 and so on (for the scale selector dropdown)
custom_scales = {                                                                                  
    'Black Notes Only':[2,4,7,9,11]
}

# Stores notes of the chromatic scale, for the note selector dropdown
piano_notes = ['A', 'A#', 'B', 'C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#'] 

scales_dict = {n+' '+ default_scales[scale_key][0]: construct_default_scale(i+1,scale_key) for scale_key in default_scales for i, n in enumerate(notes)}
scales_dict.update(custom_scales)
# ----------------------------- APPLICATION UI ----------------------------- #

class ListCtrl(wx.ListCtrl):

    def __init__(self, *args, **kw):
        super(ListCtrl, self).__init__(*args, **kw, style=wx.LC_REPORT)
        self.EnableCheckBoxes()
    
class noneObj():

    def GetWindow(self): return self
    def Show(self): return True
    def Hide(self): return True

class CheckboxComboPopup(wx.ComboPopup):
    
    def Init(self):
        self.sample_list = piano_notes
        self.check_list = None
        
    def Create(self, parent):
        self.check_list = ListCtrl(parent); self.check_list.InsertColumn(0,'')
        for item in self.sample_list: self.check_list.InsertItem(12,item)
        return True
    
    def GetControl(self): return self.check_list

    def GetAdjustedSize(self,min_width, prefHeight, max_height):
        pref_height = (len(self.sample_list) * 21)
        return wx.Size(min_width, min(pref_height, max_height))

# Application UI class 
class tunerWindow(wx.Frame):
    
    def __init__(self, *args, **kw):
    # --- CREATE WINDOW AND SIZERS --- #

        # Initialize object and screen
        super(tunerWindow, self).__init__(*args, **kw)
        self.panel = wx.Panel(self)
        self.button_pressed = 0
         
        # Initialize all sizers used in the UI
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        settings_sizer = wx.BoxSizer(wx.VERTICAL)
        radio_sizer = wx.BoxSizer()
        self.tunetype_sizer = wx.BoxSizer()
        interval_sizer = wx.BoxSizer()
        input_sizer = wx.BoxSizer()
        submit_sizer = wx.BoxSizer()
        
        # Add title text
        title_text = wx.StaticText(self.panel, label="Sinewave Speech Tuner")
        font = title_text.GetFont(); font.PointSize += 10; font = font.Bold(); title_text.SetFont(font)
        main_sizer.Add(title_text, wx.SizerFlags().Border(wx.TOP|wx.LEFT, 15))
        
    # --- FILE INPUT --- #

        # Input sheet descriptor
        input_descriptor = wx.StaticText(self.panel, label="Select Input Spreadsheet: ")
        input_sizer.Add(input_descriptor,wx.SizerFlags().Border())

        # Input selector
        self.input_filepicker = wx.FilePickerCtrl(self.panel, path = '', wildcard="SWX files (*.swx)|*.swx", style = wx.FLP_DEFAULT_STYLE)
        self.input_filepicker.Bind(wx.EVT_FILEPICKER_CHANGED,self.dataChange)
        input_sizer.Add(self.input_filepicker,wx.SizerFlags().Border())

    # --- FREQUENCY FORCING --- #

        # Scale descriptor
        scale_descriptor = wx.StaticText(self.panel, label="Force the Frequency Averages: ")
        radio_sizer.Add(scale_descriptor,wx.SizerFlags().Border(wx.TOP,11))
        
        # Radiobuttons
        self.scale_radiobuttons = wx.RadioBox(self.panel,choices=['By Scale','By Notes','No Force'], majorDimension = 1, style = wx.RA_SPECIFY_ROWS)
        self.scale_radiobuttons.Bind(wx.EVT_RADIOBOX, self.tunerChange)
        radio_sizer.Add(self.scale_radiobuttons,wx.SizerFlags().Border())
        settings_sizer.Add(radio_sizer, wx.SizerFlags().Border())
        
        # Scale selector dropdown
        self.scale_selector = wx.ComboBox(self.panel,value= '', choices=[item for item in scales_dict], style= wx.CB_READONLY)
        self.scale_selector.Bind(wx.EVT_COMBOBOX, self.dataChange)
        self.tunetype_sizer.Add(self.scale_selector,wx.SizerFlags().Border(wx.TOP, -17))
        
        # Note selector dropdown
        self.ComboPopup = CheckboxComboPopup()
        self.note_selector = wx.ComboCtrl(self,value='Select Notes',size=(150,-1),style=wx.CB_READONLY)
        self.note_selector.SetPopupControl(self.ComboPopup); self.notes = self.ComboPopup.check_list
        self.tunetype_sizer.Add(self.note_selector,wx.SizerFlags().Border(wx.TOP, -20))

        self.no_tune = noneObj()
         
        # Parameter file selector  (NOT ACTIVATED PENDING PARAMETER PROCESSING FUNCTIONALITY) #
        # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

        # self.params_filepicker = wx.FilePickerCtrl(self.panel, path = '', wildcard="XLSX files (*.xlsx)|*.xlsx", style = wx.FLP_DEFAULT_STYLE)
        # self.params_filepicker.Bind(wx.EVT_FILEPICKER_CHANGED,self.dataChange)
        # self.tunetype_sizer.Add(self.params_filepicker,wx.SizerFlags().Border(wx.TOP, -6))
        settings_sizer.Add(self.tunetype_sizer, wx.SizerFlags().Border())

        # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    
    # --- TEMPORAL AVERAGING --- #

        # Interval descriptor
        interval_descriptor = wx.StaticText(self.panel, label="Select Sampling Interval (x10 ms): ")
        interval_sizer.Add(interval_descriptor,wx.SizerFlags().Border())
        
        # Interval entering box
        self.interval_input = wx.TextCtrl(self.panel,value= '')
        self.interval_input.Bind(wx.EVT_TEXT,self.dataChange); self.interval_input.SetMaxLength(3)
        interval_sizer.Add(self.interval_input,wx.SizerFlags().Border())

    # --- SUBMIT BUTTON --- #

        submit_button = wx.Button(self.panel,label="Submit Input Data")
        submit_button.Bind(wx.EVT_BUTTON,self.onButton)
        submit_sizer.Add(submit_button,wx.SizerFlags().Border(wx.TOP, -4))
    
    # --- ARRANGING SIZERS AND CREATING MENUBAR --- #

        # Add all sizers to the main sizer, and set it as the sizer for our panel and make a menu bar for the app
        main_sizer.Add(settings_sizer,wx.SizerFlags().Border(wx.LEFT|wx.TOP,10))
        main_sizer.Add(interval_sizer,wx.SizerFlags().Border(wx.LEFT,10))
        main_sizer.Add(input_sizer,wx.SizerFlags().Border(wx.LEFT|wx.BOTTOM,10))
        main_sizer.Add(submit_sizer,wx.SizerFlags().Border(wx.LEFT, 12))
        
        self.panel.SetSizer(main_sizer)
        self.makeMenuBar()

    # Make the app's menu bar
    def makeMenuBar(self):
        
        # Initialize wxpython menu and menu bar objects
        fileMenu = wx.Menu(); menuBar = wx.MenuBar()
        
        # Add commands to the menu, and then set it as the menu bar for the app
        exitItem = fileMenu.Append(-1, "&Exit   \tCtrl-W")
        openDocs = fileMenu.Append(-1, "&Open Documentation   \tCtrl-D")
        menuBar.Append(fileMenu, "&Sinewave Tuner")
        self.SetMenuBar(menuBar)
        
        # Add functionality to the commands
        self.Bind(wx.EVT_MENU, lambda event: self.Close(True),exitItem)
        self.Bind(wx.EVT_MENU, lambda event: os.system('open http://google.com'),openDocs)

    def dataChange(self, event = None): self.button_pressed = 0

    # React when the submit button is pressed
    def onButton(self, event):
        if self.button_pressed == 0:
            
            # Get values for interval entry, file entry, and tuner type entry
            radio_selection = self.scale_radiobuttons.GetSelection()
            interval = self.interval_input.GetValue()
            input_filepath = self.input_filepicker.GetPath()

            tuner_values = [
                scales_dict[self.scale_selector.GetValue()],                # scale selector value
                [i+1 for i in range(12) if self.notes.IsItemChecked(i)],    # note selector value
                None,                                                       # don't force value
                # self.params_filepicker.GetPath()                          # params selector value
            ][radio_selection]                                      # ---> takes the checked selector's value
            
            # Set the app's corresponding attributes to these values, provided they are not invalid
            self.interval = interval.isdigit() and int(interval)
            self.filepath = input_filepath or False
            self.scale = ([0] and tuner_values is None) or (tuner_values or False)
            
            # Run the main tuning function and 'press' the button (FINISH ME)
            if all([self.interval, self.filepath, self.scale]):
                tune_cols(self.filepath, self.interval, self.scale, tune_freqs=(self.scale is [0]), open_output=True)
                self.button_pressed = 1

    # React when a new tuner radiobutton is selected
    def tunerChange(self, event):
        elems = [n.GetWindow() for n in self.tunetype_sizer.Children]+[noneObj()]
        {n.Hide() for n in elems}; elems[self.scale_radiobuttons.GetSelection()].Show()

        self.panel.Fit(); self.dataChange()
        
# ----------------------------- MAIN PROGRAM LOOP ----------------------------- #
if __name__ == '__main__':
    app = wx.App()
    frm = tunerWindow(None, title="CTSF's Sinewave Speech Musicalizer",size=(500,250))
    frm.Show(); frm.note_selector.Hide(); #frm.params_selector.Hide()
    frm.panel.Fit()
    app.MainLoop()
