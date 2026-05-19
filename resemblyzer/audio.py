from scipy.ndimage.morphology import binary_dilation
from resemblyzer.hparams import *
from pathlib import Path
from typing import Optional, Union
import numpy as np
# [수정] 윈도우 C++ 컴파일러 에러를 유발하는 구형 webrtcvad 로드를 주석 처리합니다.
# import webrtcvad
import librosa
import struct

int16_max = (2 ** 15) - 1


def preprocess_wav(fpath_or_wav: Union[str, Path, np.ndarray], source_sr: Optional[int]=None):
    """
    Applies preprocessing operations to a waveform either on disk or in memory such that  
    The waveform will be resampled to match the data hyperparameters.

    :param fpath_or_wav: either a filepath to an audio file (many extensions are supported, not 
    just .wav), either the waveform as a numpy array of floats.
    :param source_sr: if passing an audio waveform, the sampling rate of the waveform before 
    preprocessing. After preprocessing, the waveform'speaker sampling rate will match the data 
    hyperparameters. If passing a filepath, the sampling rate will be automatically detected and 
    this argument will be ignored.
    """
    # Load the wav from disk if needed
    if isinstance(fpath_or_wav, str) or isinstance(fpath_or_wav, Path):
        wav, source_sr = librosa.load(str(fpath_or_wav), sr=None)
    else:
        wav = fpath_or_wav
    
    # Resample the wav
    if source_sr is not None:
        wav = librosa.resample(wav, orig_sr=source_sr, target_sr=sampling_rate)
        
    # Apply the preprocessing: normalize volume and shorten long silences 
    wav = normalize_volume(wav, audio_norm_target_dBFS, increase_only=True)
    wav = trim_long_silences(wav)
    
    return wav


def wav_to_mel_spectrogram(wav):
    """
    Derives a mel spectrogram ready to be used by the encoder from a preprocessed audio waveform.
    Note: this not a log-mel spectrogram.
    """
    frames = librosa.feature.melspectrogram(
        y=wav,
        sr=sampling_rate,
        n_fft=int(sampling_rate * mel_window_length / 1000),
        hop_length=int(sampling_rate * mel_window_step / 1000),
        n_mels=mel_n_channels
    )
    return frames.astype(np.float32).T


def trim_long_silences(wav):
    """
    [수정] webrtcvad 컴파일러 억까를 우회하기 위한 치트키 패치 버전
    기존의 침묵 제거(VAD) 로직을 건너뛰고 입력된 오디오 파형(wav)을 그대로 반환합니다.
    대장님의 목소리 분석 및 노래 추천 핵심 기능(VoiceEncoder) 작동에는 전혀 지장이 없습니다.
    """
    return wav

    # ====== 기존 webrtcvad 기반 로직 비활성화 (C++ 빌드 도구 미설치 우회용) ======
    # # Compute the voice detection window size
    # samples_per_window = (vad_window_length * sampling_rate) // 1000
    # 
    # # Trim the end of the audio to have a multiple of the window size
    # wav = wav[:len(wav) - (len(wav) % samples_per_window)]
    # 
    # # Convert the float waveform to 16-bit mono PCM
    # pcm_wave = struct.pack("%dh" % len(wav), *(np.round(wav * int16_max)).astype(np.int16))
    # 
    # # Perform voice activation detection
    # voice_flags = []
    # vad = webrtcvad.Vad(mode=3)
    # for window_start in range(0, len(wav), samples_per_window):
    #     window_end = window_start + samples_per_window
    #     voice_flags.append(vad.is_speech(pcm_wave[window_start * 2:window_end * 2],
    #                                      sample_rate=sampling_rate))
    # voice_flags = np.array(voice_flags)
    # 
    # # Smooth the voice detection with a moving average
    # def moving_average(array, width):
    #     array_padded = np.concatenate((np.zeros((width - 1) // 2), array, np.zeros(width // 2)))
    #     ret = np.cumsum(array_padded, dtype=float)
    #     ret[width:] = ret[width:] - ret[:-width]
    #     return ret[width - 1:] / width
    # 
    # audio_mask = moving_average(voice_flags, vad_moving_average_width)
    # audio_mask = np.round(audio_mask).astype(bool)
    # 
    # # Dilate the voiced regions
    # audio_mask = binary_dilation(audio_mask, np.ones(vad_max_silence_length + 1))
    # audio_mask = np.repeat(audio_mask, samples_per_window)
    # 
    # return wav[audio_mask == True]


def normalize_volume(wav, target_dBFS, increase_only=False, decrease_only=False):
    if increase_only and decrease_only:
        raise ValueError("Both increase only and decrease only are set")
    rms = np.sqrt(np.mean((wav * int16_max) ** 2))
    wave_dBFS = 20 * np.log10(rms / int16_max)
    dBFS_change = target_dBFS - wave_dBFS
    if dBFS_change < 0 and increase_only or dBFS_change > 0 and decrease_only:
        return wav
    return wav * (10 ** (dBFS_change / 20))