# ----------------------------- IMPORTS ----------------------------- #
import wx
import os
import pandas as pd
import numpy as np
from math import ceil, floor, log
import tkinter as tk
from tkinter import filedialog

version='0.1.0'

# ----------------------------- MISCELLANEOUS ----------------------------- #
scalesDict = {
    'C Major':[1,3,5,6,8,10,12],'D Major':[2,3,5,7,8,10,12],'E Major':[2,4,5,7,9,10,12],
    'F Major':[1,3,5,6,8,10,11],'G Major':[8, 10, 12, 1, 3, 5, 6],
    'A Major':[10, 12, 1, 3, 5, 6, 8], 'B Major':[12, 1, 3, 5, 6, 8, 10],'Black Notes Only':[2,4,7,9,11]
}

pianoNotes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

# ----------------------------- THE TUNING PART ----------------------------- #
def toFreq(note): return 27.5 * (2 ** ((note - 1) / 12))

def adjust_freq(freq,scale):
    fkey=round(log(freq / 27.5, pow(2,1/12)), 0); octKey = int(fkey - (fkey - 3) % 12)
    below, octave, above = [toFreq(octKey - 12 + note) for note in scale], [toFreq(octKey + note) for note in scale], [toFreq(octKey + 12 + note) for note in scale]
    closest2 = [max([0] + [item for item in below + octave if 27.5 <= item <= freq]), min([0] + [item for item in octave + above if freq <= item <= 4187])]
    freqDist = [abs(freq - noteFreq) for noteFreq in closest2]
    return closest2[freqDist.index(min(freqDist))]

def tuneCols(df,interval,scale):

    out_df = pd.DataFrame(); df_first = df[df.columns[0]]
    modlen=len(df_first)-len(df_first)%interval
    out_df['Time (ms)'] = df_first[:modlen]
    
    for formant in range(1,int((len(df.columns)-1)/2)+1):
        freq_col = df['F'+str(formant)]; amp_col = df['A'+str(formant)]
        out_column_1 = []; out_column_2 = []
        
        for i in range(int(floor(len(df_first)/interval))):   
        
            {out_column_1.append(freq_col[i*interval+j] * ceil(amp_col[i*interval+j])) for j in range(interval) if i*interval+j < len(df_first)}
            nz=len(np.nonzero(out_column_1[i*interval:])[0]); adj_freq=0.0
            if nz > 0: adj_freq = adjust_freq(sum(out_column_1[i*interval:])/nz, scale)
            for item in np.where(np.array(out_column_1[i*interval:])!=0, adj_freq, freq_col[i*interval:(i+1)*interval]): out_column_2.append(item)
            
        out_df[f'F{formant}'] = out_column_2
        out_df[f'A{formant}'] = amp_col
        
    return out_df

def tune(scaleNotes, filepath, interval):
    df = pd.read_excel(filepath); return tuneCols(df,interval,scaleNotes)
    ##
# ----------------------------- APPLICATION UI ----------------------------- #

class ListCtrl(wx.ListCtrl):

    def __init__(self, *args, **kw):
        super(ListCtrl, self).__init__(*args, **kw, style=wx.LC_REPORT)
        self.EnableCheckBoxes()

class CheckboxComboPopup(wx.ComboPopup):
    
    def Init(self):
        self.sampleList = pianoNotes
        self.CheckList = None
        
    def Create(self, parent):
        self.CheckList = ListCtrl(parent); self.CheckList.InsertColumn(0,'')
        for item in self.sampleList: self.CheckList.InsertItem(12,item)
        return True
    
    def GetControl(self): return self.CheckList

    def GetAdjustedSize(self,minWidth,prefHeight,maxHeight):
        pref_height = (len(self.sampleList) * 21)
        return wx.Size(minWidth, min(pref_height, maxHeight))

class tunerWindow(wx.Frame):
    
    def __init__(self, *args, **kw):
        # ensure the parent's __init__ is called
        super(tunerWindow, self).__init__(*args, **kw)

        # create a panel in the frame
        self.panel = wx.Panel(self)
        self.ButtonPressed = 0
        self.ActiveTuner = 'scale'


        main_sizer = wx.BoxSizer(wx.VERTICAL)           # Initializing Sizers
        settingsSizer = wx.BoxSizer(wx.HORIZONTAL)
        intervalSizer = wx.BoxSizer(wx.HORIZONTAL)
        inputSizer = wx.BoxSizer(wx.HORIZONTAL)
        submitSizer = wx.BoxSizer(wx.HORIZONTAL)
        
        titleText = wx.StaticText(self.panel, label="Sinewave Speech Tuner")                                                                                          # Add Title Text
        font = titleText.GetFont(); font.PointSize += 10; font = font.Bold()
        titleText.SetFont(font)
        main_sizer.Add(titleText, wx.SizerFlags().Border(wx.TOP|wx.LEFT, 15))
        
        scaleDescriptor = wx.StaticText(self.panel, label="Select Tuning: ")                                                                                            # Scale Descriptor
        settingsSizer.Add(scaleDescriptor,wx.SizerFlags().Border(wx.TOP,11))
        
        self.scaleRadiobuttons = wx.RadioBox(self.panel,choices=['By Scale','By Notes'],style = wx.RA_SPECIFY_COLS)                # Radiobuttons
        self.scaleRadiobuttons.Bind(wx.EVT_RADIOBOX, self.tunerChange)
        settingsSizer.Add(self.scaleRadiobuttons,wx.SizerFlags().Border())
        
        self.scaleSelector = wx.ComboBox(self.panel,value= '', choices=[item for item in scalesDict], style= wx.CB_READONLY)      # Scale Selector Dropdown
        self.scaleSelector.Bind(wx.EVT_COMBOBOX, self.dataChange)
        settingsSizer.Add(self.scaleSelector,wx.SizerFlags().Border(wx.TOP|wx.LEFT,8))
        
        self.ComboPopup = CheckboxComboPopup()                                                                                                                            # Note Selector Dropdown
        self.noteSelector = wx.ComboCtrl(self,value='Select Notes',size=(150,-1),style=wx.CB_READONLY)
        self.noteSelector.SetPopupControl(self.ComboPopup); self.notes = self.ComboPopup.CheckList
        settingsSizer.Add(self.noteSelector,wx.SizerFlags().Border(wx.TOP|wx.LEFT,7))
        
        intervalDescriptor = wx.StaticText(self.panel, label="Select Sampling Interval (x10 ms): ")                                                        # Interval descriptor
        intervalSizer.Add(intervalDescriptor,wx.SizerFlags().Border())
        inputDescriptor = wx.StaticText(self.panel, label="Select Input Spreadsheet: ")                                                                         # Input sheet descriptor
        inputSizer.Add(inputDescriptor,wx.SizerFlags().Border())
        
        self.interval_input = wx.TextCtrl(self.panel,value= '')                                                                                                                   # Interval entering box
        self.interval_input.Bind(wx.EVT_TEXT,self.dataChange)
        self.interval_input.SetMaxLength(3)
        intervalSizer.Add(self.interval_input,wx.SizerFlags().Border())

        self.filepicker = wx.FilePickerCtrl(self.panel, path = '', wildcard="XLSX files (*.xlsx)|*.xlsx", style = wx.FLP_DEFAULT_STYLE) # Input Selector
        self.filepicker.Bind(wx.EVT_FILEPICKER_CHANGED,self.dataChange)
        inputSizer.Add(self.filepicker,wx.SizerFlags().Border())

        submitButton = wx.Button(self.panel,label="Submit Input Data")                                                                                                  # Submit Button
        submitButton.Bind(wx.EVT_BUTTON,self.onButton)
        submitSizer.Add(submitButton,wx.SizerFlags().Border())
        
        main_sizer.Add(settingsSizer,wx.SizerFlags().Border(wx.LEFT|wx.TOP,15)) # Add all sizers to the main sizer, and set it as the sizer for our panel
        main_sizer.Add(intervalSizer,wx.SizerFlags().Border(wx.LEFT|wx.BOTTOM,10))
        main_sizer.Add(inputSizer,wx.SizerFlags().Border(wx.LEFT|wx.BOTTOM,10))
        main_sizer.Add(submitSizer,wx.SizerFlags().Border(wx.LEFT|wx.BOTTOM,15))
        self.panel.SetSizer(main_sizer)

        self.makeMenuBar()

    def makeMenuBar(self):

        fileMenu = wx.Menu(); menuBar = wx.MenuBar()
        
        exitItem = fileMenu.Append(-1, "&Exit   \tCtrl-W")
        openDocs = fileMenu.Append(-1, "&Open Documentation   \tCtrl-D")
        menuBar.Append(fileMenu, "&Sinewave Tuner")
        self.SetMenuBar(menuBar)
        
        self.Bind(wx.EVT_MENU, lambda event: self.Close(True),exitItem)
        self.Bind(wx.EVT_MENU, lambda event: os.system('open http://google.com'),openDocs)

    #def OnExit(self, event): self.Close(True)
    def dataChange(self, event): self.ButtonPressed = 0

    def onButton(self, event):
        if self.ButtonPressed == 0:
            
            interval = self.interval_input.GetValue()
            filepath = self.filepicker.GetPath()
            tunerValues = [self.scaleSelector.GetValue(), [i+1 for i in range(12) if self.notes.IsItemChecked(i)]][self.ActiveTuner=='notes']
            
            self.interval = (interval if interval.isdigit() else False)
            self.filepath = (filepath if filepath != '' else False)
            self.scale = (tunerValues if tunerValues != [] else False)
            
            if self.interval and self.filepath and self.scale:
#                 tune(self.scale,self.inputSheet,self.interval)
#                 os.system('open output_sheet.xlsx')
                self.ButtonPressed = 1

    def tunerChange(self, event):
        
        self.ActiveTuner = ['scale','notes'][self.scaleRadiobuttons.GetSelection()]
        if self.ActiveTuner == 'notes': self.scaleSelector.Hide(); self.noteSelector.Show()
        else: self.noteSelector.Hide(); self.scaleSelector.Show()
        
        self.panel.Fit(); self.dataChange(None)
        
# ----------------------------- MAIN PROGRAM LOOP ----------------------------- #
if __name__ == '__main__':
    app = wx.App()
    
    frm = tunerWindow(None, title="CTSF's Sinewave Speech Musicalizer",size=(550,250))
    frm.Show(); frm.noteSelector.Hide(); frm.panel.Fit()
    
    app.MainLoop()
