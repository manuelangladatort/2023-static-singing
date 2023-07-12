from dominate import tags

from psynet.page import InfoPage

html = tags.div()

with html:
    tags.p(
        """
        In the main part of this experiment you will [EXPLAIN TASK]
        """
    )

    tags.p(
        """
        We will monitor the answers you give throughout the experiment, and will give a small additional bonus
        if you give high-quality and reliable responses. 
        """
    )

    tags.p(
        """
        Press 'Next' when you are ready to continue.
        """
    )

def instructions():
    return InfoPage(html, time_estimate=15)
