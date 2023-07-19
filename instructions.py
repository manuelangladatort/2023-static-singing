from flask import Markup
from dominate import tags
from psynet.page import InfoPage


html = tags.div()

with html:
    tags.p(
        """
        In this experiment, you will hear melodies and be asked to sing them back as accurately as possible.
        """
    )

    tags.p(
        """
        We will monitor your responses throughout the experiment, and will give a small additional bonus
        if your performance is good. 
        """
    )

    tags.p(
        """
        Press 'Next' when you are ready to continue.
        """
    )


def instructions():
    return InfoPage(html, time_estimate=15)


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
