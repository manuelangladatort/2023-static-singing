from flask import Markup

from dominate import tags

from psynet.page import InfoPage, ModularPage
from psynet.modular_page import PushButtonControl, AudioPrompt, RadioButtonControl, AudioMeterControl
from psynet.timeline import CodeBlock, PageMaker, join, Event, Module
from psynet.js_synth import JSSynth, Note
from .melodies import convert_interval_sequence_to_absolute_pitches, sample_reference_pitch, sample_interval_sequence


# common pre-screens used in singing experiments
def volume_calibration(timbre, note_duration, note_silence, time_estimate_per_trial=5):
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
                                n_int=99,
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
                time_estimate=time_estimate_per_trial
                )


def volume_calibration_page(audio, min_time=5, time_estimate=5.0):
    text = tags.div()
    with text:
        tags.p(
            """
            Please listen to the following melody and adjust your
            computer's output volume until it is at a comfortable level.
            """
        )
        tags.p(
            """
            If you can't hear anything, there may be a problem with your
            playback configuration or your internet connection.
            You can refresh the page to try loading the audio again.
            """
        )

    return ModularPage(
        "volume_calibration",
        AudioPrompt(audio, text, loop=True),
        events={
            "submitEnable": Event(is_triggered_by="trialStart", delay=min_time),
        },
        time_estimate=time_estimate,
    )


def requirements():
    html = tags.div()
    with html:
        tags.p(
            "For this experiment we need to you to be sitting in a quiet room with a good internet connection. "
            "If you can, please wear headphones or earphones for the best experience; "
            "however, we ask that you do not wear wireless headphones/earphones (e.g. EarPods), "
            "because they often introduce recording issues. "
            "If you are not able to satisfy these requirements currently, please try again later."
        )

    return InfoPage(html, time_estimate=15)


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
        AudioMeterControl(),
        time_estimate=10,
    )


def get_voice_type():
    return Module(
        "get_voice_type",
        ModularPage(
            "get_voice_type",
            tags.p(
                "We'd like to play chords that fill well with your vocal range. ",
                "What voice type best describes you?"
            ),
            PushButtonControl(
                choices=["low", "high"],
                labels=[
                    "High (or female) voice",
                    "Low (or male) voice",
                ],
            ),
            time_estimate=5,
            save_answer="voice_type"
        ),
        CodeBlock(lambda participant: participant.var.set(
            "register",
            participant.var.voice_type,
            )
        )
    )
