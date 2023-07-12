import numpy as np
from flask import Markup
from dominate import tags

import psynet.experiment
from psynet.asset import ExperimentAsset, Asset, LocalStorage, DebugStorage, FastFunctionAsset, S3Storage  # noqa
from psynet.consent import NoConsent
from psynet.modular_page import PushButtonControl, ModularPage, AudioPrompt, AudioRecordControl
from psynet.js_synth import JSSynth, Note, HarmonicTimbre
from psynet.timeline import Timeline, Event

from psynet.page import InfoPage, SuccessfulEndPage
from psynet.timeline import Event, ProgressDisplay, ProgressStage, Timeline, CodeBlock, Module
from psynet.trial.static import StaticNode, StaticTrial, StaticTrialMaker
from psynet.trial.audio import AudioRecordTrial

# experiment
from .consent import consent  # TODO: use my Oxford consent here whean ready
from .instructions import instructions
from .questionnaire import debrief, questionnaire, STOMPR, TIPI
from .pre_screens import volume_calibration, audio_output_question, audio_input_question, mic_test
from .params import singing_2intervals

# sing4me
from sing4me import singing_extract as sing
from sing4me import melodies


##########################################################################################
# Global
##########################################################################################
TIME_ESTIMATE_TRIAL = 10

# Set the size and range of the grid for the stimulus space
NUM_PARTICIPANTS = 100

N_REPEAT_TRIALS = 6
INITIAL_RECRUIT_SIZE = 20
SAVE_PLOT = True

# singing
roving_width = 2.5
roving_mean = dict(
    default=55,
    low=49,
    high=61
    )

NUM_NOTES = 3
NUM_INT = NUM_NOTES - 1

SYLLABLE = "TA"
TIME_AFTER_SINGING = 1

REFERENCE_MODE = "pitch_mode"  # pitch_mode vs previous_note vs first_note
MAX_ABS_INT_ERROR_ALLOWED = 5.5  # set to 999 if NUM_INT > 2
MAX_INT_SIZE = 999
MAX_MELODY_PITCH_RANGE = 999  # deactivated
MAX_INTERVAL2REFERENCE = 10  # set to 7.5 if NUM_INT > 2
NUM_CHAINS_EXPERIMENT = 200  # decrease if NUM_INT > 2
NUM_TRIALS_PARTICIPANT = 40  # decrease if NUM_INT > 2

# timbre
note_duration_tonejs = 0.8
note_silence_tonejs = 0
TIMBRE = dict(
    default=HarmonicTimbre(
        attack=0.01,  # Attack phase duration in seconds
        decay=0.05,  # Decay phase duration in seconds
        sustain_amp=0.6,  # Amplitude fraction to decay to relative to max amplitude --> 0.4, 0.7
        release=0.55,  # Release phase duration in seconds
        num_harmonics=10,  # Acd ctual number of partial harmonics to use
        roll_off=14,  # Roll-off in units of dB/octave,
    )
)
pitch_duration = note_duration_tonejs + note_silence_tonejs


# durations
def estimate_time_per_trial(
    # estimate time for trials: melody and singing duration
        pitch_duration,
        num_pitches,
        time_after_singing
):
    melody_duration = pitch_duration * num_pitches
    singing_duration = melody_duration + time_after_singing
    return melody_duration, singing_duration


melody_duration, singing_duration = estimate_time_per_trial(
            pitch_duration,
            (NUM_NOTES + 1),
            TIME_AFTER_SINGING
        )

##########################################################################################
# Stimuli
##########################################################################################
# Here we define the stimulus set in an analogous way to the static_audio demo,
# except we randomise the start_frequency from a continuous range.

# TODO: Kevin, we just want to use integer semitones, and make sure the trials per particiapnt is right
# TODO: 120 trials maximum

grid_size = 11
grid_range = 5

TRIALS_PER_PARTICIPANT = grid_size * grid_size  # TODO: this calculation is wrong


nodes = [
    StaticNode(
        definition={
            # "intervals": interval,
            "target_x_int": x,
            "target_y_int": y,
        },
    )
    for x in np.linspace(-grid_range, grid_range, grid_size)
    for y in np.linspace(-grid_range, grid_range, grid_size)
    # for interval in intervals
]


########################################################################################################################
# experiment parts
########################################################################################################################
def equipment_test():
    # Ask about what equipment they are using
    return Module(
        "equipment_test",
        volume_calibration(),
        audio_output_question(),
        audio_input_question(),
        mic_test(),
    )


class SingingTrial(AudioRecordTrial, StaticTrial):
    time_estimate = TIME_ESTIMATE_TRIAL
    # wait_for_feedback = True

    def finalize_definition(self, definition, experiment, participant):
        reference_pitch = melodies.sample_reference_pitch(
            roving_mean["high"],
            roving_width,
        )
        definition["reference_pitch"] = reference_pitch

        intervals = [definition["target_x_int"], definition["target_y_int"]]
        definition["target_intervals"] = intervals

        definition["target_pitches"] = melodies.convert_interval_sequence_to_absolute_pitches(
                intervals=intervals,
                reference_pitch=reference_pitch,
                reference_mode="previous_note",   # pitch mode
            )
        return definition

    def show_trial(self, experiment, participant):

        # convert to right register
        if self.participant.var.register == "high":
            target_pitches = self.definition["target_pitches"]
        else:
            target_pitches = [(i - 12) for i in self.definition["target_pitches"]]

        current_trial = self.position + 1
        show_current_trial = f'<i>Trial number {current_trial} out of {(TRIALS_PER_PARTICIPANT + N_REPEAT_TRIALS)} trials.</i>'

        return ModularPage(
        "singing",
        JSSynth(
            Markup(
                f"""
                <h3>Sing back the melody</h3>
                <hr>
                <b><b>This melody has {len(target_pitches)} notes</b></b>: Sing each note clearly using the syllable '{SYLLABLE}'.
                <br><i>Leave silent gaps between notes.</i>
                <br><br>
                {show_current_trial}
                <hr>
                """
            ),
            [Note(pitch) for pitch in target_pitches],
            timbre=TIMBRE,
            default_duration=note_duration_tonejs,
            default_silence=note_silence_tonejs,
        ),
        control=AudioRecordControl(
            duration=singing_duration,
            show_meter=True,
            controls=False,
            auto_advance=False,
            bot_response_media="example_audio.wav",
        ),
        events={
            "promptStart": Event(is_triggered_by="trialStart"),
            "recordStart": Event(is_triggered_by="promptEnd", delay=0.25),
        },
        progress_display=ProgressDisplay(
            stages=[
                ProgressStage(melody_duration, "Listen to the melody...", "orange"),
                ProgressStage(singing_duration, "Recording...SING THE MELODY!", "red"),
                ProgressStage(0.5, "Done!", "green", persistent=True),
            ],
        ),
        time_estimate=TIME_ESTIMATE_TRIAL,
    )

    def analyze_recording(self, audio_file: str, output_plot: str):
        # convert to right register
        if self.participant.var.register == "high":
            target_pitches = self.definition["target_pitches"]
            reference_pitch = self.definition["reference_pitch"]
        else:
            target_pitches = [(i - 12) for i in self.definition["target_pitches"]]
            reference_pitch = self.definition["reference_pitch"] - 12

        raw = sing.analyze(
            audio_file,
            singing_2intervals,
            target_pitches=target_pitches,
            plot_options=sing.PlotOptions(
                save=SAVE_PLOT, path=output_plot, format="png"
            ),
        )
        raw = [
            {key: melodies.as_native_type(value) for key, value in x.items()} for x in raw
        ]
        sung_pitches = [x["median_f0"] for x in raw]
        sung_intervals = melodies.convert_absolute_pitches_to_interval_sequence(
            sung_pitches,
            "previous_note"
        )
        target_intervals = melodies.convert_absolute_pitches_to_interval_sequence(
            target_pitches,
            "previous_note"
        )
        sung_intervals2reference = melodies.convert_absolute_pitches_to_intervals2reference(
            sung_pitches,
            reference_pitch
        )
        stats = sing.compute_stats(
            sung_pitches,
            target_pitches,
            sung_intervals,
            target_intervals
        )
        is_failed = melodies.failing_criteria(
            sung_intervals,
            sung_pitches,
            reference_pitch,
            NUM_INT,
            MAX_INT_SIZE,  # only used in interval representation, currently deactivated
            MAX_MELODY_PITCH_RANGE,  # only used in interval representation, currently deactivated
            REFERENCE_MODE,
            stats,
            MAX_ABS_INT_ERROR_ALLOWED,  # deactivated
            (MAX_INTERVAL2REFERENCE * 2)  # only used in pitch mode
        )

        failed = is_failed["failed"]
        reason = is_failed["reason"]

        # convert back to high register
        if self.participant.var.register == "low":
            target_pitches = [(i + 12) for i in target_pitches]
            sung_pitches = [(i + 12) for i in sung_pitches]
            reference_pitch = reference_pitch + 12

        return {
            "failed": failed,
            "reason": reason,
            "register": self.participant.var.register,
            "reference_pitch": reference_pitch,
            "target_pitches": target_pitches,
            "num_target_pitches": len(target_pitches),
            "target_intervals": target_intervals,
            "sung_pitches": sung_pitches,
            "num_sung_pitches": len(sung_pitches),
            "sung_intervals": sung_intervals,
            "sung_intervals2reference": sung_intervals2reference,
            "raw": raw,
            "save_plot": SAVE_PLOT,
            "stats": stats,
        }


class Exp(psynet.experiment.Experiment):
    label = "Static singing experiment"
    asset_storage = LocalStorage()
    # asset_storage = S3Storage("psynet-tests", "audio-record")

    config = {
        "show_bonus": False
    }

    timeline = Timeline(
        NoConsent(),
        InfoPage(
            "This experiment requires you to wear headphones. Please ensure you have plugged yours in now.",
            time_estimate=3,
        ),
        CodeBlock(lambda participant: participant.var.set("register", "low")),  # here I'm cheating and setting register manually
        # volume_calibration(TIMBRE, note_duration_tonejs, note_silence_tonejs),
        # InfoPage(
        #     """
        #     We will now perform a short listening test to verify that your audio is working properly.
        #     This test will be difficult to pass unless you listen carefully over your headphones.
        #     Press 'Next' when you are ready to start.
        #     """,
        #     time_estimate=5,
        # ),
        # AntiphaseHeadphoneTest(),
        instructions(),
        StaticTrialMaker(
            id_="singing_main_experiment",
            trial_class=SingingTrial,
            nodes=nodes,
            expected_trials_per_participant=TRIALS_PER_PARTICIPANT,
            max_trials_per_participant=TRIALS_PER_PARTICIPANT,
            recruit_mode="n_participants",
            allow_repeated_nodes=False,
            n_repeat_trials=N_REPEAT_TRIALS,
            balance_across_nodes=True,
            target_n_participants=NUM_PARTICIPANTS,
            check_performance_at_end=False,  # TODO: we want to implement a performance check using get_end_feedback_passed_page
        ),
        questionnaire(),
        InfoPage("Next, we would like to ask you some questions about your music preferences (0.15 extra bonus)", time_estimate=3),
        STOMPR(),
        InfoPage("Finally, we would like to ask you some questions about your personality (0.15 extra bonus)", time_estimate=3),
        TIPI(),
        # debrief(),
        SuccessfulEndPage(),
    )

    # uncomment for testing
    # test_n_bots = 2
    #
    # def test_experiment(self):
    #     # To run this test, manually change TRIALS_PER_PARTICIPANT to 8 and grid size to 4
    #     super().test_experiment()
    #
    #     nodes = StaticNode.query.filter_by(trial_maker_id="rating_main_experiment").all()
    #
    #     for n in nodes:
    #         n_trials = len(n.infos())
    #         assert n_trials == 1
