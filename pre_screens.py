import json

from flask import Markup

from dominate import tags

from psynet.page import InfoPage, ModularPage, wait_while
from psynet.modular_page import PushButtonControl, AudioPrompt, RadioButtonControl, AudioMeterControl, \
    AudioRecordControl
from psynet.trial.audio import AudioRecordTrial
from psynet.timeline import CodeBlock, PageMaker, join, Event, Module, ProgressStage, ProgressDisplay
from psynet.js_synth import JSSynth, Note, Rest
from psynet.trial.static import StaticNode, StaticTrial, StaticTrialMaker
from psynet.trial import compile_nodes_from_directory

# singing
from .params import singing_2intervals
from sing4me import singing_extract as sing
from sing4me import melodies
from .melodies import convert_interval_sequence_to_absolute_pitches, sample_reference_pitch, sample_interval_sequence

roving_width = 2.5
roving_mean = dict(
    default=55,
    low=49,
    high=61
)

# volume test for tone js
def tonejs_volume_test(timbre, note_duration, note_silence, time_estimate_per_trial=5):
    return ModularPage(
        "tone_js_volume_test",
        JSSynth(
            Markup(
                """
                        <h3>Volume calibration</h3>
                        <hr>
                        Set the volume in your laptop to a level in which you can hear each note properly.
                        <hr>
                        """
            ),
            sequence=[
                Note(x)
                for x in convert_interval_sequence_to_absolute_pitches(
                    intervals=sample_interval_sequence(
                        n_int=11,
                        max_interval_size=8.5,
                        max_melody_pitch_range=99,
                        discrete=False,
                        reference_mode="first_note",
                    ),
                    reference_pitch=sample_reference_pitch(55, 2.5),
                    reference_mode="first_note",
                )
            ],
            timbre=timbre,
            default_duration=note_duration,
            default_silence=note_silence,
        ),
        time_estimate=time_estimate_per_trial,
        events={
            "restartMelody": Event(
                is_triggered_by="promptEnd",
                delay=1.0,
                js="psynet.trial.restart()"
            ),
            "submitEnable": Event(is_triggered_by="trialStart", delay=5)
        }
    )


# self-report questions for input and output
def audio_output_question():
    return ModularPage(
        "audio_output",
        prompt="What are you using to play sound?",
        control=RadioButtonControl(
            choices=["headphones", "earphones", "internal_speakers", "external_speakers"],
            labels=[
                "Headphones",
                "Earphones",
                "Internal computer speakers",
                "External computer speakers",
            ],
            show_free_text_option=True,
        ),
        time_estimate=7.5,
        save_answer="audio_output"
    )


def audio_input_question():
    return ModularPage(
        "audio_input",
        prompt="What are you using to record sound?",
        control=RadioButtonControl(
            choices=["headphones", "earphones", "internal_microphone", "external_microphone"],
            labels=[
                "Headphone microphone",
                "Earphone microphone",
                "A microphone inside your computer",
                "An external microphone attached to your computer",
            ],
            show_free_text_option=True,
        ),
        time_estimate=7.5,
        save_answer="audio_input"
    )


# microphone test (optimized for singing)
class SingingTestControl(AudioMeterControl):
    # adjust default parameters to work nicely with voice
    decay = {"display": 0.1, "high": 0.1, "low": 0.1}
    threshold = {"high": -3, "low": -22}  #
    grace = {"high": 0.2, "low": 1.5}
    warn_on_clip = False
    msg_duration = {"high": 0.25, "low": 0.25}


def mic_test():
    html = tags.div()

    with html:
        tags.p(
            "Please try singing into the microphone. If your microphone is set up correctly, "
            "you should see the audio meter move. If it is not working, please update your audio settings and "
            "try again."
        )

        with tags.div():
            tags.attr(cls="alert alert-primary")
            tags.p(tags.ul(
                tags.li("If you see a dialog box requesting microphone permissions, please click 'Accept'."),
                tags.li("You can refresh the page if you like."),
            ))

    return ModularPage(
        "mic_test",
        html,
        SingingTestControl(),
        events={"submitEnable": Event(is_triggered_by="trialStart", delay=5)},
        time_estimate=10,
    )


# singing familiarization
def recording_example():
    return join(
        InfoPage(
            Markup(
                f"""
                <h3>Recording Example</h3>
                <hr>
                First, we will test if you can record your voice with the computer microphone. 
                <br><br>
                When ready, go to the next page and <b><b>sing 2 notes</b></b> using the syllable 'TA'.<br>
                (separate each note with a silence). 
                <hr>
                """
            ),
            time_estimate=5,
        ),
        ModularPage(
            "singing_record_example",
            Markup(
                f"""
                <h3>Recording Example</h3>
                Sing 2 notes to the syllable 'TA'<br> 
                <i>Leave a silent gap between the notes</i>
                """
            ),
            AudioRecordControl(
                duration=5.0,
                show_meter=True,
                controls=False,
                auto_advance=False,
            ),
            time_estimate=5,
            progress_display=ProgressDisplay(
                stages=[
                    ProgressStage(5, "Recording.. Sing 2 notes!", "red"),
                ],
            ),
        ),
        wait_while(
            lambda participant: not participant.assets["singing_record_example"].deposited,
            expected_wait=5.0,
            log_message="Waiting for the recording to finish uploading",
        ),
        PageMaker(
            lambda participant: ModularPage(
                "playback",
                AudioPrompt(
                    participant.assets["singing_record_example"],
                    Markup(
                        """
                        <h3>Can you hear your recording?</h3>
                        <hr>
                        If you do not hear your recording, please make sure
                        to use a working microphone so we can record your voice and continue with the experiment. 
                        <hr>
                        """
                    ),
                ),
            ),
            time_estimate=5,
        ),
    )


# singing performance: feedback + test
# TODO: performance test: feedback + mini test + perforamnce test

nodes_singing_performance = [
    StaticNode(
        definition={
            "interval": interval,
            "target_pitches": melodies.convert_interval_sequence_to_absolute_pitches(
                intervals=[interval],
                reference_pitch=melodies.sample_reference_pitch(
                    roving_mean[register],
                    roving_width
                ),
                reference_mode="previous_note",
            ),
        },
    )
    for interval in [-1.3, -2.6, 0.0, 1.3, 2.6]
    for register in ["low", "high"]
]


practice = InfoPage(
    Markup(
        f"""
        <h3>Singing practice</h3>
        <hr>
        In each trial, you will hear a melody with 2 notes:<br>
        <b><b>Your goal is to sing each note back as accurately as possible.</b></b><br>
        <i>Important:</i> Use the syllable 'TA' to sing each note and leave a silent gap between notes.
        <br><br>
        We will analyse your recording and provide feedback.
        <hr>
        When ready, click <b><b>next</b></b> to start singing.
        """
    ),
    time_estimate=5,
)
