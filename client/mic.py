#!/usr/bin/env python2
# -*- coding: utf-8-*-
"""
    The Mic class handles all interactions with the microphone and speaker.
"""
import logging
import tempfile
import wave
import audioop
import pyaudio
import alteration
import jasperpath
import os
import speech_recognition as sr
import time

#logging.basicConfig(level=logging.DEBUG)

class Mic:

    speechRec = None
    speechRec_persona = None
   
    def __init__(self, speaker, stt_engine):
        """
        Initiates the pocketsphinx instance.

        Arguments:
        speaker -- handles platform-independent audio output
        passive_stt_engine -- performs STT while Jasper is in passive listen
                              mode
        acive_stt_engine -- performs STT while Jasper is in active listen mode
        """
        self._logger = logging.getLogger(__name__)
        self.speaker = speaker
        self.stt_engine = stt_engine
        self._logger.info("Initializing PyAudio. ALSA/Jack error messages " +
                          "that pop up during this process are normal and " +
                          "can usually be safely ignored.")
        self._audio = pyaudio.PyAudio()
        self._logger.info("Initialization of PyAudio completed.")
       
        
    def __del__(self):
        self._audio.terminate()
        

    def passiveListen(self, PERSONA,LISTEN_TIME = 5, THRESHOLD_TIME = 5):
		"""
		First the function listen for a number of seconds (THRESHOLD_TIME) 
		to allow to establish threshold.
		Listens for PERSONA in everyday sound. Times out after LISTEN_TIME, so
		needs to be restarted.
		"""
		r = sr.Recognizer()
		m = sr.Microphone(device_index=0, sample_rate=44100)
		print("Ajustando el reconocedor al sonido ambiente por %s segundos" % str(LISTEN_TIME))
		with m as source:
			# we only need to calibrate once, before we start listening
			r.adjust_for_ambient_noise(source, duration = THRESHOLD_TIME) 
			print("Reconocedor ajustado, ya se puede hablar")
			try:
				audio = r.listen(m, timeout=LISTEN_TIME)
				mensaje = self.stt_engine.transcribe(audio)
				fraseInterpretada = mensaje.encode('utf-8')
				self._logger.debug(fraseInterpretada)
			except sr.WaitTimeoutError:
				print("No se ha escuchado nada")
				fraseInterpretada = ""
			
		if PERSONA in fraseInterpretada:
			self._logger.debug("localizada palabra clave")
		
			return (r.energy_threshold, PERSONA)
		
		return (r.energy_threshold, None)
		
		
			
        
    def activeListen(self, THRESHOLD=None, LISTEN_TIME=5, MUSIC=False):
        """
            Records until a second of silence or times out after 12 seconds

            Returns the first matching string or None
        """

        options = self.activeListenToAllOptions(THRESHOLD, LISTEN_TIME, MUSIC)
        if options:
            return options[0]

    def activeListenToAllOptions(self, threshold , listen_time=5,
                                 MUSIC=False):
		"""
			Records until a second of silence or times out after 12 seconds
		
			Returns a list of the matching options or None
		"""
		
		self.speaker.play(jasperpath.data('audio', 'beep_hi.wav'))
		
		r = sr.Recognizer()
		r.energy_threshold = threshold
		m = sr.Microphone(device_index=0, sample_rate=44100)
		
		with m as source:
			
			try:
				audio = r.listen(m, timeout=listen_time)
				mensaje = self.stt_engine.transcribe(audio)
				fraseInterpretada = mensaje.encode('utf-8')
				self._logger.debug(fraseInterpretada)
				print(fraseInterpretada)
				return fraseInterpretada
			except sr.WaitTimeoutError:
				print("No se ha escuchado nada")
				return ""

    def say(self, phrase,
            OPTIONS=" -vdefault+m3 -p 40 -s 160 --stdout > say.wav"):
        # alter phrase before speaking
        phrase = alteration.clean(phrase)
        self.speaker.say(phrase)
        
if __name__ == "__main__":
	
	pass
