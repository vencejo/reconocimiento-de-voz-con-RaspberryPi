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

logging.basicConfig(level=logging.DEBUG)
fraseInterpretada = ""

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
		self._logger.debug("Ajustando el reconocedor al sonido ambiente")
		with m as source:
			# we only need to calibrate once, before we start listening
			r.adjust_for_ambient_noise(source, duration = THRESHOLD_TIME) 
			self._logger.debug("Reconocedor ajustado, ya se puede hablar")
			
			audio = r.listen(m, timeout=LISTEN_TIME)
			mensaje = self.stt_engine.transcribe(audio)
			fraseInterpretada = mensaje.encode('utf-8')
			self._logger.debug(fraseInterpretada)
			
		
		if PERSONA in fraseInterpretada:
			self._logger.debug("localizada palabra clave")
		
			return (r.energy_threshold, PERSONA)
		
		return (r.energy_threshold, None)
		
		
			
        
    def activeListen(self, THRESHOLD=None, LISTEN=True, MUSIC=False):
        """
            Records until a second of silence or times out after 12 seconds

            Returns the first matching string or None
        """

        options = self.activeListenToAllOptions(THRESHOLD, LISTEN, MUSIC)
        if options:
            return options[0]

    def activeListenToAllOptions(self, THRESHOLD=None, LISTEN=True,
                                 MUSIC=False):
        """
            Records until a second of silence or times out after 12 seconds

            Returns a list of the matching options or None
        """

        # check if no threshold provided
        if THRESHOLD is None:
            THRESHOLD = self.fetchThreshold()

        self.speaker.play(jasperpath.data('audio', 'beep_hi.wav'))

        # prepare recording stream
        stream = self._audio.open(format=pyaudio.paInt16,
                                  channels=1,
                                  rate=RATE,
                                  input=True,
                                  frames_per_buffer=CHUNK)

        frames = []
        # increasing the range # results in longer pause after command
        # generation
        lastN = [THRESHOLD * 1.2 for i in range(30)]

        for i in range(0, RATE / CHUNK * LISTEN_TIME):

            data = stream.read(CHUNK)
            frames.append(data)
            score = self.getScore(data)

            lastN.pop(0)
            lastN.append(score)

            average = sum(lastN) / float(len(lastN))

            # TODO: 0.8 should not be a MAGIC NUMBER!
            if average < THRESHOLD * 0.8:
                break

        self.speaker.play(jasperpath.data('audio', 'beep_lo.wav'))

        # save the audio data
        stream.stop_stream()
        stream.close()

        with tempfile.SpooledTemporaryFile(mode='w+b') as f:
            wav_fp = wave.open(f, 'wb')
            wav_fp.setnchannels(1)
            wav_fp.setsampwidth(pyaudio.get_sample_size(pyaudio.paInt16))
            wav_fp.setframerate(RATE)
            wav_fp.writeframes(''.join(frames))
            wav_fp.close()
            f.seek(0)
            return self.active_stt_engine.transcribe(f)

    def say(self, phrase,
            OPTIONS=" -vdefault+m3 -p 40 -s 160 --stdout > say.wav"):
        # alter phrase before speaking
        phrase = alteration.clean(phrase)
        self.speaker.say(phrase)
        
if __name__ == "__main__":
	
	pass
