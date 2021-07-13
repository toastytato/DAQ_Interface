from math import cos, sin
import numpy as np


def three_dim_alignment(phi, theta, amplitude, kx, ky, kz):
    # peak to peak voltage
    VX_PP = kx*amplitude*cos(phi)*cos(theta)
    VY_PP = ky*amplitude*cos(phi)*sin(theta)
    VZ_PP = kz*amplitude*sin(phi)

    return [VX_PP, VY_PP, VZ_PP]

def three_dim_rotation(phi, theta, amplitude, kx, ky, kz):
    # peak to peak voltage
    VX_PP = kx*amplitude*cos(phi)
    VY_PP = ky*amplitude*cos(phi)
    VZ_PP = kz*amplitude*sin(phi)

    return [VX_PP, VY_PP, VZ_PP]


def calculate_rms_value(data, sample_rate, frequency):
    # freq = cycles / sec
    # period = 1 / freq
    # rate = samples / sec
    # data = samples
    # samples / cycle = rate * period

    if frequency != 0:
        num_samples_in_period = int(sample_rate * (1 / frequency))

        if num_samples_in_period < 500:
            num_samples_in_period = 500
    else:
        return data[0]  # only need 1st data point since DC

    # period_data = data[:num_samples_in_period]
    period_data = data
    # print(len(period_data))
    rms = round(np.sqrt(np.mean(period_data ** 2)), 3)

    return rms


# creates the sine wave to output
class WaveGenerator:
    def __init__(self):
        self.reset = False
        self.counter = 0
        self.last_freq = 0
        self.output_times = []

    def reset_counter(self):
        self.reset = True

    def generate_wave(self, voltage, frequency, shift, sample_rate, samples_per_chunk):
        """

        :param voltage: RMS voltage, which will be converted to amplitude in signal
        :param frequency: Determines if AC or DC. Frequency of signal in Hz if not 0, creates DC signal if frequency is 0
        :param shift: The phase shift in degrees
        :param sample_rate: # of data points per second
        :param samples_per_chunk: # of data points that will be written in this output buffer
        :return: np.array with waveform of input params

        """

        # return DC voltage if frequency is 0
        if frequency == 0:
            return np.full(shape=samples_per_chunk, fill_value=voltage)

        # determine if it needs to shift frequency based on which part of the waveform it's on
        if self.last_freq != frequency or self.reset:
            self.reset = False
            self.counter = 0
            self.last_freq = frequency
        else:
            self.counter += 1

        amplitude = np.sqrt(2) * voltage  # get peak voltage from RMS voltage
        # waves_per_sec = frequency
        rad_per_sec = 2 * np.pi * frequency
        chunks_per_sec = sample_rate / samples_per_chunk
        sec_per_chunk = 1 / chunks_per_sec
        waves_per_chunk = frequency / chunks_per_sec

        # phase shift based on parameter
        phase_shift = 2 * np.pi * shift / 360

        # shift the frequency if starting in the middle of a wave
        start_fraction = waves_per_chunk % 1
        freq_shifter = self.counter * 2 * np.pi * start_fraction

        self.output_times = np.linspace(
            start=0, stop=sec_per_chunk, num=samples_per_chunk
        )
        output_waveform = amplitude * np.sin(
            self.output_times * rad_per_sec + freq_shifter - phase_shift
        )

        return output_waveform

    # less used
    def generate_n_periods(self, voltage, frequency, shift, sample_rate, num=1):
        amplitude = np.sqrt(2) * voltage  # get peak voltage from RMS voltage

        rad_per_sec = 2 * np.pi * frequency
        samples_per_period = int(sample_rate / rad_per_sec)

        phase_shift = 2 * np.pi * shift / 360

        self.output_times = np.linspace(
            start=0, stop=num / frequency, num=samples_per_period * num
        )
        output_waveform = amplitude * np.sin(
            self.output_times * rad_per_sec - phase_shift
        )
        return output_waveform