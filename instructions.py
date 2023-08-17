from flask import Markup
from psynet.page import InfoPage


def instructions():
    return InfoPage(
        Markup(
            """
            <h3>Welcome</h3>
            <hr>
            In this experiment, you will hear melodies and be asked to sing them back as accurately as possible.
            <br><br>
            We will monitor your responses throughout the experiment, and will give a small additional bonus
            if your performance is good. 
            <br><br>
            Press <b><b>next</b></b> when you are ready to start.
            <hr>
            """
        ),
        time_estimate=3
    )


def requirements():
    return InfoPage(
        Markup(
            """
            <h3>Requirements</h3>
            <hr>
            <b><b>For this experiment we need you to use headphones or earplugs with a working microphone</b></b>. 
            <br><br>
            However, we ask that you do not wear wireless headphones/earphones (e.g. EarPods),
            they often introduce recording issues.
            <br><br>
            If you are not able to satisfy these requirements currently, please try again later.
            <hr>
            """
        ),
        time_estimate=3
    )
